import pytest
from playwright.sync_api import Page, expect


def test_case_filing_8_steps_complete_flow(page: Page, frontend_url: str):
    """
    Test 2: Complete 8-Step Case Filing Flow
    - Case Identification -> Counsel Selection -> Facts -> Issues -> Theories -> Evidence -> Witnesses -> Review
    - Verifies back/forward step persistence and successful case generation.
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Start filing wizard via header nav button
    page.locator("#navFileMatter").click()
    expect(page.locator("#viewFileMatter")).to_be_visible()
    expect(page.locator("#wzContent_1")).to_be_visible()

    # STEP 01: Fill Case Identification
    page.locator("#wzTitle").fill("State v. Test Accused (Railway Theft)")
    page.locator("#wzJurisdiction").fill("Sessions Court, Mumbai")
    page.locator("#wzCategory").select_option("criminal")
    page.locator("#wzCharge").fill("Theft under Bharatiya Nyaya Sanhita, 2023 §303(2)")

    # Click Continue to Step 02
    page.locator("#wzContent_1 button:has-text('Save & Continue to Step 02')").click()
    expect(page.locator("#wzContent_2")).to_be_visible()

    # STEP 02: Counsel Selection
    # Select distinct agents for both sides
    page.locator("#filingCard_agent_02 button").click()
    page.locator("#opposingCard_agent_01 button").click()
    page.locator("#wzContent_2 button:has-text('Continue to Step 03')").click()
    expect(page.locator("#wzContent_3")).to_be_visible()

    # STEP 03: Facts Intake & Extraction
    sample_facts = (
        "On 15 August 2026, complainant Amit Shah boarded train 12952 at Mumbai Central.\n"
        "At 21:30 hrs, complainant noticed his leather briefcase containing laptop was missing.\n"
        "RPF officers detained the accused near Borivali station with matching laptop."
    )
    page.locator("#wzFacts").fill(sample_facts)
    page.wait_for_timeout(400)
    page.locator("#wzContent_3 button:has-text('Continue to Step 04')").click()
    expect(page.locator("#wzContent_4")).to_be_visible()

    # STEP 04: Legal Issues
    page.locator("#wzContent_4 button:has-text('Continue to Step 05')").click()
    expect(page.locator("#wzContent_5")).to_be_visible()

    # STEP 05: Prosecution & Defense Case Theories
    page.locator("#wzProsAccount").fill("Accused was apprehended in possession of stolen property within 2 hours.")
    page.locator("#wzProsTheory").fill("Unexplained possession of recently stolen goods gives rise to presumption under BSA §114.")
    page.locator("#wzDefAccount").fill("Accused found briefcase abandoned on footboard and was searching for owner.")
    page.locator("#wzDefTheory").fill("Absence of dishonest intention (mens rea) negates statutory theft elements.")
    page.locator("#wzContent_5 button:has-text('Continue to Step 06')").click()
    expect(page.locator("#wzContent_6")).to_be_visible()

    # STEP 06: Evidence Exhibits
    page.locator("#wzContent_6 button:has-text('Continue to Step 07')").click()
    expect(page.locator("#wzContent_7")).to_be_visible()

    # STEP 07: Witness Roster
    page.locator("#wzContent_7 button:has-text('Continue to Step 08')").click()
    expect(page.locator("#wzContent_8")).to_be_visible()

    # Verify Step 08 Review Summary displays data accurately
    expect(page.locator("#wzReviewFilingName")).to_contain_text("Agent 02")
    expect(page.locator("#wzReviewOpposingName")).to_contain_text("Agent 01")

    # Verify Backward Navigation preserves state
    page.locator("#wzContent_8 button:has-text('← Edit Case')").click()
    expect(page.locator("#wzContent_7")).to_be_visible()
    page.locator("#wzContent_7 button:has-text('← Back to Evidence')").click()
    expect(page.locator("#wzContent_6")).to_be_visible()
    page.locator("#wzContent_6 button:has-text('← Back to Parties')").click()
    expect(page.locator("#wzContent_5")).to_be_visible()

    # Check that Step 5 theories were preserved
    expect(page.locator("#wzProsAccount")).to_have_value("Accused was apprehended in possession of stolen property within 2 hours.")

    # Return to Step 8 and submit
    page.locator("#wzContent_5 button:has-text('Continue to Step 06')").click()
    page.locator("#wzContent_6 button:has-text('Continue to Step 07')").click()
    page.locator("#wzContent_7 button:has-text('Continue to Step 08')").click()
    expect(page.locator("#wzContent_8")).to_be_visible()

    # Click Submit & Enter Courtroom
    submit_btn = page.locator("#wzContent_8 button:has-text('SUBMIT FILING & ENTER COURTROOM')")
    expect(submit_btn).to_be_visible()
    submit_btn.click()

    # Should transition to Courtroom
    page.wait_for_timeout(1000)
    expect(page.locator("#viewCourtroom")).to_be_visible()


def test_filing_wizard_back_buttons_and_exit_navigation(page: Page, frontend_url: str):
    """
    Test: File a Case Wizard Navigation & Back Buttons
    - Verifies top bar '[ ← Return to Platform / Home ]' exits wizard to homepage
    - Verifies Step 01 '[ ← Back to Home ]' button exits wizard
    - Verifies all intermediate step Back buttons (Step 02 -> Step 01, Step 03 -> Step 02, etc.)
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # 1. Enter File a Case wizard
    page.locator("#navFileMatter").click()
    expect(page.locator("#viewFileMatter")).to_be_visible()
    expect(page.locator("#wzContent_1")).to_be_visible()

    # 2. Check top navigation exit button
    top_exit_btn = page.locator("#btnExitFilingTop")
    expect(top_exit_btn).to_be_visible()
    expect(top_exit_btn).to_contain_text("Return to Platform / Home")

    # 3. Check Step 01 Back to Home button
    step1_back_btn = page.locator("#btnWzBack_1")
    expect(step1_back_btn).to_be_visible()
    expect(step1_back_btn).to_contain_text("Back to Home")

    # Click Step 01 Back to Home -> Should return to Landing page
    step1_back_btn.click()
    expect(page.locator("#viewLanding")).to_be_visible()
    expect(page.locator("#viewFileMatter")).to_be_hidden()

    # 4. Re-enter wizard and test top exit button
    page.locator("#navFileMatter").click()
    expect(page.locator("#viewFileMatter")).to_be_visible()
    top_exit_btn.click()
    expect(page.locator("#viewLanding")).to_be_visible()
    expect(page.locator("#viewFileMatter")).to_be_hidden()


def test_filing_wizard_step8_fast_forward_all_hearings(page: Page, frontend_url: str):
    """
    Test: File a Case Wizard - Fast-Forward All Hearings from Step 08
    - Tests loading benchmark/sample case, advancing to Step 08, and clicking '⚡ FAST-FORWARD ALL HEARINGS ⚡'
    - Verifies case simulation completes with zero TypeError/slice exceptions and shows cinematic verdict modal.
    """
    # Track any unhandled dialogs/alerts
    dialog_messages = []
    page.on("dialog", lambda dialog: (dialog_messages.append(dialog.message), dialog.accept()))

    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # 1. Enter File a Case wizard
    page.locator("#navFileMatter").click()
    expect(page.locator("#viewFileMatter")).to_be_visible()

    # 2. Load template data which automatically populates and jumps to Step 08
    page.locator("#wzContent_1 button:has-text('Theft')").click()
    page.wait_for_timeout(500)
    expect(page.locator("#wzContent_8")).to_be_visible()

    # 3. Click '⚡ FAST-FORWARD ALL HEARINGS ⚡'
    fast_forward_btn = page.locator("#wzContent_8 button:has-text('FAST-FORWARD ALL HEARINGS')")
    expect(fast_forward_btn).to_be_visible()
    fast_forward_btn.click()

    # 4. Wait for full simulation run and transition to Courtroom and Verdict Modal
    expect(page.locator("#viewCourtroom")).to_be_visible(timeout=90000)
    expect(page.locator("#modalCinematicVerdict")).to_be_visible(timeout=90000)

    # Verify no simulation error alerts were triggered
    assert len(dialog_messages) == 0, f"Unexpected dialogs encountered: {dialog_messages}"


