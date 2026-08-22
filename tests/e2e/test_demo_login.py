import pytest
from playwright.sync_api import Page, expect


def test_guest_login_persists_session(page: Page, frontend_url: str):
    """
    Test 1: Demo Login & Guest Access
    - Click User Session badge in header
    - Select 'Continue as Guest Legal Scholar'
    - Verify modal closes and header updates to 'Guest Legal Scholar'
    - Reload page and verify session persists across navigation
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Verify initial session badge
    session_badge = page.locator("#userSessionBadge")
    expect(session_badge).to_be_visible()

    # Click to open login modal
    session_badge.click()
    modal = page.locator("#modalDemoLogin")
    expect(modal).to_be_visible()

    # Click guest login button
    guest_btn = modal.locator("button:has-text('Continue as Guest Legal Scholar')")
    expect(guest_btn).to_be_visible()
    guest_btn.click()

    # Modal should dismiss
    expect(modal).to_be_hidden()

    # Header user name should update
    header_user = page.locator("#headerUserName")
    expect(header_user).to_contain_text("Guest Legal Scholar")

    # Navigate to Dashboard and verify session holds
    page.locator("#navDashboard").click()
    expect(page.locator("#viewDashboard")).to_be_visible()
    expect(header_user).to_contain_text("Guest Legal Scholar")

    # Reload page
    page.reload()
    expect(page.locator("#headerUserName")).to_contain_text("Guest Legal Scholar")


def test_custom_advocate_login(page: Page, frontend_url: str):
    """
    Test custom advocate name input and localStorage persistence.
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Open login modal
    page.locator("#userSessionBadge").click()
    modal = page.locator("#modalDemoLogin")
    expect(modal).to_be_visible()

    # Enter custom advocate name
    input_field = page.locator("#demoLoginInputName")
    input_field.fill("Adv. Vikramaditya")

    # Click submit
    submit_btn = modal.locator("button:has-text('[ ENTER COURTROOM ARENA → ]')")
    submit_btn.click()

    # Modal closes and header updates
    expect(modal).to_be_hidden()
    expect(page.locator("#headerUserName")).to_contain_text("Adv. Vikramaditya")

    # Verify stored in localStorage
    stored_name = page.evaluate("() => localStorage.getItem('nyay_manch_user')")
    assert stored_name == "Adv. Vikramaditya"
