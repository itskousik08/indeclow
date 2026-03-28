@echo off
:: ╔══════════════════════════════════════╗
:: ║   INDECLOW by AxeroAI               ║
:: ║   Installation Script (Windows)     ║
:: ╚══════════════════════════════════════╝

title INDECLOW Installer — AxeroAI

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      INDECLOW by AxeroAI            ║
echo  ║   Autonomous Multi-Agent AI System  ║
echo  ╚══════════════════════════════════════╝
echo.

:: ── Python check ─────────────────────────────────────────────────────────────
echo [*] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required.
    echo         Download from: https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER% found

:: ── Git check ─────────────────────────────────────────────────────────────────
echo [*] Checking git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] git not found — skill installation will be disabled.
    echo        Install from: https://git-scm.com
) else (
    echo [OK] git found
)

:: ── Virtual environment ───────────────────────────────────────────────────────
echo [*] Creating virtual environment (.venv)...
if exist .venv (
    echo [*] Removing existing .venv...
    rmdir /s /q .venv
)
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

:: ── Activate ──────────────────────────────────────────────────────────────────
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat
echo [OK] Activated

:: ── Upgrade pip ───────────────────────────────────────────────────────────────
echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded

:: ── Install dependencies ──────────────────────────────────────────────────────
echo [*] Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: ── .env setup ───────────────────────────────────────────────────────────────
if not exist .env (
    echo [*] Creating .env from .env.example...
    copy .env.example .env >nul
    echo [OK] .env file created
    echo.
    echo  [!] IMPORTANT: Edit .env and fill in your:
    echo      - TELEGRAM_BOT_TOKEN
    echo      - NGROK_AUTH_TOKEN  ^(optional, for public URLs^)
    echo      - OLLAMA_MODEL      ^(default: llama3.2^)
    echo.
) else (
    echo [OK] .env already exists — skipping
)

:: ── Ollama check ──────────────────────────────────────────────────────────────
echo [*] Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not found.
    echo        Install from: https://ollama.com
    echo        After installing, run: ollama serve ^&^& ollama pull llama3.2
) else (
    echo [OK] Ollama found
    echo [*] Pulling model llama3.2 ^(this may take a few minutes^)...
    ollama pull llama3.2
)

:: ── Create directories ────────────────────────────────────────────────────────
echo [*] Creating project directories...
if not exist projects mkdir projects
if not exist skills  mkdir skills
if not exist logs    mkdir logs
echo [OK] Directories ready

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   [OK]  Installation Complete!       ║
echo  ╚══════════════════════════════════════╝
echo.
echo  Next steps:
echo.
echo  1. Edit your .env file:
echo     notepad .env
echo.
echo  2. Start Ollama ^(in a separate terminal^):
echo     ollama serve
echo.
echo  3. Run INDECLOW:
echo     .venv\Scripts\activate ^&^& python main.py
echo.
echo  Telegram Bot Commands:
echo     /start   - Start a new project
echo     /skill   - Install a GitHub skill
echo     /update  - Update your project
echo     /deploy  - Refresh live preview
echo     /help    - Show all commands
echo.
echo  Powered by INDECLOW - AxeroAI
echo.
pause
