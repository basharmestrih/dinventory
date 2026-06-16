from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.history import (
    get_history_order_details_keyboard,
    get_history_orders_keyboard,
)
from app.models.order import Order
from app.services.orders.orders import OrderService, OrderServiceError
from app.services.catalog.products import SupabaseConfigError
from app.translations import t


router = Router(name="history")
order_service = OrderService()


@router.callback_query(F.data == "menu:purchase_history")
async def history_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await _show_history_orders(callback.message, callback.from_user.username)


@router.message(Command("history"))
async def history_command_handler(message: Message) -> None:
    await _show_history_orders(message, message.from_user.username if message.from_user else None)


@router.callback_query(F.data == "history:list")
async def history_list_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await _show_history_orders(callback.message, callback.from_user.username, edit=True)


@router.callback_query(F.data.startswith("history:detail:"))
async def history_detail_handler(callback: CallbackQuery) -> None:
    await callback.answer()

    user = callback.from_user
    username = user.username if user else None
    if not username:
        await callback.message.edit_text(t("history.username_missing", "ar"))
        return

    order_id_text = callback.data.rsplit(":", maxsplit=1)[-1]
    try:
        order_id = int(order_id_text)
    except ValueError:
        return

    try:
        orders = await order_service.fetch_paid_orders_by_username(username)
    except SupabaseConfigError:
        await callback.message.edit_text(t("sections.supabase_not_configured", "ar"))
        return
    except OrderServiceError as error:
        await callback.message.edit_text(
            t("history.load_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except Exception:
        await callback.message.edit_text(t("history.load_failed", "ar"))
        return

    order = next((item for item in orders if item.id == order_id), None)
    if order is None:
        await callback.message.edit_text(
            t("history.no_paid_orders", "ar").format(username=username)
        )
        return

    await callback.message.edit_text(
        _format_order_details(order),
        reply_markup=get_history_order_details_keyboard(),
    )


async def _show_history_orders(message: Message, username: str | None, *, edit: bool = False) -> None:
    if not username:
        await _send_or_edit(message, t("history.username_missing", "ar"), edit=edit)
        return

    try:
        orders = await order_service.fetch_paid_orders_by_username(username)
    except SupabaseConfigError:
        await _send_or_edit(message, t("sections.supabase_not_configured", "ar"), edit=edit)
        return
    except OrderServiceError as error:
        await _send_or_edit(message, t("history.load_failed_with_reason", "ar").format(reason=str(error)), edit=edit)
        return
    except Exception:
        await _send_or_edit(message, t("history.load_failed", "ar"), edit=edit)
        return

    if not orders:
        await _send_or_edit(message, t("history.no_paid_orders", "ar").format(username=username), edit=edit)
        return

    await _send_or_edit(
        message,
        _format_history_title(username, orders),
        reply_markup=get_history_orders_keyboard(orders),
        edit=edit,
    )


async def _send_or_edit(message: Message, text: str, *, edit: bool, reply_markup=None) -> None:
    if edit:
        await message.edit_text(text, reply_markup=reply_markup)
        return

    await message.answer(text, reply_markup=reply_markup)


def _format_history_title(username: str, orders: list[Order]) -> str:
    return t("history.title", "ar").format(username=username, count=len(orders))


def _format_order_details(order: Order) -> str:
    return (
        "تفاصيل الطلب\n\n"
        f"ID: {order.id}\n"
        f"المنتج: {order.product_title.replace('_', ' ')}\n"
        f"الكمية: {order.quantity}\n"
        f"الإجمالي: {order.total:.2f} EGP\n"
        f"طريقة الدفع: {order.payment_method}\n"
        f"رقم العملية: {order.transaction_id or '-'}\n"
        f"الحالة: {order.status}\n"
        f"تاريخ الطلب: {_format_created_at(order.created_at)}"
    )


def _format_created_at(value) -> str:
    if value is None:
        return "-"

    return value.strftime("%Y-%m-%d %H:%M")
