from pathlib import Path

from playwright.sync_api import sync_playwright


SCREENSHOT = Path("/private/tmp/magic-mapper-dashboard.png")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8765/index.html")
    page.wait_for_load_state("networkidle")

    assert page.get_by_text("Active now").is_visible()
    assert page.locator(".mapping-row").count() == 3
    assert page.get_by_role("button", name="Discover a button").is_enabled()
    page.screenshot(path=str(SCREENSHOT), full_page=True)

    page.get_by_role("button", name="Discover a button").click()
    assert page.get_by_role("heading", name="Press one remote button").is_visible()
    page.wait_for_selector("[data-action='disable']", timeout=5000)
    page.locator("[data-action='disable']").click()
    page.wait_for_selector(".mapping-row", timeout=3000)
    assert page.get_by_text("Rakuten TV", exact=True).is_visible()
    assert page.locator(".mapping-row").count() == 4

    page.get_by_role("button", name="Service & removal").click()
    assert page.get_by_role("heading", name="Service & removal").is_visible()
    assert page.get_by_text("Uninstall Magic Mapper", exact=True).is_visible()
    page.keyboard.press("Escape")
    assert page.locator("#modal").is_hidden()
    assert not errors, errors

    bridge_page = browser.new_page(viewport={"width": 1920, "height": 1080})
    bridge_page.add_init_script("""
      window.PalmServiceBridge = function () {
        this.call = () => setTimeout(() => this.onservicecallback(JSON.stringify({
          returnValue: true,
          stdoutString: JSON.stringify({ok: true, status: {
            active: true, installed: true, config: {netflix: "disabled"}
          }}),
          stderrString: ""
        })), 0);
      };
    """)
    bridge_page.goto("http://127.0.0.1:8765/index.html")
    bridge_page.wait_for_load_state("networkidle")
    assert bridge_page.get_by_text("Active now").is_visible()
    assert bridge_page.locator(".mapping-row").count() == 1
    browser.close()

print(SCREENSHOT)
