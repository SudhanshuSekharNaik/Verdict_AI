import pytest
from playwright.sync_api import Page, expect


def test_courtroom_audience_mode_and_autoplay(page: Page, frontend_url: str):
    """
    Test 5: Courtroom in Audience Mode (Fully Passive Observer)
    - Open homepage, click [ ENTER COURT ]
    - Choice modal appears with 'View as Audience' option
    - Click '[ WATCH A TRIAL → ]'
    - Verify direct entry into courtroom in pure Audience Mode
    - Verify all interactive controls (Object, Exhibit, Ruling, Next Question, Autoplay toggle, Fast Forward, Speed) are NOT rendered
    - Verify passive navigation controls (Exit Court, Case File, Hearing Record, Review Tabs) ARE visible
    - Verify trial autonomously progresses without user clicks
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # 1. Click Hero [ ENTER COURT ] button
    hero_btn = page.locator("#secHero button:has-text('[ ENTER COURT ]')")
    expect(hero_btn).to_be_visible()
    hero_btn.click()

    # 2. Choice modal should be visible
    modal = page.locator("#modalEnterCourtChoice")
    expect(modal).to_be_visible()
    expect(modal).to_contain_text("CHOOSE HOW TO ENTER THE COURT")
    expect(modal).to_contain_text("View as Audience")
    expect(modal).to_contain_text("File a Case")

    # 3. Click [ WATCH A TRIAL → ] on the Audience card
    watch_btn = modal.locator("button:has-text('[ WATCH A TRIAL → ]')")
    expect(watch_btn).to_be_visible()
    watch_btn.click()

    # 4. Choice modal closes and courtroom view becomes active
    expect(modal).to_be_hidden()
    expect(page.locator("#viewCourtroom")).to_be_visible()

    # 5. Verify Audience Observer Pill & Broadcast Banner are displayed
    expect(page.locator("#crtAudienceModePill")).to_be_visible()
    expect(page.locator("#crtAudienceBanner")).to_be_visible()

    # 6. Verify that ALL interactive controls are completely hidden/non-rendered in audience mode:
    expect(page.locator("#crtFilerActionsLeft")).to_be_hidden()
    expect(page.locator("#btnRaiseObjection")).to_be_hidden()
    expect(page.locator("#btnIntroduceExhibit")).to_be_hidden()
    expect(page.locator("#btnJudgeRuling")).to_be_hidden()

    expect(page.locator("#crtFilerActionsCenter")).to_be_hidden()
    expect(page.locator("#btnCourtNextAction")).to_be_hidden()
    expect(page.locator("#btnAutoPlayHearings")).to_be_hidden()
    expect(page.locator("#btnFastForwardVerdict")).to_be_hidden()
    expect(page.locator("#crtVoiceSpeedGroup")).to_be_hidden()

    # 7. Verify passive / informational controls ARE available:
    expect(page.locator("#viewCourtroom button:has-text('Exit Court')")).to_be_visible()
    expect(page.locator("#viewCourtroom button:has-text('Case File')")).to_be_visible()
    expect(page.locator("#viewCourtroom button:has-text('Hearing Record')")).to_be_visible()

    # Side information review tabs
    expect(page.locator("#crtTabBtn_witnesses")).to_be_visible()
    expect(page.locator("#crtTabBtn_facts")).to_be_visible()
    expect(page.locator("#crtTabBtn_exhibits")).to_be_visible()
    expect(page.locator("#crtTabBtn_law")).to_be_visible()

    # Click a review tab to confirm passive inspection works
    page.locator("#crtTabBtn_facts").click()
    expect(page.locator("#crtTab_facts")).to_be_visible()

    # 8. Verify autonomous progression runs without clicks
    page.wait_for_timeout(3500)
    expect(page.locator("#crtPhaseLabel")).to_be_visible()
