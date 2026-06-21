from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.support import get_support_keyboard
from app.translations import t


router = Router(name="support")


@router.callback_query(F.data == "menu:support")
async def support_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        t("sections.support", "ar"),
        reply_markup=get_support_keyboard("ar"),
    )


@router.message(Command("support"))
async def support_command_handler(message: Message) -> None:
    await message.answer(
        t("sections.support", "ar"),
        reply_markup=get_support_keyboard("ar"),
    )
