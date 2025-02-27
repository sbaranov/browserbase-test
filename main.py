import os
from dataclasses import dataclass
from typing import Optional

from browserbase import Browserbase
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from playwright.sync_api import sync_playwright

load_dotenv()

AMAZON_SEARCH_QUERY = "water flosser"

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

bb = Browserbase(api_key=BROWSERBASE_API_KEY)

@dataclass
class ProductInfo:
    """Information about an Amazon product."""
    title: str
    description: str
    asin: str
    url: str

class ProductAnalysis(BaseModel):
    """Analysis of a water flosser product based on its information."""
    is_portable: bool = Field(description="Whether the product is portable (compact and easy to carry)")
    is_rechargeable: bool = Field(description="Whether the product is rechargeable (has a built-in battery that can be recharged)")
    reasoning: str = Field(description="Explanation for the determinations made")

@dataclass
class ScraperDependencies:
    """Dependencies for the Amazon scraper."""
    page: Optional[object] = None
    product_info: Optional[ProductInfo] = None

# Create the agent that will analyze products
product_analyzer = Agent(
    "openai:gpt-4o",
    result_type=ProductAnalysis,
    deps_type=ScraperDependencies,
    system_prompt=(
        "You are a product analysis expert specializing in water flossers. "
        "Analyze the given product information to determine if it's portable and rechargeable. "
        "A portable product is compact and easy to carry. "
        "A rechargeable product has a built-in battery that can be recharged."
    )
)

def extract_product_info(page, asin: str) -> ProductInfo:
    """Extract product information from Amazon."""
    url = f"https://amazon.com/dp/{asin}"
    page.goto(url)
    page.wait_for_timeout(1000)
    
    title = page.locator('#productTitle').inner_text()
    description = page.locator('#feature-bullets').inner_text()
    
    return ProductInfo(
        title=title,
        description=description,
        asin=asin,
        url=url
    )

@product_analyzer.tool
def get_product_details(ctx: RunContext[ScraperDependencies]) -> str:
    """
    Get detailed information about the product to aid in analysis.
    
    Returns:
        A detailed description of the product
    """
    product_info = ctx.deps.product_info
    if not product_info:
        return "No product information available"
    
    return f"""
    Product Title: {product_info.title}
    
    Product Description:
    {product_info.description}
    
    Product URL: {product_info.url}
    """

def search_products(page, query):
    page.goto("https://amazon.com")
    page.get_by_placeholder("Search Amazon").fill(query)
    page.locator('#nav-search-submit-button').click()
    page.wait_for_timeout(1000)

    asins = []
    for result in page.locator('.s-result-item').all():
        data_asin = result.get_attribute('data-asin')
        if not data_asin:
            continue

        asins.append(data_asin)

    return asins

def analyze_product(page, asin):
    print(f"\nAnalyzing: https://amazon.com/dp/{asin}")
    
    # Extract product information
    product_info = extract_product_info(page, asin)
    
    # Set up dependencies including product_info
    deps = ScraperDependencies(page=page, product_info=product_info)
    
    try:
        # Run the agent to analyze the product
        result = product_analyzer.run_sync(
            f"""Please analyze this water flosser product:
            
            Use the get_product_details tool to get the product details and determine if it's portable and rechargeable.
            """,
            deps=deps
        )
        
        # Display results
        print(f"Portable: {result.data.is_portable}")
        print(f"Rechargeable: {result.data.is_rechargeable}")
        print(f"Reasoning: {result.data.reasoning}")
        return result.data
    except Exception as e:
        print(f"Error analyzing product: {e}")
        return None

def main():
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
    print("Session replay URL:", f"https://browserbase.com/sessions/{session.id}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # asins = search_products(page, AMAZON_SEARCH_QUERY)
        asins = ["B0BG52SJ5N"]  # For testing
        
        # Analyze first 3 products
        for asin in asins[:3]:
            analyze_product(page, asin)

        page.close()
        browser.close()
        print("\nDone")

if __name__ == "__main__":
    main()
