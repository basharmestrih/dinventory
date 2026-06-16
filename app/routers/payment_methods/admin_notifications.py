from dataclasses import dataclass
from decimal import Decimal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import settings
from app.models.order import Order
from app.services.adobe import ADOBE_DURATION_OPTIONS
from app.translations import t


INSTAPAY_SCREENSHOT_TRANSACTION_ID = "INSTAPAY_SCREENSHOT"


@dataclass(slots=True)
class PaymentProof:
    file_id: str
    file_type: str


async def notify_admins_about_order(
    message: Message,
    order: Order,
    payment_proof: PaymentProof | None = None,
) -> None:
    if settings.admin_group_chat_id is None:
        return

    admin_text = format_admin_order_notification(order)

    try:
        await _send_admin_order_notification(
            message=message,
            admin_chat_id=settings.admin_group_chat_id,
            admin_text=admin_text,
            order_id=order.id,
            order_status=order.status,
            payment_proof=payment_proof,
        )
    except Exception:
        return


async def _send_admin_order_notification(
    *,
    message: Message,
    admin_chat_id: int,
    admin_text: str,
    order_id: int,
    order_status: str,
    payment_proof: PaymentProof | None,
) -> None:
    reply_markup = _get_order_notification_keyboard(order_id, order_status)
    if payment_proof is None:
        await message.bot.send_message(
            chat_id=admin_chat_id,
            text=admin_text,
            reply_markup=reply_markup,
        )
        return

    if payment_proof.file_type == "photo":
        await message.bot.send_photo(
            chat_id=admin_chat_id,
            photo=payment_proof.file_id,
            caption=admin_text,
            reply_markup=reply_markup,
        )
        return

    await message.bot.send_document(
        chat_id=admin_chat_id,
        document=payment_proof.file_id,
        caption=admin_text,
        reply_markup=reply_markup,
    )


def _get_order_notification_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup | None:
    # Statuses that require action:
    # - pending: review keyboard (approve/reject)
    # - ActivationPending: activation keyboard (activate/reject)
    if status == "pending":
        return get_order_review_keyboard(order_id)
    if status == "ActivationPending":
        return get_order_activation_keyboard(order_id)
    return None


def get_order_review_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("purchase.review_approve_button", "ar"),
                    callback_data=f"order:review:approve:{order_id}",
                ),
                InlineKeyboardButton(
                    text=t("purchase.review_approve_with_note_button", "ar"),
                    callback_data=f"order:review:approve_note:{order_id}",
                ),
                InlineKeyboardButton(
                    text=t("purchase.review_reject_button", "ar"),
                    callback_data=f"order:review:reject:{order_id}",
                ),
            ]
        ]
    )


def get_order_activation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("purchase.activation_activate_button", "ar"),
                    callback_data=f"order:activation:activate:{order_id}",
                ),
                InlineKeyboardButton(
                    text=t("purchase.activation_activate_with_note_button", "ar"),
                    callback_data=f"order:activation:activate_note:{order_id}",
                ),
                InlineKeyboardButton(
                    text=t("purchase.activation_reject_button", "ar"),
                    callback_data=f"order:activation:reject:{order_id}",
                ),
            ]
        ]
    )


def display_text(value: str) -> str:
    return value.replace("_", " ")


def format_price(value: Decimal) -> str:
    return f"{value:.2f}"


def format_admin_order_notification(order: Order) -> str:
    emails_block = _format_activation_emails_block(order.email, order.password, order.expiry_date)
    return t("purchase.admin_order_notification", "ar").format(
        order_id=order.id,
        product_title=display_text(order.product_title),
        quantity=order.quantity,
        total=format_price(order.total),
        payment_method=order.payment_method,
        transaction_id=_format_transaction_reference(order.transaction_id),
        customer_name=order.customer_name,
        customer_username=order.customer_username or "-",
        customer_id=order.customer_telegram_id or "-",
        status=order.status,
        activation_emails_block=emails_block,
    )


def _format_activation_emails_block(email: str, password: str, expiry_date: str) -> str:
    if _looks_like_duration(expiry_date):
        return t("purchase.admin_adobe_assignment_block", "ar").format(
            email=email or "-",
            duration=_format_duration_label(expiry_date),
        )

    if password or not email:
        return ""

    return t("purchase.admin_activation_emails_block", "ar").format(emails=email)


def _looks_like_duration(value: str) -> bool:
    return value in ADOBE_DURATION_OPTIONS


def _format_duration_label(value: str) -> str:
    labels = {
        "1_month": t("purchase.duration_buttons.one_month", "ar"),
        "2_months": t("purchase.duration_buttons.two_months", "ar"),
        "6_months": t("purchase.duration_buttons.six_months", "ar"),
        "12_months": t("purchase.duration_buttons.twelve_months", "ar"),
    }
    return labels.get(value, value)


def _format_transaction_reference(transaction_id: str | None) -> str:
    if transaction_id == INSTAPAY_SCREENSHOT_TRANSACTION_ID:
        return t("purchase.instapay_screenshot_reference", "ar")

    return transaction_id or "-"
