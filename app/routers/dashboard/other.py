from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from decimal import Decimal

from app.keyboards.dashboard import (
    get_dashboard_section_keyboard,
    get_wallet_balance_action_keyboard,
    get_wallet_users_keyboard,
)
from app.routers.dashboard.shared import is_admin
from app.services.catalog.products import SupabaseConfigError
from app.services.payments.exchange_rate import (
    DEFAULT_EGP_EXCHANGE_RATE,
    get_egp_exchange_rate,
    parse_egp_exchange_rate,
    set_egp_exchange_rate,
)
from app.services.payments.instapay_settings import (
    get_instapay_phone_number,
    parse_instapay_phone_number,
    set_instapay_phone_number,
)
from app.services.payments.binance_settings import (
    get_binance_id,
    parse_binance_id,
    set_binance_id,
)
from app.routers.dashboard.shared import product_service
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.services.support_settings import (
    get_support_username,
    get_support_whatsapp_phone,
    parse_support_username,
    parse_support_whatsapp_phone,
    set_support_username,
    set_support_whatsapp_phone,
)
# Review-message editing is temporarily disabled.
# from app.services.messaging.review_messages import (
#     MESSAGE_KEYS,
#     get_review_message,
#     set_review_message,
# )
from app.states.dashboard import DashboardOtherState
from app.translations import t


router = Router(name="dashboard_other")
wallet_service = WalletService()


@router.callback_query(F.data == "dashboard:other:change_egp_exchange_rate")
async def dashboard_change_egp_exchange_rate_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.set_state(DashboardOtherState.waiting_for_egp_exchange_rate)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_egp_exchange_rate", "ar").format(
            current_rate=_format_rate(get_egp_exchange_rate()),
            default_rate=_format_rate(DEFAULT_EGP_EXCHANGE_RATE),
        )
    )


@router.callback_query(F.data == "dashboard:other:set_special_products")
async def dashboard_set_special_products_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    try:
        products = await product_service.fetch_products()
    except Exception:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.products_load_failed", "ar"))
        return

    if not products:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.no_products", "ar"))
        return

    await state.update_data(
        special_products=[{"id": product.id, "title": product.title} for product in products]
    )
    await state.set_state(DashboardOtherState.waiting_for_special_products)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_special_products", "ar").format(
            products_list=_format_numbered_products(products),
        )
    )


@router.callback_query(F.data == "dashboard:other:adjust_wallet_balance")
async def dashboard_adjust_wallet_balance_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    try:
        wallets = await wallet_service.fetch_wallets()
    except SupabaseConfigError:
        await callback.answer()
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except WalletServiceError as error:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.wallet_users_load_failed_with_reason", "ar").format(reason=str(error)))
        return
    except Exception as error:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.wallet_users_load_failed_with_reason", "ar").format(reason=str(error)))
        return

    if not wallets:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.no_wallet_users", "ar"))
        return

    await state.clear()
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_wallet_user", "ar"),
        reply_markup=get_wallet_users_keyboard(
            [(wallet.username, _format_wallet_balance(wallet.balance_egp)) for wallet in wallets],
            "ar",
        ),
    )


@router.callback_query(F.data.startswith("dashboard:other:wallet_user:"))
async def dashboard_wallet_user_selected(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    username = callback.data.rsplit(":", maxsplit=1)[-1]
    if not username:
        await callback.answer()
        return

    try:
        wallet = await wallet_service.ensure_wallet(username)
    except SupabaseConfigError:
        await callback.answer()
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except WalletServiceError as error:
        await callback.answer()
        await callback.message.answer(t("dashboard.messages.wallet_user_load_failed_with_reason", "ar").format(reason=str(error)))
        return

    await state.update_data(wallet_username=username)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_wallet_action", "ar").format(
            username=wallet.username,
            balance=_format_wallet_balance(wallet.balance_egp),
        ),
        reply_markup=get_wallet_balance_action_keyboard(username, "ar"),
    )


@router.callback_query(F.data.startswith("dashboard:other:wallet_balance:"))
async def dashboard_wallet_balance_action_selected(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer()
        return

    action = parts[3]
    username = parts[4]
    if action not in {"add", "cut"} or not username:
        await callback.answer()
        return

    await state.update_data(wallet_username=username, wallet_balance_action=action)
    await state.set_state(DashboardOtherState.waiting_for_wallet_balance_amount)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_wallet_balance_amount", "ar").format(
            action=t(f"dashboard.buttons.{ 'add_balance' if action == 'add' else 'cut_balance' }", "ar"),
            username=username,
        )
    )


@router.message(DashboardOtherState.waiting_for_egp_exchange_rate)
async def dashboard_change_egp_exchange_rate_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    try:
        rate = parse_egp_exchange_rate(message.text or "")
    except ValueError:
        await message.answer(t("dashboard.messages.invalid_egp_exchange_rate", "ar"))
        return

    old_rate = get_egp_exchange_rate()
    set_egp_exchange_rate(rate)
    await state.clear()
    await message.answer(
        t("dashboard.messages.egp_exchange_rate_updated", "ar").format(
            old_rate=_format_rate(old_rate),
            new_rate=_format_rate(rate),
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.callback_query(F.data == "dashboard:other:change_instapay_phone_number")
async def dashboard_change_instapay_phone_number_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.set_state(DashboardOtherState.waiting_for_instapay_phone_number)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_instapay_phone_number", "ar").format(
            current_phone_number=get_instapay_phone_number(),
        )
    )


@router.callback_query(F.data == "dashboard:other:change_binance_id")
async def dashboard_change_binance_id_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.set_state(DashboardOtherState.waiting_for_binance_id)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_binance_id", "ar").format(
            current_binance_id=get_binance_id(),
        )
    )


@router.callback_query(F.data == "dashboard:other:change_support_username")
async def dashboard_change_support_username_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.set_state(DashboardOtherState.waiting_for_support_username)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_support_username", "ar").format(
            current_support_username=get_support_username(),
        )
    )


@router.callback_query(F.data == "dashboard:other:change_support_whatsapp_phone")
async def dashboard_change_support_whatsapp_phone_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    await state.set_state(DashboardOtherState.waiting_for_support_whatsapp_phone)
    await callback.answer()
    await callback.message.answer(
        t("dashboard.messages.ask_support_whatsapp_phone", "ar").format(
            current_whatsapp_phone=get_support_whatsapp_phone(),
        )
    )


@router.message(DashboardOtherState.waiting_for_instapay_phone_number)
async def dashboard_change_instapay_phone_number_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    try:
        phone_number = parse_instapay_phone_number(message.text or "")
    except ValueError:
        await message.answer(t("dashboard.messages.invalid_instapay_phone_number", "ar"))
        return

    old_phone_number = get_instapay_phone_number()
    set_instapay_phone_number(phone_number)
    await state.clear()
    await message.answer(
        t("dashboard.messages.instapay_phone_number_updated", "ar").format(
            old_phone_number=old_phone_number,
            new_phone_number=phone_number,
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.message(DashboardOtherState.waiting_for_special_products)
async def dashboard_set_special_products_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    data = await state.get_data()
    products_data = data.get("special_products")
    if not isinstance(products_data, list) or not products_data:
        await state.clear()
        await message.answer(t("dashboard.messages.products_load_failed", "ar"))
        return

    choices = _parse_numeric_choices(message.text or "", len(products_data))
    if choices is None:
        await message.answer(t("dashboard.messages.invalid_special_products_selection", "ar"))
        return

    selected_products = [products_data[index - 1] for index in choices]
    updated_products = await product_service.mark_products_special(
        [int(item["id"]) for item in selected_products]
    )
    await state.clear()
    await message.answer(
        t("dashboard.messages.special_products_updated", "ar").format(
            updated_count=len(updated_products),
            selected_items=_format_selected_products(selected_products),
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.message(DashboardOtherState.waiting_for_wallet_balance_amount)
async def dashboard_wallet_balance_amount_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    data = await state.get_data()
    username = str(data.get("wallet_username") or "").strip()
    action = str(data.get("wallet_balance_action") or "").strip()
    if action not in {"add", "cut"} or not username:
        await state.clear()
        await message.answer(t("dashboard.messages.wallet_balance_context_lost", "ar"), reply_markup=get_dashboard_section_keyboard("other", "ar"))
        return

    try:
        amount = Decimal((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer(t("dashboard.messages.invalid_wallet_balance_amount", "ar"))
        return

    try:
        if action == "add":
            wallet = await wallet_service.apply_topup(username, amount)
        else:
            wallet = await wallet_service.deduct_purchase_amount(username, amount)
    except WalletServiceError as error:
        await message.answer(t("dashboard.messages.wallet_balance_update_failed_with_reason", "ar").format(reason=str(error)))
        return
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        return

    await state.clear()
    await message.answer(
        t("dashboard.messages.wallet_balance_updated", "ar").format(
            username=wallet.username,
            action=t(f"dashboard.buttons.{ 'add_balance' if action == 'add' else 'cut_balance' }", "ar"),
            amount=_format_wallet_balance(amount),
            balance=_format_wallet_balance(wallet.balance_egp),
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.message(DashboardOtherState.waiting_for_binance_id)
async def dashboard_change_binance_id_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    try:
        binance_id = parse_binance_id(message.text or "")
    except ValueError:
        await message.answer(t("dashboard.messages.invalid_binance_id", "ar"))
        return

    old_binance_id = get_binance_id()
    set_binance_id(binance_id)
    await state.clear()
    await message.answer(
        t("dashboard.messages.binance_id_updated", "ar").format(
            old_binance_id=old_binance_id,
            new_binance_id=binance_id,
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.message(DashboardOtherState.waiting_for_support_username)
async def dashboard_change_support_username_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    try:
        support_username = parse_support_username(message.text or "")
    except ValueError:
        await message.answer(t("dashboard.messages.invalid_support_username", "ar"))
        return

    old_support_username = get_support_username()
    set_support_username(support_username)
    await state.clear()
    await message.answer(
        t("dashboard.messages.support_username_updated", "ar").format(
            old_support_username=old_support_username,
            new_support_username=support_username,
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


@router.message(DashboardOtherState.waiting_for_support_whatsapp_phone)
async def dashboard_change_support_whatsapp_phone_submit(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
        await message.answer(t("dashboard.messages.access_denied", "ar"))
        return

    try:
        whatsapp_phone = parse_support_whatsapp_phone(message.text or "")
    except ValueError:
        await message.answer(t("dashboard.messages.invalid_support_whatsapp_phone", "ar"))
        return

    old_whatsapp_phone = get_support_whatsapp_phone()
    set_support_whatsapp_phone(whatsapp_phone)
    await state.clear()
    await message.answer(
        t("dashboard.messages.support_whatsapp_phone_updated", "ar").format(
            old_whatsapp_phone=old_whatsapp_phone,
            new_whatsapp_phone=whatsapp_phone,
        ),
        reply_markup=get_dashboard_section_keyboard("other", "ar"),
    )


# @router.callback_query(F.data.startswith("dashboard:other:review_message:"))
# async def dashboard_change_review_message_start(
#     callback: CallbackQuery,
#     state: FSMContext,
# ) -> None:
#     if not is_admin(callback.from_user.id):
#         await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
#         return
#
#     message_key = callback.data.rsplit(":", maxsplit=1)[-1]
#     if message_key not in MESSAGE_KEYS:
#         await callback.answer()
#         return
#
#     await state.set_state(DashboardOtherState.waiting_for_review_message)
#     await state.update_data(review_message_key=message_key)
#     await callback.answer()
#     await callback.message.answer(
#         t("dashboard.messages.ask_review_message", "ar").format(
#             current_message=get_review_message(message_key),
#             placeholders=_format_placeholders(message_key),
#         )
#     )
#
#
# @router.message(DashboardOtherState.waiting_for_review_message)
# async def dashboard_change_review_message_submit(
#     message: Message,
#     state: FSMContext,
# ) -> None:
#     if not is_admin(message.from_user.id if message.from_user else None):
#         await message.answer(t("dashboard.messages.access_denied", "ar"))
#         return
#
#     data = await state.get_data()
#     message_key = str(data.get("review_message_key") or "")
#     if message_key not in MESSAGE_KEYS:
#         await state.clear()
#         await message.answer(t("dashboard.messages.invalid_review_message", "ar"))
#         return
#
#     try:
#         set_review_message(message_key, message.text or "")
#     except ValueError:
#         await message.answer(t("dashboard.messages.invalid_review_message", "ar"))
#         return
#
#     await state.clear()
#     await message.answer(
#         t("dashboard.messages.review_message_updated", "ar"),
#         reply_markup=get_dashboard_section_keyboard("other", "ar"),
#     )


def _format_rate(value) -> str:
    return f"{value:.2f}"


def _format_wallet_balance(value: Decimal) -> str:
    return f"{value:.2f}"


def _format_numbered_products(products) -> str:
    return "\n".join(f"{index}. {product.title}" for index, product in enumerate(products, start=1))


def _format_selected_products(products_data) -> str:
    return ", ".join(f"{index}. {item['title']}" for index, item in enumerate(products_data, start=1))


def _parse_numeric_choices(value: str, max_count: int) -> list[int] | None:
    tokens = [token.strip() for token in value.replace(",", " ").split()]
    if not tokens:
        return None

    choices: list[int] = []
    for token in tokens:
        if not token.isdigit():
            return None
        number = int(token)
        if number < 1 or number > max_count or number in choices:
            return None
        choices.append(number)

    return choices


def _format_placeholders(message_key: str) -> str:
    common = ("order_id", "status") if message_key.startswith("order_") else (
        "amount",
        "payment_method",
        "currency",
        "balance",
        "balance_egp",
        "balance_usd",
    )
    return "\n".join(f"{{{placeholder}}}" for placeholder in common)
