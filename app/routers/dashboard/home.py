from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dashboard import get_dashboard_keyboard, get_dashboard_section_keyboard
from app.routers.dashboard.shared import is_admin
from app.translations import t


router = Router(name="dashboard_home")

SECTION_MESSAGE_KEYS = {
    "products": "products_section",
    "notifications": "notifications_section",
    "payment_methods": "payment_methods_section",
    "sales": "sales_section",
    "other": "other_section",
}


@router.message(Command("dashboard"))
async def dashboard_command_handler(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    await state.clear()
    await message.answer(
        t("dashboard.messages.welcome", "ar"),
        reply_markup=get_dashboard_keyboard("ar"),
    )


@router.callback_query(F.data == "dashboard:home")
async def dashboard_home_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        t("dashboard.messages.welcome", "ar"),
        reply_markup=get_dashboard_keyboard("ar"),
    )


@router.callback_query(F.data.startswith("dashboard:section:"))
async def dashboard_section_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    section = callback.data.rsplit(":", maxsplit=1)[-1]
    if section not in SECTION_MESSAGE_KEYS:
        await callback.answer()
        return

    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        t(f"dashboard.messages.{SECTION_MESSAGE_KEYS[section]}", "ar"),
        reply_markup=get_dashboard_section_keyboard(section, "ar"),
    )
