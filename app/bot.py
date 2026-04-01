"""
aiogram v3 Telegram bot.
Sends a WebApp button when the user types /start.
Runs as long-polling inside the FastAPI process.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://your-app.up.railway.app")

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    webapp_url = f"{APP_BASE_URL.rstrip('/')}/app"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌿 Open Calm Space",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )

    await message.answer(
        "👋 <b>Welcome to Calm Space</b> — your pocket anxiety support companion.\n\n"
        "✨ Track your mood, practice box breathing, reframe anxious thoughts, "
        "journal your feelings, and watch your progress over time.\n\n"
        "Tap the button below to open the app 👇",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def start_polling() -> None:
    """Start the bot with long polling. Called from FastAPI lifespan."""
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN not set — bot will not start.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting Telegram bot polling…")
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled.")
    finally:
        await bot.session.close()
