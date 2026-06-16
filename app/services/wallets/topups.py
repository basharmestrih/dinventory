from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.wallet_topup import WalletTopUpRequest
from app.services.catalog.products import SupabaseConfigError


class WalletTopUpServiceError(RuntimeError):
    """Raised when the wallet topup service receives an API error."""


class WalletTopUpService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def create_topup(
        self,
        *,
        username: str,
        amount: Decimal,
        currency: str,
        payment_method: str,
        transaction_id: str,
        payment_proof_file_id: str = "",
        payment_proof_type: str = "",
        customer_name: str,
        customer_username: str,
        customer_telegram_id: int | None,
    ) -> WalletTopUpRequest:
        payload = {
            "id": f"wallet-{uuid4().hex[:12]}",
            "username": _normalize_username(username),
            "amount": str(amount),
            "currency": currency,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "payment_proof_file_id": payment_proof_file_id,
            "payment_proof_type": payment_proof_type,
            "customer_name": customer_name,
            "customer_username": customer_username,
            "customer_telegram_id": customer_telegram_id,
            "status": "pending",
        }

        try:
            #print("binance payload is", payload)
            client = self._get_client()
            response = client.table(settings.supabase_wallet_topups_table).insert(payload).execute()
        except APIError as error:
            raise WalletTopUpServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            raise WalletTopUpServiceError("Wallet topup row was not created.")

        return _map_topup(response.data[0])

    async def fetch_topup_by_id(self, request_id: str) -> WalletTopUpRequest | None:
        return await self._fetch_one("id", request_id)

    async def fetch_topup_by_transaction_id(self, transaction_id: str) -> WalletTopUpRequest | None:
        return await self._fetch_one("transaction_id", transaction_id)

    async def update_transaction_id(self, request_id: str, transaction_id: str) -> WalletTopUpRequest | None:
        return await self._update(request_id, {"transaction_id": transaction_id})

    async def update_status(self, request_id: str, status: str) -> WalletTopUpRequest | None:
        return await self._update(request_id, {"status": status})

    async def _fetch_one(self, column: str, value: str) -> WalletTopUpRequest | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_wallet_topups_table)
                .select(_SELECT_COLUMNS)
                .eq(column, value)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise WalletTopUpServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_topup(response.data[0])

    async def _update(self, request_id: str, payload: dict[str, object]) -> WalletTopUpRequest | None:
        client = self._get_client()

        try:
            response = (
                client.table(settings.supabase_wallet_topups_table)
                .update(payload)
                .eq("id", request_id)
                .execute()
            )
        except APIError as error:
            raise WalletTopUpServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        return _map_topup(response.data[0])


_SELECT_COLUMNS = (
    "id,username,amount,currency,payment_method,transaction_id,payment_proof_file_id,"
    "payment_proof_type,customer_name,customer_username,customer_telegram_id,status,created_at"
)


def _map_topup(item: dict) -> WalletTopUpRequest:
    return WalletTopUpRequest(
        id=str(item.get("id") or ""),
        username=str(item.get("username") or ""),
        amount=Decimal(str(item.get("amount") or "0")),
        currency=str(item.get("currency") or ""),
        payment_method=str(item.get("payment_method") or ""),
        transaction_id=str(item.get("transaction_id") or ""),
        payment_proof_file_id=str(item.get("payment_proof_file_id") or ""),
        payment_proof_type=str(item.get("payment_proof_type") or ""),
        customer_name=str(item.get("customer_name") or "-"),
        customer_username=str(item.get("customer_username") or "-"),
        customer_telegram_id=_to_int(item.get("customer_telegram_id")),
        status=str(item.get("status") or ""),
        created_at=_parse_datetime(item.get("created_at")),
    )


def _normalize_username(username: str) -> str:
    return username.strip().lstrip("@")


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None

    return int(value)


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
