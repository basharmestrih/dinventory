import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.routers.payment_methods.helpers.services import order_service
from app.routers.payment_methods.helpers.credential_utils import get_order_payment_cancel_keyboard
from app.services.payments.binance import BinanceService, BinanceServiceError
from app.services.payments.binance_countdown import (
    is_checkout_active,
    is_checkout_cancelled,
    mark_checkout_paid,
    start_checkout_countdown,
)
from app.services.payments.binance_settings import get_binance_id
from app.services.payments.exchange_rate import get_egp_exchange_rate
from app.services.orders.orders import OrderServiceError
from app.services.payments.payment_methods import PAYMENT_METHOD_BINANCE, is_payment_method_enabled
from app.services.catalog.products import SupabaseConfigError
from app.states.purchase import PurchaseState
from app.translations import t


router = Router(name="payment_binance")
binance_service = BinanceService()
_BINANCE_COUNTDOWN_SECONDS = 60 * 60


@router.callback_query(F.data == "payment:binance", PurchaseState.choosing_payment_method)
async def binance_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_BINANCE):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(payment_method="Binance")
    data = await state.get_data()

    exchange_rate = get_egp_exchange_rate()
    total = Decimal(str(data["total"]))
    usd_total = total / exchange_rate

    try:
        pending_order = await order_service.create_order(
            data,
            "PENDING_ZENO_CHECKOUT",
            callback.from_user,
        )
        instruction = await binance_service.create_payment_instruction(
            order_id=str(pending_order.id),
            price_amount_usd=usd_total,
            success_redirect_url="https://example.com/success",
        )
        updated_order = await order_service.update_order_transaction_id(
            pending_order.id,
            instruction.checkout_id,
        )
        if updated_order is None:
            raise OrderServiceError("Order was created but checkout id could not be saved.")
    except SupabaseConfigError:
        await callback.answer()
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await callback.answer()
        await callback.message.answer(
            t("purchase.order_create_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except BinanceServiceError as error:
        await callback.answer()
        await callback.message.answer(str(error))
        return
    except Exception:
        await callback.answer()
        await callback.message.answer(t("purchase.order_create_failed", "ar"))
        return

    await state.clear()
    await callback.answer()
    response_message = await callback.message.answer(
        _format_binance_message(instruction),
        parse_mode="Markdown",
        reply_markup=get_order_payment_cancel_keyboard(pending_order.id),
    )

    if instruction.expires_at is not None:
        _start_binance_countdown(response_message, instruction, pending_order.id)


def mark_binance_checkout_paid(checkout_id: str) -> None:
    mark_checkout_paid(checkout_id)


def _start_binance_countdown(message: Message, instruction, order_id: int) -> None:
    checkout_id = str(getattr(instruction, "checkout_id", "") or "").strip()
    if not checkout_id:
        return
    start_checkout_countdown(checkout_id)
    asyncio.create_task(_run_binance_countdown(message, instruction, checkout_id, order_id))


def _format_binance_message(instruction, remaining_seconds: int | None = None) -> str:
    countdown_line = ""
    if remaining_seconds is not None:
        countdown_line = f"⏳ الوقت المتبقي: `{_format_duration(remaining_seconds)}`\n\n"

    return (
        "💳 *الدفع عبر Binance Pay*\n\n"
        "📌 معرّف الدفع (اضغط للنسخ):\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        f"💰 المبلغ المطلوب بعملة USDT:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        f"{countdown_line}"
        "⚠️ تأكد من إرسال القيمة المحددة عبر Binance Pay.\n"
        "🚀 سيتم تأكيد الدفع تلقائياً خلال دقائق."
    )


async def _run_binance_countdown(message: Message, instruction, checkout_id: str, order_id: int) -> None:
    expires_at = instruction.expires_at
    if expires_at is None:
        return

    now = datetime.now(timezone.utc)
    expires_at_utc = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    countdown_deadline = min(expires_at_utc, now + timedelta(seconds=_BINANCE_COUNTDOWN_SECONDS))

    remaining = _get_remaining_seconds(countdown_deadline)
    if remaining <= 0:
        await _safe_edit_message(message, instruction, remaining, order_id=order_id, expired=True)
        await _mark_order_expired(instruction)
        return

    while remaining > 0:
        await asyncio.sleep(1)
        if is_checkout_cancelled(checkout_id):
            await _safe_edit_message(message, instruction, remaining_seconds=0, order_id=order_id, expired=True)
            return
        if not is_checkout_active(checkout_id):
            await _safe_edit_message(message, instruction, remaining_seconds=0, order_id=order_id, paid=True)
            return
        remaining = _get_remaining_seconds(countdown_deadline)
        await _safe_edit_message(message, instruction, remaining, order_id=order_id)

    await _safe_edit_message(message, instruction, remaining_seconds=0, order_id=order_id, expired=True)
    await _mark_order_expired(instruction)


def _get_remaining_seconds(expires_at: datetime) -> int:
    target = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining = int((target - now).total_seconds())
    return remaining if remaining > 0 else 0


def _format_duration(seconds: int) -> str:
    seconds = max(seconds, 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_usdt_amount(value: Decimal) -> str:
    return f"{value:.2f}"


async def _mark_order_expired(instruction) -> None:
    order_id_text = str(getattr(instruction, "order_id", "") or "").strip()
    if not order_id_text:
        return

    try:
        order_id = int(order_id_text)
    except ValueError:
        return

    try:
        current_order = await order_service.fetch_order_by_id(order_id)
    except (SupabaseConfigError, OrderServiceError):
        return

    if current_order is None:
        return
    if current_order.status.strip().lower() != "pending":
        return

    try:
        await order_service.update_order_status(order_id, "expired")
    except (SupabaseConfigError, OrderServiceError):
        return


async def _safe_edit_message(
    message: Message,
    instruction,
    remaining_seconds: int,
    *,
    order_id: int,
    paid: bool = False,
    expired: bool = False,
) -> None:
    try:
        if paid:
            await message.edit_text(
                _format_binance_paid_message(instruction),
                parse_mode="Markdown",
            )
            return
        if expired:
            await message.edit_text(
                _format_binance_expired_message(instruction),
                parse_mode="Markdown",
            )
            return
        await message.edit_text(
            _format_binance_message(instruction, remaining_seconds),
            parse_mode="Markdown",
            reply_markup=get_order_payment_cancel_keyboard(order_id),
        )
    except Exception:
        return


def _format_binance_paid_message(instruction) -> str:
    return (
        "💳 *الدفع عبر Binance Pay*\n\n"
        "✅ تم تأكيد الدفع بنجاح.\n\n"
        "📌 معرّف الدفع (اضغط للنسخ):\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        f"💰 المبلغ المطلوب بعملة USDT:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        "🚀 سيتم إرسال تفاصيل الطلب بعد المعالجة."
    )


def _format_binance_expired_message(instruction) -> str:
    return (
        "💳 *الدفع عبر Binance Pay*\n\n"
        "⛔️ انتهت مدة الدفع وتم إلغاء الطلب.\n\n"
        "🔁 الرجاء إنشاء طلب جديد والمحاولة مرة أخرى.\n\n"
        "📌 معرّف الدفع (اضغط للنسخ):\n"
        f"`{get_binance_id() or instruction.deposit_account_id}`\n\n"
        f"💰 المبلغ المطلوب بعملة USDT:\n"
        f"`{instruction.token_pay_amount} USDT`\n\n"
        "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
    )
