from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dashboard import get_dashboard_section_keyboard
from app.routers.dashboard.shared import is_admin
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
