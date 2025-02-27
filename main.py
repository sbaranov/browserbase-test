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
    value_score: float = Field(description="Score from 1-10 indicating the overall value of the product")
    brand_reputation: int = Field(description="Score from 1-5 indicating the brand's reputation in the market")
    reasoning: str = Field(description="Explanation for the determinations made")

def extract_product_info(page, asin: str) -> Dict[str, str]:
    """Extract product information from Amazon."""
    url = f"https://amazon.com/dp/{asin}"
    page.goto(url)
    page.wait_for_timeout(1000)
    
    title = page.locator('#productTitle').inner_text()
    description = page.locator('#feature-bullets').inner_text()
    
    # Try to extract price information if available
    price = ""
    try:
        price_element = page.locator('.a-price .a-offscreen').first
        if price_element:
            price = price_element.inner_text()
    except:
        pass
    
    # Try to extract brand information if available
    brand = ""
    try:
        # Try method 1: Check for brand element
        brand_element = page.locator('a#bylineInfo').first
        if brand_element:
            brand = brand_element.inner_text().replace("Brand: ", "").strip()
        
        # If not found, try method 2: Extract from title
        if not brand and title:
            # Extract first word as potential brand
            brand = title.split()[0]
    except:
        # If all methods fail, extract first word from title as fallback
        if title:
            brand = title.split()[0]
    
    # Try to extract ratings information
    ratings = ""
    try:
        ratings_element = page.locator('#acrPopover').first
        if ratings_element:
            ratings = ratings_element.get_attribute('title')
    except:
        pass
    
    # Try to extract number of reviews
    reviews = ""
    try:
        reviews_element = page.locator('#acrCustomerReviewText').first
        if reviews_element:
            reviews = reviews_element.inner_text()
    except:
        pass
    
    return {
        "title": title,
        "description": description,
        "price": price,
        "brand": brand,
        "ratings": ratings,
        "reviews": reviews,
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
    
    Brand: {product_info.get('brand', 'Not specified')}
    
    Price: {product_info.get('price', 'Not available')}
    
    Ratings: {product_info.get('ratings', 'Not available')}
    
    Reviews: {product_info.get('reviews', 'Not available')}
    
    Product URL: {product_info['url']}
    """
    
    # Create the analysis prompt
    system_prompt = """
    You are a product analysis expert specializing in water flossers.
    Analyze the given product information to determine:
    
    1. If it's portable (compact and easy to carry)
    2. If it's rechargeable (has a built-in battery that can be recharged)
    3. A value score from 1-10 based on the following criteria:
       - Features relative to typical market offerings
       - Portability benefits (if applicable)
       - Battery life and charging features (if applicable)
       - Water tank capacity and pressure settings
       - Durability based on materials mentioned
       - Overall usefulness for oral hygiene
       - Brand reputation (as assessed in point 4)
       - Price competitiveness for features offered
       
    4. A brand reputation score from 1-5 where:
       - 5: Industry leader, well-established with excellent reputation
       - 4: Well-known brand with good reputation
       - 3: Average brand recognition and reputation
       - 2: Lesser-known brand with limited reputation
       - 1: Unknown brand or known for poor quality
       
    Consider the brand name, ratings, number of reviews, and any mentions of brand reputation in reviews.
       
    A value score of 10 means exceptional value, while 1 means poor value.
    
    Return your analysis in JSON format with these fields:
    - is_portable (boolean): Whether the product is portable
    - is_rechargeable (boolean): Whether the product is rechargeable
    - value_score (number): Score from 1-10 indicating the overall value
    - brand_reputation (number): Score from 1-5 for the brand's reputation
    - reasoning (string): Your explanation for all determinations, including separate sections for portability, rechargeability, value assessment, and brand reputation
    """
    
    user_prompt = f"""
    Here's the product information:
    {product_info_text}
    
    Analyze if this product is portable, rechargeable, provide a value score, and assess the brand reputation based on the information provided.
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
            value_score=float(result["value_score"]),
            brand_reputation=int(result["brand_reputation"]),
            reasoning=result["reasoning"]
        )
    except Exception as e:
        print(f"Error analyzing product: {e}")
        # Return a default analysis in case of error
        return ProductAnalysis(
            is_portable=False,
            is_rechargeable=False,
            value_score=0.0,
            brand_reputation=1,
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

        asins = search_products(page, AMAZON_SEARCH_QUERY)
        # asins = ["B0BG52SJ5N"]  # For testing only
        
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
            print(f"Brand Reputation: {analysis.brand_reputation}/5")
            print(f"Value Score: {analysis.value_score}/10")
            print(f"Reasoning: {analysis.reasoning}")

        page.close()
        browser.close()
        print("\nDone")

if __name__ == "__main__":
    main()
