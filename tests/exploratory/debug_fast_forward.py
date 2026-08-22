from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
    page.on("dialog", lambda d: (print(f"[DIALOG {d.type}] {d.message}"), d.accept()))

    page.goto("http://localhost:5500/")
    page.wait_for_load_state("domcontentloaded")

    # Go to File a case
    page.locator("#navFileMatter").click()
    page.wait_for_timeout(500)

    # Click Nanavati template
    page.locator("#wzContent_1 button:has-text('Nanavati')").click()
    page.wait_for_timeout(500)

    print("Directly calling finalizeWizardAndRunAllHearings() in page context...")
    res = page.evaluate("""async () => {
        try {
            console.log("Calling finalizeWizardAndRunAllHearings...");
            await finalizeWizardAndRunAllHearings();
            console.log("finalizeWizardAndRunAllHearings finished successfully!");
            return { ok: true, activeCaseId, currentCaseDataStatus: currentCaseData?.status };
        } catch (err) {
            console.error("Caught error in finalizeWizardAndRunAllHearings:", err);
            return { ok: false, error: err.toString(), stack: err.stack };
        }
    }""")
    print("Evaluate result:", res)

    print("Current view display states:")
    for view in ["viewLanding", "viewFileMatter", "viewCourtroom", "viewCaseRoom"]:
        disp = page.eval_on_selector(f"#{view}", "el => el.style.display")
        print(f"  {view}: {disp}")

    browser.close()
