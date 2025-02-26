import os

from browserbase import Browserbase
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

bb = Browserbase(api_key=BROWSERBASE_API_KEY)

def main():
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
    print("Session replay URL:", f"https://browserbase.com/sessions/{session.id}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        page.goto("https://example.com")
        # page.get_by_role("button", name="Submit").click()
        page.screenshot(path="screenshot.png")

        page.close()
        browser.close()
        print("Done!")

if __name__ == "__main__":
    main()
