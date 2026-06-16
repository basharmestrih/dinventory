from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import RESELLER_USERS_URL

DURATION_VALUE_MAP = {
    "1_month": "1",
    "2_months": "2",
    "6_months": "6",
    "12_months": "12",
}

EXTEND_SUCCESS_KEYWORDS = (
    "User extended successfully",
    "User renewed successfully",
)


def extend_user(page, customer_email, duration_key):
    # go to page
    page.goto(RESELLER_USERS_URL, wait_until="domcontentloaded")

    # search user
    page.wait_for_selector("#instantSearch")
    page.fill("#instantSearch", customer_email)

    page.wait_for_timeout(2000)

    # find correct card
    cards = page.locator(".user-card", has_text=customer_email)
    if cards.count() == 0:
        return False

    card = cards.first

    # select duration
    select = card.locator("select.ab-months")
    if duration_key in DURATION_VALUE_MAP:
        select.select_option(value=DURATION_VALUE_MAP[duration_key])
    else:
        select.select_option(index=0)

    extend_button = card.locator("button.ab-extend")
    if extend_button.count() == 0:
        extend_button = card.locator("button.ab-renew")
    if extend_button.count() == 0:
        raise RuntimeError("Extend or Renew button was not found for the selected user.")

    with page.expect_response(
        lambda response: (
            "?page=reseller_users" in response.url
            and response.request.method == "POST"
        ),
        timeout=30000,
    ) as response_info:
        extend_button.first.click()

    response = response_info.value

    toast_text = ""
    success_toast = page.locator("div.ok").last
    try:
        success_toast.wait_for(state="visible", timeout=10000)
        toast_text = success_toast.inner_text()
    except PlaywrightTimeoutError:
        pass

    page.screenshot(path="extend.png")

    if response.status != 200 or not any(keyword in toast_text for keyword in EXTEND_SUCCESS_KEYWORDS):
        raise RuntimeError(
            "Adobe extend was not confirmed. "
            f"HTTP={response.status} toast={toast_text or '-'}"
        )

    print(f"[OK] Extended user: {customer_email} ({duration_key})")
    print(f"ADOBE_EXTEND_TOAST={toast_text}")
    return True
