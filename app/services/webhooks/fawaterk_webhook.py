from __future__ import annotations

from dataclasses import dataclass
import logging
from types import SimpleNamespace

from aiogram import Bot

from app.routers.payment_methods.helpers.customer_notifications import (
    notify_customer_about_server_error,
    notify_customer_about_processed_order,
)
from app.routers.payment_methods.helpers.order_processing import process_paid_order
from app.routers.payment_methods.helpers.services import order_service
from app.routers.payment_methods.admin_notifications import format_price
from app.services.orders.orders import OrderServiceError
from app.services.catalog.products import ProductServiceError, SupabaseConfigError
from app.services.payments.fawaterk_invoice_countdown import mark_invoice_paid
from app.services.wallets.topups import WalletTopUpService, WalletTopUpServiceError
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.services.drive_sheets_tool import schedule_drive_sheets_sync


logger = logging.getLogger(__name__)
wallet_service = WalletService()
wallet_topup_service = WalletTopUpService()


class FawaterkWebhookError(RuntimeError):
    """Raised when a Fawaterk webhook cannot be applied."""


@dataclass(slots=True)
class FawaterkWebhookResult:
    handled: bool
    target: str
    message: str


async def handle_fawaterk_invoice_webhook(payload: dict, bot: Bot) -> FawaterkWebhookResult:
    invoice_status = str(payload.get("invoice_status") or "").strip().lower()
    logger.info("Fawaterk webhook processing started: invoice_status=%s", invoice_status or "-")
    if invoice_status != "paid":
        logger.info("Fawaterk webhook ignored: invoice_status=%s", invoice_status or "-")
        return FawaterkWebhookResult(False, "ignored", f"Ignored invoice status: {invoice_status or '-'}")

    invoice_id = str(payload.get("invoice_id") or "").strip()
    if not invoice_id:
        raise FawaterkWebhookError("Webhook payload is missing invoice_id.")

    wallet_result = await _handle_wallet_topup(invoice_id=invoice_id, bot=bot)
    if wallet_result is not None:
        return wallet_result

    return await _handle_purchase_order(invoice_id=invoice_id, bot=bot)


async def _handle_wallet_topup(*, invoice_id: str, bot: Bot) -> FawaterkWebhookResult | None:
    try:
        request = await wallet_topup_service.fetch_topup_by_transaction_id(invoice_id)
    except (SupabaseConfigError, WalletTopUpServiceError) as error:
        raise FawaterkWebhookError(str(error)) from error

    if request is None:
        logger.info("Fawaterk webhook did not match wallet topup: invoice_id=%s", invoice_id)
        return None

    logger.info(
        "Fawaterk webhook matched wallet topup: request_id=%s username=%s status=%s amount=%s",
        request.id,
        request.username,
        request.status,
        request.amount,
    )
    if not _is_ewallet_payment_method(request.payment_method):
        raise FawaterkWebhookError("Matched wallet topup is not an EWallet request.")
    if request.status == "approved":
        logger.info("Fawaterk webhook wallet topup already approved: request_id=%s", request.id)
        return FawaterkWebhookResult(True, "wallet", "Wallet topup was already approved.")
    if request.status != "pending":
        raise FawaterkWebhookError(f"Wallet topup is not pending: {request.status}.")
    if request.currency.upper() != "EGP":
        raise FawaterkWebhookError("Matched EWallet wallet topup is not stored in EGP.")

    try:
        updated_wallet = await wallet_service.apply_topup(
            username=request.username,
            amount_egp=request.amount,
        )
        await wallet_topup_service.update_status(request.id, "approved")
    except (SupabaseConfigError, WalletServiceError, WalletTopUpServiceError) as error:
        raise FawaterkWebhookError(str(error)) from error

    if request.customer_telegram_id:
        try:
            await bot.send_message(
                chat_id=request.customer_telegram_id,
                text=(
                    "تم تأكيد إيداع المحفظة تلقائياً.\n\n"
                    f"المبلغ: {format_price(request.amount)} جنيه مصري\n"
                    f"رصيدك الحالي بالجنيه المصري: {format_price(updated_wallet.balance_egp)}\n"
                    f"رصيدك الحالي بالدولار: {format_price(updated_wallet.balance_usd)}"
                ),
            )
        except Exception:
            pass

    logger.info("Fawaterk webhook approved wallet topup: request_id=%s username=%s", request.id, request.username)
    schedule_drive_sheets_sync(reason=f"wallet_topup_approved:{request.id}")
    return FawaterkWebhookResult(True, "wallet", f"Approved wallet topup {request.id}.")


async def _handle_purchase_order(*, invoice_id: str, bot: Bot) -> FawaterkWebhookResult:
    try:
        current_order = await order_service.fetch_order_by_transaction_id(invoice_id)
    except (SupabaseConfigError, OrderServiceError) as error:
        raise FawaterkWebhookError(str(error)) from error

    if current_order is None:
        raise FawaterkWebhookError("Pending order was not found for this invoice_id.")
    logger.info(
        "Fawaterk webhook matched order: order_id=%s status=%s payment_method=%s transaction_id=%s",
        current_order.id,
        current_order.status,
        current_order.payment_method,
        current_order.transaction_id,
    )
    if not _is_ewallet_payment_method(current_order.payment_method):
        raise FawaterkWebhookError("Matched order is not an EWallet order.")
    if current_order.status == "Paid":
        logger.info("Fawaterk webhook order already paid: order_id=%s", current_order.id)
        return FawaterkWebhookResult(True, "order", f"Order {current_order.id} was already paid.")
    if current_order.status.strip().lower() == "expired":
        logger.info("Fawaterk webhook ignored: order is expired: order_id=%s", current_order.id)
        return FawaterkWebhookResult(True, "ignored", f"Order {current_order.id} is expired.")
    if current_order.status != "pending":
        raise FawaterkWebhookError(f"Order is not pending: {current_order.status}.")

    # Stop the customer countdown as soon as payment is confirmed.
    mark_invoice_paid(invoice_id)

    try:
        updated_order, product, error_message, order_action_label = await process_paid_order(current_order)
    except (SupabaseConfigError, OrderServiceError, ProductServiceError) as error:
        await notify_customer_about_server_error(SimpleNamespace(bot=bot), current_order)
        raise FawaterkWebhookError(str(error)) from error

    if updated_order is None:
        await notify_customer_about_server_error(SimpleNamespace(bot=bot), current_order)
        raise FawaterkWebhookError(error_message or "Order could not be marked as paid.")

    if updated_order.status == "ActivationPending":
        from app.routers.payment_methods.admin_notifications import notify_admins_about_order

        await notify_admins_about_order(SimpleNamespace(bot=bot), updated_order)

    await notify_customer_about_processed_order(
        context=SimpleNamespace(bot=bot),
        updated_order=updated_order,
        product=product,
        order_action_label=order_action_label,
    )
    logger.info("Fawaterk webhook marked order paid and notified customer: order_id=%s", updated_order.id)
    return FawaterkWebhookResult(True, "order", f"Marked order {updated_order.id} as paid.")


def _is_ewallet_payment_method(method: str) -> bool:
    normalized = (method or "").strip()
    if not normalized:
        return False

    allowed = {
        "Mobile Wallet",
        "Fawry",
    }
    return normalized in allowed
