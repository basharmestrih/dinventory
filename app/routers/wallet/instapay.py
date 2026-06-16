from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.services.payments.payment_methods import PAYMENT_METHOD_INSTAPAY, is_payment_method_enabled
from app.states.wallet import WalletTopUpState
from app.translations import t

router = Router(name="wallet_instapay")


@router.callback_query(F.data == "wallet:topup:instapay", WalletTopUpState.choosing_method)
async def wallet_instapay_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_INSTAPAY):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await state.update_data(
        topup_method="InstaPay",
        topup_currency="EGP",
        topup_method_key="instapay",
    )
    await state.set_state(WalletTopUpState.waiting_for_amount)

    await callback.answer()
    await callback.message.answer(t("purchase.instapay_ask_for_amount", "ar"))
