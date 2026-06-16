from aiogram.fsm.state import State, StatesGroup


class WalletTopUpState(StatesGroup):
    choosing_method = State()
    choosing_ewallet_option = State()
    waiting_for_amount = State()
    waiting_for_ewallet_phone = State()
    waiting_for_transaction_id = State()
    waiting_for_instapay_screenshot = State()
    waiting_for_rejection_message = State()
