from app.config import settings


DEFAULT_SUPPORT_USERNAME = "support"
DEFAULT_SUPPORT_WHATSAPP_PHONE = "+963937138915"

_support_username = settings.support_username or DEFAULT_SUPPORT_USERNAME
_support_whatsapp_phone = settings.support_whatsapp_phone or DEFAULT_SUPPORT_WHATSAPP_PHONE


def get_support_username() -> str:
    return _support_username


def get_support_whatsapp_phone() -> str:
    return _support_whatsapp_phone


def set_support_username(value: str) -> None:
    global _support_username
    parsed = parse_support_username(value)
    _support_username = parsed


def set_support_whatsapp_phone(value: str) -> None:
    global _support_whatsapp_phone
    parsed = parse_support_whatsapp_phone(value)
    _support_whatsapp_phone = parsed


def parse_support_username(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("Support username is required.")

    normalized = text.lstrip("@").strip()
    if not normalized:
        raise ValueError("Support username is required.")

    if not _is_valid_username(normalized):
        raise ValueError("Invalid support username.")

    return normalized


def parse_support_whatsapp_phone(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("WhatsApp phone is required.")

    normalized = text.replace(" ", "").replace("-", "")
    digits = normalized[1:] if normalized.startswith("+") else normalized
    if not digits.isdigit() or not 6 <= len(digits) <= 15:
        raise ValueError("Invalid WhatsApp phone number.")

    return normalized if normalized.startswith("+") else f"+{normalized}"


def _is_valid_username(value: str) -> bool:
    if not 5 <= len(value) <= 32:
        return False
    for char in value:
        if char.isalnum() or char == "_":
            continue
        return False
    return True
