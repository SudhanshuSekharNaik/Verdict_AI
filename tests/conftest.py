import os
import pytest
import httpx
from playwright.sync_api import sync_playwright, Page, BrowserContext

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def frontend_url():
    return FRONTEND_URL


@pytest.fixture(scope="session")
def backend_url():
    return BACKEND_URL


@pytest.fixture(scope="session")
def api_client():
    with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="function")
def browser_context(request):
    try:
        headed = request.config.getoption("--headed")
    except Exception:
        headed = False

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=not headed, args=["--no-sandbox", "--disable-dev-shm-usage"])
        except Exception:
            # Fallback to system-installed msedge or chrome if playwright chromium binary is not cached
            try:
                browser = p.chromium.launch(channel="msedge", headless=not headed)
            except Exception:
                browser = p.chromium.launch(channel="chrome", headless=not headed)

        context = browser.new_context(
            viewport={"width": 1366, "height": 850},
            base_url=FRONTEND_URL,
            ignore_https_errors=True
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext) -> Page:
    pg = browser_context.new_page()
    console_errors = []
    pg.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    pg.console_errors = console_errors
    yield pg
    pg.close()


@pytest.fixture(scope="function")
def logged_in_page(page: Page) -> Page:
    """Fixture that initializes the session with a known advocate name."""
    page.goto(f"{FRONTEND_URL}/")
    page.evaluate("() => localStorage.setItem('nyay_manch_user', 'Advocate Sudhanshu')")
    page.reload()
    page.wait_for_selector("#headerUserName", state="visible")
    return page
