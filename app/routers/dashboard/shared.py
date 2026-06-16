from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.config import settings
from app.models.product import Product
from app.services.exports.dashboard_exports import DashboardExportService
from app.services.messaging.notifications import NotificationService
from app.services.catalog.products import ProductService


product_service = ProductService()
dashboard_export_service = DashboardExportService()
notification_service = NotificationService()
EXPORT_DIR = Path("exports")


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_user_ids


def parse_positive_int(value: str | None) -> int | None:
    try:
        parsed = int((value or "").strip())
    except ValueError:
        return None

    return parsed if parsed > 0 else None


def parse_decimal(value: str | None) -> Decimal | None:
    try:
        parsed = Decimal((value or "").strip())
    except (InvalidOperation, ValueError):
        return None

    return parsed if parsed >= 0 else None


def with_skip(value: str | None, current: str) -> str:
    text = (value or "").strip()
    return current if text == "-" else text


def original_product_from_state(data: dict) -> Product:
    return Product(
        id=int(data["product_id"]),
        title=str(data["original_title"]),
        description=str(data["original_description"]),
        quantity=int(data["original_quantity"]),
        supplier_price=Decimal(str(data["original_supplier_price"])),
        price=Decimal(str(data["original_price"])),
        created_at=None,
        credentials=[],
        uses_manual_activation_emails=False,
    )
