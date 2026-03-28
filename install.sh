#!/usr/bin/env bash
# ╔══════════════════════════════════════╗
# ║   INDECLOW by AxeroAI               ║
# ║   Installation Script (Linux/macOS) ║
# ╚══════════════════════════════════════╝
set -e

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

banner() {
  echo ""
  echo -e "${CYAN}${BOLD}╔══════════════════════════════════════╗${RESET}"
  echo -e "${CYAN}${BOLD}║      INDECLOW by AxeroAI            ║${RESET}"
  echo -e "${CYAN}${BOLD}║   Autonomous Multi-Agent AI System  ║${RESET}"
  echo -e "${CYAN}${BOLD}╚══════════════════════════════════════╝${RESET}"
  echo ""
}

ok()   { echo -e "${GREEN}  ✅  $1${RESET}"; }
info() { echo -e "${CYAN}  ℹ️   $1${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠️   $1${RESET}"; }
fail() { echo -e "${RED}  ❌  $1${RESET}"; exit 1; }

banner

# ── Python check ──────────────────────────────────────────────────────────────
info "Checking Python version..."
if ! command -v python3 &>/dev/null; then
  fail "Python 3.10+ is required. Install from https://python.org"
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  fail "Python 3.10+ required. Found: $PY_VER"
fi
ok "Python $PY_VER found"

# ── Git check ─────────────────────────────────────────────────────────────────
info "Checking git..."
if ! command -v git &>/dev/null; then
  warn "git not found — skill installation will be disabled."
else
  ok "git found"
fi

# ── Virtual environment ───────────────────────────────────────────────────────
info "Creating virtual environment (.venv)..."
if [ -d ".venv" ]; then
  warn "Existing .venv found — removing and recreating..."
  rm -rf .venv
fi
python3 -m venv .venv
ok "Virtual environment created"

# ── Activate ──────────────────────────────────────────────────────────────────
info "Activating virtual environment..."
# shellcheck source=/dev/null
source .venv/bin/activate
ok "Virtual environment activated"

# ── Upgrade pip ───────────────────────────────────────────────────────────────
info "Upgrading pip..."
pip install --upgrade pip --quiet
ok "pip upgraded"

# ── Install dependencies ──────────────────────────────────────────────────────
info "Installing Python dependencies..."
pip install -r requirements.txt --quiet
ok "Dependencies installed"

# ── .env setup ───────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  info "Creating .env from .env.example..."
  cp .env.example .env
  ok ".env file created"
  warn "⚡ IMPORTANT: Edit .env and fill in your:"
  warn "   → TELEGRAM_BOT_TOKEN"
  warn "   → NGROK_AUTH_TOKEN (optional, for public URLs)"
  warn "   → OLLAMA_MODEL (default: llama3.2)"
else
  ok ".env already exists — skipping"
fi

# ── Ollama check ──────────────────────────────────────────────────────────────
echo ""
info "Checking Ollama..."
if command -v ollama &>/dev/null; then
  ok "Ollama found"
  OLLAMA_MODEL=$(grep "OLLAMA_MODEL" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo "llama3.2")
  info "Pulling model: $OLLAMA_MODEL (this may take a few minutes)..."
  if ollama pull "$OLLAMA_MODEL" 2>/dev/null; then
    ok "Model '$OLLAMA_MODEL' ready"
  else
    warn "Could not pull '$OLLAMA_MODEL'. Make sure Ollama is running: ollama serve"
  fi
else
  warn "Ollama not found. Install from: https://ollama.com"
  warn "After installing, run: ollama serve && ollama pull llama3.2"
fi

# ── Create directories ────────────────────────────────────────────────────────
info "Creating project directories..."
mkdir -p projects skills logs
ok "Directories ready"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║   ✅  Installation Complete!         ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${RESET}"
echo ""
echo -e "${BOLD}Next steps:${RESET}"
echo ""
echo -e "  1. ${CYAN}Edit your .env file:${RESET}"
echo -e "     nano .env"
echo ""
echo -e "  2. ${CYAN}Start Ollama (in a separate terminal):${RESET}"
echo -e "     ollama serve"
echo ""
echo -e "  3. ${CYAN}Run INDECLOW:${RESET}"
echo -e "     source .venv/bin/activate && python main.py"
echo ""
echo -e "  ${YELLOW}Telegram Bot Commands:${RESET}"
echo -e "     /start   → Start a new project"
echo -e "     /skill   → Install a GitHub skill"
echo -e "     /update  → Update your project"
echo -e "     /deploy  → Refresh live preview"
echo -e "     /help    → Show all commands"
echo ""
echo -e "  ${CYAN}Powered by INDECLOW — AxeroAI${RESET}"
echo ""
