from datetime import datetime
from decimal import Decimal

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.order import Order
from app.services.catalog.products import SupabaseConfigError


class OrderServiceError(RuntimeError):
    """Raised when the orders service receives an API error."""


class OrderService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def create_order(self, data: dict, transaction_id: str | None, customer: object) -> Order:
        client = self._get_client()
        uses_manual_activation = bool(data.get("uses_manual_activation_emails"))
        expiry_date = _normalize_multiline_text(data.get("expiry_date") or data.get("duration"))
        payload = {
            "product_id": _to_int(data.get("product_id")),
            "product_title": str(data.get("product_title") or "-"),
            "product_description": str(data.get("product_description") or ""),
            "unit_price": str(data.get("product_price") or "0"),
            "quantity": _to_int(data.get("quantity")) or 0,
            "total": str(data.get("total") or "0"),
            "payment_method": str(data.get("payment_method") or "-"),
            "transaction_id": transaction_id,
            "status": "pending",
            "email": _normalize_multiline_text(data.get("email")),
            "password": "" if uses_manual_activation else _normalize_multiline_text(data.get("password")),
            "ExpiryDate": expiry_date if uses_manual_activation else "",
            "customer_name": getattr(customer, "full_name", None) or "-",
            "customer_username": _normalize_username(getattr(customer, "username", None)),
            "customer_telegram_id": getattr(customer, "id", None),
        }

        try:
            response = client.table(settings.supabase_orders_table).insert(payload).execute()
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        return _map_order(response.data[0])

    async def fetch_order_by_id(self, order_id: int) -> Order | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .select(
                    "id,product_id,product_title,product_description,unit_price,quantity,total,"
                    "payment_method,transaction_id,status,email,password,ExpiryDate,customer_name,customer_username,"
                    "customer_telegram_id,created_at"
                )
                .eq("id", order_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_order(response.data[0])

    async def fetch_order_by_transaction_id(self, transaction_id: str) -> Order | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .select(
                    "id,product_id,product_title,product_description,unit_price,quantity,total,"
                    "payment_method,transaction_id,status,email,password,ExpiryDate,customer_name,customer_username,"
                    "customer_telegram_id,created_at"
                )
                .eq("transaction_id", transaction_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_order(response.data[0])

    async def update_order_status(self, order_id: int, status: str) -> Order | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .update({"status": status})
                .eq("id", order_id)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_order(response.data[0])

    async def update_order_transaction_id(self, order_id: int, transaction_id: str | None) -> Order | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .update({"transaction_id": transaction_id})
                .eq("id", order_id)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_order(response.data[0])

    async def update_order_review_result(
        self,
        order_id: int,
        status: str,
        *,
        email: str = "",
        password: str = "",
        expiry_date: str = "",
    ) -> Order | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .update({"status": status, "email": email, "password": password, "ExpiryDate": expiry_date})
                .eq("id", order_id)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_order(response.data[0])

    async def fetch_paid_orders_by_username(self, username: str) -> list[Order]:
        client = self._get_client()
        normalized_username = _normalize_username(username)
        if normalized_username is None:
            return []

        try:
            response = (
                client.table(settings.supabase_orders_table)
                .select(
                    "id,product_id,product_title,product_description,unit_price,quantity,total,"
                    "payment_method,transaction_id,status,email,password,ExpiryDate,customer_name,customer_username,"
                    "customer_telegram_id,created_at"
                )
                .eq("customer_username", normalized_username)
                .eq("status", "Paid")
                .order("created_at", desc=True)
                .execute()
            )
        except APIError as error:
            raise OrderServiceError(_extract_api_error_message(error)) from error

        return [_map_order(item) for item in (response.data or [])]


def _map_order(item: dict) -> Order:
    return Order(
        id=int(item["id"]),
        product_id=_to_int(item.get("product_id")),
        product_title=str(item.get("product_title") or ""),
        product_description=str(item.get("product_description") or ""),
        unit_price=Decimal(str(item.get("unit_price") or "0")),
        quantity=_to_int(item.get("quantity")) or 0,
        total=Decimal(str(item.get("total") or "0")),
        payment_method=str(item.get("payment_method") or ""),
        transaction_id=_normalize_nullable_text(item.get("transaction_id")),
        status=str(item.get("status") or ""),
        email=str(item.get("email") or ""),
        password=str(item.get("password") or ""),
        expiry_date=str(item.get("ExpiryDate") or item.get("expiry_date") or ""),
        customer_name=str(item.get("customer_name") or "-"),
        customer_username=_normalize_nullable_text(item.get("customer_username")),
        customer_telegram_id=_to_int(item.get("customer_telegram_id")),
        created_at=_parse_datetime(item.get("created_at")),
    )


def _parse_datetime(value: object) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _extract_api_error_message(error: APIError) -> str:
    details = getattr(error, "details", None)
    message = getattr(error, "message", None)
    code = getattr(error, "code", None)

    parts = [part for part in [message, details, code] if part]
    return " | ".join(parts) if parts else str(error)


def _normalize_username(username: object) -> str | None:
    text = _normalize_nullable_text(username)
    if text is None:
        return None

    return text if text.startswith("@") else f"@{text}"


def _normalize_nullable_text(value: object) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _normalize_multiline_text(value: object) -> str:
    if value is None:
        return ""

    lines = [line.strip() for line in str(value).splitlines()]
    return "\n".join(line for line in lines if line)


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None

    return int(value)
