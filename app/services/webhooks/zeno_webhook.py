from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import logging
from types import SimpleNamespace

from aiogram import Bot

from app.config import settings
from app.routers.payment_methods.helpers.customer_notifications import (
    notify_customer_about_server_error,
    notify_customer_about_processed_order,
)
from app.routers.payment_methods.helpers.order_processing import process_paid_order
from app.routers.payment_methods.helpers.services import order_service
from app.routers.payment_methods.admin_notifications import format_price
from app.routers.wallet.store import get_wallet_topup_request, update_wallet_topup_status
from app.services.payments.exchange_rate import get_egp_exchange_rate, rate_change_handler
from app.services.payments.binance_countdown import mark_checkout_paid
from app.services.orders.orders import OrderServiceError
from app.services.catalog.products import ProductServiceError, SupabaseConfigError
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.services.drive_sheets_tool import schedule_drive_sheets_sync


logger = logging.getLogger(__name__)


class ZenoWebhookError(RuntimeError):
    """Raised when a Zeno webhook cannot be applied."""


@dataclass(slots=True)
class ZenoWebhookResult:
    handled: bool
    target: str
    message: str


wallet_service = WalletService()


async def handle_zeno_checkout_webhook(payload: dict, bot: Bot) -> ZenoWebhookResult:
    event_type = str(payload.get("type") or "").strip()
    logger.info("Zeno webhook processing started: event_type=%s", event_type or "-")
    if event_type != "checkout.completed":
        logger.info("Zeno webhook ignored: event_type=%s", event_type or "-")
        return ZenoWebhookResult(False, "ignored", f"Ignored event type: {event_type or '-'}")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ZenoWebhookError("Webhook payload is missing data.")

    checkout_id = str(data.get("id") or "").strip()
    order_id = str(data.get("orderId") or "").strip()
    status = str(data.get("status") or "").strip().upper()
    price_currency = str(data.get("priceCurrency") or "").strip().upper()
    price_amount = _parse_decimal(data.get("priceAmount"))
    paid_amount = _parse_decimal(data.get("paidAmount"))

    if not checkout_id:
        raise ZenoWebhookError("Webhook data is missing checkout id.")
    if not order_id:
        raise ZenoWebhookError("Webhook data is missing orderId.")
    if status != "COMPLETED":
        logger.info("Zeno webhook ignored: checkout_id=%s order_id=%s status=%s", checkout_id, order_id, status or "-")
        return ZenoWebhookResult(False, "ignored", f"Ignored checkout status: {status or '-'}")
    if price_currency != "USD":
        raise ZenoWebhookError(f"Unsupported checkout currency: {price_currency or '-'}.")
    if price_amount is None or price_amount <= 0:
        raise ZenoWebhookError("Webhook data has an invalid priceAmount.")
    if paid_amount is None or paid_amount < price_amount:
        raise ZenoWebhookError("Webhook paidAmount is less than priceAmount.")

    if order_id.startswith("wallet-topup-"):
        raise ZenoWebhookError(
            "This wallet checkout was created by the old flow. Create a new topup so it can be matched by id."
        )

    wallet_result = await _handle_wallet_topup(
        order_id=order_id,
        checkout_id=checkout_id,
        price_amount_usd=price_amount,
        paid_amount_usd=paid_amount,
        bot=bot,
    )
    if wallet_result is not None:
        return wallet_result

    return await _handle_purchase_order(
        price_amount=price_amount,
        checkout_id=checkout_id,
        bot=bot,
    )


async def _handle_wallet_topup(
    *,
    order_id: str,
    checkout_id: str,
    price_amount_usd: Decimal,
    paid_amount_usd: Decimal,
    bot: Bot,
) -> ZenoWebhookResult | None:
    request = await get_wallet_topup_request(order_id)
    if request is None:
        logger.info("Zeno webhook did not match wallet topup: order_id=%s checkout_id=%s", order_id, checkout_id)
        return None

    logger.info(
        "Zeno webhook matched wallet topup: request_id=%s username=%s status=%s amount=%s",
        request.id,
        request.username,
        request.status,
        request.amount,
    )
    if request.payment_method.strip().lower() != "binance":
        raise ZenoWebhookError("Matched wallet topup is not a Binance request.")
    if request.transaction_id != checkout_id:
        raise ZenoWebhookError("Webhook checkout id does not match the pending wallet topup.")
    if request.status == "approved":
        logger.info("Zeno webhook wallet topup already approved: request_id=%s", request.id)
        return ZenoWebhookResult(True, "wallet", "Wallet topup was already approved.")
    if request.status != "pending":
        raise ZenoWebhookError(f"Wallet topup is not pending: {request.status}.")
    if request.currency.upper() != "EGP":
        raise ZenoWebhookError("Matched Binance wallet topup is not stored in EGP.")

    #expected_price_amount_usd = _to_wallet_usd_checkout_amount(request.amount)
    #if price_amount_usd != expected_price_amount_usd:
       # raise ZenoWebhookError("Webhook amount does not match the pending wallet topup.")

    amount_egp = request.amount
    try:
        updated_wallet = await wallet_service.apply_topup(
            username=request.username,
            amount_egp=amount_egp,
        )
    except (SupabaseConfigError, WalletServiceError) as error:
        raise ZenoWebhookError(str(error)) from error

    request = await update_wallet_topup_status(request.id, "approved") or request
    if request.transaction_id:
        from app.routers.wallet.helpers.binance import mark_binance_topup_paid

        mark_binance_topup_paid(request.transaction_id)
    logger.info(
        "Zeno webhook approved wallet topup: request_id=%s username=%s amount_usd=%s amount_egp=%s",
        request.id,
        request.username,
        #expected_price_amount_usd,
        amount_egp,
    )
    if request.customer_telegram_id:
        try:
            await bot.send_message(
                chat_id=request.customer_telegram_id,
                text=(
                    "تم تأكيد إيداع Binance تلقائياً.\n\n"
                    f"المبلغ: {format_price(request.amount)} EGP\n"
                    f"رصيدك الحالي بالجنيه المصري: {format_price(updated_wallet.balance_egp)}\n"
                ),
            )
        except Exception:
            pass

    schedule_drive_sheets_sync(reason=f"wallet_topup_approved:{request.id}")
    return ZenoWebhookResult(True, "wallet", f"Approved wallet topup {request.id}.")


async def _handle_purchase_order(
    *,
    price_amount: Decimal,
    checkout_id: str,
    bot: Bot,
) -> ZenoWebhookResult:
    try:
        numeric_checkout_id = str(checkout_id)
    except ValueError as error:
        raise ZenoWebhookError("Webhook orderId did not match a wallet topup or numeric order id.") from error

    try:
        current_order = await order_service.fetch_order_by_transaction_id(numeric_checkout_id)
    except (SupabaseConfigError, OrderServiceError) as error:
        raise ZenoWebhookError(str(error)) from error

    if current_order is None:
        raise ZenoWebhookError("Pending order was not found.")
    logger.info(
        "Zeno webhook matched order: order_id=%s status=%s payment_method=%s transaction_id=%s",
        current_order.id,
        current_order.status,
        current_order.payment_method,
        current_order.transaction_id,
    )
    if current_order.payment_method.strip().lower() != "binance":
        raise ZenoWebhookError("Matched order is not a Binance order.")
    if current_order.transaction_id != checkout_id:
        raise ZenoWebhookError("Webhook checkout id does not match the pending order.")
    if current_order.status == "Paid":
        logger.info("Zeno webhook order already paid: order_id=%s", current_order.id)
        return ZenoWebhookResult(True, "order", f"Order {current_order.id} was already paid.")
    if current_order.status.strip().lower() == "expired":
        logger.info("Zeno webhook ignored: order is expired: order_id=%s", current_order.id)
        return ZenoWebhookResult(True, "ignored", f"Order {current_order.id} is expired.")
    if current_order.status != "pending":
        raise ZenoWebhookError(f"Order is not pending: {current_order.status}.")
    if _to_usd_checkout_amount(current_order.total) != price_amount:
        raise ZenoWebhookError("Webhook priceAmount does not match the pending order total.")

    # Stop the customer countdown as soon as payment is confirmed.
    mark_checkout_paid(checkout_id)

    try:
        updated_order, product, error_message, order_action_label = await process_paid_order(current_order)
    except (SupabaseConfigError, OrderServiceError, ProductServiceError) as error:
        await notify_customer_about_server_error(SimpleNamespace(bot=bot), current_order)
        raise ZenoWebhookError(str(error)) from error

    if updated_order is None:
        await notify_customer_about_server_error(SimpleNamespace(bot=bot), current_order)
        raise ZenoWebhookError(error_message or "Order could not be marked as paid.")

    if updated_order.status == "ActivationPending":
        from app.routers.payment_methods.admin_notifications import notify_admins_about_order

        await notify_admins_about_order(SimpleNamespace(bot=bot), updated_order)

    await notify_customer_about_processed_order(
        context=SimpleNamespace(bot=bot),
        updated_order=updated_order,
        product=product,
        order_action_label=order_action_label,
    )
    logger.info("Zeno webhook marked order paid and notified customer: order_id=%s", updated_order.id)
    return ZenoWebhookResult(True, "order", f"Marked order {updated_order.id} as paid.")


def _parse_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value or "").strip())
    except (InvalidOperation, ValueError):
        return None


def _to_usd_checkout_amount(amount_egp: Decimal) -> Decimal:
    return (amount_egp / get_egp_exchange_rate()).quantize(Decimal("0.01"))


def _to_wallet_usd_checkout_amount(amount_egp: Decimal) -> Decimal:
    return rate_change_handler(amount_egp / get_egp_exchange_rate()).quantize(Decimal("0.01"))
