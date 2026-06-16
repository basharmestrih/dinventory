from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.translations import t


def get_main_menu_keyboard(lang: str = "ar", *, is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t("buttons.profile", lang), callback_data="menu:profile"),
            InlineKeyboardButton(text=t("buttons.buy", lang), callback_data="menu:buy"),
        ],
        [
            InlineKeyboardButton(text=t("buttons.api_link", lang), callback_data="menu:api_link"),
            InlineKeyboardButton(text=t("buttons.support", lang), callback_data="menu:support"),
        ],
        [
            InlineKeyboardButton(
                text=t("buttons.purchase_history", lang),
                callback_data="menu:purchase_history",
            ),
            InlineKeyboardButton(text=t("buttons.wallet", lang), callback_data="menu:wallet"),
        ],
    ]

    if is_admin:
        rows.append(
            [InlineKeyboardButton(text=t("buttons.dashboard", lang), callback_data="dashboard:home")]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
