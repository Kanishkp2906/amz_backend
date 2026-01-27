import re
from playwright.async_api import async_playwright

def clean_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


async def get_amazon_price(product_url: str):

    async with async_playwright() as playwright:
        # Launch browser (headless=True is standard for servers)
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Navigating to Amazon...")
            await page.goto(product_url, timeout=60000) # 60s timeout for safety

            await page.locator("#productTitle").wait_for(timeout=10000)
            title = await page.locator("#productTitle").inner_text()
            title = title.strip()

            price_locator = page.locator("span.a-price-whole").first
            
            if await price_locator.count() > 0:
                raw_price = await price_locator.inner_text()
                price = clean_price(raw_price)
            else:
                # Fallback: Sometimes price is hidden or different structure
                price = 0.0
                print("Warning: Could not find price element.")

            image_locator = page.locator("#landingImage, #imgBlkFront").first
            
            image_url = None
            if await image_locator.count() > 0:
                image_url = await image_locator.get_attribute("src")

            print(f"Success! Found: {title[:30]}... | Price: {price}")
            
            return {"title": title, "price": price}

        except Exception as e:
            print(f"Scraping failed: {e}")
            return None
        
        finally:
            await browser.close()