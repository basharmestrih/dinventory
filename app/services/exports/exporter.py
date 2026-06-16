from pathlib import Path
import time
from uuid import uuid4

from openpyxl import Workbook

from app.models.product import Product


def build_products_excel(products: list[Product], export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Products"

    worksheet.append(
        ["id", "title", "description", "quantity", "supplier_price", "price", "created_at"]
    )

    for product in products:
        worksheet.append(
            [
                product.id,
                product.title,
                product.description,
                product.quantity,
                str(product.supplier_price),
                str(product.price),
                product.created_at.isoformat(sep=" ") if product.created_at else "",
            ]
        )

    file_path = export_dir / f"products_{uuid4().hex}.xlsx"
    workbook.save(file_path)
    return file_path


def build_rows_excel(
    rows: list[dict],
    headers: list[str],
    sheet_name: str,
    file_prefix: str,
    export_dir: Path,
) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(headers)

    for row in rows:
        worksheet.append([_stringify_excel_value(row.get(header)) for header in headers])

    last_error: Exception | None = None
    for attempt in range(5):
        file_path = export_dir / f"{file_prefix}_{uuid4().hex}.xlsx"
        try:
            workbook.save(file_path)
            return file_path
        except PermissionError as error:
            last_error = error
            time.sleep(0.25 * (attempt + 1))

    raise last_error or PermissionError("Failed to save Excel export file.")


def _stringify_excel_value(value: object) -> str:
    if value is None:
        return ""

    return str(value)
