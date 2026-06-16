_invoice_active: dict[str, bool] = {}


def start_invoice_countdown(invoice_id: str) -> None:
    invoice_id = str(invoice_id or "").strip()
    if not invoice_id:
        return

    _invoice_active[invoice_id] = True


def mark_invoice_paid(invoice_id: str) -> None:
    invoice_id = str(invoice_id or "").strip()
    if not invoice_id:
        return

    _invoice_active[invoice_id] = False


def is_invoice_active(invoice_id: str) -> bool:
    invoice_id = str(invoice_id or "").strip()
    if not invoice_id:
        return True

    return _invoice_active.get(invoice_id, True)
