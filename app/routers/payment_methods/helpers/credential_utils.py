from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.messaging.review_messages import (
    ORDER_ACTIVATION_PENDING,
    ORDER_ACTIVATION_REJECTED,
    ORDER_APPROVED,
    ORDER_REJECTED,
    render_review_message,
)
from app.translations import t


def parse_activation_emails(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def map_review_action_to_status(action: str) -> str | None:
    statuses = {
        "approve": "Paid",
        "approve_note": "Paid",
        "reject": "Rejected",
    }
    return statuses.get(action)


def get_order_result_message(
    order_id: int,
    status: str,
    *,
    order_action_label: str | None = None,
) -> str:
    if status == "Paid":
        message_key = ORDER_APPROVED
    elif status == "ActivationPending":
        message_key = ORDER_ACTIVATION_PENDING
    elif status == "ActivationRejected":
        message_key = ORDER_ACTIVATION_REJECTED
    else:
        message_key = ORDER_REJECTED
    action_line = f"\nحالة الطلب: {order_action_label}" if order_action_label else ""
    return render_review_message(
        message_key,
        {
            "order_id": order_id,
            "status": status,
            "order_action_line": action_line,
        },
    )



def get_order_result_keyboard(status: str) -> InlineKeyboardMarkup | None:
    if status not in {"Rejected", "ActivationRejected"}:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("purchase.contact_support_button", "ar"),
                    url="https://t.me/basharmestrih01",
                )
            ]
        ]
    )


def get_order_credentials_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="نسخ الحسابات",
                    callback_data=f"order:copy_accounts:{order_id}",
                )
            ]
        ]
    )


def get_order_payment_cancel_keyboard(order_id: int, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("wallet.cancel_topup_button", lang),
                    callback_data=f"order:payment:cancel:{order_id}",
                )
            ]
        ]
    )


def has_valid_credentials(credentials: list[dict[str, str]]) -> bool:
    for item in credentials:
        email = str(item.get("email") or "").strip()
        password = str(item.get("password") or "").strip()
        if not email and not password:
            return False

    return True


def serialize_order_credential_field(
    credentials: list[dict[str, str]],
    *,
    key: str,
) -> str:
    return "\n".join(str(item.get(key) or "").strip() for item in credentials)


def deserialize_order_credentials(email: str, password: str) -> list[dict[str, str]]:
    emails = email.splitlines()
    passwords = password.splitlines()
    total = max(len(emails), len(passwords))

    credentials: list[dict[str, str]] = []
    for index in range(total):
        credential_email = emails[index].strip() if index < len(emails) else ""
        credential_password = passwords[index].strip() if index < len(passwords) else ""
        if not credential_email and not credential_password:
            continue

        credentials.append(
            {
                "email": credential_email,
                "password": credential_password,
            }
        )

    return credentials


def format_credentials_message(credentials: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(credentials, start=1):
        lines.append(
            t("purchase.order_credential_item", "ar").format(
                index=index,
                email=item.get("email", "") or "-",
                password=item.get("password", "") or "-",
            )
        )

    return "\n\n".join(lines)
