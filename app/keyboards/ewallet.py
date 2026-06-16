from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_ewallet_payment_options_keyboard(callback_prefix: str = "payment:ewallet") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="فوري", callback_data=f"{callback_prefix}:3"),
                InlineKeyboardButton(text="فودافون كاش/اورانج", callback_data=f"{callback_prefix}:4"),
            ]
        ]
    )
