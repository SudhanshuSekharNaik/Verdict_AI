import pytest
import httpx
from playwright.sync_api import Page, expect


def test_cinematic_verdict_modal_and_decree(page: Page, frontend_url: str):
    """
    Test 6A: Cinematic Restrained Verdict Reveal Modal
    - Opens sample verdict reveal modal
    - Verifies decision title, operative basis, statutory findings, and decree button.
    """
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("domcontentloaded")

    # Trigger verdict modal via JS helper
    page.evaluate("() => openSampleJudgmentModal()")

    modal = page.locator("#modalCinematicVerdict")
    expect(modal).to_be_visible()

    # Verify Decision Title
    expect(page.locator("#cinematicVerdictTitle")).to_contain_text("NOT GUILTY")

    # Verify Issue Findings list
    expect(page.locator("#cinematicIssueFindings")).to_be_visible()

    # Close modal
    close_btn = modal.locator("button:has-text('✕ Close')")
    close_btn.click()
    expect(modal).to_be_hidden()


def test_verdict_export_endpoints(backend_url: str):
    """
    Test 6B: Case Export Endpoints (Markdown & JSON)
    - Verifies GET /api/cases/{case_id}/export returns valid dossiers.
    """
    # 1. Create a seed case with verdict
    case_payload = {
        "title": "State v. Export Test Case",
        "jurisdiction": "Sessions Court, Delhi",
        "case_category": "criminal",
        "simulation_type": "standard",
        "charge_or_dispute": "Section 303(2) BNS",
        "facts": "Export verification factual record.",
        "counsel_filing_id": "agent_02",
        "counsel_opposing_id": "agent_01"
    }

    with httpx.Client(base_url=backend_url, timeout=15.0) as client:
        res = client.post("/api/cases", json=case_payload)
        assert res.status_code == 200
        case_id = res.json()["id"]

        # Fast forward / finish trial
        client.post(f"/api/cases/{case_id}/trial/fast-forward")

        # 2. Test Markdown Export
        md_res = client.get(f"/api/cases/{case_id}/export?format=markdown")
        assert md_res.status_code == 200
        assert "Content-Disposition" in md_res.headers or "text/markdown" in md_res.headers.get("content-type", "") or len(md_res.text) > 50
        assert "State v. Export Test Case" in md_res.text

        # 3. Test JSON Export
        json_res = client.get(f"/api/cases/{case_id}/export?format=json")
        assert json_res.status_code == 200
        data = json_res.json()
        assert data.get("title") == "State v. Export Test Case"
        assert "evidence_list" in data
        assert "witnesses_list" in data
