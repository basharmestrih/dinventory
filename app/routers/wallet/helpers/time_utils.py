from datetime import datetime, timedelta, timezone


def get_fixed_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=40)


def get_remaining_seconds(expires_at: datetime) -> int:
    target = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining = int((target - now).total_seconds())
    return remaining if remaining > 0 else 0


def format_duration(seconds: int) -> str:
    seconds = max(seconds, 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
