from app.config import settings


DEFAULT_BINANCE_ID = "000000"

_binance_id = settings.binance_id or DEFAULT_BINANCE_ID


def get_binance_id() -> str:
    return _binance_id


def set_binance_id(value: str) -> None:
    global _binance_id
    parsed = parse_binance_id(value)
    _binance_id = parsed


def parse_binance_id(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("Binance ID is required.")

    normalized = text.replace(" ", "")
    if not normalized.isdigit():
        raise ValueError("Binance ID must be numeric.")
    if not 6 <= len(normalized) <= 20:
        raise ValueError("Binance ID length is invalid.")

    return normalized
