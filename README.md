<div align="center">

```
╔══════════════════════════════════════════════╗
║         INDECLOW by AxeroAI                 ║
║   Autonomous Multi-Agent AI System          ║
╚══════════════════════════════════════════════╝
```

**An autonomous AI software engineer that builds, updates, and deploys projects via Telegram — powered entirely by local LLMs through Ollama.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-orange)](https://ollama.com)
[![Telegram](https://img.shields.io/badge/Bot-Telegram-2CA5E0)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

</div>

---

## ✨ What is INDECLOW?

INDECLOW (**IN**telligent **DE**velopment **C**ontroller with **L**LM-powered **O**rchestration **W**orkflow) is a fully autonomous AI development system by **AxeroAI** that:

- 💬 Listens to your requests via **Telegram**
- 🧠 Asks smart questions **before** building anything
- 🤖 Uses **11 specialized AI agents** to plan, build, debug, and deploy
- 🔋 Runs on **local LLMs** via Ollama — no cloud API keys needed
- 🌐 Generates **live preview URLs** via ngrok
- 📦 Delivers your project as a **ZIP file** in Telegram
- 🧩 Learns new capabilities from **GitHub skill repositories**

---

## 🤖 Multi-Agent Architecture

| Agent | Role |
|-------|------|
| 🧠 **Requirement Agent** | Asks ALL questions before building. Never assumes. |
| 📋 **Planner Agent** | Converts requirements into a step-by-step execution plan. |
| 🏗️ **Architect Agent** | Designs modular, scalable project structures. |
| 🎨 **Developer Agent** | Generates complete, production-grade HTML/CSS/JS/Python code. |
| 💻 **Terminal Agent** | Executes safe shell commands with whitelist validation. |
| 🐞 **Debug Agent** | Scans generated files and auto-fixes detected issues. |
| 🌐 **Deployment Agent** | Starts HTTP server + creates public ngrok URL. |
| 📩 **Communication Agent** | Sends real-time progress updates via Telegram. |
| 🔄 **Update Agent** | Applies targeted partial updates — never rewrites full projects. |
| 🧩 **Skill Agent** | Downloads and activates skills from GitHub repositories. |

---

## 📋 Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Ollama | Latest |
| Git | Any |
| Telegram Bot Token | From @BotFather |
| ngrok Auth Token | From dashboard.ngrok.com *(optional)* |

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/axeroai/indeclow.git
cd indeclow
```

### 2. Run the Installer

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
install.bat
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env   # or: notepad .env on Windows
```

Fill in:
```env
TELEGRAM_BOT_TOKEN=your_token_here      # from @BotFather
NGROK_AUTH_TOKEN=your_token_here         # from dashboard.ngrok.com
OLLAMA_MODEL=llama3.2                    # or any Ollama model
```

### 4. Start Ollama

In a separate terminal:
```bash
ollama serve
ollama pull llama3.2
```

### 5. Run INDECLOW

```bash
# Linux/macOS
source .venv/bin/activate
python main.py

# Windows
.venv\Scripts\activate
python main.py
```

You'll see:
```
╔══════════════════════════════════════════════╗
║         INDECLOW by AxeroAI                 ║
╚══════════════════════════════════════════════╝
✅ Bot connected: @YourBotName
🚀 INDECLOW is LIVE — waiting for Telegram messages...
```

---

## 💬 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/start <request>` | Start building immediately |
| `/update <changes>` | Apply targeted changes to your project |
| `/deploy` | Regenerate live preview URL |
| `/skill <GitHub URL>` | Install a skill from GitHub |
| `/skills` | List all installed skills |
| `/status` | Check current build status |
| `/logs` | View terminal command logs |
| `/cancel` | Cancel current operation |
| `/help` | Show help message |

---

## 🏗️ How It Works

### Building a Project

```
You: Create a portfolio website for a photographer

INDECLOW: 🧠 Requirement Agent activated!
          I detected you want to build a Portfolio project.
          Total questions: 8

          ❓ Question 1/8
          What is your full name?

You: Jane Smith

INDECLOW: ❓ Question 2/8
          What sections do you want?

You: About, Gallery, Contact

[... answers 8 questions ...]

INDECLOW: ✅ All requirements collected!
          📋 Creating your build plan...

          📋 Build Plan: Jane Smith Portfolio
          🛠️ Stack: html, css, js
          📌 Steps: 6
          
          🎨 Step 1: Build HTML structure
          🎨 Step 2: Add CSS styling
          🎨 Step 3: Add JavaScript
          🐞 Step 4: Debug and validate
          🌐 Step 5: Deploy

          🚀 Build Started!

          ✅ Generated: index.html
          ✅ Generated: style.css
          ✅ Generated: script.js
          
          🌐 Project is LIVE!
          Preview: https://abc123.ngrok.io

          [sends ZIP file]
```

### Updating a Project

```
You: /update change the background color to dark navy blue

INDECLOW: 🔄 Update Agent activated
          🎯 Updating style.css...
          ✅ style.css updated successfully!
```

### Installing a Skill

```
You: /skill https://github.com/user/react-expert-skill

INDECLOW: 📥 Downloading skill: react-expert-skill...
          📖 Reading skill documentation...
          🧠 Extracting skill instructions via Ollama...
          ✅ Skill react-expert-skill installed and activated!
```

---

## 📁 Project Structure

```
indeclow/
├── main.py                    # Entry point: terminal UI + Telegram bot
├── config.py                  # All configuration settings
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── install.sh                 # Linux/macOS installer
├── install.bat                # Windows installer
├── .gitignore
│
├── agents/                    # All 10 specialized agents
│   ├── requirement_agent.py   # 🧠 Question-gathering engine
│   ├── planner_agent.py       # 📋 Execution plan generator
│   ├── developer_agent.py     # 🎨 Code generation (HTML/CSS/JS)
│   ├── terminal_agent.py      # 💻 Safe command execution
│   ├── debug_agent.py         # 🐞 Error detection & auto-fix
│   ├── deployment_agent.py    # 🌐 ngrok + HTTP server
│   ├── communication_agent.py # 📩 Telegram messaging
│   ├── skill_agent.py         # 🧩 GitHub skill installer
│   └── update_agent.py        # 🔄 Partial file updater
│
├── core/
│   ├── agent_manager.py       # Agent registry & singleton manager
│   └── controller.py          # Full pipeline orchestration
│
├── tools/
│   └── tools.json             # Tool definitions (AxeroAI branded)
│
├── prompts/
│   ├── system_prompt.txt      # Core INDECLOW system prompt
│   └── prompt.txt             # Rebranded operational prompt
│
├── utils/
│   ├── logger.py              # Rich console + file logging
│   ├── ollama_client.py       # Ollama API wrapper
│   └── file_utils.py          # File I/O, ZIP, code extraction
│
├── projects/                  # Generated project output (gitignored)
├── skills/                    # Installed skill repos (gitignored)
└── logs/                      # Runtime logs (gitignored)
```

---

## 🧩 Skill System

INDECLOW can learn new capabilities from GitHub repositories:

```bash
/skill https://github.com/user/react-expert-skill
/skill https://github.com/user/tailwind-master
/skill https://github.com/user/fastapi-patterns
```

**How it works:**
1. Clones the GitHub repository
2. Reads `README.md`, `INSTRUCTIONS.md`, `SKILL.md`, `config.json`
3. Uses Ollama to extract capability instructions
4. Activates the skill for all future builds

**Skill stays active** until you uninstall it. Skills influence how the Developer Agent generates code.

---

## 🔐 Security

- **Safe command whitelist** — only pre-approved commands run via Terminal Agent
- **Blocked patterns** — destructive commands (`rm -rf /`, etc.) are rejected
- **No cloud API keys** — all LLM inference runs locally via Ollama
- **Sandboxed projects** — all builds go to `./projects/` directory
- **No secret logging** — environment variables never appear in logs

---

## 🛠️ Supported LLM Models (Ollama)

| Model | Size | Recommended For |
|-------|------|----------------|
| `llama3.2` | 2GB | Default — fast and capable |
| `llama3.1:8b` | 4.7GB | Better code quality |
| `codellama:13b` | 7.4GB | Best for complex code |
| `mistral` | 4.1GB | Good balance |
| `deepseek-coder` | 4.2GB | Excellent for coding |

Change model in `.env`:
```env
OLLAMA_MODEL=codellama:13b
```

---

## 🌐 Live Preview Setup (ngrok)

1. Sign up at [dashboard.ngrok.com](https://dashboard.ngrok.com)
2. Copy your authtoken
3. Add to `.env`:
```env
NGROK_AUTH_TOKEN=your_token_here
```

Without ngrok, INDECLOW will provide a local `http://localhost:PORT` URL instead.

---

## 🔧 Telegram Bot Setup

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow prompts
3. Copy the bot token
4. Add to `.env`:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## 📄 License

MIT License — Copyright (c) 2024 AxeroAI

---

<div align="center">

**Built with ❤️ by [AxeroAI](https://axeroai.com)**

*INDECLOW — Think before you build. Ask before you code. Deploy with confidence.*

</div>
