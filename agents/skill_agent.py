"""
INDECLOW by AxeroAI
🧩 Skill Agent — Load and manage external skills from GitHub
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from config import SKILLS_DIR
from utils.ollama_client import ollama
from utils.logger import logger


class Skill:
    def __init__(self, name: str, source_url: str, description: str,
                 instructions: str, skill_dir: Path):
        self.name = name
        self.source_url = source_url
        self.description = description
        self.instructions = instructions
        self.skill_dir = skill_dir
        self.active = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_url": self.source_url,
            "description": self.description,
            "active": self.active,
        }


class SkillAgent:
    """
    🧩 Skill Agent
    Downloads GitHub repositories, reads their instructions,
    extracts capabilities, and activates them as system skills.
    """

    def __init__(self):
        self.loaded_skills: Dict[str, Skill] = {}
        self._load_existing_skills()

    def _load_existing_skills(self) -> None:
        registry = SKILLS_DIR / "registry.json"
        if registry.exists():
            try:
                data = json.loads(registry.read_text())
                for sname, sdata in data.items():
                    skill_dir = SKILLS_DIR / sname
                    if skill_dir.exists():
                        skill = Skill(
                            name=sname,
                            source_url=sdata.get("source_url", ""),
                            description=sdata.get("description", ""),
                            instructions=sdata.get("instructions", ""),
                            skill_dir=skill_dir,
                        )
                        skill.active = sdata.get("active", True)
                        self.loaded_skills[sname] = skill
                logger.info(f"Loaded {len(self.loaded_skills)} existing skills")
            except Exception as e:
                logger.error(f"Failed to load skill registry: {e}")

    def _save_registry(self) -> None:
        registry = SKILLS_DIR / "registry.json"
        data = {name: skill.to_dict() for name, skill in self.loaded_skills.items()}
        registry.write_text(json.dumps(data, indent=2))

    def extract_skill_name(self, repo_url: str) -> str:
        match = re.search(r"/([^/]+?)(?:\.git)?$", repo_url)
        return match.group(1).lower() if match else "unknown-skill"

    def clone_repo(self, repo_url: str, skill_name: str) -> Optional[Path]:
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists():
            shutil.rmtree(skill_dir)

        try:
            result = subprocess.run(
                ["git", "clone", "--depth=1", repo_url, str(skill_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                logger.info(f"Cloned skill repo: {repo_url} → {skill_dir}")
                return skill_dir
            else:
                logger.error(f"Git clone failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("Git clone timed out")
            return None
        except FileNotFoundError:
            logger.error("git not found — please install git")
            return None

    def read_skill_files(self, skill_dir: Path) -> str:
        """Read README, config, and instruction files from the skill repo."""
        content_parts = []
        priority_files = [
            "README.md", "readme.md", "INSTRUCTIONS.md",
            "SKILL.md", "config.json", "skill.json",
            "PROMPT.txt", "prompt.txt", "system.txt",
        ]

        for fname in priority_files:
            fpath = skill_dir / fname
            if fpath.exists():
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                content_parts.append(f"=== {fname} ===\n{text[:3000]}")

        if not content_parts:
            for fpath in skill_dir.rglob("*.md"):
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                content_parts.append(f"=== {fpath.name} ===\n{text[:2000]}")
                if len(content_parts) >= 3:
                    break

        return "\n\n".join(content_parts)

    def extract_instructions(self, raw_content: str, skill_name: str) -> str:
        """Use Ollama to extract key instructions from skill repo content."""
        prompt = f"""
A GitHub skill repository named "{skill_name}" has this content:
{raw_content[:4000]}

Extract the key instructions, rules, and capabilities for this skill.
Write a concise set of instructions (max 500 words) that INDECLOW should follow when this skill is active.
Focus on: what patterns to use, what to avoid, specific best practices.
"""
        return ollama.generate(prompt, temperature=0.3)

    def install(self, repo_url: str, progress_callback=None) -> Optional[Skill]:
        skill_name = self.extract_skill_name(repo_url)

        if progress_callback:
            progress_callback(f"📥 Downloading skill: `{skill_name}` from GitHub...")

        skill_dir = self.clone_repo(repo_url, skill_name)
        if not skill_dir:
            if progress_callback:
                progress_callback(f"❌ Failed to clone: {repo_url}")
            return None

        if progress_callback:
            progress_callback(f"📖 Reading skill documentation...")

        raw_content = self.read_skill_files(skill_dir)
        if not raw_content:
            raw_content = f"Skill: {skill_name} from {repo_url}"

        if progress_callback:
            progress_callback(f"🧠 Extracting skill instructions via Ollama...")

        instructions = self.extract_instructions(raw_content, skill_name)

        description_prompt = f"""
Based on this skill repository content:
{raw_content[:1000]}

Write a ONE sentence description of what this skill enables INDECLOW to do.
"""
        description = ollama.generate(description_prompt, temperature=0.3)

        skill = Skill(
            name=skill_name,
            source_url=repo_url,
            description=description.strip()[:200],
            instructions=instructions,
            skill_dir=skill_dir,
        )

        self.loaded_skills[skill_name] = skill
        self._save_registry()

        if progress_callback:
            progress_callback(f"✅ Skill `{skill_name}` installed and activated!")

        logger.info(f"Skill installed: {skill_name}")
        return skill

    def uninstall(self, skill_name: str) -> bool:
        if skill_name not in self.loaded_skills:
            return False
        skill = self.loaded_skills.pop(skill_name)
        if skill.skill_dir.exists():
            shutil.rmtree(skill.skill_dir)
        self._save_registry()
        logger.info(f"Skill uninstalled: {skill_name}")
        return True

    def toggle(self, skill_name: str) -> bool:
        if skill_name not in self.loaded_skills:
            return False
        skill = self.loaded_skills[skill_name]
        skill.active = not skill.active
        self._save_registry()
        return True

    def get_active_instructions(self) -> str:
        """Combine all active skill instructions for injection into prompts."""
        active = [s for s in self.loaded_skills.values() if s.active]
        if not active:
            return ""
        parts = [f"## Active Skill: {s.name}\n{s.instructions}" for s in active]
        return "\n\n".join(parts)

    def list_skills(self) -> List[dict]:
        return [
            {
                "name": name,
                "description": skill.description,
                "active": skill.active,
                "source": skill.source_url,
            }
            for name, skill in self.loaded_skills.items()
        ]

    def format_skills_list(self) -> str:
        skills = self.list_skills()
        if not skills:
            return "🧩 No skills installed yet.\n\nUse /skill <GitHub URL> to install one."
        lines = ["🧩 *Installed Skills*\n"]
        for s in skills:
            icon = "✅" if s["active"] else "⏸️"
            lines.append(f"{icon} `{s['name']}` — {s['description']}")
        return "\n".join(lines)
