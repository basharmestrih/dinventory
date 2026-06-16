from dataclasses import dataclass
from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from postgrest import APIError
from supabase import Client, create_client

from app.config import settings
from app.models.product import Product
from app.services.catalog.products import SupabaseConfigError
from app.translations import t


class NotificationServiceError(RuntimeError):
    """Raised when notification recipients cannot be loaded."""


@dataclass(slots=True)
class BroadcastResult:
    total_recipients: int
    success_count: int
    failed_count: int


@dataclass(slots=True)
class NotificationPayload:
    text: str
    reply_markup: InlineKeyboardMarkup | None = None


class NotificationService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def fetch_recipient_ids(self) -> list[int]:
        client = self._get_client()
        telegram_id_column = settings.supabase_users_telegram_id_column

        try:
            response = (
                client.table(settings.supabase_users_table)
                .select(telegram_id_column)
                .order(telegram_id_column)
                .execute()
            )
        except APIError as error:
            raise NotificationServiceError(_extract_api_error_message(error)) from error

        recipient_ids: list[int] = []
        seen_ids: set[int] = set()
        for item in response.data or []:
            try:
                recipient_id = int(item[telegram_id_column])
            except (KeyError, TypeError, ValueError):
                continue
            if recipient_id in seen_ids:
                continue
            seen_ids.add(recipient_id)
            recipient_ids.append(recipient_id)

        return recipient_ids

    async def broadcast_text(
        self,
        bot: Bot,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> BroadcastResult:
        recipient_ids = await self.fetch_recipient_ids()

        success_count = 0
        failed_count = 0

        for recipient_id in recipient_ids:
            try:
                await bot.send_message(
                    chat_id=recipient_id,
                    text=text,
                    reply_markup=reply_markup,
                )
                success_count += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                failed_count += 1
            except TelegramAPIError:
                failed_count += 1

        return BroadcastResult(
            total_recipients=len(recipient_ids),
            success_count=success_count,
            failed_count=failed_count,
        )

    def build_product_created_notification(self, product: Product) -> NotificationPayload:
        return NotificationPayload(
            text=self._build_stock_notification_text(
                product.title,
                price=product.price,
                added_quantity=product.quantity,
                current_quantity=product.quantity,
                is_new_product=True,
            ),
            reply_markup=self._build_product_cta_keyboard(product.id),
        )

    def build_product_updated_notification(
        self,
        before: Product,
        after: Product,
    ) -> NotificationPayload | None:
        if before.quantity < after.quantity:
            text = self._build_stock_notification_text(
                after.title,
                price=after.price,
                added_quantity=after.quantity - before.quantity,
                current_quantity=after.quantity,
            )
        elif before.price > after.price:
            text = (
                "عرض خاص لمحبي التوفير\n\n"
                f"المنتج: {after.title}\n"
                f"السعر نزل من {self._format_price(before.price)} إلى {self._format_price(after.price)}\n\n"
                "لا تفوت الفرصة واطلب الآن بالسعر الجديد قبل انتهاء الميزة."
            )
        else:
            text = self._build_default_product_update_text(before, after)

        if text is None:
            return None

        return NotificationPayload(
            text=text,
            reply_markup=self._build_product_cta_keyboard(after.id),
        )

    def _build_default_product_update_text(self, before: Product, after: Product) -> str | None:
        changes: list[str] = []

        if before.price != after.price:
            changes.append(
                f"تم تحديث السعر من {self._format_price(before.price)} إلى {self._format_price(after.price)}"
            )

        if before.quantity != after.quantity:
            changes.append(f"الكمية المتاحة الآن: {after.quantity}")

        if not changes:
            return None

        changes_text = "\n".join(changes)
        return (
            "تحديث جديد على أحد منتجاتنا\n\n"
            f"المنتج: {after.title}\n"
            f"{changes_text}\n\n"
            "تابع المتجر باستمرار واقتنص الفرصة قبل نفاد الكمية."
        )

    @staticmethod
    def _build_stock_notification_text(
        title: str,
        *,
        price: Decimal,
        added_quantity: int,
        current_quantity: int,
        is_new_product: bool = False,
    ) -> str:
        label_line = "✨ منتج جديد\n" if is_new_product else ""
        return (
            f"{title}\n"
            f"{label_line}"
            f"💰 السعر: {NotificationService._format_price(price)}\n"
            f"📥 الكمية المضافة: {added_quantity}\n"
            f"🏬 المتوفر الآن: {current_quantity}"
        )

    def _build_product_cta_keyboard(self, product_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("buttons.buy_now", "ar"),
                        callback_data=f"product:view:{product_id}",
                    )
                ]
            ]
        )

    @staticmethod
    def _format_price(value: Decimal) -> str:
        normalized = format(value.normalize(), "f") if value != 0 else "0"
        return normalized.rstrip("0").rstrip(".") if "." in normalized else normalized


def _extract_api_error_message(error: APIError) -> str:
    details = getattr(error, "details", None)
    message = getattr(error, "message", None)
    code = getattr(error, "code", None)

    parts = [part for part in [message, details, code] if part]
    return " | ".join(parts) if parts else str(error)

