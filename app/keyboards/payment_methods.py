from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.translations import t


def get_payment_methods_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("purchase.buttons.wallet", lang), callback_data="payment:wallet"),
                InlineKeyboardButton(text=t("purchase.buttons.ewallet", lang), callback_data="payment:ewallet"),
            ],
            [
                InlineKeyboardButton(text=t("purchase.buttons.fawry", lang), callback_data="payment:fawry"),
                InlineKeyboardButton(text=t("purchase.buttons.instapay", lang), callback_data="payment:instapay"),
            ],
            [
                InlineKeyboardButton(text=t("purchase.buttons.binance", lang), callback_data="payment:binance"),
            ],
        ]
    )
