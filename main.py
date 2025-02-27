import os
import json
from typing import Dict, List
from dataclasses import dataclass

from browserbase import Browserbase
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright
import openai  # Direct OpenAI client

load_dotenv()

AMAZON_SEARCH_QUERY = "water flosser"

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bb = Browserbase(api_key=BROWSERBASE_API_KEY)
openai.api_key = OPENAI_API_KEY

class ProductAnalysis(BaseModel):
    """Analysis of a water flosser product based on its information."""
    is_portable: bool = Field(description="Whether the product is portable (compact and easy to carry)")
    is_rechargeable: bool = Field(description="Whether the product is rechargeable (has a built-in battery that can be recharged)")
    reasoning: str = Field(description="Explanation for the determinations made")

def extract_product_info(page, asin: str) -> Dict[str, str]:
    """Extract product information from Amazon."""
    url = f"https://amazon.com/dp/{asin}"
    page.goto(url)
    page.wait_for_timeout(1000)
    
    title = page.locator('#productTitle').inner_text()
    description = page.locator('#feature-bullets').inner_text()
    
    return {
        "title": title,
        "description": description,
        "asin": asin,
        "url": url
    }

def analyze_product_with_openai(product_info: Dict[str, str]) -> ProductAnalysis:
    """Use OpenAI directly to analyze if a product is portable and rechargeable."""
    # Format the product info as a string for the prompt
    product_info_text = f"""
    Product Title: {product_info['title']}
    
    Product Description:
    {product_info['description']}
    
    Product URL: {product_info['url']}
    """
    
    # Create the analysis prompt
    system_prompt = """
    You are a product analysis expert specializing in water flossers.
    Analyze the given product information to determine if it's portable and rechargeable.
    
    A portable product is compact and easy to carry.
    A rechargeable product has a built-in battery that can be recharged.
    
    Return your analysis in JSON format with these fields:
    - is_portable (boolean): Whether the product is portable
    - is_rechargeable (boolean): Whether the product is rechargeable
    - reasoning (string): Your explanation for these determinations
    """
    
    user_prompt = f"""
    Here's the product information:
    {product_info_text}
    
    Analyze if this product is portable and rechargeable based on the information provided.
    """
    
    # Use the OpenAI client to get the result
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return ProductAnalysis(
            is_portable=result["is_portable"],
            is_rechargeable=result["is_rechargeable"],
            reasoning=result["reasoning"]
        )
    except Exception as e:
        print(f"Error analyzing product: {e}")
        # Return a default analysis in case of error
        return ProductAnalysis(
            is_portable=False,
            is_rechargeable=False,
            reasoning=f"Error analyzing product: {str(e)}"
        )

def search_products(page, query) -> List[str]:
    """Search Amazon for products and extract their ASINs."""
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

def main():
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
    print("Session replay URL:", f"https://browserbase.com/sessions/{session.id}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # For testing, use a specific ASIN
        asins = ["B0BG52SJ5N"]  # For testing only
        # Uncomment to search for real products
        # asins = search_products(page, AMAZON_SEARCH_QUERY)
        
        # Analyze first 3 products
        for asin in asins[:3]:
            print(f"\nAnalyzing: https://amazon.com/dp/{asin}")
            
            # Get product information
            product_info = extract_product_info(page, asin)
            
            # Analyze the product
            analysis = analyze_product_with_openai(product_info)
            
            # Display results
            print(f"Portable: {analysis.is_portable}")
            print(f"Rechargeable: {analysis.is_rechargeable}")
            print(f"Reasoning: {analysis.reasoning}")

        page.close()
        browser.close()
        print("\nDone")

if __name__ == "__main__":
    main()
