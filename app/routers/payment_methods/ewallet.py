import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.routers.wallet.helpers.time_utils import (
    format_duration,
    get_fixed_expiry,
    get_remaining_seconds,
)
from app.services.payments.fawaterk_invoice_countdown import (
    is_invoice_active,
    start_invoice_countdown,
)
from app.services.payments.ewallet_constants import (
    FAWRY_PAYMENT_METHOD_ID,
    MEEZA_PAYMENT_METHOD_ID,
)
from app.routers.payment_methods.helpers.services import order_service
from app.services.payments.ewallet_utils import build_qr_code_image, is_valid_phone, split_name
from app.services.payments.ewallet import EWalletService, EWalletServiceError
from app.services.orders.orders import OrderServiceError
from app.services.payments.payment_methods import (
    PAYMENT_METHOD_EWALLET,
    PAYMENT_METHOD_FAWRY,
    is_payment_method_enabled,
)
from app.services.catalog.products import SupabaseConfigError
from app.states.purchase import PurchaseState
from app.translations import t


router = Router(name="payment_ewallet")
ewallet_service = EWalletService()

@router.callback_query(F.data == "payment:ewallet", PurchaseState.choosing_payment_method)
async def ewallet_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_EWALLET):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        payment_method="Mobile Wallet",
        ewallet_payment_method_id=MEEZA_PAYMENT_METHOD_ID,
    )
    await callback.answer()
    await state.set_state(PurchaseState.waiting_for_ewallet_phone)
    await callback.message.answer("أرسل رقم الهاتف الذي ستستخدمه في الدفع.")


@router.callback_query(F.data == "payment:fawry", PurchaseState.choosing_payment_method)
async def fawry_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_FAWRY):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        payment_method="Fawry",
        ewallet_payment_method_id=FAWRY_PAYMENT_METHOD_ID,
    )
    await callback.answer()
    await _create_ewallet_invoice(callback.message, callback.from_user, state, phone="null")


@router.message(PurchaseState.waiting_for_ewallet_phone)
async def ewallet_phone_handler(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not is_valid_phone(phone):
        await message.answer("أرسل رقم هاتف صحيح لاستخدامه في عملية الدفع.")
        return

    await _create_ewallet_invoice(message, message.from_user, state, phone=phone)


async def _create_ewallet_invoice(message, customer, state: FSMContext, *, phone: str) -> None:
    data = await state.get_data()
    payment_method_id = int(data.get("ewallet_payment_method_id") or 0)
    #making total global variable
    total = Decimal(str(data.get("total") or "0"))
    unit_price = Decimal(str(data.get("product_price") or total))
    quantity = int(data.get("quantity") or 1)
    product_title = str(data.get("product_title") or "طلب جديد")
    customer_name = (customer.full_name or "").strip()
    first_name, last_name = split_name(customer_name)

    try:
        pending_order = await order_service.create_order(
            data,
            "PENDING_FAWATERK_INVOICE",
            customer,
        )
        invoice = await ewallet_service.create_invoice(
            payment_method_id=payment_method_id,
            total_egp=total,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            item_name=product_title,
            item_price=unit_price,
            quantity=quantity,
        )
        print("invoice data:", invoice)
        updated_order = await order_service.update_order_transaction_id(
            pending_order.id,
            str(invoice.invoice_id),
        )
        if updated_order is None:
            raise OrderServiceError("Order was created but invoice id could not be saved.")
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await message.answer(
            t("purchase.order_create_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except EWalletServiceError as error:
        await message.answer(str(error))
        return
    except Exception:
        await message.answer(t("purchase.order_create_failed", "ar"))
        return

    await state.clear()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=12)
        if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID
        else get_fixed_expiry()
    )
    start_invoice_countdown(str(invoice.invoice_id))
    if invoice.payment_method_id == MEEZA_PAYMENT_METHOD_ID and invoice.meeza_qr_code:
        qr_bytes = build_qr_code_image(invoice.meeza_qr_code)
        await message.answer_photo(
            BufferedInputFile(qr_bytes, filename=f"meeza_qr_{invoice.invoice_id}.png"),
        )
        response_message = await message.answer(
            _format_invoice_message(invoice,total=str(total)),
            parse_mode="Markdown",
        )
        asyncio.create_task(
            _run_ewallet_order_countdown(response_message, invoice, expires_at,total=str(total))
        )
        return

    response_message = await message.answer(
        _format_invoice_message(invoice,total=str(total)),
        parse_mode="Markdown",
    )
    asyncio.create_task(_run_ewallet_order_countdown(response_message, invoice, expires_at,total=str(total)))


def _format_invoice_message(invoice, remaining_seconds: int | None = None, total: str | None = None) -> str:
    countdown_line = ""
    if remaining_seconds is not None:
        countdown_line = f"⏳ الوقت المتبقي: `{format_duration(remaining_seconds)}`\n\n"

    if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return (
            "💵 *الدفع عبر فوري*\n\n"
            "✅ تم تجهيز طلب الدفع بنجاح.\n\n"
            #add amount
            f"💰 مبلغ الدفع: `{total} جنيه مصري`\n\n"
            "🔢 كود فوري:\n"
            f"`{invoice.fawry_code or '-'}`\n\n"
            f"{countdown_line}"
            "📌 توجّه إلى أقرب نقطة فوري واستخدم الكود قبل انتهاء الصلاحية."
        )

    return (
        "📱 *الدفع عبر محفظة الموبايل*\n\n"
        "✅ تم تجهيز طلب الدفع بنجاح.\n\n"
         f"💰 مبلغ الدفع: `{total} جنيه مصري`\n\n"
        "🔢 كود العملية:\n"
        f"`{invoice.meeza_reference or '-'}`\n\n"
        f"{countdown_line}"
        "⚠️ يمكنك اختيار *أحد الطريقتين* التالية لإتمام الدفع:\n\n"
        "1. 🧾 امسح صورة الـ QR المرسلة بالأعلى لإتمام الدفع مباشرة.\n\n"
        "2. 📩  راجع رسائل SMS من مزود الخدمة على رقمك، "
        "واستخدم كود العملية إذا طُلب منك ذلك.\n\n"
        "✅ سيتم تنفيذ الطلب تلقائياً بمجرد اكتمال الدفع."
    )


async def _run_ewallet_order_countdown(
    message: Message,
    invoice,
    expires_at,
    total:str,
) -> None:
    invoice_id = str(getattr(invoice, "invoice_id", "") or "").strip()
    remaining = get_remaining_seconds(expires_at)
    if remaining <= 0:
        await _safe_edit_ewallet_order_message(message, invoice, remaining, expired=True,total=str(total))
        await _mark_ewallet_order_expired(invoice)
        return

    while remaining > 0:
        await asyncio.sleep(1)
        if invoice_id and not is_invoice_active(invoice_id):
            await _safe_edit_ewallet_order_message(message, invoice, remaining_seconds=0, paid=True,total=str(total))
            return
        remaining = get_remaining_seconds(expires_at)
        await _safe_edit_ewallet_order_message(message, invoice, remaining,total=str(total))

    await _safe_edit_ewallet_order_message(message, invoice, remaining_seconds=0, expired=True,total=str(total))
    await _mark_ewallet_order_expired(invoice)


async def _safe_edit_ewallet_order_message(
    message: Message,
    invoice,
    remaining_seconds: int,
    *,
    total:str,
    paid: bool = False,
    expired: bool = False,
) -> None:
    try:
        if paid:
            await message.edit_text(
                _format_invoice_paid_message(invoice),
                parse_mode="Markdown",
            )
            return
        if expired:
            await message.edit_text(
                _format_invoice_expired_message(invoice),
                parse_mode="Markdown",
            )
            return
        await message.edit_text(
            _format_invoice_message(invoice, remaining_seconds,total=str(total)),
            parse_mode="Markdown",
        )
    except Exception:
        return


def _format_invoice_paid_message(invoice) -> str:
    if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return (
            "💵 *الدفع عبر فوري*\n\n"
            "✅ تم تأكيد الدفع بنجاح.\n\n"
            "🔢 كود فوري:\n"
            f"`{invoice.fawry_code or '-'}`\n\n"
            "🚀 سيتم إرسال تفاصيل الطلب بعد المعالجة."
        )

    return (
        "📱 *الدفع عبر محفظة الموبايل*\n\n"
        "✅ تم تأكيد الدفع بنجاح.\n\n"
        "🔢 كود العملية:\n"
        f"`{invoice.meeza_reference or '-'}`\n\n"
        "🚀 سيتم إرسال تفاصيل الطلب بعد المعالجة."
    )


def _format_invoice_expired_message(invoice) -> str:
    if invoice.payment_method_id == FAWRY_PAYMENT_METHOD_ID:
        return (
            "💵 *الدفع عبر فوري*\n\n"
            "⛔️ انتهت مدة الدفع وتم إلغاء الطلب.\n\n"
            "🔁 الرجاء إنشاء طلب جديد والمحاولة مرة أخرى.\n\n"
            "🔢 كود فوري:\n"
            f"`{invoice.fawry_code or '-'}`\n\n"
            "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
        )

    return (
        "📱 *الدفع عبر محفظة الموبايل*\n\n"
        "⛔️ انتهت مدة الدفع وتم إلغاء الطلب.\n\n"
        "🔁 الرجاء إنشاء طلب جديد والمحاولة مرة أخرى.\n\n"
        "🔢 كود العملية:\n"
        f"`{invoice.meeza_reference or '-'}`\n\n"
        "✅ إذا كنت قد قمت بالدفع بعد انتهاء المدة، تواصل مع الدعم."
    )


async def _mark_ewallet_order_expired(invoice) -> None:
    invoice_id = str(getattr(invoice, "invoice_id", "") or "").strip()
    if not invoice_id:
        return

    try:
        current_order = await order_service.fetch_order_by_transaction_id(invoice_id)
    except (SupabaseConfigError, OrderServiceError):
        return

    if current_order is None:
        return
    if current_order.status.strip().lower() != "pending":
        return

    try:
        await order_service.update_order_status(current_order.id, "expired")
    except (SupabaseConfigError, OrderServiceError):
        return
