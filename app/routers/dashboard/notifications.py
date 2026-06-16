from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dashboard import get_dashboard_keyboard
from app.routers.dashboard.shared import is_admin, notification_service
from app.services.messaging.notifications import NotificationServiceError
from app.services.catalog.products import SupabaseConfigError
from app.states.dashboard import BroadcastNotificationState
from app.translations import t


router = Router(name="dashboard_notifications")


@router.callback_query(F.data == "dashboard:broadcast")
async def dashboard_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.clear()
    await state.set_state(BroadcastNotificationState.text)
    await callback.answer()
    await callback.message.answer(t("dashboard.messages.broadcast_prompt", "ar"))


@router.message(BroadcastNotificationState.text)
async def broadcast_notification_handler(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer(t("dashboard.messages.broadcast_empty", "ar"))
        return

    try:
        result = await notification_service.broadcast_text(
            message.bot,
            _format_admin_broadcast_message(text),
        )
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        await state.clear()
        return
    except NotificationServiceError as error:
        await message.answer(
            t("dashboard.messages.broadcast_failed_with_reason", "ar").format(reason=str(error))
        )
        await state.clear()
        return
    except Exception:
        await message.answer(t("dashboard.messages.broadcast_failed", "ar"))
        await state.clear()
        return

    await state.clear()
    await message.answer(
        t("dashboard.messages.broadcast_success", "ar").format(
            success_count=result.success_count,
            total_recipients=result.total_recipients,
            failed_count=result.failed_count,
        ),
        reply_markup=get_dashboard_keyboard("ar"),
    )


def _format_admin_broadcast_message(note: str) -> str:
    return f"🚨 تنبيه من الادمن\n\nملاحظة:\n{note}"
