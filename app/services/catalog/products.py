from datetime import datetime
from decimal import Decimal

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.product import Product


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase credentials are missing."""


class ProductServiceError(RuntimeError):
    """Raised when the products service receives an API error."""


class ProductService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def fetch_products(self) -> list[Product]:
        client = self._get_client()
        response = (
            client.table(settings.supabase_products_table)
            .select("id,title,description,quantity,isSpecial,image,supplier_price,price,created_at,credentials")
            .execute()
        )

        products = [_map_product(item) for item in (response.data or [])]
        return sorted(products, key=_product_sort_key)

    async def fetch_product_by_id(self, product_id: int) -> Product | None:
        client = self._get_client()
        response = (
            client.table(settings.supabase_products_table)
            .select("id,title,description,quantity,isSpecial,image,supplier_price,price,created_at,credentials")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return _map_product(response.data[0])

    async def create_product(
        self,
        title: str,
        description: str,
        quantity: int,
        image: str | None,
        supplier_price: Decimal,
        price: Decimal,
        credentials: object = "none",
    ) -> Product:
        client = self._get_client()
        try:
            print("Creating product with data:", {
                "title": title,
                "description": description,
                "quantity": quantity,
                "image": image,
                "supplier_price": str(supplier_price),
                "price": str(price),
                "credentials": credentials,
            })
            response = (
                client.table(settings.supabase_products_table)
                .insert(
                    {
                        "title": title,
                        "description": description,
                        "quantity": quantity,
                        "image": image,
                        "supplier_price": str(supplier_price),
                        "price": str(price),
                        "credentials": credentials,
                    }
                )
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        return _map_product(response.data[0])

    async def update_product(
        self,
        product_id: int,
        title: str,
        description: str,
        quantity: int,
        supplier_price: Decimal,
        price: Decimal,
        credentials: object,
    ) -> Product | None:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_products_table)
                .update(
                    {
                        "title": title,
                        "description": description,
                        "quantity": quantity,
                        "supplier_price": str(supplier_price),
                        "price": str(price),
                        "credentials": credentials,
                    }
                )
                .eq("id", product_id)
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_product(response.data[0])

    async def update_product_quantity(self, product_id: int, quantity: int) -> Product | None:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_products_table)
                .update({"quantity": quantity})
                .eq("id", product_id)
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_product(response.data[0])

    async def update_product_credentials(
        self,
        product_id: int,
        credentials: list[dict[str, str]],
    ) -> Product | None:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_products_table)
                .update({"credentials": credentials})
                .eq("id", product_id)
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_product(response.data[0])

    async def mark_products_special(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []

        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_products_table)
                .update({"isSpecial": True})
                .in_("id", product_ids)
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        return [_map_product(item) for item in (response.data or [])]

    async def delete_product(self, product_id: int) -> bool:
        client = self._get_client()
        try:
            response = (
                client.table(settings.supabase_products_table)
                .delete()
                .eq("id", product_id)
                .execute()
            )
        except APIError as error:
            raise ProductServiceError(_extract_api_error_message(error)) from error

        return bool(response.data)


def _map_product(item: dict) -> Product:
    raw_credentials = item.get("credentials")
    return Product(
        id=int(item["id"]),
        title=str(item["title"]),
        description=str(item.get("description", "")),
        quantity=int(item.get("quantity") or 0),
        is_special=_parse_bool(item.get("isSpecial")),
        image=_optional_text(item.get("image")),
        supplier_price=Decimal(str(item.get("supplier_price") or "0")),
        price=Decimal(str(item.get("price") or "0")),
        created_at=_parse_datetime(item.get("created_at")),
        credentials=_parse_credentials(raw_credentials),
        uses_manual_activation_emails=_uses_manual_activation_emails(raw_credentials),
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


def _parse_credentials(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    parsed_credentials: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        email = str(item.get("email") or "").strip()
        password = str(item.get("password") or "").strip()
        if not email and not password:
            continue

        parsed_credentials.append(
            {
                "email": email,
                "password": password,
            }
        )

    return parsed_credentials


def _uses_manual_activation_emails(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() == "none"


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return False


def _product_sort_key(product: Product) -> tuple[int, str]:
    return (0 if product.is_special else 1, product.title.casefold())


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
