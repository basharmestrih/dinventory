from decimal import Decimal, InvalidOperation


def parse_positive_decimal(value: str | None) -> Decimal | None:
    try:
        parsed = Decimal((value or "").strip())
    except (InvalidOperation, ValueError):
        return None

    return parsed if parsed > 0 else None
