import os
from dotenv import load_dotenv
from browserbase import Browserbase
from playwright.sync_api import sync_playwright

def main():
    load_dotenv()
    bb = Browserbase()
    session = bb.sessions.create(project_id=os.getenv('BROWSERBASE_PROJECT_ID'))

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        default_context = browser.contexts[0]

        page = default_context.pages[0]
        page.goto("https://example.com")
        page.get_by_role("button", name="Submit").click()
        page.screenshot(path="screenshot.png")
        page.close()

        browser.close()
        print(f"Session complete! View replay at https://browserbase.com/sessions/{session.id}")

if __name__ == "__main__":
    main()
