from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.order import Order


def get_history_orders_keyboard(orders: list[Order]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for order in orders:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_format_order_button_text(order),
                    callback_data=f"history:detail:{order.id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="رجوع",
                callback_data="menu:home",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_history_order_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="رجوع",
                    callback_data="history:list",
                )
            ]
        ]
    )


def _format_order_button_text(order: Order) -> str:
    return (
        f"ID:{order.id} | "
        f"{order.product_title.replace('_', ' ')} | "
        f"{order.payment_method} | "
        f"{order.total:.2f}EGP | "
        "🎁"
    )
