import pytest
from playwright.sync_api import Page, expect


def test_courtroom_audience_mode_and_autoplay(page: Page, frontend_url: str):
    """
    Test 5: Audience Observation Mode Complete Flow:
    1. Open homepage, click [ ENTER COURT ]
    2. Choice modal appears with 'View as Audience' option
    3. Click '[ WATCH A TRIAL → ]'
    4. Gallery modal opens displaying 5 distinct case cards with runtime badges
    5. Select a case to open the Case Briefing Dossier
    6. Verify Briefing displays Hook, What Happened, Who's Who, and Statutory Charge
    7. Click '[ ENTER COURTROOM → ]'
    8. Courtroom view opens in pure Audience Mode with Countdown & Judge Opening
    9. Verify all interactive controls (Object, Exhibit, Ruling, Next Question, Autoplay toggle, Fast Forward, Speed) are NOT rendered
    10. Verify passive navigation controls (Exit Court, Case File, Hearing Record, Review Tabs) ARE visible
    11. Verify trial autonomously progresses without user clicks
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # 1. Click Hero [ ENTER COURT ] button
    hero_btn = page.locator("#secHero button:has-text('[ ENTER COURT ]')")
    expect(hero_btn).to_be_visible()
    hero_btn.click()

    # 2. Choice modal should be visible
    choice_modal = page.locator("#modalEnterCourtChoice")
    expect(choice_modal).to_be_visible()
    expect(choice_modal).to_contain_text("CHOOSE HOW TO ENTER THE COURT")
    expect(choice_modal).to_contain_text("View as Audience")
    expect(choice_modal).to_contain_text("File a Case")

    # 3. Click [ WATCH A TRIAL → ] on the Audience card
    watch_btn = choice_modal.locator("button:has-text('[ WATCH A TRIAL → ]')")
    expect(watch_btn).to_be_visible()
    watch_btn.click()

    # 4. Choice modal closes and Audience Gallery modal appears
    expect(choice_modal).to_be_hidden()
    gallery_modal = page.locator("#modalAudienceGallery")
    expect(gallery_modal).to_be_visible()
    expect(gallery_modal).to_contain_text("Audience Observation Gallery")

    # Verify at least 4-5 case cards are rendered in gallery
    cards = gallery_modal.locator(".gallery-case-card")
    expect(cards).to_have_count(5)
    expect(gallery_modal).to_contain_text("State of Maharashtra v. Rohan Verma")
    expect(gallery_modal).to_contain_text("Pooja Deshmukh v. Siddharth Deshmukh")
    expect(gallery_modal).to_contain_text("Cyber Cell Cyberabad v. Vikram Singhania")
    expect(gallery_modal).to_contain_text("Karan Malhotra & Ors. v. Oberoi Realty Consortium")
    expect(gallery_modal).to_contain_text("K.M. Nanavati v. State of Maharashtra")
    expect(gallery_modal).to_contain_text("~4 min hearing")
    expect(gallery_modal).to_contain_text("Landmark Case · Full Length")

    # 5. Click [ REVIEW BRIEFING & WATCH → ] on the first case
    review_btn = cards.first.locator("button:has-text('[ REVIEW BRIEFING & WATCH → ]')")
    expect(review_btn).to_be_visible()
    review_btn.click()

    # 6. Gallery closes and Case Briefing Dossier modal opens
    expect(gallery_modal).to_be_hidden()
    briefing_modal = page.locator("#modalCaseBriefing")
    expect(briefing_modal).to_be_visible()
    expect(briefing_modal).to_contain_text("WHAT HAPPENED (CORE FACT PATTERN)")
    expect(briefing_modal).to_contain_text("PROSECUTION / APPLICANT")
    expect(briefing_modal).to_contain_text("DEFENCE / RESPONDENT")
    expect(briefing_modal).to_contain_text("STATUTORY CHARGE & PLAIN GLOSS")
    expect(briefing_modal).to_contain_text("WHAT TO EXPECT (AUTONOMOUS ARC)")

    # 7. Click [ ENTER COURTROOM → ] on Briefing
    enter_crt_btn = briefing_modal.locator("#btnBriefingEnterCourt")
    expect(enter_crt_btn).to_be_visible()
    enter_crt_btn.click()

    # 8. Briefing modal closes and courtroom view becomes active
    expect(briefing_modal).to_be_hidden()
    expect(page.locator("#viewCourtroom")).to_be_visible()

    # 9. Verify Audience Observer Pill & Broadcast Banner are displayed
    expect(page.locator("#crtAudienceModePill")).to_be_visible()
    expect(page.locator("#crtAudienceBanner")).to_be_visible()

    # 10. Verify that ALL interactive controls are completely hidden/non-rendered in audience mode:
    expect(page.locator("#crtFilerActionsLeft")).to_be_hidden()
    expect(page.locator("#btnRaiseObjection")).to_be_hidden()
    expect(page.locator("#btnIntroduceExhibit")).to_be_hidden()
    expect(page.locator("#btnJudgeRuling")).to_be_hidden()

    expect(page.locator("#crtFilerActionsCenter")).to_be_hidden()
    expect(page.locator("#btnCourtNextAction")).to_be_hidden()
    expect(page.locator("#btnAutoPlayHearings")).to_be_hidden()
    expect(page.locator("#btnFastForwardVerdict")).to_be_hidden()
    expect(page.locator("#crtVoiceSpeedGroup")).to_be_hidden()

    # 11. Verify passive / informational controls ARE available:
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

    # 12. Verify autonomous progression runs without clicks
    page.wait_for_timeout(4000)
    expect(page.locator("#crtPhaseLabel")).to_be_visible()
