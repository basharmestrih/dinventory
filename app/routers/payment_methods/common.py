from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ForceReply, Message

from app.config import settings
from app.routers.payment_methods.admin_notifications import (
    INSTAPAY_SCREENSHOT_TRANSACTION_ID,
    PaymentProof,
)
from app.routers.payment_methods.helpers import (
    ReviewMessageContext,
    create_order_and_notify,
    process_order_review,
)
from app.routers.payment_methods.helpers.credential_utils import (
    map_review_action_to_status,
    parse_activation_emails,
)
from app.states.purchase import PurchaseState
from app.translations import t
from app.routers.payment_methods.helpers.services import order_service
from app.services.orders.orders import OrderServiceError
from app.services.catalog.products import SupabaseConfigError
from app.routers.payment_methods.admin_notifications import format_admin_order_notification


router = Router(name="payment_common")


@router.message(PurchaseState.waiting_for_transaction_id)
async def transaction_id_handler(message: Message, state: FSMContext) -> None:
    transaction_id = (message.text or "").strip()
    if not transaction_id:
        await message.answer(t("purchase.invalid_transaction_id", "ar"))
        return

    await state.update_data(transaction_id=transaction_id)
    data = await state.get_data()

    if data.get("uses_manual_activation_emails") and not data.get("email"):
        await state.set_state(PurchaseState.waiting_for_activation_emails)
        await message.answer(
            t("purchase.ask_activation_emails", "ar").format(quantity=data["quantity"])
        )
        return

    await create_order_and_notify(message, state, transaction_id)


@router.message(PurchaseState.waiting_for_instapay_screenshot, F.photo | F.document)
async def instapay_screenshot_handler(message: Message, state: FSMContext) -> None:
    payment_proof = _extract_payment_proof(message)
    if payment_proof is None:
        await message.answer(t("purchase.invalid_instapay_screenshot", "ar"))
        return

    await state.update_data(
        transaction_id=INSTAPAY_SCREENSHOT_TRANSACTION_ID,
        payment_proof_file_id=payment_proof.file_id,
        payment_proof_type=payment_proof.file_type,
    )
    data = await state.get_data()

    if data.get("uses_manual_activation_emails") and not data.get("email"):
        await state.set_state(PurchaseState.waiting_for_activation_emails)
        await message.answer(
            t("purchase.ask_activation_emails", "ar").format(quantity=data["quantity"])
        )
        return

    await create_order_and_notify(
        message,
        state,
        INSTAPAY_SCREENSHOT_TRANSACTION_ID,
        payment_proof=payment_proof,
    )


@router.message(PurchaseState.waiting_for_instapay_screenshot)
async def invalid_instapay_screenshot_handler(message: Message) -> None:
    await message.answer(t("purchase.invalid_instapay_screenshot", "ar"))


@router.message(PurchaseState.waiting_for_activation_emails)
async def activation_emails_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    quantity = int(data.get("quantity") or 0)
    emails = parse_activation_emails(message.text or "")

    if len(emails) != quantity:
        await message.answer(
            t("purchase.invalid_activation_emails_count", "ar").format(
                quantity=quantity,
                emails_count=len(emails),
            )
        )
        return

    await state.update_data(email="\n".join(emails), password="")
    await create_order_and_notify(
        message,
        state,
        str(data.get("transaction_id") or ""),
        payment_proof=_get_payment_proof_from_state(data),
    )


@router.callback_query(F.data.startswith("order:review:"))
async def review_order_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.admin_user_ids:
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return

    _, _, action, order_id_text = parts

    try:
        order_id = int(order_id_text)
    except ValueError:
        await callback.answer()
        return

    new_status = map_review_action_to_status(action)
    if new_status is None:
        await callback.answer()
        return

    if action in {"approve_note", "reject"}:
        await state.set_state(PurchaseState.waiting_for_review_note)
        await state.update_data(
            review_order_id=order_id,
            review_new_status=new_status,
            review_message_id=callback.message.message_id if callback.message else None,
            review_chat_id=callback.message.chat.id if callback.message else None,
        )
        await callback.answer()
        await callback.message.answer(
            t("purchase.ask_review_note", "ar"),
            reply_markup=ForceReply(selective=True),
        )
        return

    await callback.answer()
    await process_order_review(
        context=callback,
        order_id=order_id,
        new_status=new_status,
    )


@router.message(PurchaseState.waiting_for_review_note)
async def review_note_handler(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in settings.admin_user_ids:
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    note_text = (message.text or "").strip()
    if not note_text:
        await message.answer(t("purchase.review_note_empty", "ar"))
        return

    data = await state.get_data()
    order_id = data.get("review_order_id")
    new_status = data.get("review_new_status")
    review_message_id = data.get("review_message_id")
    review_chat_id = data.get("review_chat_id")

    if (
        not isinstance(order_id, int)
        or not isinstance(new_status, str)
        or not isinstance(review_message_id, int)
        or not isinstance(review_chat_id, int)
    ):
        await state.clear()
        await message.answer(t("purchase.order_not_found", "ar"))
        return

    await process_order_review(
        context=ReviewMessageContext(message=message, review_chat_id=review_chat_id),
        order_id=order_id,
        new_status=new_status,
        note_text=note_text,
        review_message_id=review_message_id,
    )
    await state.clear()


@router.callback_query(F.data.startswith("order:activation:"))
async def activation_order_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.admin_user_ids:
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return

    _, _, action, order_id_text = parts
    try:
        order_id = int(order_id_text)
    except ValueError:
        await callback.answer()
        return

    status_map = {
        "activate": "Paid",
        "activate_note": "Paid",
        "reject": "ActivationRejected",
    }
    new_status = status_map.get(action)
    if new_status is None:
        await callback.answer()
        return

    if action in {"activate_note", "reject"}:
        await state.set_state(PurchaseState.waiting_for_activation_note)
        await state.update_data(
            activation_order_id=order_id,
            activation_new_status=new_status,
            activation_message_id=callback.message.message_id if callback.message else None,
            activation_chat_id=callback.message.chat.id if callback.message else None,
        )
        await callback.answer()
        await callback.message.answer(
            t("purchase.ask_activation_note", "ar"),
            reply_markup=ForceReply(selective=True),
        )
        return

    await callback.answer()
    await _process_order_activation(
        context=callback,
        order_id=order_id,
        new_status=new_status,
    )


@router.message(PurchaseState.waiting_for_activation_note)
async def activation_note_handler(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in settings.admin_user_ids:
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    note_text = (message.text or "").strip()
    if not note_text:
        await message.answer(t("purchase.review_note_empty", "ar"))
        return

    data = await state.get_data()
    order_id = data.get("activation_order_id")
    new_status = data.get("activation_new_status")
    message_id = data.get("activation_message_id")
    chat_id = data.get("activation_chat_id")

    if (
        not isinstance(order_id, int)
        or not isinstance(new_status, str)
        or not isinstance(message_id, int)
        or not isinstance(chat_id, int)
    ):
        await state.clear()
        await message.answer(t("purchase.order_not_found", "ar"))
        return

    await _process_order_activation(
        context=ReviewMessageContext(message=message, review_chat_id=chat_id),
        order_id=order_id,
        new_status=new_status,
        note_text=note_text,
        review_message_id=message_id,
    )
    await state.clear()


async def _process_order_activation(
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
        await context.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await context.message.answer(str(error))
        return

    if current_order is None:
        await context.message.answer(t("purchase.order_not_found", "ar"))
        return

    if current_order.status != "ActivationPending":
        await context.message.answer(t("purchase.order_already_processed", "ar"))
        return

    try:
        updated_order = await order_service.update_order_review_result(
            order_id,
            new_status,
            email=current_order.email,
            password=current_order.password,
            expiry_date=current_order.expiry_date,
        )
    except SupabaseConfigError:
        await context.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await context.message.answer(str(error))
        return

    if updated_order is None:
        await context.message.answer(t("purchase.order_not_found", "ar"))
        return

    await context.message.answer(t("purchase.order_status_updated", "ar"))

    from app.routers.payment_methods.helpers.review import edit_review_message
    from app.routers.payment_methods.helpers.customer_notifications import (
        notify_customer_about_processed_order,
    )

    product = None
    try:
        from app.services.catalog.products import ProductService

        product_service = ProductService()
        if updated_order.product_id is not None:
            product = await product_service.fetch_product_by_id(updated_order.product_id)
    except Exception:
        product = None

    await edit_review_message(
        context=context,
        text=format_admin_order_notification(updated_order),
        review_message_id=review_message_id,
    )

    await notify_customer_about_processed_order(
        context=context,
        updated_order=updated_order,
        product=product,
        note_text=note_text,
    )


def _extract_payment_proof(message: Message) -> PaymentProof | None:
    if message.photo:
        return PaymentProof(file_id=message.photo[-1].file_id, file_type="photo")

    document = message.document
    if document and (document.mime_type or "").startswith("image/"):
        return PaymentProof(file_id=document.file_id, file_type="document")

    return None


def _get_payment_proof_from_state(data: dict) -> PaymentProof | None:
    file_id = str(data.get("payment_proof_file_id") or "").strip()
    file_type = str(data.get("payment_proof_type") or "").strip()
    if not file_id or not file_type:
        return None

    return PaymentProof(file_id=file_id, file_type=file_type)
