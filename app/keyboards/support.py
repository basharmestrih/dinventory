from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.support_settings import get_support_username, get_support_whatsapp_phone
from app.translations import t


def get_support_keyboard(lang: str = "ar") -> InlineKeyboardMarkup | None:
    username = get_support_username()
    whatsapp_phone = get_support_whatsapp_phone()

    rows: list[list[InlineKeyboardButton]] = []

    if username:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("buttons.contact_support_telegram_button", lang),
                    url=f"https://t.me/{username}",
                )
            ]
        )

    if whatsapp_phone:
        whatsapp_text = quote(
            "مرحباً، أواجه مشكلة بخصوص منتج غير متوفر حالياً وأحتاج إلى المساعدة."
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("buttons.contact_support_whatsapp_button", lang),
                    url=f"https://wa.me/{whatsapp_phone}?text={whatsapp_text}",
                )
            ]
        )

    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)
