from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.services.payments.payment_methods import PAYMENT_METHOD_BINANCE, is_payment_method_enabled
from app.states.wallet import WalletTopUpState
from app.translations import t


router = Router(name="wallet_binance")


@router.callback_query(F.data == "wallet:topup:binance", WalletTopUpState.choosing_method)
async def wallet_binance_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_BINANCE):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        topup_method="Binance",
        topup_currency="EGP",
        topup_method_key="binance",
    )
    await state.set_state(WalletTopUpState.waiting_for_amount)

    await callback.answer()
    await callback.message.answer(
        "أدخل مبلغ الشحن عبر Binance بالجنيه المصري.\n"
        "مثال: 500"
    )
