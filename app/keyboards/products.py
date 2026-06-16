from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.product import Product
from app.translations import t


def get_products_keyboard(products: list[Product], lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_format_product_button_text(product),
                    callback_data=f"product:view:{product.id}",
                )
            ]
            for product in products
        ]
        + [[InlineKeyboardButton(text=t("buttons.back_to_menu", lang), callback_data="menu:home")]]
    )


def _format_product_button_text(product: Product) -> str:
    price = f"{product.price:.2f}".rstrip("0").rstrip(".")
    quantity_text = "❌" if product.quantity <= 0 else str(product.quantity)
    return f"{product.title} | {price} EGP | {quantity_text} 🎁"


def get_adobe_duration_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("purchase.duration_buttons.one_month", lang),
                    callback_data="purchase:duration:1_month",
                ),
                InlineKeyboardButton(
                    text=t("purchase.duration_buttons.two_months", lang),
                    callback_data="purchase:duration:2_months",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("purchase.duration_buttons.six_months", lang),
                    callback_data="purchase:duration:6_months",
                ),
                InlineKeyboardButton(
                    text=t("purchase.duration_buttons.twelve_months", lang),
                    callback_data="purchase:duration:12_months",
                ),
            ],
        ]
    )
