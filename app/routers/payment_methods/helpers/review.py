from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.routers.payment_methods.admin_notifications import (
    INSTAPAY_SCREENSHOT_TRANSACTION_ID,
    PaymentProof,
    format_admin_order_notification,
    get_order_activation_keyboard,
    notify_admins_about_order,
)
from app.routers.payment_methods.helpers.customer_notifications import (
    notify_customer_about_processed_order,
)
from app.routers.payment_methods.helpers.order_processing import process_paid_order
from app.routers.payment_methods.helpers.services import order_service
from app.services.orders.orders import OrderServiceError
from app.services.catalog.products import ProductServiceError, SupabaseConfigError
from app.translations import t


async def create_order_and_notify(
    message: Message,
    state: FSMContext,
    transaction_id: str | None,
    payment_proof: PaymentProof | None = None,
) -> None:
    data = await state.get_data()
    display_transaction_id = transaction_id or "-"
    stored_transaction_id = _get_stored_transaction_id(data, transaction_id)

    try:
        order = await order_service.create_order(data, stored_transaction_id, message.from_user)
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await message.answer(
            t("purchase.order_create_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except Exception:
        await message.answer(t("purchase.order_create_failed", "ar"))
        return

    await notify_admins_about_order(message, order, payment_proof)
    await state.clear()
    confirmation_key = (
        "purchase.order_under_review_with_screenshot"
        if transaction_id == INSTAPAY_SCREENSHOT_TRANSACTION_ID
        else "purchase.order_under_review"
    )
    await message.answer(t(confirmation_key, "ar").format(transaction_id=display_transaction_id))


def _get_stored_transaction_id(data: dict, transaction_id: str | None) -> str | None:
    payment_method = str(data.get("payment_method") or "").strip().lower()
    if payment_method in {"instapay", "wallet"}:
        return None

    return transaction_id


async def process_order_review(
    context,
    order_id: int,
    new_status: str,
    *,
    note_text: str = "",
    review_message_id: int | None = None,
) -> None:
    try:
        current_order = await order_service.fetch_order_by_id(order_id)
    except SupabaseConfigError:
        await send_review_feedback(context, t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await send_review_feedback(context, str(error))
        return

    if current_order is None:
        await send_review_feedback(context, t("purchase.order_not_found", "ar"))
        return

    if current_order.status != "pending":
        await send_review_feedback(context, t("purchase.order_already_processed", "ar"))
        return

    product = None
    order_action_label = None
    if new_status == "Paid":
        try:
            updated_order, product, error_message, order_action_label = await process_paid_order(current_order)
        except SupabaseConfigError:
            await send_review_feedback(context, t("sections.supabase_not_configured", "ar"))
            return
        except OrderServiceError as error:
            await send_review_feedback(context, str(error))
            return
        except ProductServiceError as error:
            await send_review_feedback(context, str(error))
            return
        except Exception:
            await send_review_feedback(context, t("purchase.order_stock_update_failed", "ar"))
            return

        if updated_order is None:
            await send_review_feedback(context, error_message or t("purchase.order_not_found", "ar"))
            return
    else:
        try:
            updated_order = await order_service.update_order_review_result(
                order_id,
                new_status,
                email=current_order.email,
                password=current_order.password,
                expiry_date=current_order.expiry_date,
            )
        except SupabaseConfigError:
            await send_review_feedback(context, t("sections.supabase_not_configured", "ar"))
            return
        except OrderServiceError as error:
            await send_review_feedback(context, str(error))
            return

        if updated_order is None:
            await send_review_feedback(context, t("purchase.order_not_found", "ar"))
            return

    await send_review_feedback(context, t("purchase.order_status_updated", "ar"))

    await edit_review_message(
        context=context,
        text=format_admin_order_notification(updated_order),
        review_message_id=review_message_id,
        reply_markup=(
            get_order_activation_keyboard(updated_order.id)
            if updated_order.status == "ActivationPending"
            else None
        ),
    )

    await notify_customer_about_processed_order(
        context=context,
        updated_order=updated_order,
        product=product,
        note_text=note_text,
        order_action_label=order_action_label,
    )


async def edit_review_message(
    context,
    text: str,
    *,
    review_message_id: int | None = None,
    reply_markup=None,
) -> None:
    if review_message_id is None:
        await _edit_message_content(context.message, text, reply_markup=reply_markup)
        return

    await _edit_message_content(
        context.bot,
        text,
        chat_id=context.review_chat_id,
        message_id=review_message_id,
        reply_markup=reply_markup,
    )


class ReviewMessageContext:
    def __init__(self, message: Message, review_chat_id: int) -> None:
        self.from_user = message.from_user
        self.message = message
        self.bot = message.bot
        self.review_chat_id = review_chat_id

    async def answer(self, text: str | None = None, show_alert: bool = False) -> None:
        if text:
            await self.message.answer(text)


async def send_review_feedback(context, text: str) -> None:
    if not text:
        return

    if isinstance(context, ReviewMessageContext):
        await context.answer(text)
        return

    if isinstance(context, CallbackQuery):
        if context.message:
            await context.message.answer(text)
            return
        try:
            await context.answer(text)
        except Exception:
            return
        return

    if hasattr(context, "answer"):
        await context.answer(text)


async def _edit_message_content(
    target,
    text: str,
    *,
    chat_id: int | None = None,
    message_id: int | None = None,
    reply_markup=None,
) -> None:
    if hasattr(target, "edit_caption"):
        try:
            await target.edit_caption(caption=text, reply_markup=reply_markup)
            return
        except Exception:
            pass

    if hasattr(target, "edit_text"):
        await target.edit_text(text, reply_markup=reply_markup)
        return

    try:
        await target.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=text,
            reply_markup=reply_markup,
        )
        return
    except Exception:
        await target.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
