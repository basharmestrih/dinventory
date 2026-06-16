from decimal import Decimal, InvalidOperation

DEFAULT_EGP_EXCHANGE_RATE = Decimal("54")

_egp_exchange_rate = DEFAULT_EGP_EXCHANGE_RATE


def get_egp_exchange_rate() -> Decimal:
    return _egp_exchange_rate


def rate_change_handler(usd_value: Decimal) -> Decimal:
    return usd_value - Decimal("0.001")


def set_egp_exchange_rate(value: Decimal) -> None:
    global _egp_exchange_rate
    if value <= 0:
        raise ValueError("Exchange rate must be greater than zero.")
    _egp_exchange_rate = value


def parse_egp_exchange_rate(value: str) -> Decimal:
    try:
        rate = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as error:
        raise ValueError("Invalid exchange rate value.") from error

    if rate <= 0:
        raise ValueError("Exchange rate must be greater than zero.")

    return rate
