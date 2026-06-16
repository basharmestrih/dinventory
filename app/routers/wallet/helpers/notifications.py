from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import settings
from app.keyboards.wallet import get_wallet_topup_review_keyboard
from app.routers.payment_methods.admin_notifications import (
    INSTAPAY_SCREENSHOT_TRANSACTION_ID,
    PaymentProof,
    format_price,
)
from app.routers.wallet.store import WalletTopUpRequest
from app.services.messaging.review_messages import render_review_message
from app.services.support_settings import get_support_username
from app.translations import t


def format_wallet_topup_review_text(request: WalletTopUpRequest) -> str:
    transaction_reference = (
        t("purchase.instapay_screenshot_reference", "ar")
        if request.transaction_id == INSTAPAY_SCREENSHOT_TRANSACTION_ID
        else request.transaction_id
    )
    return (
        "طلب إيداع جديد للمحفظة\n\n"
        f"اسم المستخدم: @{request.username}\n"
        f"المبلغ: {format_price(request.amount)} {request.currency}\n"
        f"طريقة الإيداع: {request.payment_method}\n"
        "بيانات العميل:\n"
        f"الاسم: {request.customer_name}\n"
        f"اليوزر: {request.customer_username}\n"
        f"الآيدي: {request.customer_telegram_id or '-'}"
    )


def render_wallet_topup_message(
    request: WalletTopUpRequest,
    message_key: str,
    *,
    balance_egp=None,
    balance_usd=None,
) -> str:
    formatted_balance_egp = format_price(balance_egp) if balance_egp is not None else "-"
    formatted_balance_usd = format_price(balance_usd) if balance_usd is not None else "-"
    return render_review_message(
        message_key,
        {
            "amount": format_price(request.amount),
            "payment_method": request.payment_method,
            "currency": "EGP",
            "balance": formatted_balance_egp,
            "balance_egp": formatted_balance_egp,
            "balance_usd": formatted_balance_usd,
        },
    )


async def edit_wallet_topup_review_message(message: Message, text: str) -> None:
    try:
        if message.caption is not None:
            await message.edit_caption(caption=text, reply_markup=None)
            return

        await message.edit_text(text, reply_markup=None)
    except Exception:
        try:
            await message.answer(text)
        except Exception:
            pass


async def notify_admins_about_wallet_topup(
    message: Message,
    request: WalletTopUpRequest,
    payment_proof: PaymentProof | None,
) -> None:
    if settings.admin_group_chat_id is None:
        return

    review_text = format_wallet_topup_review_text(request)
    reply_markup = get_wallet_topup_review_keyboard(request.id, "ar")

    try:
        if payment_proof is None:
            await message.bot.send_message(
                chat_id=settings.admin_group_chat_id,
                text=review_text,
                reply_markup=reply_markup,
            )
            return

        if payment_proof.file_type == "photo":
            await message.bot.send_photo(
                chat_id=settings.admin_group_chat_id,
                photo=payment_proof.file_id,
                caption=review_text,
                reply_markup=reply_markup,
            )
            return

        await message.bot.send_document(
            chat_id=settings.admin_group_chat_id,
            document=payment_proof.file_id,
            caption=review_text,
            reply_markup=reply_markup,
        )
    except Exception:
        return


async def notify_customer_about_wallet_topup_rejection(
    message: Message,
    request: WalletTopUpRequest,
    rejection_message: str,
) -> None:
    if not request.customer_telegram_id:
        return

    try:
        await message.bot.send_message(
            chat_id=request.customer_telegram_id,
            text=rejection_message,
            reply_markup=_get_support_keyboard(),
        )
    except Exception:
        return


def extract_payment_proof(message: Message) -> PaymentProof | None:
    if message.photo:
        return PaymentProof(file_id=message.photo[-1].file_id, file_type="photo")

    document = message.document
    if document and (document.mime_type or "").startswith("image/"):
        return PaymentProof(file_id=document.file_id, file_type="document")

    return None


def _get_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("purchase.contact_support_button", "ar"),
                    url=f"https://t.me/{get_support_username()}",
                )
            ]
        ]
    )
