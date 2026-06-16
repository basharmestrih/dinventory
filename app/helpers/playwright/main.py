import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from assign import assign_user
from login import login
from extend import extend_user

DEFAULT_CUSTOMER_EMAIL = ""
DEFAULT_DURATION = "12_months"
DEFAULT_REQUEST_TYPE = "auto"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def run(
    customer_email: str = DEFAULT_CUSTOMER_EMAIL,
    duration: str = DEFAULT_DURATION,
    request_type: str = DEFAULT_REQUEST_TYPE,
) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            print("request_type:", request_type)
            print("email:", customer_email)
            print("duration:", duration)
            login(page)
            was_extended = extend_user(page, customer_email, duration)
            if was_extended:
                print("ADOBE_ACTION=extend")
            else:
                assign_user(page, customer_email, duration)
                print("ADOBE_ACTION=assign")

        except Exception:
            _save_debug_artifacts(page)
            print(f"[ERROR] Playwright flow failed on URL: {page.url}")
            raise
        finally:
            context.close()
            browser.close()


def _save_debug_artifacts(page: Page) -> None:
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    screenshot_path = ARTIFACTS_DIR / "playwright_error.png"
    html_path = ARTIFACTS_DIR / "playwright_error.html"

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[DEBUG] Saved screenshot to: {screenshot_path}")
    except Exception as error:
        print(f"[DEBUG] Failed to save screenshot: {error}")

    try:
        html_path.write_text(page.content(), encoding="utf-8")
        print(f"[DEBUG] Saved page HTML to: {html_path}")
    except Exception as error:
        print(f"[DEBUG] Failed to save HTML: {error}")


def _parse_args(argv: list[str]) -> tuple[str, str, str]:
    args = argv[1:]
    if not args:
        return DEFAULT_REQUEST_TYPE, DEFAULT_CUSTOMER_EMAIL, DEFAULT_DURATION

    if args[0] in {"auto", "assign", "extend"}:
        request_type = args[0]
        customer_email = args[1] if len(args) > 1 else DEFAULT_CUSTOMER_EMAIL
        duration = args[2] if len(args) > 2 else DEFAULT_DURATION
        return request_type, customer_email, duration

    customer_email = args[0]
    duration = args[1] if len(args) > 1 else DEFAULT_DURATION
    return DEFAULT_REQUEST_TYPE, customer_email, duration


if __name__ == "__main__":
    request_type, customer_email, duration = _parse_args(sys.argv)
    run(customer_email, duration, request_type)



    
