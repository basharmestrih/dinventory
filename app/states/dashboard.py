from aiogram.fsm.state import State, StatesGroup


class AddProductState(StatesGroup):
    title = State()
    description = State()
    supplier_price = State()
    price = State()
    image = State()
    account_type = State()
    quantity = State()
    credentials = State()


class EditProductState(StatesGroup):
    choosing_field = State()
    waiting_for_value = State()
    waiting_for_credentials = State()
    waiting_for_credentials_replacement = State()


class BroadcastNotificationState(StatesGroup):
    text = State()


class DashboardOtherState(StatesGroup):
    waiting_for_egp_exchange_rate = State()
    waiting_for_instapay_phone_number = State()
    waiting_for_binance_id = State()
    waiting_for_support_username = State()
    waiting_for_support_whatsapp_phone = State()
    waiting_for_special_products = State()
    waiting_for_wallet_balance_amount = State()
    # waiting_for_review_message = State()


class AdminGetProductState(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_duration = State()
    waiting_for_assignment_email = State()
