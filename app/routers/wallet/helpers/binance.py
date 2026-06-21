import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram.types import Message

from app.keyboards.wallet import get_wallet_topup_cancel_keyboard
from app.routers.payment_methods.admin_notifications import format_price
from app.services.payments.binance_settings import get_binance_id
from app.routers.wallet.helpers.time_utils import format_duration, get_remaining_seconds
from app.routers.wallet.store import get_wallet_topup_request, update_wallet_topup_status


_topup_countdown_active: dict[str, bool] = {}
_topup_countdown_cancelled: dict[str, bool] = {}
_WALLET_TOPUP_COUNTDOWN_SECONDS = 60 * 60


def format_binance_topup_message(
    instruction,
    amount: float,
    remaining_seconds: int | None = None,
) -> str:
    countdown_line = ""
    if remaining_seconds is not None:
        countdown_line = f"⏳ الوقت المتبقي: `{format_duration(remaining_seconds)}`\n\n"

    return (
        "الدفع عبر Binance Pay\n\n"
        "معرف الدفع، اضغط عليه للنسخ:\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        #f"مبلغ الشحن بالجنيه المصري: {format_price(amount)} EGP\n"
        "المبلغ المطلوب إرساله عبر Binance:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        f"{countdown_line}"
        "تأكد من إرسال نفس القيمة بالضبط عبر Binance Pay.\n"
        "بعد تأكيد الدفع من الخدمة سيتم شحن رصيد محفظتك تلقائياً خلال دقائق."
    )


async def run_binance_topup_countdown(message: Message, instruction, amount: Decimal, request_id: str) -> None:
    checkout_id = str(getattr(instruction, "checkout_id", "") or "").strip()
    if checkout_id:
        _topup_countdown_active[checkout_id] = True
        _topup_countdown_cancelled[checkout_id] = False

    expires_at = instruction.expires_at
    if expires_at is None:
        return

    now = datetime.now(timezone.utc)
    expires_at_utc = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    countdown_deadline = min(expires_at_utc, now + timedelta(seconds=_WALLET_TOPUP_COUNTDOWN_SECONDS))

    remaining = get_remaining_seconds(countdown_deadline)
    if remaining <= 0:
        await _safe_edit_binance_topup(message, instruction, amount, remaining, request_id, expired=True)
        await _mark_wallet_topup_expired(request_id)
        return

    while remaining > 0:
        await asyncio.sleep(1)
        if checkout_id and _topup_countdown_cancelled.get(checkout_id, False):
            await _safe_edit_binance_topup(message, instruction, amount, remaining, request_id, cancelled=True)
            await _mark_wallet_topup_expired(request_id)
            return
        if checkout_id and not _topup_countdown_active.get(checkout_id, True):
            await _safe_edit_binance_topup(message, instruction, amount, remaining, request_id, paid=True)
            return
        remaining = get_remaining_seconds(countdown_deadline)
        await _safe_edit_binance_topup(message, instruction, amount, remaining, request_id)

    await _safe_edit_binance_topup(message, instruction, amount, remaining_seconds=0, request_id=request_id, expired=True)
    await _mark_wallet_topup_expired(request_id)


async def _safe_edit_binance_topup(
    message: Message,
    instruction,
    amount: Decimal,
    remaining_seconds: int,
    request_id: str,
    *,
    paid: bool = False,
    cancelled: bool = False,
    expired: bool = False,
) -> None:
    try:
        if paid:
            await message.edit_text(
                format_binance_topup_paid_message(instruction, amount),
                parse_mode="Markdown",
            )
            return
        if cancelled:
            await message.edit_text(
                format_binance_topup_cancelled_message(instruction, amount),
                parse_mode="Markdown",
            )
            return
        if expired:
            await message.edit_text(
                format_binance_topup_expired_message(instruction, amount),
                parse_mode="Markdown",
            )
            return
        await message.edit_text(
            format_binance_topup_message(instruction, amount, remaining_seconds),
            parse_mode="Markdown",
            reply_markup=get_wallet_topup_cancel_keyboard(request_id),
        )
    except Exception:
        return


def mark_binance_topup_paid(checkout_id: str) -> None:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return
    _topup_countdown_active[checkout_id] = False


def mark_wallet_topup_countdown_cancelled(request_id: str) -> None:
    request_id = str(request_id or "").strip()
    if not request_id:
        return
    _topup_countdown_active[request_id] = False
    _topup_countdown_cancelled[request_id] = True


def format_binance_topup_paid_message(instruction, amount: Decimal) -> str:
    return (
        "الدفع عبر Binance Pay\n\n"
        "✅ تم تأكيد الإيداع بنجاح.\n\n"
        "معرف الدفع، اضغط عليه للنسخ:\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        #f"مبلغ الشحن بالجنيه المصري: {format_price(amount)} EGP\n"
        "المبلغ المطلوب إرساله عبر Binance:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        "سيتم إضافة الرصيد تلقائياً إلى محفظتك."
    )


def format_binance_topup_expired_message(instruction, amount: Decimal) -> str:
    return (
        "💳 *إيداع المحفظة عبر Binance Pay*\n\n"
        "⛔️ انتهت مدة الإيداع وتم إلغاء الطلب.\n\n"
        "🔁 الرجاء إنشاء طلب إيداع جديد والمحاولة مرة أخرى.\n\n"
        "📌 معرّف الدفع (اضغط للنسخ):\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        #f"💰 مبلغ الإيداع: `{format_price(amount)} EGP`\n"
        "💰 المبلغ المطلوب إرساله عبر Binance:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
    )


def format_binance_topup_cancelled_message(instruction, amount: Decimal) -> str:
    return (
        "💳 *إيداع المحفظة عبر Binance Pay*\n\n"
        "⛔️ تم إلغاء عملية الإيداع.\n\n"
        "📌 معرف الدفع (اضغط للنسخ):\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        "💰 المبلغ المطلوب إرساله عبر Binance:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        "يمكنك إنشاء طلب جديد في أي وقت."
    )


async def _mark_wallet_topup_expired(request_id: str) -> None:
    print("startinggggggggggggggggggggggggggggg")
    request_id = str(request_id or "").strip()
    if not request_id:
        return

    try:
        request = await get_wallet_topup_request(request_id)
        print("request data:---------\n" + str(request))
    except Exception:
        return

    if request is None:
        return
    if str(request.status or "").strip().lower() != "pending":
        return

    try:
        await update_wallet_topup_status(request_id, "expired")
    except Exception:
        return
