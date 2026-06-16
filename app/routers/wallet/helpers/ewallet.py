import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram.types import BufferedInputFile, Message

from app.routers.payment_methods.admin_notifications import format_price
from app.services.payments.ewallet_utils import build_qr_code_image, split_name
from app.services.payments.ewallet_constants import (
    FAWRY_PAYMENT_METHOD_ID,
    MEEZA_PAYMENT_METHOD_ID,
)
from app.routers.wallet.helpers.time_utils import (
    format_duration,
    get_fixed_expiry,
    get_remaining_seconds,
)
from app.routers.wallet.store import create_wallet_topup_request, get_wallet_topup_request, update_wallet_topup_status
from app.services.payments.ewallet import EWalletService, EWalletServiceError
from app.services.payments.payment_method_usage import PaymentMethodUsageService


ewallet_service = EWalletService()
payment_method_usage_service = PaymentMethodUsageService()


async def create_wallet_ewallet_invoice(
    message: Message,
    customer,
    state,
    *,
    phone: str,
) -> None:
    data = await state.get_data()
    payment_method_id = int(data.get("ewallet_payment_method_id") or 0)
    amount = Decimal(str(data.get("topup_amount") or "0"))
    username = str(data.get("wallet_username") or customer.username or "").strip()
    customer_name = (customer.full_name or "").strip()
    first_name, last_name = split_name(customer_name)
    item_name = f"Wallet deposit @{username}" if username else "Wallet deposit"

    try:
        invoice = await ewallet_service.create_invoice(
            payment_method_id=payment_method_id,
            total_egp=amount,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            item_name=item_name,
            item_price=amount,
            quantity=1,
        )
    except EWalletServiceError as error:
        await message.answer(str(error))
        return
    except Exception:
        await message.answer("تعذر إنشاء طلب إيداع المحفظة عبر المحفظة الإلكترونية.")
        return

    request = await create_wallet_topup_request(
        username=username,
        amount=amount,
        currency="EGP",
        payment_method=_format_payment_method_name(invoice.payment_method_id),
        transaction_id=str(invoice.invoice_id),
        customer_name=customer.full_name or "-",
        customer_username=f"@{customer.username}" if customer.username else "-",
        customer_telegram_id=customer.id,
    )

    try:
        await payment_method_usage_service.record_usage(request.payment_method)
    except Exception:
        pass
    await state.clear()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=12)
        if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID
        else get_fixed_expiry()
    )
    if invoice.payment_method_id == MEEZA_PAYMENT_METHOD_ID and invoice.meeza_qr_code:
        qr_bytes = build_qr_code_image(invoice.meeza_qr_code)
        await message.answer_photo(
            BufferedInputFile(qr_bytes, filename=f"wallet_meeza_qr_{invoice.invoice_id}.png"),
        )
        response_message = await message.answer(
            _format_wallet_invoice_message(invoice, amount),
            parse_mode="Markdown",
        )
        asyncio.create_task(
            _run_ewallet_countdown(response_message, invoice, amount, expires_at, request.id)
        )
        return

    response_message = await message.answer(
        _format_wallet_invoice_message(invoice, amount),
        parse_mode="Markdown",
    )
    asyncio.create_task(_run_ewallet_countdown(response_message, invoice, amount, expires_at, request.id))


def _format_payment_method_name(payment_method_id: int) -> str:
    if payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return "Fawry"
    return "Mobile Wallet"


def _format_wallet_invoice_message(
    invoice,
    amount: Decimal,
    remaining_seconds: int | None = None,
) -> str:
    countdown_line = ""
    if remaining_seconds is not None:
        countdown_line = f"⏳ الوقت المتبقي: `{format_duration(remaining_seconds)}`\n\n"

    if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return (
            "💵 *إيداع المحفظة عبر فوري*\n\n"
            "✅ تم تجهيز طلب الإيداع بنجاح.\n\n"
            f"💰 مبلغ الإيداع: `{format_price(amount)} EGP`\n\n"
            "🔢 كود فوري:\n"
            f"`{invoice.fawry_code or '-'}`\n\n"
            f"{countdown_line}"
            "📌 توجه إلى أقرب نقطة فوري واستخدم الكود قبل انتهاء الصلاحية.\n"
            "بعد تأكيد الدفع سيتم مراجعة الإيداع وإضافة الرصيد إلى محفظتك."
        )

    return (
        "📱 *إيداع المحفظة عبر محفظة الموبايل*\n\n"
        "✅ تم تجهيز طلب الإيداع بنجاح.\n\n"
        f"💰 مبلغ الإيداع: `{format_price(amount)} EGP`\n\n"
        "🔢 كود العملية:\n"
        f"`{invoice.meeza_reference or '-'}`\n\n"
        f"{countdown_line}"
        "يمكنك إتمام الإيداع بإحدى الطريقتين:\n\n"
        "1. امسح صورة الـ QR المرسلة بالأعلى لإتمام الدفع مباشرة.\n\n"
        "2. راجع رسائل SMS من مزود الخدمة على رقمك، "
        "واستخدم كود العملية إذا طُلب منك ذلك.\n\n"
        "بعد تأكيد الدفع سيتم مراجعة الإيداع وإضافة الرصيد إلى محفظتك."
    )


async def _run_ewallet_countdown(
    message: Message,
    invoice,
    amount: Decimal,
    expires_at,
    request_id: str,
) -> None:
    remaining = get_remaining_seconds(expires_at)
    if remaining <= 0:
        await _safe_edit_ewallet_message(message, invoice, amount, remaining, expired=True)
        await _mark_wallet_topup_expired(request_id)
        return

    while remaining > 0:
        await asyncio.sleep(1)
        remaining = get_remaining_seconds(expires_at)
        await _safe_edit_ewallet_message(message, invoice, amount, remaining)

    await _safe_edit_ewallet_message(message, invoice, amount, remaining_seconds=0, expired=True)
    await _mark_wallet_topup_expired(request_id)


async def _safe_edit_ewallet_message(
    message: Message,
    invoice,
    amount: Decimal,
    remaining_seconds: int,
    *,
    expired: bool = False,
) -> None:
    try:
        if expired:
            await message.edit_text(
                _format_wallet_invoice_expired_message(invoice, amount),
                parse_mode="Markdown",
            )
            return
        await message.edit_text(
            _format_wallet_invoice_message(invoice, amount, remaining_seconds),
            parse_mode="Markdown",
        )
    except Exception:
        return


def _format_wallet_invoice_expired_message(invoice, amount: Decimal) -> str:
    if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return (
            "💵 *إيداع المحفظة عبر فوري*\n\n"
            "⛔️ انتهت مدة الإيداع وتم إلغاء الطلب.\n\n"
            "🔁 الرجاء إنشاء طلب إيداع جديد والمحاولة مرة أخرى.\n\n"
            f"💰 مبلغ الإيداع: `{format_price(amount)} EGP`\n\n"
            "🔢 كود فوري:\n"
            f"`{invoice.fawry_code or '-'}`\n\n"
            "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
        )

    return (
        "📱 *إيداع المحفظة عبر محفظة الموبايل*\n\n"
        "⛔️ انتهت مدة الإيداع وتم إلغاء الطلب.\n\n"
        "🔁 الرجاء إنشاء طلب إيداع جديد والمحاولة مرة أخرى.\n\n"
        f"💰 مبلغ الإيداع: `{format_price(amount)} EGP`\n\n"
        "🔢 كود العملية:\n"
        f"`{invoice.meeza_reference or '-'}`\n\n"
        "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
    )


async def _mark_wallet_topup_expired(request_id: str) -> None:
    request_id = str(request_id or "").strip()
    if not request_id:
        return

    try:
        request = await get_wallet_topup_request(request_id)
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
