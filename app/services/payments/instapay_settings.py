from app.config import settings


DEFAULT_INSTAPAY_PHONE_NUMBER = "+51324355"

_instapay_phone_number = settings.instapay_phone_number or DEFAULT_INSTAPAY_PHONE_NUMBER


def get_instapay_phone_number() -> str:
    return _instapay_phone_number


def set_instapay_phone_number(value: str) -> None:
    global _instapay_phone_number
    parsed = parse_instapay_phone_number(value)
    _instapay_phone_number = parsed


def parse_instapay_phone_number(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("InstaPay phone number is required.")

    normalized = text.replace(" ", "").replace("-", "")
    digits = normalized[1:] if normalized.startswith("+") else normalized
    if not digits.isdigit() or not 6 <= len(digits) <= 15:
        raise ValueError("Invalid InstaPay phone number.")

    return normalized
