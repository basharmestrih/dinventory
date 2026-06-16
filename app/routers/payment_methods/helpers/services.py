from pathlib import Path

from app.services.adobe import ADOBE_DURATION_OPTIONS
from app.services.orders.orders import OrderService
from app.services.catalog.products import ProductService

order_service = OrderService()
product_service = ProductService()
playwright_dir = Path(__file__).resolve().parents[3] / "helpers" / "playwright"
adobe_duration_options = set(ADOBE_DURATION_OPTIONS)
