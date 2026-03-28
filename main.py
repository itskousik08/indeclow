#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║         INDECLOW by AxeroAI         ║
║   Autonomous Multi-Agent AI System  ║
╚══════════════════════════════════════╝

Entry point: terminal UI + Telegram bot runner.
"""

import sys
import asyncio
import signal
import threading

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, OLLAMA_MODEL, OLLAMA_BASE_URL, VERSION
from core.agent_manager import AgentManager
from core.controller import Controller
from utils.ollama_client import ollama
from utils.logger import logger

console = Console()

# ── Banner ─────────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]╔══════════════════════════════════════════════╗[/]
[bold cyan]║[/]  [bold white]██╗███╗   ██╗██████╗ ███████╗ ██████╗[/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║████╗  ██║██╔══██╗██╔════╝██╔════╝[/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║██╔██╗ ██║██║  ██║█████╗  ██║     [/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║██║╚██╗██║██║  ██║██╔══╝  ██║     [/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║██║ ╚████║██████╔╝███████╗╚██████╗[/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝ ╚═════╝[/]      [bold cyan]║[/]
[bold cyan]║[/]  [bold white]     ██████╗[/] [bold cyan]██╗      ██████╗[/] [bold white]██╗    ██╗[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]    ██╔════╝[/] [bold cyan]██║     ██╔═══██╗[/] [bold white]██║    ██║[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]    ██║     [/] [bold cyan]██║     ██║   ██║[/] [bold white]██║ █╗ ██║[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]    ██║     [/] [bold cyan]██║     ██║   ██║[/] [bold white]██║███╗██║[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]    ╚██████╗[/] [bold cyan]███████╗╚██████╔╝[/] [bold white]╚███╔███╔╝[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]     ╚═════╝[/] [bold cyan]╚══════╝ ╚═════╝ [/]  [bold white]╚══╝╚══╝ [/]  [bold cyan]║[/]
[bold cyan]║[/]                                              [bold cyan]║[/]
[bold cyan]║[/]  [dim]Autonomous Multi-Agent AI System v{VERSION}[/]    [bold cyan]║[/]
[bold cyan]║[/]  [dim]Powered by AxeroAI  ●  Built for builders[/]    [bold cyan]║[/]
[bold cyan]╚══════════════════════════════════════════════╝[/]
"""


def print_banner():
    console.print(BANNER)


def print_status_table(llm_ok: bool, bot_token_ok: bool):
    table = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Value", style="dim")

    llm_status = f"[green]✅ {OLLAMA_MODEL}[/]" if llm_ok else "[red]❌ Offline — start Ollama[/]"
    bot_status = "[green]✅ Connected[/]" if bot_token_ok else "[red]❌ Missing — set TELEGRAM_BOT_TOKEN[/]"

    table.add_row("LLM (Ollama)", llm_status)
    table.add_row("Ollama URL", OLLAMA_BASE_URL)
    table.add_row("Telegram Bot", bot_status)
    table.add_row("Version", f"v{VERSION}")

    console.print(Panel(table, title="[bold cyan]System Status[/]", border_style="cyan"))


def print_commands():
    table = Table(box=box.SIMPLE, border_style="cyan", show_header=False, padding=(0, 2))
    table.add_column("Cmd", style="bold yellow")
    table.add_column("Description", style="dim white")

    commands = [
        ("/start",   "Start a new build project"),
        ("/update",  "Update part of your project"),
        ("/deploy",  "Regenerate live preview URL"),
        ("/skill",   "Install a GitHub skill"),
        ("/skills",  "List installed skills"),
        ("/status",  "Check current build status"),
        ("/logs",    "View terminal command logs"),
        ("/cancel",  "Cancel current operation"),
        ("/help",    "Show help message"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(Panel(table, title="[bold cyan]Telegram Bot Commands[/]", border_style="cyan"))


# ── Pre-flight checks ──────────────────────────────────────────────────────────

def run_preflight() -> tuple[bool, bool]:
    llm_ok = ollama.is_available()
    bot_ok = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here")

    if not llm_ok:
        console.print("[red]⚠️  Ollama is not running.[/]")
        console.print("   Run: [bold]ollama serve[/]")
        console.print(f"   Then pull a model: [bold]ollama pull {OLLAMA_MODEL}[/]\n")

    if not bot_ok:
        console.print("[red]⚠️  Telegram bot token not configured.[/]")
        console.print("   Copy [bold].env.example[/] → [bold].env[/] and fill in your token.\n")

    return llm_ok, bot_ok


# ── Telegram Handlers ─────────────────────────────────────────────────────────

agents = AgentManager()
controller = Controller(agents)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    controller.clear_session(chat_id)

    # Show welcome on very first /start with no args
    if not ctx.args:
        await agents.communication.send_welcome(chat_id, user.first_name)
        return

    # /start <request> — begin building immediately
    request = " ".join(ctx.args)
    await controller.handle_new_request(chat_id, request)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await agents.communication.send_welcome(chat_id, update.effective_user.first_name)


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    controller.clear_session(chat_id)
    await agents.communication.send_message(
        chat_id,
        "🛑 *Operation cancelled.*\n\nSend me a message to start a new project!",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await controller.handle_status(chat_id)


async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await controller.handle_logs(chat_id)


async def cmd_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not ctx.args:
        await agents.communication.send_message(
            chat_id,
            "🔄 *Update Agent*\n\nUsage: `/update <what to change>`\n\n"
            "Examples:\n"
            "• `/update change background color to dark blue`\n"
            "• `/update add a contact section`\n"
            "• `/update make the navbar sticky`",
        )
        return
    request = " ".join(ctx.args)
    await controller.handle_update(chat_id, request)


async def cmd_deploy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await controller.handle_redeploy(chat_id)


async def cmd_skill(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not ctx.args:
        skills_msg = agents.skill.format_skills_list()
        await agents.communication.send_message(
            chat_id,
            f"🧩 *Skill Agent*\n\n"
            f"Install a skill: `/skill <GitHub URL>`\n\n"
            f"Example:\n"
            f"`/skill https://github.com/user/react-expert-skill`\n\n"
            f"{skills_msg}",
        )
        return
    repo_url = ctx.args[0]
    await controller.handle_skill_install(chat_id, repo_url)


async def cmd_skills(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    msg = agents.skill.format_skills_list()
    await agents.communication.send_message(chat_id, msg)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()

    if not text:
        return

    session = controller.get_session(chat_id)

    # Route based on session state
    if session.state == "gathering":
        await controller.handle_answer(chat_id, text)

    elif session.state in ("done", "idle"):
        # Treat any free-text message as a new build request
        await controller.handle_new_request(chat_id, text)

    elif session.state == "building":
        await agents.communication.send_message(
            chat_id,
            "⏳ Build in progress... please wait until it completes.",
        )
    else:
        await agents.communication.send_message(
            chat_id,
            "👋 Send me a description of what you want to build!\n\n"
            "Example: _'Create a portfolio website for a photographer'_",
        )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = str(query.message.chat_id)
    data = query.data

    if data == "confirm_yes":
        await agents.communication.send_message(chat_id, "✅ Confirmed!")
    elif data == "confirm_no":
        await agents.communication.send_message(chat_id, "❌ Cancelled.")


async def post_init(app):
    """Called after the bot is initialized."""
    agents.set_bot(app.bot)
    bot_info = await app.bot.get_me()
    console.print(f"\n[green]✅ Bot connected: @{bot_info.username}[/]")
    console.print("[bold green]🚀 INDECLOW is LIVE — waiting for Telegram messages...[/]\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print_banner()

    llm_ok, bot_ok = run_preflight()
    print_status_table(llm_ok, bot_ok)
    print_commands()

    if not bot_ok:
        console.print(
            Panel(
                "[red]Cannot start: Telegram bot token is missing.\n"
                "Edit [bold].env[/] and set [bold]TELEGRAM_BOT_TOKEN[/].",
                border_style="red",
                title="Startup Failed",
            )
        )
        sys.exit(1)

    if not llm_ok:
        console.print(
            "[yellow]⚠️  Ollama is offline. Starting anyway — LLM calls will retry.[/]\n"
        )

    console.print("[bold cyan]Starting Telegram bot...[/]\n")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("logs",   cmd_logs))
    app.add_handler(CommandHandler("update", cmd_update))
    app.add_handler(CommandHandler("deploy", cmd_deploy))
    app.add_handler(CommandHandler("skill",  cmd_skill))
    app.add_handler(CommandHandler("skills", cmd_skills))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Graceful shutdown
    def handle_exit(sig, frame):
        console.print("\n[yellow]Shutting down INDECLOW...[/]")
        agents.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
