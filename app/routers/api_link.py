from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.translations import t


router = Router(name="api_link")


@router.callback_query(F.data == "menu:api_link")
async def api_link_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(t("sections.api_link", "ar"))
