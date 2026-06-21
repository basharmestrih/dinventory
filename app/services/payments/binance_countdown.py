import asyncio


_countdown_active: dict[str, bool] = {}
_countdown_cancelled: dict[str, bool] = {}


def start_checkout_countdown(checkout_id: str) -> None:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return

    _countdown_active[checkout_id] = True
    _countdown_cancelled[checkout_id] = False


def mark_checkout_paid(checkout_id: str) -> None:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return

    _countdown_active[checkout_id] = False


def mark_checkout_cancelled(checkout_id: str) -> None:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return

    _countdown_active[checkout_id] = False
    _countdown_cancelled[checkout_id] = True


def is_checkout_active(checkout_id: str) -> bool:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return True

    return _countdown_active.get(checkout_id, True)


def is_checkout_cancelled(checkout_id: str) -> bool:
    checkout_id = str(checkout_id or "").strip()
    if not checkout_id:
        return False

    return _countdown_cancelled.get(checkout_id, False)
