from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.wallet_balance import WalletBalance
from app.services.catalog.products import SupabaseConfigError
from app.services.payments.exchange_rate import get_egp_exchange_rate



class WalletServiceError(RuntimeError):
    """Raised when the wallet service receives an API error."""


class WalletService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def fetch_wallet_by_username(self, username: str) -> WalletBalance | None:
        client = self._get_client()
        normalized_username = _normalize_wallet_username(username)

        try:
            response = (
                client.table(settings.supabase_wallet_table)
                .select("username,balance_usd,balance_egp,last_deposit_at")
                .eq("username", normalized_username)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise WalletServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            return None

        try:
            return _map_wallet_balance(response.data[0])
        except Exception as error:
            raise WalletServiceError(f"Invalid wallet data format: {error}") from error

    async def ensure_wallet(self, username: str) -> WalletBalance:
        existing_wallet = await self.fetch_wallet_by_username(username)
        if existing_wallet is not None:
            return existing_wallet

        client = self._get_client()
        normalized_username = _normalize_wallet_username(username)

        try:
            response = (
                client.table(settings.supabase_wallet_table)
                .insert(
                    {
                        "username": normalized_username,
                        "balance_usd": "0",
                        "balance_egp": "0",
                        "last_deposit_at": None,
                    }
                )
                .execute()
            )
        except APIError as error:
            raise WalletServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            raise WalletServiceError("Wallet row was not created.")

        try:
            return _map_wallet_balance(response.data[0])
        except Exception as error:
            raise WalletServiceError(f"Invalid wallet data format: {error}") from error

    async def apply_topup(self, username: str, amount_egp: Decimal) -> WalletBalance:
        if amount_egp <= 0:
            raise WalletServiceError("Top-up amount must be greater than zero.")

        return await self._apply_egp_balance_delta(username, amount_egp, update_last_deposit_at=True)

    async def deduct_purchase_amount(self, username: str, amount_egp: Decimal) -> WalletBalance:
        if amount_egp <= 0:
            raise WalletServiceError("Purchase amount must be greater than zero.")

        wallet = await self.ensure_wallet(username)
        print(wallet.balance_egp)
        print(amount_egp)
        if wallet.balance_egp < amount_egp:
            raise WalletServiceError("Insufficient wallet balance.")

        return await self._apply_egp_balance_delta(username, -amount_egp, update_last_deposit_at=False)


    async def _apply_egp_balance_delta(
        self,
        username: str,
        amount_egp_delta: Decimal,
        *,
        update_last_deposit_at: bool,
    ) -> WalletBalance:
        wallet = await self.ensure_wallet(username)

        client = self._get_client()
        normalized_username = _normalize_wallet_username(username)

        balance_egp = wallet.balance_egp + amount_egp_delta
        if balance_egp < 0:
            raise WalletServiceError("Insufficient wallet balance.")

        exchange_rate = get_egp_exchange_rate()
        if exchange_rate <= 0:
            raise WalletServiceError("Invalid exchange rate.")

        balance_usd = _to_three_decimal_places(balance_egp / exchange_rate)

        update_payload: dict[str, object] = {
            "balance_usd": str(balance_usd),
            "balance_egp": str(balance_egp),
        }
        if update_last_deposit_at:
            # Store date only (YYYY-MM-DD) to keep it consistent and easy to display.
            update_payload["last_deposit_at"] = datetime.now(timezone.utc).date().isoformat()

        try:
            response = (
                client.table(settings.supabase_wallet_table)
                .update(
                    update_payload
                )
                .eq("username", normalized_username)
                .execute()
            )
        except APIError as error:
            raise WalletServiceError(_extract_api_error_message(error)) from error

        if not response.data:
            raise WalletServiceError("Wallet row was not updated.")

        try:
            return _map_wallet_balance(response.data[0])
        except Exception as error:
            raise WalletServiceError(f"Invalid wallet data format: {error}") from error


def _map_wallet_balance(item: dict) -> WalletBalance:
    return WalletBalance(
        username=_normalize_display_username(item.get("username")),
        balance_usd=_to_decimal(item.get("balance_usd")),
        balance_egp=_to_decimal(item.get("balance_egp")),
        last_deposit_at=_parse_datetime(item.get("last_deposit_at")),
    )


def _normalize_wallet_username(username: str) -> str:
    cleaned = username.strip()
    return cleaned[1:] if cleaned.startswith("@") else cleaned


def _normalize_display_username(value: object) -> str:
    text = str(value or "").strip()
    return text[1:] if text.startswith("@") else text


def _to_decimal(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


def _to_three_decimal_places(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_DOWN)


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
