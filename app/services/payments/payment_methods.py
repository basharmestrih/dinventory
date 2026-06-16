PAYMENT_METHOD_WALLET = "wallet"
PAYMENT_METHOD_EWALLET = "ewallet"
PAYMENT_METHOD_FAWRY = "fawry"
PAYMENT_METHOD_INSTAPAY = "instapay"
PAYMENT_METHOD_BINANCE = "binance"

PAYMENT_METHODS = (
    PAYMENT_METHOD_WALLET,
    PAYMENT_METHOD_EWALLET,
    PAYMENT_METHOD_FAWRY,
    PAYMENT_METHOD_INSTAPAY,
    PAYMENT_METHOD_BINANCE,
)

_payment_method_enabled: dict[str, bool] = {
    PAYMENT_METHOD_WALLET: True,
    PAYMENT_METHOD_EWALLET: True,
    PAYMENT_METHOD_FAWRY: True,
    PAYMENT_METHOD_INSTAPAY: True,
    PAYMENT_METHOD_BINANCE: True,
}


def is_payment_method_enabled(method: str) -> bool:
    return _payment_method_enabled.get(method, False)


def set_payment_method_enabled(method: str, enabled: bool) -> bool:
    if method not in _payment_method_enabled:
        return False

    _payment_method_enabled[method] = enabled
    return True


def get_payment_methods_status() -> dict[str, bool]:
    return dict(_payment_method_enabled)
