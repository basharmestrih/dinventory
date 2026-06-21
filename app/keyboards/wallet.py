from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.translations import t


def get_wallet_topup_methods_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="محفظة الموبايل",
                    callback_data="wallet:topup:ewallet",
                )
            ],
            [
                InlineKeyboardButton(
                    text="فوري",
                    callback_data="wallet:topup:fawry",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="بينانس",
                    callback_data="wallet:topup:binance",
                ),
                InlineKeyboardButton(
                    text="إنستا باي",
                    callback_data="wallet:topup:instapay",
                ),
            ],
        ]
    )


def get_wallet_topup_cancel_keyboard(request_id: str, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("wallet.cancel_topup_button", lang),
                    callback_data=f"wallet:topup:cancel:{request_id}",
                )
            ]
        ]
    )


def get_wallet_topup_review_keyboard(request_id: str, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="موافقة",
                    callback_data=f"wallet:review:approve:{request_id}",
                ),
                InlineKeyboardButton(
                    text="رفض",
                    callback_data=f"wallet:review:reject:{request_id}",
                ),
            ]
        ]
    )
