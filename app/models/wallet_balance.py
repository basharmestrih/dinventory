from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class WalletBalance:
    username: str
    balance_usd: Decimal
    balance_egp: Decimal
    last_deposit_at: datetime | None
