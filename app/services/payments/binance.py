from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from urllib import error, request

from app.config import settings


class BinanceServiceError(RuntimeError):
    """Raised when the Binance/Zeno checkout flow fails."""


@dataclass(slots=True)
class BinancePaymentInstruction:
    checkout_id: str
    order_id: str
    deposit_account_id: str
    token_pay_amount: float
    token_id: str
    expires_at: datetime | None


class BinanceService:
    _base_url = "https://api.zenobank.io/api/v1"
    _binance_token_id = "USDT_BINANCE_PAY"

    async def create_payment_instruction(
        self,
        *,
        order_id: str,
        price_amount_usd: Decimal,
        success_redirect_url: str,
    ) -> BinancePaymentInstruction:
        api_key = (settings.zeno_bank_api_key or "").strip()
        if not api_key:
            raise BinanceServiceError("ZENO_BANK_API_KEY is missing in .env.")

        checkout = await self._post(
            "/checkouts",
            {
                "orderId": order_id,
                "priceAmount": self._format_decimal(price_amount_usd),
                "priceCurrency": "USD",
                "successRedirectUrl": success_redirect_url,
            },
            api_key=api_key,
        )
        print(checkout)
        checkout_id = str(checkout.get("id") or "").strip()
        if not checkout_id:
            raise BinanceServiceError("Zeno checkout response did not include an id.")

        attempt = await self._post(
            f"/public/checkouts/{checkout_id}/attempts/binance-pay",
            {
                #"checkoutId": checkout_id,
                "tokenId": self._binance_token_id,
            },
            api_key=api_key,
        )
        deposit_account_id = str(attempt.get("depositAccountId") or "").strip()
        if not deposit_account_id:
            raise BinanceServiceError("Zeno Binance Pay response did not include depositAccountId.")

        token_pay_amount_text = str(attempt.get("tokenPayAmount") or "").strip()
        if not token_pay_amount_text:
            raise BinanceServiceError("Zeno Binance Pay response did not include tokenPayAmount.")

        expires_at = _parse_datetime(checkout.get("expiresAt") or attempt.get("expiresAt"))

        return BinancePaymentInstruction(
            checkout_id=checkout_id,
            order_id=str(checkout.get("orderId") or order_id),
            deposit_account_id=deposit_account_id,
            token_pay_amount=float(token_pay_amount_text),
            token_id=str(attempt.get("binanceTokenId") or "USDT").strip() or "USDT",
            expires_at=expires_at,
        )

    async def _post(self, path: str, payload: dict[str, object], *, api_key: str) -> dict:
        return await asyncio.to_thread(self._post_sync, path, payload, api_key)

    def _post_sync(self, path: str, payload: dict[str, object], api_key: str) -> dict:
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self._base_url}{path}",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-Key": api_key,
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=30) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            message = self._extract_error_message(error_body)
            raise BinanceServiceError(message or f"Zeno API request failed with HTTP {exc.code}.") from exc
        except error.URLError as exc:
            raise BinanceServiceError(f"Could not reach Zeno API: {exc.reason}") from exc

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise BinanceServiceError("Zeno API returned an invalid JSON response.") from exc

        if not isinstance(data, dict):
            raise BinanceServiceError("Zeno API returned an unexpected response format.")

        return data

    @staticmethod
    def _extract_error_message(error_body: str) -> str:
        try:
            parsed = json.loads(error_body)
        except json.JSONDecodeError:
            return error_body.strip()

        if not isinstance(parsed, dict):
            return error_body.strip()

        for key in ("message", "error", "details"):
            value = str(parsed.get(key) or "").strip()
            if value:
                return value

        return error_body.strip()

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")), "f")


def _parse_datetime(value: object) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
