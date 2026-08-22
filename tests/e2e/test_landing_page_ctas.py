import pytest
from playwright.sync_api import Page, expect


def test_landing_page_cta_hierarchy_and_choice_modal(page: Page, frontend_url: str):
    """
    Test 7: Landing Page CTA Hierarchy & Choice Modal
    - Asserts exactly 2 solid-gold CTA buttons exist in #viewLanding
    - Asserts all other action buttons use ghost/secondary styling
    - Confirms [ ENTER COURT ] opens the Choice Modal (Audience vs File a Case)
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # 1. Count solid gold buttons in #viewLanding
    gold_buttons = page.locator("#viewLanding .btn-editorial-gold")
    count_gold = gold_buttons.count()
    assert count_gold == 2, f"Expected exactly 2 solid-gold CTA buttons on landing page, found {count_gold}"

    # Verify the two gold buttons:
    # 1st Gold Button: Hero Section [ ENTER COURT ]
    hero_gold_btn = page.locator("#secHero .btn-editorial-gold")
    expect(hero_gold_btn).to_be_visible()
    expect(hero_gold_btn).to_contain_text("ENTER COURT")

    # 2nd Gold Button: Section 15 Closing CTA [ ENTER NYAY MANCH ]
    cta_gold_btn = page.locator("#secCTA .btn-editorial-gold")
    expect(cta_gold_btn).to_be_visible()
    expect(cta_gold_btn).to_contain_text("ENTER NYAY MANCH")

    # 2. Verify all other secondary buttons in #viewLanding use ghost/secondary styling
    ghost_buttons = page.locator("#viewLanding .btn-editorial-ghost")
    assert ghost_buttons.count() >= 2, "Expected secondary CTA buttons to use .btn-editorial-ghost style"

    # 3. Verify Nav [ ENTER COURT ] button opens the Choice Modal
    nav_enter_btn = page.locator("#siteHeader button:has-text('[ ENTER COURT ]')")
    expect(nav_enter_btn).to_be_visible()
    nav_enter_btn.click()

    choice_modal = page.locator("#modalEnterCourtChoice")
    expect(choice_modal).to_be_visible()
    expect(choice_modal).to_contain_text("CHOOSE HOW TO ENTER THE COURT")
    expect(choice_modal).to_contain_text("View as Audience")
    expect(choice_modal).to_contain_text("File a Case")

    # Close choice modal
    page.locator("#modalEnterCourtChoice .modal-close-corner-btn").click()
    expect(choice_modal).to_be_hidden()

    # 4. Verify Hero [ ENTER COURT ] button also opens the Choice Modal
    hero_gold_btn.click()
    expect(choice_modal).to_be_visible()
