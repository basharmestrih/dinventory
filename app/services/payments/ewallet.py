from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from urllib import error, request

from app.config import settings

logger = logging.getLogger(__name__)


class EWalletServiceError(RuntimeError):
    """Raised when the Fawaterk e-wallet flow fails."""


@dataclass(slots=True)
class EWalletInvoice:
    invoice_id: int
    invoice_key: str
    payment_method_id: int
    fawry_code: str | None = None
    expire_date: str | None = None
    meeza_reference: str | None = None
    meeza_qr_code: str | None = None


class EWalletService:
    _base_url = "https://app.fawaterk.com/api/v2/invoiceInitPay"

    async def create_invoice(
        self,
        *,
        payment_method_id: int,
        total_egp: Decimal,
        first_name: str,
        last_name: str,
        phone: str,
        item_name: str,
        item_price: Decimal,
        quantity: int,
    ) -> EWalletInvoice:
        api_key = (settings.fawaterk_api_key or "").strip()
        if not api_key:
            raise EWalletServiceError("FAWATERK_API_KEY is missing in .env.")

        payload = {
            "payment_method_id": payment_method_id,
            "cartTotal": self._format_decimal(total_egp),
            "currency": "EGP",
            "customer": {
                "first_name": first_name or "Unknown",
                "last_name": last_name or "Customer",
                #"email": "mestbashar@gmail.com",
                "phone": phone,
                "sendEmail": True,
            },
            "cartItems": [
                {
                    "name": item_name,
                    "price": self._format_decimal(item_price),
                    "quantity": str(quantity),
                }
            ],
        }
        logger.info(
            "Sending Fawaterk invoice request: payment_method_id=%s total_egp=%s quantity=%s phone=%s item_name=%s payload=%s",
            payment_method_id,
            self._format_decimal(total_egp),
            quantity,
            phone,
            item_name,
            json.dumps(payload, ensure_ascii=False),
        )
        response = await asyncio.to_thread(self._post_sync, payload, api_key)
        logger.info(
            "Received Fawaterk invoice response: payment_method_id=%s response=%s",
            payment_method_id,
            json.dumps(response, ensure_ascii=False),
        )
        if str(response.get("status") or "").lower() != "success":
            logger.warning("Fawaterk response status was not success: %s", response.get("status"))
            raise EWalletServiceError("Fawaterk did not return a successful response.")

        data = response.get("data")
        if not isinstance(data, dict):
            raise EWalletServiceError("Fawaterk response is missing invoice data.")

        payment_data = data.get("payment_data")
        if not isinstance(payment_data, dict):
            raise EWalletServiceError("Fawaterk response is missing payment data.")

        return EWalletInvoice(
            invoice_id=int(data["invoice_id"]),
            invoice_key=str(data.get("invoice_key") or ""),
            payment_method_id=payment_method_id,
            fawry_code=_optional_text(payment_data.get("fawryCode")),
            expire_date=_optional_text(payment_data.get("expireDate")),
            meeza_reference=_optional_text(payment_data.get("meezaReference")),
            meeza_qr_code=_optional_text(payment_data.get("meezaQrCode")),
        )

    def _post_sync(self, payload: dict[str, object], api_key: str) -> dict:
        body = json.dumps(payload).encode("utf-8")
        logger.debug(
            "Preparing Fawaterk HTTP request: url=%s auth_prefix=%s payload_size=%s",
            self._base_url,
            _mask_api_key(api_key),
            len(body),
        )
        http_request = request.Request(
            url=self._base_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=30) as response:
                raw_body = response.read().decode("utf-8")
                logger.info(
                    "Fawaterk HTTP request succeeded: status=%s body=%s",
                    getattr(response, "status", "unknown"),
                    raw_body,
                )
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.exception(
                "Fawaterk HTTPError: status=%s body=%s",
                exc.code,
                error_body,
            )
            raise EWalletServiceError(_extract_error_message(error_body) or f"Fawaterk request failed with HTTP {exc.code}.") from exc
        except error.URLError as exc:
            logger.exception("Fawaterk URLError: reason=%s", exc.reason)
            raise EWalletServiceError(f"Could not reach Fawaterk API: {exc.reason}") from exc

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            logger.exception("Fawaterk returned invalid JSON: body=%s", raw_body)
            raise EWalletServiceError("Fawaterk API returned invalid JSON.") from exc

        if not isinstance(data, dict):
            logger.error("Fawaterk returned non-dict response: %r", data)
            raise EWalletServiceError("Fawaterk API returned an unexpected response format.")
        return data

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")), "f")


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _extract_error_message(error_body: str) -> str:
    try:
        parsed = json.loads(error_body)
    except json.JSONDecodeError:
        return error_body.strip()

    if not isinstance(parsed, dict):
        return error_body.strip()

    for key in ("message", "error", "status"):
        value = str(parsed.get(key) or "").strip()
        if value:
            return value

    return error_body.strip()


def _mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"
