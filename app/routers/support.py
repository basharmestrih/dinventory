from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import quote

from app.translations import t
from app.services.support_settings import get_support_username, get_support_whatsapp_phone


router = Router(name="support")


@router.callback_query(F.data == "menu:support")
async def support_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        t("sections.support", "ar"),
        reply_markup=_build_support_keyboard(),
    )


@router.message(Command("support"))
async def support_command_handler(message: Message) -> None:
    await message.answer(
        t("sections.support", "ar"),
        reply_markup=_build_support_keyboard(),
    )


def _build_support_keyboard() -> InlineKeyboardMarkup | None:
    username = get_support_username()
    whatsapp_phone = get_support_whatsapp_phone()
    if not username and not whatsapp_phone:
        return None

    whatsapp_text_ar = (
        "مرحباً، أنا مستخدم في بوت 3allemny للمنتجات الرقمية. "
        "لدي مشكلة تقنية وأحتاج المساعدة."
    )
    whatsapp_url = f"https://wa.me/{whatsapp_phone}?text={quote(whatsapp_text_ar)}" if whatsapp_phone else ""

    rows: list[list[InlineKeyboardButton]] = []
    if username:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("purchase.contact_support_button", "ar"),
                    url=f"https://t.me/{username}",
                )
            ]
        )
    if whatsapp_url:
        rows.append([InlineKeyboardButton(text="الدعم (واتساب)", url=whatsapp_url)])

    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
