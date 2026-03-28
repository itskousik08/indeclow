"""
INDECLOW by AxeroAI
🔄 Update Agent — Performs targeted partial file updates
"""

from pathlib import Path
from typing import Optional, Dict, List
from utils.ollama_client import ollama
from utils.file_utils import read_file, save_file, update_file
from utils.logger import logger


class UpdateAgent:
    """
    🔄 Update Agent
    Applies intelligent, partial updates to existing project files.
    NEVER rewrites the full project — only changes what's needed.
    """

    SYSTEM_PROMPT = """You are INDECLOW's Update Agent by AxeroAI.
You receive an existing file and an update request. Apply ONLY the requested change.

Rules:
- Return the COMPLETE updated file (not just the changed part)
- Preserve ALL existing code, styles, and structure
- Only modify the specific section requested
- Maintain the same code style and formatting
- Do not add unrequested features
- Do not remove existing functionality
"""

    def identify_target_file(
        self, project_dir: Path, update_request: str
    ) -> Optional[Path]:
        """Find which file needs to be updated based on the request."""
        files = list(project_dir.rglob("*"))
        file_list = "\n".join(str(f.relative_to(project_dir)) for f in files if f.is_file())

        prompt = f"""
Project files:
{file_list}

Update request: "{update_request}"

Which single file should be updated? Reply with ONLY the filename (e.g. "index.html" or "style.css").
"""
        response = ollama.generate(prompt, temperature=0.1)
        target = response.strip().strip("`").strip('"').strip("'")

        # Search for it
        for f in files:
            if f.is_file() and target in str(f):
                return f

        # Fallback: guess from keywords
        lower = update_request.lower()
        if any(w in lower for w in ["color", "style", "font", "layout", "css"]):
            for f in files:
                if f.suffix == ".css":
                    return f
        if any(w in lower for w in ["click", "button", "function", "script", "js"]):
            for f in files:
                if f.suffix == ".js":
                    return f
        if any(w in lower for w in ["html", "content", "text", "heading", "section"]):
            for f in files:
                if f.suffix == ".html":
                    return f

        return None

    def apply_update(
        self,
        project_dir: Path,
        update_request: str,
        progress_callback=None,
    ) -> Dict[str, any]:
        result = {"success": False, "file": None, "changes": []}

        if progress_callback:
            progress_callback(f"🔄 Identifying target file...")

        target_file = self.identify_target_file(project_dir, update_request)

        if not target_file:
            result["error"] = "Could not identify which file to update"
            return result

        rel_name = str(target_file.relative_to(project_dir))
        if progress_callback:
            progress_callback(f"🎯 Updating `{rel_name}`...")

        current_content = read_file(target_file)
        if not current_content:
            result["error"] = f"Could not read {rel_name}"
            return result

        prompt = f"""
File: {rel_name}
Current content:
{current_content}

Update request: "{update_request}"

Apply ONLY this update and return the complete updated file.
"""
        updated_content = ollama.generate(
            prompt, system=self.SYSTEM_PROMPT, temperature=0.3
        )

        if not updated_content or len(updated_content) < 50:
            result["error"] = "LLM returned empty/invalid update"
            return result

        if save_file(target_file, updated_content):
            result["success"] = True
            result["file"] = rel_name
            result["changes"].append(f"Updated `{rel_name}` per request")
            if progress_callback:
                progress_callback(f"✅ `{rel_name}` updated successfully!")
            logger.info(f"Update Agent: updated {rel_name}")
        else:
            result["error"] = f"Failed to save {rel_name}"

        return result

    def apply_multiple_updates(
        self,
        project_dir: Path,
        updates: List[str],
        progress_callback=None,
    ) -> List[dict]:
        results = []
        for update in updates:
            r = self.apply_update(project_dir, update, progress_callback)
            results.append(r)
        return results
