import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards import get_main_menu_keyboard
from app.services.catalog.products import SupabaseConfigError
from app.services.users.users import UserService, UserServiceError
from app.translations import t


router = Router(name="start")
user_service = UserService()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    lang = "ar"
    if message.from_user is not None:
        try:
            await user_service.register_bot_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
        except (SupabaseConfigError, UserServiceError) as error:
            logger.warning("Failed to register bot user on /start: %s", error)

    await message.answer(
        t("messages.welcome", lang),
        reply_markup=get_main_menu_keyboard(
            lang,
            is_admin=message.from_user is not None and message.from_user.id in settings.admin_user_ids,
        ),
    )


@router.callback_query(F.data == "menu:home")
async def home_handler(callback: CallbackQuery) -> None:
    lang = "ar"
    await callback.answer()
    await callback.message.edit_text(
        t("messages.welcome", lang),
        reply_markup=get_main_menu_keyboard(
            lang,
            is_admin=callback.from_user.id in settings.admin_user_ids,
        ),
    )
