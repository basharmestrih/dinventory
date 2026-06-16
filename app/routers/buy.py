from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.products import get_products_keyboard
from app.services.catalog.products import ProductService, SupabaseConfigError
from app.translations import t


router = Router(name="buy")
product_service = ProductService()


@router.callback_query(F.data == "menu:buy")
async def buy_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await _show_products(callback.message)


@router.message(Command("products"))
async def products_command_handler(message: Message) -> None:
    await _show_products(message)


async def _show_products(message: Message) -> None:

    try:
        products = await product_service.fetch_products()
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except Exception:
        await message.answer(t("sections.products_load_failed", "ar"))
        return

    if not products:
        await message.answer(t("sections.no_products", "ar"))
        return

    await message.answer(
        t("sections.buy", "ar"),
        reply_markup=get_products_keyboard(products, "ar"),
    )
