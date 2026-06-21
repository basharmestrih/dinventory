from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class Product:
    id: int
    title: str
    description: str
    quantity: int
    is_special: bool
    image: str | None
    supplier_price: Decimal
    price: Decimal
    created_at: datetime | None
    credentials: list[dict[str, str]]
    uses_manual_activation_emails: bool
