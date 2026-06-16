import asyncio
import subprocess
import sys
from pathlib import Path

from app.models.order import Order
from app.services.adobe.constants import (
    ADOBE_ACTION_ASSIGN,
    ADOBE_ACTION_EXTEND,
    ADOBE_DURATION_OPTIONS,
    is_adobe_product,
)

ACTION_TOKEN = "ADOBE_ACTION="
PLAYWRIGHT_DIR = Path(__file__).resolve().parents[2] / "helpers" / "playwright"


def _parse_action(output: str) -> str:
    for line in output.splitlines():
        if not line.startswith(ACTION_TOKEN):
            continue
        value = line.split("=", maxsplit=1)[-1].strip().lower()
        if value in {ADOBE_ACTION_EXTEND, ADOBE_ACTION_ASSIGN}:
            return value

    raise RuntimeError("Adobe action was not reported by Playwright.")


async def run_adobe_fulfillment(order: Order) -> str | None:
    if not is_adobe_product(order.product_title):
        return None

    duration = str(order.expiry_date or "").strip()
    email = str(order.email or "").strip()
    if duration not in ADOBE_DURATION_OPTIONS or not email:
        return None

    def _run() -> str:
        result = subprocess.run(
            [sys.executable, "main.py", "auto", email, duration],
            cwd=str(PLAYWRIGHT_DIR),
            capture_output=True,
            text=True,
            timeout=180,
        )
        output = "\n".join([result.stdout or "", result.stderr or ""]).strip()
        if result.returncode != 0:
            raise RuntimeError(output or "Adobe automation process failed.")

        return _parse_action(output)

    return await asyncio.to_thread(_run)
