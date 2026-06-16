from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.services.payments.ewallet_constants import (
    FAWRY_PAYMENT_METHOD_ID,
    MEEZA_PAYMENT_METHOD_ID,
)
from app.services.payments.ewallet_utils import is_valid_phone
from app.routers.wallet.helpers import create_wallet_ewallet_invoice
from app.services.payments.payment_methods import (
    PAYMENT_METHOD_EWALLET,
    PAYMENT_METHOD_FAWRY,
    is_payment_method_enabled,
)
from app.states.wallet import WalletTopUpState
from app.translations import t


router = Router(name="wallet_ewallet")


@router.callback_query(F.data == "wallet:topup:ewallet", WalletTopUpState.choosing_method)
async def wallet_ewallet_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_EWALLET):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        topup_method="محفظة الموبايل",
        topup_currency="EGP",
        topup_method_key="ewallet",
        ewallet_payment_method_id=MEEZA_PAYMENT_METHOD_ID,
    )
    await state.set_state(WalletTopUpState.waiting_for_amount)

    await callback.answer()
    await callback.message.answer(
        "أدخل مبلغ الإيداع في محفظة الموبايل بالجنيه المصري.\n"
        "مثال: 250"
    )


@router.callback_query(F.data == "wallet:topup:fawry", WalletTopUpState.choosing_method)
async def wallet_fawry_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_FAWRY):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        topup_method="فوري",
        topup_currency="EGP",
        topup_method_key="ewallet",
        ewallet_payment_method_id=FAWRY_PAYMENT_METHOD_ID,
    )
    await state.set_state(WalletTopUpState.waiting_for_amount)

    await callback.answer()
    await callback.message.answer(
        "أدخل مبلغ الإيداع عبر فوري بالجنيه المصري.\n"
        "مثال: 250"
    )


@router.message(WalletTopUpState.waiting_for_ewallet_phone)
async def wallet_ewallet_phone_handler(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not is_valid_phone(phone):
        await message.answer("أرسل رقم هاتف صحيح لاستخدامه في عملية الإيداع.")
        return

    await create_wallet_ewallet_invoice(message, message.from_user, state, phone=phone)
