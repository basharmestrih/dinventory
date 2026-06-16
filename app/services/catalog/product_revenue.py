from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.order import Order
from app.services.catalog.products import SupabaseConfigError


class ProductRevenueServiceError(RuntimeError):
    """Raised when product revenue archiving fails."""


class ProductRevenueService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def add_paid_order(self, order: Order) -> None:
        if order.product_id is None:
            return

        product_id = int(order.product_id)
        revenue_delta = _decimal_to_table_integer(order.total)
        sold_delta = int(order.quantity)
        if revenue_delta <= 0 and sold_delta <= 0:
            return

        existing_row = await self._fetch_revenue_row(product_id)
        if existing_row is None:
            await self._create_revenue_row(
                product_id=product_id,
                product_title=order.product_title,
                total_revenue=revenue_delta,
                total_sold_count=sold_delta,
            )
            return

        await self._update_revenue_row(
            product_id=product_id,
            product_title=order.product_title,
            total_revenue=int(existing_row.get("total_revenue") or 0) + revenue_delta,
            total_sold_count=int(existing_row.get("total_sold_count") or 0) + sold_delta,
        )

    async def _fetch_revenue_row(self, product_id: int) -> dict | None:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_product_revenue_table)
                .select("id,product_title,total_revenue,total_sold_count,created_at")
                .eq("id", product_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise ProductRevenueServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return response.data[0]

    async def _create_revenue_row(
        self,
        *,
        product_id: int,
        product_title: str,
        total_revenue: int,
        total_sold_count: int,
    ) -> None:
        client = self._get_client()
        payload = {
            "id": product_id,
            "product_title": product_title,
            "total_revenue": total_revenue,
            "total_sold_count": total_sold_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            client.table(settings.supabase_product_revenue_table).insert(payload).execute()
        except APIError as error:
            if _is_duplicate_key_error(error):
                existing_row = await self._fetch_revenue_row(product_id)
                if existing_row is not None:
                    await self._update_revenue_row(
                        product_id=product_id,
                        product_title=product_title,
                        total_revenue=int(existing_row.get("total_revenue") or 0) + total_revenue,
                        total_sold_count=int(existing_row.get("total_sold_count") or 0) + total_sold_count,
                    )
                    return
            raise ProductRevenueServiceError(_extract_api_error_message(error)) from error

    async def _update_revenue_row(
        self,
        *,
        product_id: int,
        product_title: str,
        total_revenue: int,
        total_sold_count: int,
    ) -> None:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_product_revenue_table)
                .update(
                    {
                        "product_title": product_title,
                        "total_revenue": total_revenue,
                        "total_sold_count": total_sold_count,
                    }
                )
                .eq("id", product_id)
                .execute()
            )
        except APIError as error:
            raise ProductRevenueServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            raise ProductRevenueServiceError("Product revenue row was not updated.")


def _decimal_to_table_integer(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _extract_api_error_message(error: APIError) -> str:
    details = getattr(error, "details", None)
    message = getattr(error, "message", None)
    code = getattr(error, "code", None)

    parts = [part for part in [message, details, code] if part]
    return " | ".join(parts) if parts else str(error)


def _is_duplicate_key_error(error: APIError) -> bool:
    return str(getattr(error, "code", "")).strip() == "23505"
