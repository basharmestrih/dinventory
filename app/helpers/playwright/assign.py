from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import ASSIGN_URL

PRODUCT_NAME_KEYWORDS = ("Creative Cloud Pro",)
ASSIGN_SUCCESS_TEXT = "User assigned in Adobe + saved locally"
DURATION_VALUE_MAP = {
    "1_month": "1",
    "2_months": "2",
    "6_months": "6",
    "12_months": "12",
}


def assign_user(page, customer_email, duration_key):
    if duration_key not in DURATION_VALUE_MAP:
        raise ValueError(f"Unsupported Adobe duration: {duration_key}")

    # 1. go to assign page
    page.goto(ASSIGN_URL, wait_until="domcontentloaded")

    # 2. wait for email input and fill it
    page.wait_for_selector("input[name='email']", state="visible")
    page.fill("input[name='email']", customer_email)

    # 3. check product checkbox
    product_checkboxes = page.locator("input[type='checkbox'][name='product_profile[]']")
    checkbox_count = product_checkboxes.count()
    if checkbox_count == 0:
        raise RuntimeError("No Adobe product profiles were found on the assign page.")

    selected_checkbox = product_checkboxes.first
    for index in range(checkbox_count):
        checkbox = product_checkboxes.nth(index)
        value = checkbox.get_attribute("value") or ""
        if all(keyword in value for keyword in PRODUCT_NAME_KEYWORDS):
            selected_checkbox = checkbox
            break
    selected_checkbox.check()

    # 4. select requested duration
    page.wait_for_selector("#assignMonths", state="visible")
    page.locator("#assignMonths").select_option(value=DURATION_VALUE_MAP[duration_key])

    # 5. click assign button and track the server response
    with page.expect_response(
        lambda response: (
            "?page=reseller_assign" in response.url
            and response.request.method == "POST"
        ),
        timeout=30000,
    ) as response_info:
        page.click("button[type='submit']:has-text('Assign User')")

    response = response_info.value

    # 6. confirm the browser-visible success toast
    toast_text = ""
    success_toast = page.locator("div.ok", has_text=ASSIGN_SUCCESS_TEXT).last
    try:
        success_toast.wait_for(state="visible", timeout=10000)
        toast_text = success_toast.inner_text()
    except PlaywrightTimeoutError:
        pass

    page.screenshot(path="assign.png")

    if response.status != 200 or ASSIGN_SUCCESS_TEXT not in toast_text:
        raise RuntimeError(
            "Adobe assign was not confirmed. "
            f"HTTP={response.status} toast={toast_text or '-'}"
        )

    print(f"[OK] Assigned user: {customer_email} ({duration_key})")
    print(f"ADOBE_ASSIGN_TOAST={toast_text}")
