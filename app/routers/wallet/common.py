import asyncio
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ForceReply, Message

from app.config import settings
from app.routers.payment_methods.admin_notifications import (
    INSTAPAY_SCREENSHOT_TRANSACTION_ID,
    format_price,
)
from app.services.payments.ewallet_constants import FAWRY_PAYMENT_METHOD_ID
from app.routers.wallet.helpers import (
    create_wallet_ewallet_invoice,
    edit_wallet_topup_review_message,
    extract_payment_proof,
    format_binance_topup_message,
    format_wallet_topup_review_text,
    notify_customer_about_wallet_topup_rejection,
    notify_admins_about_wallet_topup,
    parse_positive_decimal,
    render_wallet_topup_message,
    run_binance_topup_countdown,
)
from app.routers.wallet.store import (
    WalletTopUpRequest,
    create_wallet_topup_request,
    get_wallet_topup_request,
    update_wallet_topup_status,
    update_wallet_topup_transaction_id,
)
from app.services.payments.binance import BinanceService, BinanceServiceError
from app.services.payments.payment_method_usage import PaymentMethodUsageService
from app.services.payments.exchange_rate import get_egp_exchange_rate, rate_change_handler
from app.services.payments.instapay_settings import get_instapay_phone_number
from app.services.catalog.products import SupabaseConfigError
from app.services.drive_sheets_tool import schedule_drive_sheets_sync
from app.services.messaging.review_messages import (
    WALLET_TOPUP_APPROVED,
    WALLET_TOPUP_REJECTED,
)
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.states.wallet import WalletTopUpState
from app.translations import t


router = Router(name="wallet_common")
wallet_service = WalletService()
binance_service = BinanceService()
payment_method_usage_service = PaymentMethodUsageService()


@router.message(WalletTopUpState.waiting_for_amount)
async def wallet_topup_amount_handler(message: Message, state: FSMContext) -> None:
    amount = parse_positive_decimal(message.text)
    if amount is None:
        await message.answer("أرسل مبلغاً صحيحاً أكبر من صفر.")
        return

    await state.update_data(topup_amount=str(amount))
    data = await state.get_data()
    method_key = str(data.get("topup_method_key") or "")

    if method_key == "binance":
        username = str(data.get("wallet_username") or message.from_user.username or "wallet-user").strip()
        amount_usd = rate_change_handler(amount / get_egp_exchange_rate())
        try:
            request = await create_wallet_topup_request(
                username=username,
                amount=amount,
                currency="EGP",
                payment_method="Binance",
                transaction_id="PENDING_ZENO_CHECKOUT",
                customer_name=message.from_user.full_name or "-",
                customer_username=f"@{message.from_user.username}" if message.from_user.username else "-",
                customer_telegram_id=message.from_user.id,
            )
        except Exception:
            await message.answer("تعذر حفظ طلب شحن المحفظة. حاول مرة أخرى.")
            await state.clear()
            return

        try:
            await payment_method_usage_service.record_usage("Binance")
        except Exception:
            pass

        try:
            instruction = await binance_service.create_payment_instruction(
                order_id=request.id,
                price_amount_usd=amount_usd,
                success_redirect_url="https://example.com/success",
            )
            await update_wallet_topup_transaction_id(request.id, instruction.checkout_id)
            request.transaction_id = instruction.checkout_id
        except BinanceServiceError as error:
            await update_wallet_topup_status(request.id, "failed")
            await message.answer(str(error))
            await state.clear()
            return

        await state.clear()
        response_message = await message.answer(
            format_binance_topup_message(instruction, amount),
            parse_mode="Markdown",
        )
        if instruction.expires_at is not None:
            asyncio.create_task(
                run_binance_topup_countdown(response_message, instruction, amount, request.id)
            )
        return


    if method_key == "instapay":
        await state.set_state(WalletTopUpState.waiting_for_instapay_screenshot)
        await message.answer(
            t("purchase.deposit_instapay_instructions", "ar").format(
                total=format_price(amount),
                phone_number=get_instapay_phone_number(),
            )
        )
        return

    if method_key == "ewallet":
        payment_method_id = int(data.get("ewallet_payment_method_id") or 0)
        if payment_method_id == FAWRY_PAYMENT_METHOD_ID:
            await create_wallet_ewallet_invoice(message, message.from_user, state, phone="null")
            return

        await state.set_state(WalletTopUpState.waiting_for_ewallet_phone)
        await message.answer("أرسل رقم الهاتف الذي ستستخدمه لإيداع محفظة الموبايل.")
        return

    await state.set_state(WalletTopUpState.waiting_for_transaction_id)
    await message.answer("طريقة الإيداع غير صحيحة.")
    await state.clear()


@router.message(WalletTopUpState.waiting_for_transaction_id)
async def wallet_topup_transaction_handler(message: Message, state: FSMContext) -> None:
    transaction_id = (message.text or "").strip()
    if not transaction_id:
        await message.answer("أرسل رقم عملية صحيح بعد إتمام الإيداع.")
        return

    data = await state.get_data()
    amount = Decimal(str(data.get("topup_amount") or "0"))
    payment_method = str(data.get("topup_method") or "")
    username = str(data.get("wallet_username") or message.from_user.username or "").strip()

    request = await create_wallet_topup_request(
        username=username,
        amount=amount,
        currency="EGP",
        payment_method=payment_method,
        transaction_id=transaction_id,
        customer_name=message.from_user.full_name or "-",
        customer_username=f"@{message.from_user.username}" if message.from_user.username else "-",
        customer_telegram_id=message.from_user.id,
    )

    try:
        await payment_method_usage_service.record_usage(payment_method)
    except Exception:
        pass

    await _notify_admins_about_wallet_topup(message, request, payment_proof=None)
    await state.clear()
    await message.answer(
        "تم استلام طلب الإيداع برقم العملية "
        f"{transaction_id}.\n\n"
        "سيقوم الأدمن بمراجعة الطلب، وبعد الموافقة سيتم إضافة الرصيد إلى محفظتك."
    )


@router.message(WalletTopUpState.waiting_for_instapay_screenshot, F.photo | F.document)
async def wallet_topup_instapay_screenshot_handler(message: Message, state: FSMContext) -> None:
    payment_proof = extract_payment_proof(message)
    if payment_proof is None:
        await message.answer(t("purchase.invalid_instapay_screenshot", "ar"))
        return

    data = await state.get_data()
    amount = Decimal(str(data.get("topup_amount") or "0"))
    payment_method = str(data.get("topup_method") or "")
    username = str(data.get("wallet_username") or message.from_user.username or "").strip()

    request = await create_wallet_topup_request(
        username=username,
        amount=amount,
        currency="EGP",
        payment_method=payment_method,
        transaction_id=INSTAPAY_SCREENSHOT_TRANSACTION_ID,
        payment_proof_file_id=payment_proof.file_id,
        payment_proof_type=payment_proof.file_type,
        customer_name=message.from_user.full_name or "-",
        customer_username=f"@{message.from_user.username}" if message.from_user.username else "-",
        customer_telegram_id=message.from_user.id,
    )

    try:
        await payment_method_usage_service.record_usage(payment_method)
    except Exception:
        pass

    await notify_admins_about_wallet_topup(message, request, payment_proof=payment_proof)
    await state.clear()
    await message.answer(
        "تم استلام صورة إثبات الدفع.\n\n"
        "سيقوم الأدمن بمراجعة طلب الإيداع، وبعد الموافقة سيتم إضافة الرصيد إلى محفظتك."
    )


@router.message(WalletTopUpState.waiting_for_instapay_screenshot)
async def invalid_wallet_topup_instapay_screenshot_handler(message: Message) -> None:
    await message.answer(t("purchase.invalid_instapay_screenshot", "ar"))


@router.callback_query(F.data.startswith("wallet:review:"))
async def wallet_review_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.admin_user_ids:
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return

    _, _, action, request_id = parts
    request = await get_wallet_topup_request(request_id)
    if request is None:
        await callback.answer("طلب الإيداع غير موجود.", show_alert=True)
        return

    if request.status != "pending":
        await callback.answer("تمت معالجة طلب الإيداع مسبقاً.", show_alert=True)
        return

    if action == "reject":
        await state.set_state(WalletTopUpState.waiting_for_rejection_message)
        await state.update_data(
            wallet_rejection_request_id=request.id,
            wallet_rejection_message_id=callback.message.message_id if callback.message else None,
            wallet_rejection_chat_id=callback.message.chat.id if callback.message else None,
            wallet_rejection_has_caption=callback.message.caption is not None if callback.message else False,
        )
        await callback.answer()
        await callback.message.answer(
            "أرسل الرسالة التي تريد إرسالها للمستخدم بسبب رفض طلب الإيداع.",
            reply_markup=ForceReply(selective=True),
        )
        return

    if action != "approve":
        await callback.answer()
        return

    try:
        updated_wallet = await wallet_service.apply_topup(
            username=request.username,
            amount_egp=_get_topup_amount_egp(request),
        )
    except SupabaseConfigError:
        await callback.answer(t("sections.supabase_not_configured", "ar"), show_alert=True)
        return
    except WalletServiceError as error:
        await callback.answer(str(error), show_alert=True)
        return
    except Exception:
        await callback.answer("حدث خطأ أثناء إضافة الرصيد إلى المحفظة.", show_alert=True)
        return

    request = await update_wallet_topup_status(request.id, "approved") or request
    schedule_drive_sheets_sync(f"wallet_topup:{request.id}")
    await callback.answer("تمت الموافقة على طلب الإيداع.")
    if callback.message:
        await edit_wallet_topup_review_message(callback.message, format_wallet_topup_review_text(request))

    customer_telegram_id = request.customer_telegram_id
    if customer_telegram_id:
        try:
                await callback.bot.send_message(
                    chat_id=customer_telegram_id,
                    text=(
                        "✅ "
                        + render_wallet_topup_message(
                            request,
                            WALLET_TOPUP_APPROVED,
                            balance_egp=updated_wallet.balance_egp,
                            balance_usd=updated_wallet.balance_usd,
                        )
                    ),
                )
        except Exception:
            pass


@router.message(WalletTopUpState.waiting_for_rejection_message)
async def wallet_rejection_message_handler(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in settings.admin_user_ids:
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    rejection_message = (message.text or "").strip()
    if not rejection_message:
        await message.answer("أرسل رسالة صالحة لإرسالها للمستخدم.")
        return

    data = await state.get_data()
    request_id = str(data.get("wallet_rejection_request_id") or "").strip()
    review_message_id = data.get("wallet_rejection_message_id")
    review_chat_id = data.get("wallet_rejection_chat_id")
    has_caption = bool(data.get("wallet_rejection_has_caption"))

    if not request_id:
        await state.clear()
        await message.answer("طلب الإيداع غير موجود.")
        return

    request = await get_wallet_topup_request(request_id)
    if request is None:
        await state.clear()
        await message.answer("طلب الإيداع غير موجود.")
        return

    if request.status != "pending":
        await state.clear()
        await message.answer("تمت معالجة طلب الإيداع مسبقاً.")
        return

    request = await update_wallet_topup_status(request.id, "rejected") or request
    await _edit_wallet_review_message_by_id(
        message,
        request,
        review_chat_id=review_chat_id,
        review_message_id=review_message_id,
        has_caption=has_caption,
    )
    if request.customer_telegram_id:
        try:
            await message.bot.send_message(
                chat_id=request.customer_telegram_id,
                text=f"❌ {render_wallet_topup_message(request, WALLET_TOPUP_REJECTED)}",
            )
        except Exception:
            pass
    await notify_customer_about_wallet_topup_rejection(message, request, f"السبب:\n{rejection_message}")
    await state.clear()
    await message.answer("تم رفض طلب الإيداع وإرسال رسالتك للمستخدم.")


@router.callback_query(F.data.startswith("wallet:topup:cancel:"))
async def wallet_topup_cancel_handler(callback: CallbackQuery) -> None:
    request_id = callback.data.rsplit(":", maxsplit=1)[-1]
    request = await get_wallet_topup_request(request_id)
    if request is None:
        await callback.answer()
        return

    if str(request.status or "").strip().lower() != "pending":
        await callback.answer()
        return

    await update_wallet_topup_status(request.id, "expired")

    try:
        from app.routers.wallet.helpers.binance import mark_wallet_topup_countdown_cancelled
        from app.routers.wallet.helpers.ewallet import mark_wallet_topup_countdown_cancelled as mark_ewallet_countdown_cancelled

        if request.transaction_id:
            mark_wallet_topup_countdown_cancelled(request.transaction_id)
        mark_ewallet_countdown_cancelled(request.id)
    except Exception:
        pass

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.answer(t("wallet.topup_cancelled", "ar"))


def _get_topup_amount_egp(request: WalletTopUpRequest) -> Decimal:
    if request.currency.upper() == "USD":
        return request.amount * get_egp_exchange_rate()

    return request.amount


async def _edit_wallet_review_message_by_id(
    message: Message,
    request: WalletTopUpRequest,
    *,
    review_chat_id: object,
    review_message_id: object,
    has_caption: bool,
) -> None:
    if not isinstance(review_chat_id, int) or not isinstance(review_message_id, int):
        return

    text = format_wallet_topup_review_text(request)
    try:
        if has_caption:
            await message.bot.edit_message_caption(
                chat_id=review_chat_id,
                message_id=review_message_id,
                caption=text,
                reply_markup=None,
            )
            return

        await message.bot.edit_message_text(
            chat_id=review_chat_id,
            message_id=review_message_id,
            text=text,
            reply_markup=None,
        )
    except Exception:
        return


