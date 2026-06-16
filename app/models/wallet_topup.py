from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class WalletTopUpRequest:
    id: str
    username: str
    amount: Decimal
    currency: str
    payment_method: str
    transaction_id: str
    customer_name: str
    customer_username: str
    customer_telegram_id: int | None
    payment_proof_file_id: str = ""
    payment_proof_type: str = ""
    status: str = "pending"
    created_at: datetime | None = None
