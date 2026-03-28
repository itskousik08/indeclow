"""
INDECLOW by AxeroAI
File Utilities
"""

import os
import re
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from config import PROJECTS_DIR
from utils.logger import logger


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50]


def create_project_dir(project_name: str) -> Path:
    slug = slugify(project_name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    proj_dir = PROJECTS_DIR / f"{slug}_{ts}"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets").mkdir(exist_ok=True)
    (proj_dir / "components").mkdir(exist_ok=True)
    logger.info(f"Created project directory: {proj_dir}")
    return proj_dir


def save_file(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Saved file: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")
        return False


def update_file(path: Path, old_content: str, new_content: str) -> bool:
    """Partial file update — replaces only the matched section."""
    try:
        current = path.read_text(encoding="utf-8")
        if old_content not in current:
            logger.warning(f"Update target not found in {path}")
            return False
        updated = current.replace(old_content, new_content, 1)
        path.write_text(updated, encoding="utf-8")
        logger.info(f"Updated file: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update {path}: {e}")
        return False


def zip_project(project_dir: Path) -> Optional[Path]:
    try:
        zip_path = project_dir.parent / f"{project_dir.name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(project_dir.parent))
        logger.info(f"Zipped project: {zip_path}")
        return zip_path
    except Exception as e:
        logger.error(f"Failed to zip project: {e}")
        return None


def read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return None


def list_project_files(project_dir: Path) -> List[str]:
    files = []
    for f in project_dir.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(project_dir)))
    return sorted(files)


def save_project_manifest(project_dir: Path, metadata: dict) -> None:
    manifest = {
        "created_at": datetime.now().isoformat(),
        "indeclow_version": "1.0.0",
        **metadata,
    }
    save_file(project_dir / "indeclow_manifest.json", json.dumps(manifest, indent=2))


def extract_code_blocks(text: str) -> Dict[str, str]:
    """Extract filename→code from LLM output with fenced code blocks."""
    blocks = {}
    pattern = re.compile(
        r"(?:#+\s*(?:File:\s*)?`?(?P<fname1>[^\n`]+)`?\s*\n)?"
        r"```(?:\w+)?\s*\n(?:// (?P<fname2>[^\n]+)\n)?(?P<code>.*?)```",
        re.DOTALL,
    )
    for i, m in enumerate(pattern.finditer(text)):
        fname = m.group("fname1") or m.group("fname2") or f"file_{i+1}.txt"
        fname = fname.strip().strip("`").strip()
        code = m.group("code").strip()
        if fname and code:
            blocks[fname] = code

    if not blocks:
        raw = re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
        for i, code in enumerate(raw):
            blocks[f"output_{i+1}.txt"] = code.strip()

    return blocks
