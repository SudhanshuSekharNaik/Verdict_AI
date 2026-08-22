import re
import pytest
import httpx
from playwright.sync_api import Page, expect


def test_ui_counsel_mutual_exclusivity(page: Page, frontend_url: str):
    """
    Test 3A: Counsel Selection Constraint in Frontend UI
    - Selecting an agent in Filing window dims & blocks that agent in Opposing window
    - Confirms that both windows cannot simultaneously select the same agent.
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Navigate to Step 02 of Filing Wizard
    page.locator("#navFileMatter").click()
    page.locator("#wzTitle").fill("Test Counsel Conflict Case")
    page.locator("#wzCharge").fill("Statutory Compliance Test")
    page.locator("#wzContent_1 button:has-text('Save & Continue to Step 02')").click()
    expect(page.locator("#wzContent_2")).to_be_visible()

    # Select Agent 02 as Filing Counsel
    filing_card_02 = page.locator("#filingCard_agent_02")
    filing_card_02.locator("button").click()
    expect(filing_card_02).to_have_class(re.compile(r"selected-active-filing"))

    # In Opposing Window, Agent 02 should be disabled with assigned indicator
    opposing_card_02 = page.locator("#opposingCard_agent_02")
    expect(opposing_card_02).to_have_class(re.compile(r"card-disabled-other-side"))
    expect(opposing_card_02).to_contain_text("Assigned to Filing Counsel")

    # Clicking the disabled button in Opposing window should not select it
    opposing_card_02.locator("button").click()
    expect(opposing_card_02).not_to_have_class(re.compile(r"selected-active-opposing"))

    # Select a valid distinct opposing counsel (e.g. Agent 01)
    opposing_card_01 = page.locator("#opposingCard_agent_01")
    opposing_card_01.locator("button").click()
    expect(opposing_card_01).to_have_class(re.compile(r"selected-active-opposing"))

    # Verify Continue button allows proceeding
    continue_btn = page.locator("#wzContent_2 button:has-text('Continue to Step 03')")
    continue_btn.click(force=True)
    expect(page.locator("#wzContent_3")).to_be_visible()


def test_backend_rejects_identical_counsel(backend_url: str):
    """
    Test 3B: Counsel Selection Constraint on Backend API
    - Directly sends a case payload with counsel_filing_id == counsel_opposing_id == 'agent_01'
    - Confirms backend returns HTTP 422 Unprocessable Entity.
    """
    payload = {
        "title": "State v. Duplicate Counsel Test",
        "jurisdiction": "Sessions Court, Delhi",
        "case_category": "criminal",
        "simulation_type": "standard",
        "charge_or_dispute": "Section 303(2) BNS",
        "facts": "Sample facts for constraint testing.",
        "counsel_filing_id": "agent_01",
        "counsel_opposing_id": "agent_01"  # ILLEGAL: Duplicate counsel
    }

    with httpx.Client(base_url=backend_url, timeout=10.0) as client:
        res = client.post("/api/cases", json=payload)
        assert res.status_code == 422, f"Expected 422 Unprocessable Entity, got {res.status_code}: {res.text}"
        data = res.json()
        assert "cannot be the same agent" in data.get("detail", "").lower()
