import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}", flush=True))
    page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}", flush=True))
    page.on("dialog", lambda d: (print(f"[DIALOG {d.type}] {d.message}", flush=True), d.accept()))
    page.on("request", lambda req: print(f"-> {req.method} {req.url}", flush=True))
    page.on("response", lambda res: print(f"<- {res.status} {res.url}", flush=True))

    page.goto("http://localhost:5500/")
    page.wait_for_load_state("domcontentloaded")

    # Enter wizard
    page.locator("#navFileMatter").click()
    page.wait_for_timeout(300)

    # Click Nanavati template
    page.locator("#wzContent_1 button:has-text('Nanavati')").click()
    page.wait_for_timeout(500)

    print("Clicking fast forward...", flush=True)
    page.locator("#wzContent_8 button:has-text('FAST-FORWARD ALL HEARINGS')").click()

    # Wait for completion or errors
    page.wait_for_timeout(15000)

    print("Courtroom visible:", page.locator("#viewCourtroom").is_visible(), flush=True)
    print("Verdict modal visible:", page.locator("#modalCinematicVerdict").is_visible(), flush=True)

    browser.close()
