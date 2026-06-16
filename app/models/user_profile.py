from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class UserProfile:
    id: int
    username: str
    total_spent: Decimal
    last_spent_order: str | None
    created_at: datetime | None
