from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.routers.payment_methods.admin_notifications import format_price
from app.services.payments.instapay_settings import get_instapay_phone_number
from app.services.payments.payment_methods import PAYMENT_METHOD_INSTAPAY, is_payment_method_enabled
from app.states.purchase import PurchaseState
from app.translations import t


router = Router(name="payment_instapay")


@router.callback_query(F.data == "payment:instapay", PurchaseState.choosing_payment_method)
async def instapay_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_INSTAPAY):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    data = await state.get_data()

    await state.update_data(payment_method="InstaPay")
    await state.set_state(PurchaseState.waiting_for_instapay_screenshot)

    await callback.answer()
    await callback.message.answer(
        t("purchase.instapay_instructions").format(
            total=format_price(Decimal(str(data["total"]))),
            phone_number=get_instapay_phone_number(),
        )
    )
