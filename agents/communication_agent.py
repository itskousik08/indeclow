"""
INDECLOW by AxeroAI
📩 Communication Agent — Handles all Telegram messaging
"""

import asyncio
from typing import Optional, Union
from telegram import Bot, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from config import TELEGRAM_BOT_TOKEN
from utils.logger import logger


class CommunicationAgent:
    """
    📩 Communication Agent
    Sends real-time updates, progress notifications,
    files, and structured messages via Telegram.
    """

    PROGRESS_ICONS = {
        "start": "🚀",
        "requirement": "🧠",
        "question": "❓",
        "planning": "📋",
        "architect": "🏗️",
        "frontend": "🎨",
        "backend": "⚙️",
        "terminal": "💻",
        "debug": "🐞",
        "deploy": "🌐",
        "done": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "file": "📁",
        "zip": "📦",
    }

    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot

    def set_bot(self, bot: Bot) -> None:
        self.bot = bot

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup=None,
    ) -> Optional[Message]:
        if not self.bot:
            logger.warning("Bot not initialized in CommunicationAgent")
            return None
        try:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except TelegramError as e:
            logger.error(f"Telegram send_message failed: {e}")
            # Try without markdown if parsing fails
            try:
                return await self.bot.send_message(
                    chat_id=chat_id, text=text, parse_mode=None
                )
            except Exception:
                return None

    async def send_progress(
        self, chat_id: Union[int, str], stage: str, message: str
    ) -> None:
        icon = self.PROGRESS_ICONS.get(stage, "⚡")
        await self.send_message(chat_id, f"{icon} {message}")

    async def send_document(
        self,
        chat_id: Union[int, str],
        file_path: str,
        caption: str = "",
    ) -> bool:
        if not self.bot:
            return False
        try:
            with open(file_path, "rb") as f:
                await self.bot.send_document(
                    chat_id=chat_id, document=f, caption=caption
                )
            return True
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            return False

    async def send_question(
        self,
        chat_id: Union[int, str],
        question: str,
        q_num: int,
        total: int,
    ) -> None:
        text = (
            f"❓ *Question {q_num}/{total}*\n\n"
            f"{question}"
        )
        await self.send_message(chat_id, text)

    async def send_plan(
        self, chat_id: Union[int, str], plan_message: str
    ) -> None:
        await self.send_message(
            chat_id,
            f"📋 *Execution Plan Ready*\n\n{plan_message}"
        )

    async def send_build_started(self, chat_id: Union[int, str]) -> None:
        text = (
            "🚀 *Build Started!*\n\n"
            "INDECLOW is now building your project...\n"
            "I'll send you updates as each step completes.\n\n"
            "_Powered by AxeroAI_"
        )
        await self.send_message(chat_id, text)

    async def send_build_complete(
        self,
        chat_id: Union[int, str],
        project_name: str,
        preview_url: str,
        files_count: int,
    ) -> None:
        text = (
            f"✅ *Build Complete!*\n\n"
            f"📦 Project: *{project_name}*\n"
            f"📁 Files Generated: {files_count}\n"
            f"🌐 Preview URL: {preview_url}\n\n"
            f"The ZIP file is being sent to you now...\n\n"
            f"_Built by INDECLOW — AxeroAI_"
        )
        await self.send_message(chat_id, text)

    async def send_error(
        self, chat_id: Union[int, str], error: str, recoverable: bool = True
    ) -> None:
        icon = "⚠️" if recoverable else "❌"
        text = f"{icon} *Error*\n\n{error}"
        if recoverable:
            text += "\n\nType /start to begin a new project or /help for options."
        await self.send_message(chat_id, text)

    async def send_welcome(self, chat_id: Union[int, str], user_name: str) -> None:
        text = (
            f"👋 Hello *{user_name}*!\n\n"
            "I'm *INDECLOW* by *AxeroAI* — your autonomous AI software engineer.\n\n"
            "I can build:\n"
            "• 🎨 Portfolio websites\n"
            "• 🛒 E-commerce stores\n"
            "• 🚀 Landing pages\n"
            "• 📊 Dashboards\n"
            "• ⚙️ APIs & backends\n"
            "• 🌐 Any web project\n\n"
            "Just tell me what you want to build!\n\n"
            "*Commands:*\n"
            "/start — Start new project\n"
            "/status — Check current build\n"
            "/skill — Install a GitHub skill\n"
            "/logs — View recent logs\n"
            "/cancel — Cancel current operation\n"
            "/help — Show this help"
        )
        await self.send_message(chat_id, text)

    async def send_typing(self, chat_id: Union[int, str]) -> None:
        if not self.bot:
            return
        try:
            await self.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception:
            pass

    def make_confirm_keyboard(
        self, yes_label: str = "✅ Yes", no_label: str = "❌ No"
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(yes_label, callback_data="confirm_yes"),
                InlineKeyboardButton(no_label, callback_data="confirm_no"),
            ]
        ])
