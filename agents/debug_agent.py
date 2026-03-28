"""
INDECLOW by AxeroAI
🐞 Debug Agent — Detects and auto-fixes errors in generated code
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from utils.ollama_client import ollama
from utils.file_utils import read_file, save_file
from utils.logger import logger


class DebugAgent:
    """
    🐞 Debug Agent
    Validates generated files, detects common errors,
    and uses Ollama to auto-fix issues.
    """

    SYSTEM_PROMPT = """You are INDECLOW's Debug Agent by AxeroAI.
You receive code that may contain bugs or issues. Fix them and return the corrected code.

Rules:
- Return ONLY the fixed code, nothing else
- Do not add explanations or comments
- Preserve the original intent and style
- Fix syntax errors, missing closing tags, broken CSS, undefined variables
- Ensure all file references (src, href, link) are consistent
"""

    def validate_html(self, content: str) -> List[str]:
        issues = []
        if "<!DOCTYPE html>" not in content:
            issues.append("Missing <!DOCTYPE html>")
        if "<html" not in content:
            issues.append("Missing <html> tag")
        if "</html>" not in content:
            issues.append("Missing closing </html>")
        if "<head>" not in content and "<head " not in content:
            issues.append("Missing <head> section")
        if "<body>" not in content and "<body " not in content:
            issues.append("Missing <body> section")

        # Check for unclosed common tags
        for tag in ["div", "section", "nav", "footer", "header", "main", "ul", "ol"]:
            opens = len(re.findall(f"<{tag}[\\s>]", content, re.IGNORECASE))
            closes = len(re.findall(f"</{tag}>", content, re.IGNORECASE))
            if opens != closes:
                issues.append(f"Unclosed <{tag}> tags: {opens} open, {closes} close")

        return issues

    def validate_css(self, content: str) -> List[str]:
        issues = []
        open_braces = content.count("{")
        close_braces = content.count("}")
        if open_braces != close_braces:
            issues.append(f"CSS brace mismatch: {open_braces} open, {close_braces} close")
        return issues

    def validate_js(self, content: str) -> List[str]:
        issues = []
        open_parens = content.count("(")
        close_parens = content.count(")")
        if abs(open_parens - close_parens) > 2:
            issues.append(f"Possible unmatched parentheses: {open_parens} open, {close_parens} close")

        open_braces = content.count("{")
        close_braces = content.count("}")
        if abs(open_braces - close_braces) > 2:
            issues.append(f"Possible unmatched braces: {open_braces} open, {close_braces} close")

        return issues

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        content = read_file(file_path)
        if not content:
            return False, ["File is empty or unreadable"]

        ext = file_path.suffix.lower()
        issues = []

        if ext == ".html":
            issues = self.validate_html(content)
        elif ext == ".css":
            issues = self.validate_css(content)
        elif ext == ".js":
            issues = self.validate_js(content)

        return len(issues) == 0, issues

    def fix_file(self, file_path: Path, issues: List[str]) -> bool:
        content = read_file(file_path)
        if not content:
            return False

        issues_str = "\n".join(f"- {i}" for i in issues)
        prompt = f"""
File: {file_path.name}
Issues found:
{issues_str}

Original code:
{content}

Return ONLY the fixed, complete code with all issues resolved.
"""
        logger.info(f"Debug Agent fixing {file_path.name}: {len(issues)} issues")
        fixed = ollama.generate(prompt, system=self.SYSTEM_PROMPT, temperature=0.2)

        if fixed and len(fixed) > 50:
            return save_file(file_path, fixed)
        return False

    def debug_project(
        self, project_dir: Path, progress_callback=None
    ) -> Dict[str, dict]:
        results = {}
        target_exts = {".html", ".css", ".js", ".py", ".ts"}

        for file_path in project_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in target_exts:
                valid, issues = self.validate_file(file_path)
                rel_name = str(file_path.relative_to(project_dir))

                if not valid and issues:
                    if progress_callback:
                        progress_callback(f"🐞 Found {len(issues)} issue(s) in `{rel_name}`, fixing...")
                    fixed = self.fix_file(file_path, issues)
                    results[rel_name] = {
                        "issues": issues,
                        "fixed": fixed,
                        "status": "fixed" if fixed else "unfixed",
                    }
                    if progress_callback:
                        icon = "✅" if fixed else "⚠️"
                        progress_callback(f"{icon} `{rel_name}`: {'fixed' if fixed else 'could not auto-fix'}")
                else:
                    results[rel_name] = {"issues": [], "fixed": True, "status": "clean"}

        total = len(results)
        issues_found = sum(1 for r in results.values() if r["status"] != "clean")
        logger.info(f"Debug scan: {total} files, {issues_found} with issues")
        return results

    def format_debug_report(self, results: dict) -> str:
        lines = ["🐞 **Debug Report**\n"]
        for fname, info in results.items():
            if info["status"] == "clean":
                lines.append(f"✅ `{fname}` — clean")
            elif info["status"] == "fixed":
                lines.append(f"🔧 `{fname}` — {len(info['issues'])} issue(s) fixed")
            else:
                lines.append(f"⚠️ `{fname}` — {len(info['issues'])} issue(s) could not be auto-fixed")
                for issue in info["issues"][:3]:
                    lines.append(f"   → {issue}")
        return "\n".join(lines)
