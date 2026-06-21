from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dashboard import (
    get_account_type_keyboard,
    get_dashboard_keyboard,
    get_dashboard_products_keyboard,
    get_product_edit_fields_keyboard,
)
from app.models.product import Product
from app.routers.dashboard.shared import (
    is_admin,
    notification_service,
    original_product_from_state,
    parse_decimal,
    parse_positive_int,
    product_service,
)
from app.services.messaging.notifications import NotificationServiceError
from app.services.catalog.products import ProductServiceError, SupabaseConfigError
from app.states.dashboard import AddProductState, EditProductState
from app.translations import t


router = Router(name="dashboard_products")


@router.callback_query(F.data == "dashboard:add")
async def dashboard_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.clear()
    await state.set_state(AddProductState.title)
    await callback.answer()
    await callback.message.answer(t("dashboard.add.ask_title", "ar"))


@router.message(AddProductState.title)
async def add_title_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddProductState.description)
    await message.answer(t("dashboard.add.ask_description", "ar"))


@router.message(AddProductState.description)
async def add_description_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AddProductState.supplier_price)
    await message.answer(t("dashboard.add.ask_supplier_price", "ar"))


@router.message(AddProductState.supplier_price)
async def add_supplier_price_handler(message: Message, state: FSMContext) -> None:
    supplier_price = parse_decimal(message.text)
    if supplier_price is None:
        await message.answer(t("dashboard.validation.invalid_price", "ar"))
        return

    await state.update_data(supplier_price=str(supplier_price))
    await state.set_state(AddProductState.price)
    await message.answer(t("dashboard.add.ask_price", "ar"))


@router.message(AddProductState.price)
async def add_price_handler(message: Message, state: FSMContext) -> None:
    price = parse_decimal(message.text)
    if price is None:
        await message.answer(t("dashboard.validation.invalid_price", "ar"))
        return

    await state.update_data(price=str(price))
    await state.set_state(AddProductState.image)
    await message.answer(t("dashboard.add.ask_image", "ar"))


@router.message(AddProductState.image)
async def add_image_handler(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1] if message.photo else None
    if photo is None:
        await message.answer(t("dashboard.validation.invalid_image", "ar"))
        return

    await state.update_data(image=photo.file_id)
    await state.set_state(AddProductState.account_type)
    await message.answer(
        t("dashboard.add.ask_account_type", "ar"),
        reply_markup=get_account_type_keyboard("ar"),
    )


@router.callback_query(F.data == "dashboard:add:account_type:personal", AddProductState.account_type)
async def add_personal_account_type(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.update_data(credentials="none", uses_manual_activation_emails=True)
    await state.set_state(AddProductState.quantity)
    await callback.answer()
    await callback.message.answer(t("dashboard.add.ask_quantity", "ar"))


@router.callback_query(F.data == "dashboard:add:account_type:new", AddProductState.account_type)
async def add_new_account_type(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.update_data(uses_manual_activation_emails=False)
    await state.set_state(AddProductState.credentials)
    await callback.answer()
    await callback.message.answer(t("dashboard.add.ask_credentials", "ar"))


@router.message(AddProductState.account_type)
async def add_account_type_text_fallback(message: Message) -> None:
    await message.answer("اختر نوع الحساب من الأزرار.")


@router.message(AddProductState.quantity)
async def add_quantity_handler(message: Message, state: FSMContext) -> None:
    quantity = parse_positive_int(message.text)
    if quantity is None:
        await message.answer(t("dashboard.validation.invalid_quantity", "ar"))
        return

    await state.update_data(quantity=quantity)
    await state.update_data(credentials="none")
    await create_product_from_state(message, state)


@router.message(AddProductState.credentials)
async def add_credentials_handler(message: Message, state: FSMContext) -> None:
    parsed_credentials = _parse_credentials_input(message.text)
    if parsed_credentials is None:
        await message.answer(t("dashboard.validation.invalid_credentials_format", "ar"))
        return

    await state.update_data(
        credentials=parsed_credentials,
        quantity=len(parsed_credentials),
    )
    await create_product_from_state(message, state)


async def create_product_from_state(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    try:
        created_product = await product_service.create_product(
            title=data["title"],
            description=data["description"],
            quantity=int(data["quantity"]),
            image=str(data.get("image") or ""),
            supplier_price=Decimal(data["supplier_price"]),
            price=Decimal(str(data["price"])),
            credentials=data["credentials"],
        )
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        await state.clear()
        return
    except ProductServiceError as error:
        await message.answer(
            t("dashboard.messages.create_failed_with_reason", "ar").format(reason=str(error))
        )
        await state.clear()
        return
    except Exception:
        await message.answer(t("dashboard.messages.create_failed", "ar"))
        await state.clear()
        return

    await state.clear()
    await broadcast_product_created(message, created_product)
    await message.answer(
        t("dashboard.messages.product_created", "ar"),
        reply_markup=get_dashboard_keyboard("ar"),
    )


@router.callback_query(F.data == "dashboard:edit")
async def dashboard_edit_start(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await callback.answer()
    await send_product_selection(callback, action="edit")


@router.callback_query(F.data == "dashboard:delete")
async def dashboard_delete_start(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await callback.answer()
    await send_product_selection(callback, action="delete")


@router.callback_query(F.data.startswith("dashboard:edit:"))
async def dashboard_edit_select(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    product_id = int(callback.data.rsplit(":", maxsplit=1)[-1])

    try:
        product = await product_service.fetch_product_by_id(product_id)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return

    if product is None:
        await callback.message.answer(t("sections.product_not_found", "ar"))
        return

    await state.clear()
    await state.set_state(EditProductState.choosing_field)
    await state.update_data(
        product_id=product.id,
        title=product.title,
        description=product.description,
        quantity=product.quantity,
        supplier_price=str(product.supplier_price),
        price=str(product.price),
        credentials="none" if product.uses_manual_activation_emails else product.credentials,
        uses_manual_activation_emails=product.uses_manual_activation_emails,
        original_title=product.title,
        original_description=product.description,
        original_quantity=product.quantity,
        original_image=product.image,
        original_supplier_price=str(product.supplier_price),
        original_price=str(product.price),
    )

    await callback.answer()
    await callback.message.answer(
        _format_edit_menu(await state.get_data()),
        reply_markup=_get_product_edit_fields_keyboard(await state.get_data()),
    )


@router.callback_query(F.data.startswith("dashboard:edit_field:"), EditProductState.choosing_field)
async def dashboard_edit_field_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    field = callback.data.rsplit(":", maxsplit=1)[-1]
    if field == "finish":
        await callback.answer()
        await _finish_product_edit(callback.message, state)
        return

    if field == "credentials":
        data = await state.get_data()
        credentials = data.get("credentials")
        if not isinstance(credentials, list) or not credentials:
            await callback.answer("هذا المنتج لا يحتوي على بيانات حسابات قابلة للتعديل.", show_alert=True)
            return

        await state.set_state(EditProductState.waiting_for_credentials_replacement)
        await callback.answer()
        await callback.message.answer(
            _format_credentials_replacement_prompt(credentials),
            parse_mode="HTML",
        )
        return

    field_config = _get_edit_field_config(field)
    if field_config is None:
        await callback.answer()
        return

    data = await state.get_data()
    await state.update_data(edit_field=field)
    await state.set_state(EditProductState.waiting_for_value)
    await callback.answer()
    await callback.message.answer(
        t(field_config["prompt_key"], "ar").format(current=data[field_config["data_key"]])
    )


@router.message(EditProductState.waiting_for_value)
async def dashboard_edit_value_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = str(data.get("edit_field") or "")
    field_config = _get_edit_field_config(field)
    if field_config is None:
        await state.set_state(EditProductState.choosing_field)
        await message.answer(
            _format_edit_menu(data),
            reply_markup=_get_product_edit_fields_keyboard(data),
        )
        return

    parsed_value = field_config["parser"](message.text)
    if parsed_value is None:
        await message.answer(t(field_config["error_key"], "ar"))
        return

    serialized_value = field_config["serializer"](parsed_value)

    if field == "quantity" and not bool(data.get("uses_manual_activation_emails")):
        current_quantity = int(data["quantity"])
        quantity_increment = int(serialized_value)
        await state.set_state(EditProductState.waiting_for_credentials)
        await state.update_data(
            pending_quantity_increment=quantity_increment,
            quantity=current_quantity + quantity_increment,
        )
        await message.answer(t("dashboard.add.ask_credentials", "ar"))
        return

    if field == "quantity":
        current_quantity = int(data["quantity"])
        await state.update_data(quantity=current_quantity + int(serialized_value))
    else:
        await state.update_data(**{field_config["data_key"]: serialized_value})

    await state.set_state(EditProductState.choosing_field)
    updated_data = await state.get_data()
    await message.answer(
        _format_edit_menu(updated_data),
        reply_markup=_get_product_edit_fields_keyboard(updated_data),
    )


@router.message(EditProductState.waiting_for_credentials)
async def dashboard_edit_credentials_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    parsed_credentials = _parse_credentials_input(message.text)
    if parsed_credentials is None:
        await message.answer(t("dashboard.validation.invalid_credentials_format", "ar"))
        return

    quantity_increment = int(data.get("pending_quantity_increment") or 0)
    if len(parsed_credentials) != quantity_increment:
        await message.answer(
            t("dashboard.validation.credentials_count_mismatch", "ar").format(
                quantity=quantity_increment,
                credentials_count=len(parsed_credentials),
            )
        )
        return

    existing_credentials = data.get("credentials")
    if not isinstance(existing_credentials, list):
        existing_credentials = []

    await state.update_data(
        credentials=[*existing_credentials, *parsed_credentials],
        pending_quantity_increment=None,
    )
    await state.set_state(EditProductState.choosing_field)
    updated_data = await state.get_data()
    await message.answer(
        _format_edit_menu(updated_data),
        reply_markup=_get_product_edit_fields_keyboard(updated_data),
    )


@router.message(EditProductState.waiting_for_credentials_replacement)
async def dashboard_replace_credentials_handler(message: Message, state: FSMContext) -> None:
    parsed_credentials = _parse_credentials_input(message.text)
    if parsed_credentials is None:
        await message.answer(t("dashboard.validation.invalid_credentials_format", "ar"))
        return

    await state.update_data(
        credentials=parsed_credentials,
        quantity=len(parsed_credentials),
    )
    await state.set_state(EditProductState.choosing_field)
    updated_data = await state.get_data()
    await message.answer(
        _format_edit_menu(updated_data),
        reply_markup=_get_product_edit_fields_keyboard(updated_data),
    )


@router.callback_query(F.data.startswith("dashboard:delete:"))
async def dashboard_delete_confirm(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    product_id = int(callback.data.rsplit(":", maxsplit=1)[-1])

    try:
        deleted = await product_service.delete_product(product_id)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except ProductServiceError as error:
        await callback.message.answer(
            t("dashboard.messages.delete_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except Exception:
        await callback.message.answer(t("dashboard.messages.delete_failed", "ar"))
        return

    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.product_deleted", "ar")
        if deleted
        else t("sections.product_not_found", "ar"),
        reply_markup=get_dashboard_keyboard("ar"),
    )


async def send_product_selection(callback: CallbackQuery, action: str) -> None:
    try:
        products = await product_service.fetch_products()
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except Exception:
        await callback.message.answer(t("sections.products_load_failed", "ar"))
        return

    if not products:
        await callback.message.answer(t("sections.no_products", "ar"))
        return

    await callback.message.answer(
        t(f"dashboard.messages.select_for_{action}", "ar"),
        reply_markup=get_dashboard_products_keyboard(products, action, "ar"),
    )


async def broadcast_product_created(message: Message, product: Product) -> None:
    notification = notification_service.build_product_created_notification(product)

    try:
        await notification_service.broadcast_text(
            message.bot,
            notification.text,
            reply_markup=notification.reply_markup,
        )
    except (SupabaseConfigError, NotificationServiceError, Exception):
        return


async def broadcast_product_updated(message: Message, before: Product, after: Product) -> None:
    notification = notification_service.build_product_updated_notification(before, after)
    if notification is None:
        return

    try:
        await notification_service.broadcast_text(
            message.bot,
            notification.text,
            reply_markup=notification.reply_markup,
        )
    except (SupabaseConfigError, NotificationServiceError, Exception):
        return


async def _finish_product_edit(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    original_product = original_product_from_state(data)

    try:
        updated = await product_service.update_product(
            product_id=int(data["product_id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            quantity=int(data["quantity"]),
            supplier_price=Decimal(str(data["supplier_price"])),
            price=Decimal(str(data["price"])),
            credentials=data["credentials"],
        )
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        await state.clear()
        return
    except ProductServiceError as error:
        await message.answer(
            t("dashboard.messages.update_failed_with_reason", "ar").format(reason=str(error))
        )
        await state.clear()
        return
    except Exception:
        await message.answer(t("dashboard.messages.update_failed", "ar"))
        await state.clear()
        return

    await state.clear()
    if updated is not None:
        await broadcast_product_updated(message, original_product, updated)
    await message.answer(
        t("dashboard.messages.product_updated", "ar")
        if updated
        else t("sections.product_not_found", "ar"),
        reply_markup=get_dashboard_keyboard("ar"),
    )


def _get_edit_field_config(field: str) -> dict | None:
    field_configs = {
        "title": {
            "data_key": "title",
            "prompt_key": "dashboard.edit.ask_title",
            "error_key": "dashboard.validation.invalid_edit_text",
            "parser": _parse_required_text,
            "serializer": str,
        },
        "description": {
            "data_key": "description",
            "prompt_key": "dashboard.edit.ask_description",
            "error_key": "dashboard.validation.invalid_edit_text",
            "parser": _parse_required_text,
            "serializer": str,
        },
        "quantity": {
            "data_key": "quantity",
            "prompt_key": "dashboard.edit.ask_quantity",
            "error_key": "dashboard.validation.invalid_quantity_or_skip",
            "parser": parse_positive_int,
            "serializer": int,
        },
        "supplier_price": {
            "data_key": "supplier_price",
            "prompt_key": "dashboard.edit.ask_supplier_price",
            "error_key": "dashboard.validation.invalid_price_or_skip",
            "parser": parse_decimal,
            "serializer": _serialize_decimal,
        },
        "price": {
            "data_key": "price",
            "prompt_key": "dashboard.edit.ask_price",
            "error_key": "dashboard.validation.invalid_price_or_skip",
            "parser": parse_decimal,
            "serializer": _serialize_decimal,
        },
    }
    return field_configs.get(field)


def _format_edit_menu(data: dict) -> str:
    return t("dashboard.messages.edit_menu", "ar").format(
        title=data["title"],
        description=data["description"],
        quantity=data["quantity"],
        supplier_price=data["supplier_price"],
        price=data["price"],
    )


def _get_product_edit_fields_keyboard(data: dict):
    credentials = data.get("credentials")
    return get_product_edit_fields_keyboard(
        "ar",
        can_edit_credentials=isinstance(credentials, list) and bool(credentials),
    )


def _format_credentials_replacement_prompt(credentials: list[dict[str, str]]) -> str:
    return (
        "تعديل بيانات الحسابات\n\n"
        "انسخ بيانات الحسابات من المربع التالي، عدّل ما تريد، ثم أرسلها هنا مرة أخرى ليتم استبدال البيانات القديمة.\n\n"
        f"<pre>{escape(_format_credentials_lines(credentials))}</pre>"
    )


def _format_credentials_lines(credentials: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{str(item.get('email') or '').strip()} | {str(item.get('password') or '').strip()}"
        for item in credentials
    )


def _parse_required_text(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def _serialize_decimal(value: Decimal) -> str:
    return str(value)


def _parse_credentials_input(value: str | None) -> list[dict[str, str]] | None:
    lines = [line.strip() for line in (value or "").splitlines() if line.strip()]
    if not lines:
        return None

    credentials: list[dict[str, str]] = []
    for line in lines:
        if "|" not in line:
            return None

        email, password = [part.strip() for part in line.split("|", maxsplit=1)]
        if not email or not password:
            return None

        credentials.append(
            {
                "email": email,
                "password": password,
            }
        )

    return credentials
