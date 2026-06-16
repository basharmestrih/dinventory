from collections.abc import Mapping

from app.translations import t


ORDER_APPROVED = "order_approved"
ORDER_REJECTED = "order_rejected"
ORDER_ACTIVATION_PENDING = "order_activation_pending"
ORDER_ACTIVATION_REJECTED = "order_activation_rejected"
WALLET_TOPUP_APPROVED = "wallet_topup_approved"
WALLET_TOPUP_REJECTED = "wallet_topup_rejected"

MESSAGE_KEYS = (
    ORDER_APPROVED,
    ORDER_REJECTED,
    ORDER_ACTIVATION_PENDING,
    ORDER_ACTIVATION_REJECTED,
    WALLET_TOPUP_APPROVED,
    WALLET_TOPUP_REJECTED,
)

_messages: dict[str, str] = {}


def get_review_message(message_key: str) -> str:
    _validate_message_key(message_key)
    return _messages.get(message_key) or get_default_review_message(message_key)


def get_default_review_message(message_key: str) -> str:
    _validate_message_key(message_key)

    defaults = {
        ORDER_APPROVED: t("purchase.order_paid_to_user", "ar"),
        ORDER_REJECTED: t("purchase.order_rejected_to_user", "ar"),
        ORDER_ACTIVATION_PENDING: t("purchase.order_activation_pending_to_user", "ar"),
        ORDER_ACTIVATION_REJECTED: t("purchase.order_activation_rejected_to_user", "ar"),
        WALLET_TOPUP_APPROVED: t("wallet.topup_approved_to_user", "ar"),
        WALLET_TOPUP_REJECTED: t("wallet.topup_rejected_to_user", "ar"),
    }
    return defaults[message_key]


def set_review_message(message_key: str, value: str) -> None:
    _validate_message_key(message_key)
    text = (value or "").strip()
    if not text:
        raise ValueError("Review message cannot be empty.")
    _messages[message_key] = text


def render_review_message(message_key: str, values: Mapping[str, object]) -> str:
    template = get_review_message(message_key)
    return _SafeFormatDict(values).format(template)


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"

    def format(self, template: str) -> str:
        return template.format_map(self)


def _validate_message_key(message_key: str) -> None:
    if message_key not in MESSAGE_KEYS:
        raise ValueError(f"Unknown review message key: {message_key}")
