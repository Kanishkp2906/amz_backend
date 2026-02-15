import requests
from bs4 import BeautifulSoup
import re
import asyncio

SCRAPINGANT_URL = "https://api.scrapingant.com/v2/general"

def clean_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
    
async def get_amazon_price(product_url: str, api_key: str):
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            params = {
                'url': product_url,
                'x-api-key': api_key,
                'wait_for_selector': "span#productTitle",
                'browser': 'true'
            }

            response = requests.get(SCRAPINGANT_URL, params=params, timeout=60)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            title_elem = soup.select_one('span#productTitle')
            title = title_elem.get_text(strip= True) if title_elem else None

            price = 0.0
            price_selectors = [
                "span.a-price-whole",
                "span.a-price .a-offscreen",
                "span.a-offscreen"
            ]

            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = clean_price(price_text)
                    if price > 0:
                        break
            
            image_elem = soup.select_one("#landingImage, #imgBlkFront")
            image_url = image_elem.get("src") if image_elem else None
            
            if title and price > 0:
                return {
                    "title": title,
                    "price": price,
                    "image_url": image_url,
                    "success": True
                }
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)

    return {
        "title": None,
        "price": 0.0,
        "image_url": None,
        "success": False
    }