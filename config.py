"""
INDECLOW by AxeroAI
Configuration Module
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ── Telegram ──────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Ollama ────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── ngrok ─────────────────────────────────────────
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "")

# ── Directories ───────────────────────────────────
PROJECTS_DIR = BASE_DIR / os.getenv("PROJECTS_DIR", "projects")
SKILLS_DIR = BASE_DIR / os.getenv("SKILLS_DIR", "skills")
LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "logs")
PROMPTS_DIR = BASE_DIR / "prompts"
TOOLS_DIR = BASE_DIR / "tools"

# Create dirs if missing
for d in [PROJECTS_DIR, SKILLS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Agent Settings ────────────────────────────────
MAX_LLM_RETRIES = int(os.getenv("MAX_LLM_RETRIES", "3"))
TERMINAL_TIMEOUT = int(os.getenv("TERMINAL_TIMEOUT", "60"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# ── Safe Command Whitelist ────────────────────────
SAFE_COMMANDS = [
    "ls", "pwd", "echo", "mkdir", "touch", "cp", "mv",
    "npm", "npx", "node", "python", "python3", "pip",
    "pip3", "git", "curl", "wget", "cat", "find",
    "grep", "sed", "awk", "head", "tail", "wc",
    "chmod", "chown", "zip", "unzip", "tar",
    "which", "env", "export", "source",
]

BLOCKED_COMMANDS = [
    "rm -rf /", "sudo rm", "dd if=", "mkfs",
    ":(){ :|:& };:", "chmod 777 /", "> /dev/sda",
    "shutdown", "reboot", "halt", "poweroff",
]

# ── Version ───────────────────────────────────────
VERSION = "1.0.0"
SYSTEM_NAME = "INDECLOW"
BRAND = "AxeroAI"
