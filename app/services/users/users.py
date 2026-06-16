from datetime import datetime
from decimal import Decimal

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.user_profile import UserProfile
from app.models.order import Order
from app.services.catalog.products import SupabaseConfigError


class UserServiceError(RuntimeError):
    """Raised when the users service receives an API error."""


class UserService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def fetch_user_by_username(self, username: str) -> UserProfile | None:
        client = self._get_client()

        try:
            print("Fetching user by username:", username)  # Debug log
            response = (
                client.table(settings.supabase_users_table)
                .select("id,username,total_spent,last_spent_order,created_at")
                .eq("username", f"@{username}")
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise UserServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_user_profile(response.data[0])

    async def register_bot_user(self, telegram_id: int, username: str | None) -> None:
        client = self._get_client()
        telegram_id_column = settings.supabase_users_telegram_id_column
        payload = {
            telegram_id_column: telegram_id,
            "username": _normalize_username(username),
        }

        try:
            existing_user = (
                client.table(settings.supabase_users_table)
                .select("id")
                .eq(telegram_id_column, telegram_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise UserServiceError(_extract_api_error_message(error)) from error

        try:
            if existing_user.data:
                (
                    client.table(settings.supabase_users_table)
                    .update(payload)
                    .eq(telegram_id_column, telegram_id)
                    .execute()
                )
            else:
                client.table(settings.supabase_users_table).insert(payload).execute()
        except APIError as error:
            raise UserServiceError(_extract_api_error_message(error)) from error

    async def add_paid_order_spending(self, order: Order) -> None:
        client = self._get_client()
        telegram_id_column = settings.supabase_users_telegram_id_column
        username = _normalize_username(order.customer_username)
        last_spent_order = _format_last_spent_order(order)

        try:
            existing_user = await self._fetch_user_row_for_order(client, order, username)
            if existing_user is None:
                payload = {
                    telegram_id_column: order.customer_telegram_id,
                    "username": username,
                    "total_spent": str(order.total),
                    "last_spent_order": last_spent_order,
                }
                client.table(settings.supabase_users_table).insert(payload).execute()
                return

            current_total = Decimal(str(existing_user.get("total_spent") or "0"))
            payload = {
                "username": username or existing_user.get("username"),
                "total_spent": str(current_total + order.total),
                "last_spent_order": last_spent_order,
            }
            (
                client.table(settings.supabase_users_table)
                .update(payload)
                .eq("id", existing_user["id"])
                .execute()
            )
        except APIError as error:
            raise UserServiceError(_extract_api_error_message(error)) from error

    async def _fetch_user_row_for_order(
        self,
        client: Client,
        order: Order,
        username: str | None,
    ) -> dict | None:
        telegram_id_column = settings.supabase_users_telegram_id_column
        columns = f"id,username,total_spent,last_spent_order,{telegram_id_column}"

        if order.customer_telegram_id is not None:
            response = (
                client.table(settings.supabase_users_table)
                .select(columns)
                .eq(telegram_id_column, order.customer_telegram_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]

        if username:
            response = (
                client.table(settings.supabase_users_table)
                .select(columns)
                .eq("username", username)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]

        return None


def _map_user_profile(item: dict) -> UserProfile:
    return UserProfile(
        id=int(item["id"]),
        username=str(item.get("username") or ""),
        total_spent=Decimal(str(item.get("total_spent") or "0")),
        last_spent_order=str(item["last_spent_order"]) if item.get("last_spent_order") else None,
        created_at=_parse_datetime(item.get("created_at")),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _extract_api_error_message(error: APIError) -> str:
    details = getattr(error, "details", None)
    message = getattr(error, "message", None)
    code = getattr(error, "code", None)

    parts = [part for part in [message, details, code] if part]
    return " | ".join(parts) if parts else str(error)


def _normalize_username(username: str | None) -> str | None:
    if username is None:
        return None

    cleaned = username.strip()
    if not cleaned:
        return None

    return cleaned if cleaned.startswith("@") else f"@{cleaned}"


def _format_last_spent_order(order: Order) -> str:
    title = str(order.product_title or "-").strip() or "-"
    return title
