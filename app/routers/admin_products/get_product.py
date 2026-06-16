from __future__ import annotations

from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dashboard import get_dashboard_products_keyboard
from app.keyboards.products import get_adobe_duration_keyboard
from app.routers.dashboard.shared import is_admin
from app.services.adobe import ADOBE_DURATION_OPTIONS, get_duration_price, is_adobe_product
from app.services.admin_products import AdminProductFulfillmentService, AdminProductFulfillmentServiceError
from app.services.catalog.products import ProductService, SupabaseConfigError
from app.states.dashboard import AdminGetProductState
from app.translations import t


router = Router(name="admin_products_get_product")
product_service = ProductService()
fulfillment_service = AdminProductFulfillmentService(product_service)


@router.callback_query(F.data == "admin_products:list")
async def admin_products_list_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await callback.answer()
    await state.clear()
    await _show_admin_products(callback.message)


@router.callback_query(F.data.startswith("dashboard:admin_get:"))
async def admin_product_selected_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

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

    await state.update_data(
        admin_product_id=product.id,
        admin_product_title=product.title,
        admin_product_price=str(product.price),
        admin_max_quantity=product.quantity,
        admin_uses_manual_activation_emails=product.uses_manual_activation_emails,
    )

    if product.uses_manual_activation_emails:
        await state.update_data(admin_quantity=1)
        if is_adobe_product(product.title):
            await state.set_state(AdminGetProductState.waiting_for_duration)
            await callback.message.answer(
                t("purchase.ask_duration", "ar"),
                reply_markup=get_adobe_duration_keyboard("ar"),
            )
            return

        await state.set_state(AdminGetProductState.waiting_for_assignment_email)
        await callback.message.answer(t("purchase.ask_assignment_email", "ar"))
        return

    await state.set_state(AdminGetProductState.waiting_for_quantity)
    await callback.message.answer(
        "أدخل الكمية التي تريد الحصول عليها مباشرة.\n\n"
        f"المنتج: {product.title.replace('_', ' ')}\n"
        f"المتاح: {product.quantity}"
    )


@router.message(AdminGetProductState.waiting_for_quantity)
async def admin_product_quantity_handler(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    data = await state.get_data()
    quantity_text = (message.text or "").strip()
    if not quantity_text.isdigit():
        await message.answer(t("purchase.invalid_quantity", "ar").format(max_quantity=data["admin_max_quantity"]))
        return

    quantity = int(quantity_text)
    max_quantity = int(data["admin_max_quantity"])
    if quantity < 1 or quantity > max_quantity:
        await message.answer(t("purchase.invalid_quantity", "ar").format(max_quantity=max_quantity))
        return

    await state.update_data(admin_quantity=quantity)
    await _fulfill_for_admin(message, state)


@router.callback_query(F.data.startswith("purchase:duration:"), AdminGetProductState.waiting_for_duration)
async def admin_product_duration_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await callback.answer()
    duration_value = callback.data.rsplit(":", maxsplit=1)[-1]
    if duration_value not in ADOBE_DURATION_OPTIONS:
        return

    duration_price = get_duration_price(duration_value)
    if duration_price is None:
        return

    await state.update_data(
        admin_duration=duration_value,
        admin_product_price=str(Decimal(duration_price)),
    )
    await state.set_state(AdminGetProductState.waiting_for_assignment_email)
    await callback.message.answer(t("purchase.ask_assignment_email", "ar"))


@router.message(AdminGetProductState.waiting_for_assignment_email)
async def admin_product_assignment_email_handler(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    email = (message.text or "").strip()
    if not _is_valid_email(email):
        await message.answer(t("purchase.invalid_assignment_email", "ar"))
        return

    await state.update_data(admin_assignment_email=email)
    await _fulfill_for_admin(message, state)


async def _show_admin_products(message: Message) -> None:
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
        "اختر المنتج الذي تريد الحصول عليه مباشرة.",
        reply_markup=get_dashboard_products_keyboard(products, "admin_get", "ar"),
    )


async def _fulfill_for_admin(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = int(data["admin_product_id"])
    quantity = int(data.get("admin_quantity") or 1)
    assignment_email = str(data.get("admin_assignment_email") or "").strip()
    duration = str(data.get("admin_duration") or "").strip()

    try:
        result = await fulfillment_service.fulfill(
            product_id=product_id,
            quantity=quantity,
            assignment_email=assignment_email,
            duration=duration,
        )
    except (SupabaseConfigError, AdminProductFulfillmentServiceError) as error:
        await message.answer(str(error))
        await state.clear()
        return
    except Exception:
        await message.answer("تعذر الحصول على المنتج مباشرة. حاول مرة أخرى.")
        await state.clear()
        return

    await state.clear()
    await message.answer(_format_admin_product_result(result), parse_mode="HTML")


def _format_admin_product_result(result) -> str:
    lines = [
        "المنتج جاهز",
        "",
        f"المنتج: {escape(result.product.title.replace('_', ' '))}",
        f"الكمية: {result.quantity}",
    ]
    if result.duration:
        lines.append(f"مدة الاشتراك: {escape(result.duration)}")
    if result.action_label:
        lines.append(f"حالة الطلب: {escape(result.action_label)}")
    if result.credentials:
        lines.extend(["", "معلومات الحساب:", f"<pre>{escape(_format_credentials(result.credentials))}</pre>"])

    return "\n".join(lines)


def _format_credentials(credentials: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(credentials, start=1):
        email = str(item.get("email") or "").strip() or "-"
        password = str(item.get("password") or "").strip()
        lines.append(f"{index}. {email}" if not password else f"{index}. {email} | {password}")

    return "\n".join(lines)


def _is_valid_email(value: str) -> bool:
    if not value or "@" not in value:
        return False

    local_part, _, domain_part = value.partition("@")
    return bool(local_part and domain_part and "." in domain_part)
