"""
INDECLOW by AxeroAI
💻 Terminal Agent — Safe command execution with logging
"""

import subprocess
import shlex
import os
import platform
from pathlib import Path
from typing import Tuple, Optional, List
from config import SAFE_COMMANDS, BLOCKED_COMMANDS, TERMINAL_TIMEOUT
from utils.logger import logger


class TerminalAgent:
    """
    💻 Terminal Agent
    Executes shell commands safely with whitelist validation,
    logging, and output capture.
    """

    def __init__(self):
        self.command_log: List[dict] = []
        self.current_dir = Path.cwd()

    def is_safe(self, command: str) -> Tuple[bool, str]:
        cmd_lower = command.lower().strip()

        for blocked in BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False, f"Blocked pattern: `{blocked}`"

        # Extract base command
        try:
            parts = shlex.split(command)
        except ValueError:
            return False, "Invalid command syntax"

        if not parts:
            return False, "Empty command"

        base = parts[0].split("/")[-1]  # handle /usr/bin/python → python

        if base in SAFE_COMMANDS:
            return True, "OK"

        # Allow if it's a relative script execution
        if base.endswith(".py") or base.endswith(".sh") or base.endswith(".js"):
            return True, "Script execution"

        # Allow common dev patterns
        allowed_patterns = ["npm", "npx", "node", "python", "python3", "pip", "pip3", "git"]
        for p in allowed_patterns:
            if base.startswith(p):
                return True, "Dev tool"

        return False, f"Command `{base}` is not in the safe command whitelist"

    def run(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
        allow_unsafe: bool = False,
    ) -> Tuple[bool, str, str]:
        """
        Execute a command.
        Returns (success, stdout, stderr)
        """
        safe, reason = self.is_safe(command)
        if not safe and not allow_unsafe:
            msg = f"🚫 BLOCKED: {reason}"
            logger.warning(msg)
            return False, "", msg

        work_dir = str(cwd or self.current_dir)
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        logger.info(f"💻 EXEC: {command} (cwd={work_dir})")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=TERMINAL_TIMEOUT,
                env=exec_env,
            )

            success = result.returncode == 0
            self.command_log.append({
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
            })

            if not success:
                logger.warning(f"Command failed (rc={result.returncode}): {result.stderr[:200]}")
            else:
                logger.info(f"Command succeeded: {result.stdout[:100]}")

            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            msg = f"⏱️ Command timed out after {TERMINAL_TIMEOUT}s: {command}"
            logger.error(msg)
            return False, "", msg
        except Exception as e:
            msg = f"❌ Command error: {str(e)}"
            logger.error(msg)
            return False, "", msg

    def create_project_structure(self, project_dir: Path, structure: List[str]) -> bool:
        """Create directories and empty files for a project structure."""
        try:
            for path_str in structure:
                full_path = project_dir / path_str
                if path_str.endswith("/"):
                    full_path.mkdir(parents=True, exist_ok=True)
                else:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    if not full_path.exists():
                        full_path.touch()
            logger.info(f"Created project structure with {len(structure)} items")
            return True
        except Exception as e:
            logger.error(f"Structure creation failed: {e}")
            return False

    def install_npm_deps(self, project_dir: Path) -> Tuple[bool, str]:
        if (project_dir / "package.json").exists():
            success, out, err = self.run("npm install", cwd=project_dir)
            return success, out or err
        return True, "No package.json, skipping npm install"

    def install_pip_deps(self, project_dir: Path) -> Tuple[bool, str]:
        if (project_dir / "requirements.txt").exists():
            success, out, err = self.run(
                "pip install -r requirements.txt --break-system-packages",
                cwd=project_dir
            )
            return success, out or err
        return True, "No requirements.txt, skipping pip install"

    def start_http_server(self, project_dir: Path, port: int = 8080) -> Tuple[bool, str]:
        """Start Python's built-in HTTP server in background."""
        cmd = f"python3 -m http.server {port}"
        success, out, err = self.run(cmd, cwd=project_dir)
        return success, out or err

    def get_log(self) -> List[dict]:
        return self.command_log

    def clear_log(self) -> None:
        self.command_log.clear()
