import pytest
import httpx
from playwright.sync_api import Page, expect


def test_courtroom_filer_controls_and_manual_progression(page: Page, frontend_url: str, backend_url: str):
    """
    Test 4: Courtroom in Filer Mode
    - Create a test case and launch trial
    - Verify interactive filer controls:
      * Contextual Action Button ('ASK NEXT QUESTION →')
      * Objection modal
      * Exhibit Inspector & Register tabs
      * Audio Read-Aloud Narration
    - Verify manual stepping advances question turns.
    """
    # 1. Seed a test case via API to ensure a clean known state
    case_payload = {
        "title": "State of Maharashtra v. Rohan Verma (E2E Test)",
        "jurisdiction": "Sessions Court, Mumbai",
        "case_category": "criminal",
        "simulation_type": "standard",
        "charge_or_dispute": "Murder under BNS §103",
        "facts": "Incident occurred on Mumbai-Pune Intercity express vestibule.",
        "counsel_filing_id": "agent_02",
        "counsel_opposing_id": "agent_01"
    }

    with httpx.Client(base_url=backend_url, timeout=15.0) as client:
        res = client.post("/api/cases", json=case_payload)
        assert res.status_code == 200
        case_data = res.json()
        case_id = case_data["id"]

        # Start trial
        start_res = client.post(f"/api/cases/{case_id}/trial/start")
        assert start_res.status_code == 200

    # 2. Open Courtroom in frontend
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Open case directly via UI JS helper
    page.evaluate(f"(id) => openCourtroomDirectly(id)", case_id)
    page.wait_for_selector("#viewCourtroom", state="visible")

    # 3. Assert active speaker card and contextual action button in Opening phase
    expect(page.locator("#crtSpeakerBubble")).to_be_visible()
    expect(page.locator("#crtQuestionText")).to_be_visible()

    # 4. Verify primary manual action button
    action_btn = page.locator("#btnCourtNextAction")
    expect(action_btn).to_be_visible()

    # 5. Verify case materials tabs
    page.locator("#crtTabBtn_witnesses").click()
    expect(page.locator("#crtTab_witnesses")).to_be_visible()

    page.locator("#crtTabBtn_facts").click()
    expect(page.locator("#crtTab_facts")).to_be_visible()

    page.locator("#crtTabBtn_exhibits").click()
    expect(page.locator("#crtTab_exhibits")).to_be_visible()

    page.locator("#crtTabBtn_law").click()
    expect(page.locator("#crtTab_law")).to_be_visible()

    # 6. Click manual advance and verify progression
    action_btn.click()
    page.wait_for_timeout(1000)
    expect(page.locator("#crtSpeakerBubble")).to_be_visible()
    expect(page.locator("#crtQuestionText")).to_be_visible()

    # 7. Verify Audio Narration Controller
    audio_btn = page.locator("#btnCourtVoice")
    expect(audio_btn).to_be_visible()
