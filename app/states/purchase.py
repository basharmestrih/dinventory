from aiogram.fsm.state import State, StatesGroup


class PurchaseState(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_duration = State()
    waiting_for_assignment_email = State()
    choosing_payment_method = State()
    waiting_for_ewallet_phone = State()
    waiting_for_transaction_id = State()
    waiting_for_instapay_screenshot = State()
    waiting_for_activation_emails = State()
    waiting_for_review_note = State()
    waiting_for_activation_note = State()
