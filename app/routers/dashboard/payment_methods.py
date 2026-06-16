from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.dashboard import get_dashboard_section_keyboard
from app.routers.dashboard.shared import is_admin
from app.services.payments.payment_methods import PAYMENT_METHODS, set_payment_method_enabled
from app.translations import t


router = Router(name="dashboard_payment_methods")


@router.callback_query(F.data.startswith("dashboard:payment_methods:"))
async def dashboard_payment_methods_handler(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return

    _, _, action, method = parts

    if method not in PAYMENT_METHODS:
        await callback.answer()
        return

    if action == "noop":
        await callback.answer()
        return

    enabled = {"enable": True, "disable": False}.get(action)
    if enabled is None:
        await callback.answer()
        return

    set_payment_method_enabled(method, enabled)
    await callback.answer(t("dashboard.messages.payment_method_status_updated", "ar"))
    await callback.message.edit_text(
        t("dashboard.messages.payment_methods_section", "ar"),
        reply_markup=get_dashboard_section_keyboard("payment_methods", "ar"),
    )
