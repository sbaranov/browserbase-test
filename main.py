import os

from browserbase import Browserbase
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

AMAZON_SEARCH_QUERY = "water flosser"

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

bb = Browserbase(api_key=BROWSERBASE_API_KEY)

def get_product_asins(page, query):
    page.goto("https://amazon.com")
    page.get_by_placeholder("Search Amazon").fill(query)
    page.locator('#nav-search-submit-button').click()
    page.wait_for_timeout(1000)

    product_asins = []
    for result in page.locator('.s-result-item').all():
        data_asin = result.get_attribute('data-asin')
        if not data_asin:
            continue

        product_asins.append(data_asin)

    return product_asins

def main():
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
    print("Session replay URL:", f"https://browserbase.com/sessions/{session.id}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        product_asins = get_product_asins(page, AMAZON_SEARCH_QUERY)
        for product_asin in product_asins[:3]:
            print(f"https://amazon.com/dp/{product_asin}")
            page.goto(f"https://amazon.com/dp/{product_asin}")
            page.wait_for_timeout(1000)

        page.close()
        browser.close()
        print("Done")

if __name__ == "__main__":
    main()
