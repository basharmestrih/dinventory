import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from app.config import settings


logger = logging.getLogger(__name__)

DEFAULT_COMMANDS = [
    BotCommand(command="start", description="ابدأ"),
    BotCommand(command="products", description="المنتجات"),
    BotCommand(command="wallet", description="المحفظة"),
    BotCommand(command="history", description="السجل"),
    BotCommand(command="support", description="الدعم"),
]

ADMIN_COMMANDS = [
    *DEFAULT_COMMANDS,
    BotCommand(command="dashboard", description="لوحة التحكم"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(DEFAULT_COMMANDS, scope=BotCommandScopeDefault())

    for admin_id in settings.admin_user_ids:
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as error:
            logger.warning("Failed to set admin bot commands for %s: %s", admin_id, error)
