from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.models.order import Order
from app.models.product import Product
from app.routers.payment_methods.helpers.order_processing import (
    consume_product_credentials,
    decrease_product_quantity_for_order,
    restore_product_credentials,
    restore_product_quantity,
)
from app.services.adobe import get_action_label, is_adobe_product
from app.services.adobe.fulfillment import run_adobe_fulfillment
from app.services.catalog.products import ProductService
from app.translations import t


logger = logging.getLogger(__name__)


class AdminProductFulfillmentServiceError(RuntimeError):
    """Raised when an admin direct product fulfillment cannot be completed."""


@dataclass(slots=True)
class AdminProductFulfillmentResult:
    product: Product
    quantity: int
    credentials: list[dict[str, str]]
    assignment_email: str
    duration: str
    action_label: str | None = None


class AdminProductFulfillmentService:
    def __init__(self, product_service: ProductService | None = None) -> None:
        self._product_service = product_service or ProductService()

    async def fulfill(
        self,
        *,
        product_id: int,
        quantity: int,
        assignment_email: str = "",
        duration: str = "",
    ) -> AdminProductFulfillmentResult:
        if quantity < 1:
            raise AdminProductFulfillmentServiceError("يجب أن تكون الكمية أكبر من صفر.")

        product = await self._product_service.fetch_product_by_id(product_id)
        if product is None:
            raise AdminProductFulfillmentServiceError(t("purchase.order_product_not_found", "ar"))

        direct_order = _build_direct_order(
            product=product,
            quantity=quantity,
            assignment_email=assignment_email,
            duration=duration,
        )
        stock_context = await decrease_product_quantity_for_order(direct_order)
        if stock_context is None:
            raise AdminProductFulfillmentServiceError(t("purchase.order_stock_update_failed", "ar"))
        if stock_context.get("error_message"):
            raise AdminProductFulfillmentServiceError(str(stock_context["error_message"]))

        credential_context: dict | None = None
        credentials: list[dict[str, str]] = []

        try:
            if product.uses_manual_activation_emails:
                credentials = [{"email": assignment_email, "password": ""}]
                action_label = await self._run_manual_fulfillment(direct_order, product)
            else:
                credential_context = await consume_product_credentials(direct_order, product)
                if credential_context is None:
                    await restore_product_quantity(stock_context)
                    raise AdminProductFulfillmentServiceError(t("purchase.order_credentials_unavailable", "ar"))

                credentials = list(credential_context["credentials"])
                action_label = None
        except Exception:
            if credential_context is not None:
                await restore_product_credentials(credential_context)
            await restore_product_quantity(stock_context)
            raise

        return AdminProductFulfillmentResult(
            product=product,
            quantity=quantity,
            credentials=credentials,
            assignment_email=assignment_email,
            duration=duration,
            action_label=action_label,
        )

    async def _run_manual_fulfillment(
        self,
        direct_order: Order,
        product: Product,
    ) -> str | None:
        if not is_adobe_product(product.title):
            return None

        try:
            action = await run_adobe_fulfillment(direct_order)
        except Exception as error:
            logger.exception("Admin Adobe fulfillment failed for product %s: %s", product.id, error)
            raise AdminProductFulfillmentServiceError(t("purchase.adobe_order_credentials_unavailable", "ar")) from error

        return get_action_label(action)


def _build_direct_order(
    *,
    product: Product,
    quantity: int,
    assignment_email: str,
    duration: str,
) -> Order:
    total = product.price * Decimal(quantity)
    return Order(
        id=0,
        product_id=product.id,
        product_title=product.title,
        product_description=product.description,
        unit_price=product.price,
        quantity=quantity,
        total=total,
        payment_method="admin",
        transaction_id=None,
        status="Paid",
        email=assignment_email,
        password="",
        expiry_date=duration,
        customer_name="Admin",
        customer_username=None,
        customer_telegram_id=None,
        created_at=datetime.now(),
    )
