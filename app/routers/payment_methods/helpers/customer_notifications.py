from datetime import datetime
import logging
from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.models.order import Order
from app.models.product import Product
from app.routers.payment_methods.helpers.credential_utils import (
    deserialize_order_credentials,
    get_order_credentials_keyboard,
    get_order_result_keyboard,
    get_order_result_message,
)
from app.services.adobe import ADOBE_DURATION_OPTIONS
from app.services.orders.orders import OrderService, OrderServiceError
from app.services.catalog.products import SupabaseConfigError
from app.services.drive_sheets_tool import schedule_drive_sheets_sync
from app.services.support_settings import get_support_username
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.translations import t


router = Router(name="payment_customer_notifications")
order_service = OrderService()
wallet_service = WalletService()
logger = logging.getLogger(__name__)

SERVER_ERROR_SUPPORT_MESSAGE = "عذرا هنالك خطأ من المخدم يرجى التواصل مع الدعم"


async def notify_customer_about_processed_order(
    context,
    updated_order: Order,
    product: Product | None,
    *,
    note_text: str = "",
    order_action_label: str | None = None,
) -> None:
    if not updated_order.customer_telegram_id:
        logger.info("Order notify skipped: missing customer_telegram_id order_id=%s", updated_order.id)
        return

    try:
        logger.info(
            "Order notify start: order_id=%s status=%s chat_id=%s",
            updated_order.id,
            updated_order.status,
            updated_order.customer_telegram_id,
        )
        await context.bot.send_message(
            chat_id=updated_order.customer_telegram_id,
            text=get_order_result_message(
                updated_order.id,
                updated_order.status,
                order_action_label=order_action_label,
            ),
            reply_markup=get_order_result_keyboard(updated_order.status),
        )
        if updated_order.status == "Paid":
            await send_order_credentials(
                callback=context,
                order=updated_order,
                chat_id=updated_order.customer_telegram_id,
                email=updated_order.email,
                password=updated_order.password,
            )
        if updated_order.status == "Paid":
            await send_wallet_balance_after_purchase(
                callback=context,
                order=updated_order,
            )
        if note_text:
            await context.bot.send_message(
                chat_id=updated_order.customer_telegram_id,
                text=t("purchase.order_review_note_message", "ar").format(note=note_text),
            )
        if updated_order.status == "Paid":
            schedule_drive_sheets_sync(f"order:{updated_order.id}")
        logger.info("Order notify done: order_id=%s", updated_order.id)
    except Exception:
        logger.exception("Order notify failed: order_id=%s", updated_order.id)


async def notify_customer_about_server_error(context, order: Order) -> None:
    if not order.customer_telegram_id:
        logger.info("Server error notify skipped: missing customer_telegram_id order_id=%s", order.id)
        return

    try:
        support_username = get_support_username()
        await context.bot.send_message(
            chat_id=order.customer_telegram_id,
            text=SERVER_ERROR_SUPPORT_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=t("purchase.contact_support_button", "ar"),
                            url=f"https://t.me/{support_username}",
                        )
                    ]
                ]
            ),
        )
    except Exception:
        logger.exception("Server error notify failed: order_id=%s", order.id)


async def send_order_credentials(
    callback,
    order: Order,
    chat_id: int,
    email: str,
    password: str,
) -> None:
    if not email and not password:
        return

    credential_entries = deserialize_order_credentials(email, password)
    if not credential_entries:
        return

    await callback.bot.send_message(
        chat_id=chat_id,
        text=_format_order_credentials_message(order, credential_entries),
        parse_mode="HTML",
        reply_markup=get_order_credentials_keyboard(order.id),
    )


async def send_wallet_balance_after_purchase(callback, order: Order) -> None:
    if order.payment_method.strip().lower() != "wallet":
        return

    username = str(order.customer_username or "").strip()
    if not username:
        return

    try:
        wallet = await wallet_service.fetch_wallet_by_username(username)
    except (SupabaseConfigError, WalletServiceError):
        return
    except Exception:
        return

    if wallet is None:
        return

    await callback.bot.send_message(
        chat_id=order.customer_telegram_id,
        text=(
            "تم إكمال الدفع من رصيد محفظتك بنجاح.\n\n"
            f"رصيدك المتبقي الآن: {wallet.balance_egp:.2f} جنيه مصري."
        ),
    )


@router.callback_query(F.data.startswith("order:copy_accounts:"))
async def copy_order_accounts_handler(callback: CallbackQuery) -> None:
    await callback.answer()

    order_id_text = callback.data.rsplit(":", maxsplit=1)[-1]
    try:
        order_id = int(order_id_text)
    except ValueError:
        return

    try:
        order = await order_service.fetch_order_by_id(order_id)
    except (SupabaseConfigError, OrderServiceError):
        await callback.message.answer("تعذر تجهيز الحسابات للنسخ.")
        return
    except Exception:
        await callback.message.answer("تعذر تجهيز الحسابات للنسخ.")
        return

    if order is None or callback.from_user.id != order.customer_telegram_id or order.status != "Paid":
        await callback.message.answer("تعذر تجهيز الحسابات للنسخ.")
        return

    credential_entries = deserialize_order_credentials(order.email, order.password)
    if not credential_entries:
        await callback.message.answer("تعذر تجهيز الحسابات للنسخ.")
        return

    await callback.message.answer(
        _format_copy_ready_accounts_message(credential_entries),
        parse_mode="HTML",
    )


def _format_order_credentials_message(order: Order, credentials: list[dict[str, str]]) -> str:
    duration_line = ""
    if order.expiry_date and order.expiry_date in ADOBE_DURATION_OPTIONS:
        duration_line = f"\n⏳ مدة الاشتراك: {_format_duration_label(order.expiry_date)}"
    return (
        "📋 تفاصيل الطلب\n\n"
        f"🧾 كود الطلب: {_format_order_code(order)}\n"
        f"📦 المنتج: {escape(order.product_title.replace('_', ' '))}\n"
        f"🔢 الكمية: {order.quantity}\n"
        f"💲 المبلغ: {order.total:.2f} ج.م\n"
        f"📌 الحالة: {_format_order_status(order.status)}\n"
        f"🕒 الوقت: {_format_created_at(order.created_at)}{duration_line}\n\n"
        "🔐 الحسابات المسلمة:\n"
        f"<pre>{escape(_format_credentials_lines(credentials))}</pre>"
    )


def _format_duration_label(value: str) -> str:
    labels = {
        "1_month": t("purchase.duration_buttons.one_month", "ar"),
        "2_months": t("purchase.duration_buttons.two_months", "ar"),
        "6_months": t("purchase.duration_buttons.six_months", "ar"),
        "12_months": t("purchase.duration_buttons.twelve_months", "ar"),
    }
    return labels.get(value, value)


def _format_copy_ready_accounts_message(credentials: list[dict[str, str]]) -> str:
    return (
        "🔐 الحسابات للنسخ:\n"
        f"<pre>{escape(_format_credentials_lines(credentials))}</pre>"
    )


def _format_credentials_lines(credentials: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(credentials, start=1):
        email = str(item.get("email") or "").strip() or "-"
        password = str(item.get("password") or "").strip()
        lines.append(f"{index}. {email}" if not password else f"{index}. {email} | {password}")

    return "\n".join(lines)


def _format_order_code(order: Order) -> str:
    return f"ORD-{order.id}"


def _format_order_status(status: str) -> str:
    labels = {
        "Paid": "مكتمل",
        "Rejected": "مرفوض",
        "pending": "قيد المراجعة",
        "ActivationPending": "قيد التفعيل",
        "ActivationRejected": "مرفوض",
    }
    return labels.get(status, status)


def _format_created_at(value: datetime | None) -> str:
    if value is None:
        return "-"

    return value.strftime("%d/%m/%Y %H:%M")
