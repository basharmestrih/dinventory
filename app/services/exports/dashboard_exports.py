from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.services.catalog.products import SupabaseConfigError


class DashboardExportServiceError(RuntimeError):
    """Raised when dashboard export data cannot be fetched."""


class DashboardExportService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def fetch_product_revenue_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_product_revenue_table,
            columns="id,product_title,total_revenue,total_sold_count,created_at",
            order_by="id",
        )

    async def fetch_payment_method_usage_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_payment_method_usage_table,
            columns="id,payment_method,usage_count,created_at",
            order_by="id",
        )

    async def fetch_daily_revenue_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_daily_revenue_table,
            columns="id,date,total_revenue,total_sold_items,sold_items,created_at",
            order_by="date",
        )

    async def fetch_users_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_users_table,
            columns="id,username,total_spent,last_spent_order,created_at",
            order_by="id",
        )

    async def fetch_orders_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_orders_table,
            columns=(
                "id,product_id,product_title,product_description,unit_price,quantity,total,"
                "payment_method,transaction_id,status,customer_name,customer_username,"
                "customer_telegram_id,created_at"
            ),
            order_by="id",
        )

    async def fetch_wallet_topups_rows(self) -> list[dict]:
        return await self._fetch_rows(
            table_name=settings.supabase_wallet_topups_table,
            columns=(
                "id,username,amount,currency,payment_method,transaction_id,"
                "payment_proof_file_id,payment_proof_type,customer_name,customer_username,"
                "customer_telegram_id,status,created_at"
            ),
            order_by="created_at",
        )

    async def _fetch_rows(self, table_name: str, columns: str, order_by: str) -> list[dict]:
        client = self._get_client()

        try:
            response = client.table(table_name).select(columns).order(order_by, desc=False).execute()
        except APIError as error:
            raise DashboardExportServiceError(_extract_api_error_message(error)) from error

        return list(response.data or [])


def _extract_api_error_message(error: APIError) -> str:
    details = getattr(error, "details", None)
    message = getattr(error, "message", None)
    code = getattr(error, "code", None)

    parts = [part for part in [message, details, code] if part]
    return " | ".join(parts) if parts else str(error)
