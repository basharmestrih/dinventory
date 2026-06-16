from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.payment_methods import get_payment_methods_keyboard
from app.keyboards.products import get_adobe_duration_keyboard
from app.services.adobe import ADOBE_DURATION_OPTIONS, get_duration_price, is_adobe_product
from app.services.catalog.products import ProductService, SupabaseConfigError
from app.states.purchase import PurchaseState
from app.translations import t


router = Router(name="selected_product")
product_service = ProductService()


@router.callback_query(F.data.startswith("product:view:"))
async def selected_product_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    product_id = int(callback.data.rsplit(":", maxsplit=1)[-1])

    try:
        product = await product_service.fetch_product_by_id(product_id)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except Exception:
        await callback.message.answer(t("sections.products_load_failed", "ar"))
        return

    if product is None:
        await callback.message.answer(t("sections.product_not_found", "ar"))
        return

    if product.quantity <= 0:
        await callback.message.answer(t("purchase.product_out_of_stock", "ar"))
        return

    await state.update_data(
        product_id=product.id,
        product_title=product.title,
        product_description=product.description,
        product_price=str(product.price),
        max_quantity=product.quantity,
        uses_manual_activation_emails=product.uses_manual_activation_emails,
    )

    if product.uses_manual_activation_emails:
        total = Decimal(str(product.price))
        await state.update_data(quantity=1, total=str(total))

        if is_adobe_product(product.title):
            await state.set_state(PurchaseState.waiting_for_duration)
            await callback.message.answer(
                t("purchase.ask_duration", "ar"),
                reply_markup=get_adobe_duration_keyboard("ar"),
            )
            return

        await state.set_state(PurchaseState.waiting_for_assignment_email)
        await callback.message.answer(t("purchase.ask_assignment_email", "ar"))
        return

    await state.set_state(PurchaseState.waiting_for_quantity)

    await callback.message.answer(
        t("purchase.selected_product", "ar").format(
            title=_display_text(product.title),
            description=_display_text(product.description),
            max_quantity=product.quantity,
        )
    )


@router.message(PurchaseState.waiting_for_quantity)
async def quantity_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    quantity_text = (message.text or "").strip()

    if not quantity_text.isdigit():
        await message.answer(
            t("purchase.invalid_quantity", "ar").format(max_quantity=data["max_quantity"])
        )
        return

    quantity = int(quantity_text)
    max_quantity = int(data["max_quantity"])

    if quantity < 1 or quantity > max_quantity:
        await message.answer(
            t("purchase.invalid_quantity", "ar").format(max_quantity=max_quantity)
        )
        return

    total = Decimal(data["product_price"]) * quantity

    await state.update_data(quantity=quantity, total=str(total))
    if is_adobe_product(data.get("product_title")):
        await state.set_state(PurchaseState.waiting_for_duration)
        await message.answer(
            t("purchase.ask_duration", "ar"),
            reply_markup=get_adobe_duration_keyboard("ar"),
        )
        return

    await _prompt_for_payment_method(message, state, quantity=quantity, total=total)


@router.callback_query(F.data.startswith("purchase:duration:"), PurchaseState.waiting_for_duration)
async def adobe_duration_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    duration_value = callback.data.rsplit(":", maxsplit=1)[-1]
    if duration_value not in ADOBE_DURATION_OPTIONS:
        return

    data = await state.get_data()
    quantity = int(data.get("quantity") or 1)
    duration_price = get_duration_price(duration_value)
    if duration_price is None:
        return

    unit_price = Decimal(duration_price)
    total = unit_price * quantity

    await state.update_data(
        duration=duration_value,
        expiry_date=duration_value,
        password="",
        product_price=str(unit_price),
        total=str(total),
    )
    await state.set_state(PurchaseState.waiting_for_assignment_email)
    await callback.message.answer(t("purchase.ask_assignment_email", "ar"))


@router.message(PurchaseState.waiting_for_assignment_email)
async def adobe_assignment_email_handler(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not _is_valid_email(email):
        await message.answer(t("purchase.invalid_assignment_email", "ar"))
        return

    data = await state.get_data()
    quantity = int(data["quantity"])
    total = Decimal(str(data["total"]))

    await state.update_data(email=email)
    await _prompt_for_payment_method(message, state, quantity=quantity, total=total)


def _display_text(value: str) -> str:
    return value.replace("_", " ")


def _format_price(value: Decimal) -> str:
    return f"{value:.2f}"


async def _prompt_for_payment_method(
    message: Message,
    state: FSMContext,
    *,
    quantity: int,
    total: Decimal,
) -> None:
    await state.set_state(PurchaseState.choosing_payment_method)
    await message.answer(
        t("purchase.choose_payment_method", "ar").format(
            quantity=quantity,
            total=_format_price(total),
        ),
        reply_markup=get_payment_methods_keyboard(),
    )


def _is_valid_email(value: str) -> bool:
    if not value or "@" not in value:
        return False

    local_part, _, domain_part = value.partition("@")
    return bool(local_part and domain_part and "." in domain_part)
