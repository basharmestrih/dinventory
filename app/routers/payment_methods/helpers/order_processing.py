import logging

from app.models.order import Order
from app.models.product import Product
from app.routers.payment_methods.helpers.credential_utils import (
    has_valid_credentials,
    serialize_order_credential_field,
)
from app.routers.payment_methods.helpers.services import order_service, product_service
from app.services.adobe import get_action_label, is_adobe_product
from app.services.adobe.fulfillment import run_adobe_fulfillment
from app.services.catalog.product_revenue import ProductRevenueService, ProductRevenueServiceError
from app.services.catalog.products import SupabaseConfigError
from app.services.users.users import UserService, UserServiceError
from app.translations import t


logger = logging.getLogger(__name__)
product_revenue_service = ProductRevenueService()
user_service = UserService()


async def process_paid_order(
    current_order: Order,
) -> tuple[Order | None, Product | None, str | None, str | None]:
    stock_context = await decrease_product_quantity_for_order(current_order)
    if stock_context is None:
        return None, None, t("purchase.order_stock_update_failed", "ar"), None

    if stock_context.get("error_message"):
        return None, None, str(stock_context["error_message"]), None

    product = await product_service.fetch_product_by_id(current_order.product_id)
    if product is None:
        await restore_product_quantity(stock_context)
        return None, None, t("purchase.order_product_not_found", "ar"), None

    credential_email = ""
    credential_password = ""
    credential_context: dict | None = None

    if product.uses_manual_activation_emails:
        credential_email = current_order.email
        credential_password = current_order.password
        credential_expiry_date = current_order.expiry_date
    else:
        credential_context = await consume_product_credentials(current_order, product)
        if credential_context is None:
            await restore_product_quantity(stock_context)
            return None, None, t("purchase.order_credentials_unavailable", "ar"), None

        credential_email = serialize_order_credential_field(
            credential_context["credentials"],
            key="email",
        )
        credential_password = serialize_order_credential_field(
            credential_context["credentials"],
            key="password",
        )
        credential_expiry_date = current_order.expiry_date

    try:
        if product.uses_manual_activation_emails and is_adobe_product(product.title):
            new_status = "Paid"
        else:
            new_status = "ActivationPending" if product.uses_manual_activation_emails else "Paid"
        updated_order = await order_service.update_order_review_result(
            current_order.id,
            new_status,
            email=credential_email,
            password=credential_password,
            expiry_date=credential_expiry_date,
        )
    except Exception:
        if credential_context is not None:
            await restore_product_credentials(credential_context)
        await restore_product_quantity(stock_context)
        raise

    if updated_order is None:
        if credential_context is not None:
            await restore_product_credentials(credential_context)
        await restore_product_quantity(stock_context)
        return None, None, t("purchase.order_not_found", "ar"), None

    order_action_label = None
    if product.uses_manual_activation_emails and is_adobe_product(product.title):
        try:
            order_action = await run_adobe_fulfillment(updated_order)
            order_action_label = get_action_label(order_action)
        except Exception as error:
            logger.exception("Adobe fulfillment failed for order %s: %s", current_order.id, error)
            try:
                await order_service.update_order_review_result(
                    current_order.id,
                    "pending",
                    email=current_order.email,
                    password=current_order.password,
                    expiry_date=current_order.expiry_date,
                )
            except Exception:
                pass
            await restore_product_quantity(stock_context)
            return None, None, t("purchase.order_credentials_unavailable", "ar"), None

    try:
        await product_revenue_service.add_paid_order(updated_order)
    except (SupabaseConfigError, ProductRevenueServiceError) as error:
        logger.exception("Product revenue archive failed for order %s: %s", current_order.id, error)
        if credential_context is not None:
            await restore_product_credentials(credential_context)
        await restore_product_quantity(stock_context)
        try:
            await order_service.update_order_review_result(
                current_order.id,
                "pending",
                email=current_order.email,
                password=current_order.password,
                expiry_date=current_order.expiry_date,
            )
        except Exception:
            pass
        return None, None, t("purchase.order_create_failed", "ar"), None

    if updated_order.status == "Paid":
        payment_method = str(updated_order.payment_method or "").strip().lower()
        transaction_id = str(updated_order.transaction_id or "").strip()
        if payment_method == "binance" and transaction_id:
            from app.routers.payment_methods.binance import mark_binance_checkout_paid

            mark_binance_checkout_paid(transaction_id)

    try:
        await user_service.add_paid_order_spending(updated_order)
    except (SupabaseConfigError, UserServiceError) as error:
        logger.exception("User spending update failed for order %s: %s", current_order.id, error)
        return None, None, t("purchase.order_create_failed", "ar"), None

    return updated_order, product, None, order_action_label


async def decrease_product_quantity_for_order(order: Order) -> dict:
    if order.product_id is None:
        return {"product_id": None, "previous_quantity": 0, "error_message": None}

    product = await product_service.fetch_product_by_id(order.product_id)
    if product is None:
        return {
            "product_id": order.product_id,
            "previous_quantity": 0,
            "error_message": t("purchase.order_product_not_found", "ar"),
        }

    if product.quantity < order.quantity:
        return {
            "product_id": order.product_id,
            "previous_quantity": product.quantity,
            "error_message": t("purchase.order_insufficient_stock", "ar").format(
                available_quantity=product.quantity
            ),
        }

    updated_product = await product_service.update_product_quantity(
        product_id=order.product_id,
        quantity=product.quantity - order.quantity,
    )
    if updated_product is None:
        return {
            "product_id": order.product_id,
            "previous_quantity": product.quantity,
            "error_message": t("purchase.order_product_not_found", "ar"),
        }

    return {
        "product_id": order.product_id,
        "previous_quantity": product.quantity,
        "error_message": None,
    }


async def consume_product_credentials(order: Order, product: Product | None) -> dict | None:
    if order.product_id is None:
        return None

    if product is None or not product.credentials:
        return None

    if len(product.credentials) < order.quantity:
        return None

    selected_credentials = product.credentials[: order.quantity]
    if not has_valid_credentials(selected_credentials):
        return None

    remaining_credentials = product.credentials[order.quantity :]
    updated_product = await product_service.update_product_credentials(
        product_id=order.product_id,
        credentials=remaining_credentials,
    )
    if updated_product is None:
        return None

    return {
        "product_id": order.product_id,
        "credentials": selected_credentials,
        "original_credentials": product.credentials,
    }


async def restore_product_credentials(credential_context: dict) -> None:
    try:
        await product_service.update_product_credentials(
            product_id=int(credential_context["product_id"]),
            credentials=list(credential_context["original_credentials"]),
        )
    except Exception:
        return


async def restore_product_quantity(stock_context: dict) -> None:
    product_id = stock_context.get("product_id")
    if product_id is None:
        return

    try:
        await product_service.update_product_quantity(
            product_id=int(product_id),
            quantity=int(stock_context["previous_quantity"]),
        )
    except Exception:
        return
