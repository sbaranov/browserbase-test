from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        
        # Modern auto-waiting capabilities
        page.get_by_role("button", name="Submit").click()
        
        # Take a screenshot
        page.screenshot(path="screenshot.png")
        browser.close()

if __name__ == "__main__":
    main()
