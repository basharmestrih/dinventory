from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class Order:
    id: int
    product_id: int | None
    product_title: str
    product_description: str
    unit_price: Decimal
    quantity: int
    total: Decimal
    payment_method: str
    transaction_id: str | None
    status: str
    email: str
    password: str
    expiry_date: str
    customer_name: str
    customer_username: str | None
    customer_telegram_id: int | None
    created_at: datetime | None
