from config import URL, USERNAME, PASSWORD

def login(page):
    page.goto(URL, wait_until="domcontentloaded")
    print("url is:::::::::", URL)

    page.wait_for_selector("#username", state="visible")
    page.fill("#username", USERNAME)
    page.fill("#password", PASSWORD)

    page.press("#password", "Enter")
    page.wait_for_url(lambda current_url: current_url != "about:blank", timeout=60000)
    page.wait_for_load_state("domcontentloaded")
