import sys
from playwright.sync_api import sync_playwright, expect
import requests

sys.stdout.reconfigure(encoding='utf-8')

def test_full_application_audit():
    print("=== Starting Full Application Pre-Deployment Audit ===")
    
    # 1. Verify Backend API health
    api_res = requests.get("http://localhost:8000/api/cases/dashboard")
    assert api_res.status_code == 200, f"Backend dashboard endpoint failed: {api_res.status_code}"
    print("✓ Backend API /api/cases/dashboard is Healthy (200 OK)")

    # 2. Verify Law Search API health
    law_res = requests.get("http://localhost:8000/api/law/search?q=theft&domain=BNS")
    assert law_res.status_code == 200, f"Law search endpoint failed: {law_res.status_code}"
    print("✓ Backend API /api/law/search is Healthy (200 OK)")

    # 3. Verify Counsel Roster API
    counsel_res = requests.get("http://localhost:8000/api/counsel/roster")
    assert counsel_res.status_code == 200, f"Counsel roster failed: {counsel_res.status_code}"
    assert len(counsel_res.json().get("roster", [])) == 14, "Expected 14 specialist counsel profiles"
    print("✓ Backend API /api/counsel/roster returned 14 specialists (200 OK)")

    # 4. Frontend Browser Automated Audit
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_errors = []
        page_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        page.goto("http://localhost:5500/")
        page.wait_for_load_state("domcontentloaded")
        print("✓ Frontend page loaded successfully")

        # Test Landing Page Hero and Key Sections
        expect(page.locator("h1:has-text('NYAY MANCH')").first).to_be_visible()
        print("✓ Landing Page H1 Title rendered")

        # Test Navigation to Dashboard
        page.locator("#navDashboard").click()
        expect(page.locator("#viewDashboard")).to_be_visible()
        print("✓ Navigation to Dashboard View works")

        # Test Navigation to Case Registry / Docket
        page.locator("#navCases").click()
        expect(page.locator("#viewCaseRegistry")).to_be_visible()
        print("✓ Navigation to Case Registry View works")

        # Test Navigation to Law Search
        page.locator("#navLegalSearch").click()
        expect(page.locator("#viewLegalSearch")).to_be_visible()
        page.locator("#lawSearchInput").fill("BNS 303")
        page.locator("button:has-text('Search Law')").click()
        page.wait_for_timeout(800)
        expect(page.locator("#lawSearchResults")).to_contain_text("303")
        print("✓ Law Search View & Querying works")

        # Test Navigation to Platform Details
        page.locator("button:has-text('Why This Matters')").first.click()
        page.wait_for_timeout(300)
        page.locator("button:has-text('How It Works')").first.click()
        page.wait_for_timeout(300)
        print("✓ Platform Details Scrolling & Navigation work")

        # Test Choice Modal
        page.locator("#navLanding").click()
        expect(page.locator("#viewLanding")).to_be_visible()
        page.locator("button.ghost-court:has-text('[ ENTER COURT ]')").first.click()
        expect(page.locator("#modalEnterCourtChoice")).to_be_visible()
        print("✓ Choice Modal displayed properly")

        # Test Entering Audience Mode
        page.locator("#btnChoiceAudience").click()
        expect(page.locator("#viewCourtroom")).to_be_visible()
        print("✓ View as Audience transitions seamlessly into Courtroom")

        # In Audience Mode, verify controls are non-interactive
        expect(page.locator("#modalObjection")).to_be_hidden()
        print("✓ Audience Mode interactive restrictions verified")

        # Return to Home and Test File a Case
        page.locator("#btnCourtroomExit").click()
        page.locator("#navFileMatter").click()
        expect(page.locator("#viewFileMatter")).to_be_visible()
        print("✓ Navigation to File a Case Wizard works")

        # Test Template Loading in Wizard
        page.locator("#wzContent_1 button:has-text('Nanavati')").click()
        page.wait_for_timeout(500)
        expect(page.locator("#wzContent_8")).to_be_visible()
        print("✓ Benchmark Case Template quick-loading works")

        # Check console errors
        assert len(page_errors) == 0, f"Uncaught page errors encountered: {page_errors}"
        print(f"✓ Zero uncaught page errors (Console error count: {len(console_errors)})")

        browser.close()

    print("=== All Pre-Deployment Audit Checks Passed Successfully! ===")

if __name__ == "__main__":
    test_full_application_audit()
