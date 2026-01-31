import re
import asyncio
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
    MAX_RETRIES = 3
    RETRY_DELAY = 5 

    async with async_playwright() as playwright:
        for attempt in range(MAX_RETRIES):
            browser = None
            try:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # UPDATED: Newer User Agent (Chrome 120)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()

                # Stealth Script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                # ... (Resource blocking code stays the same) ...
                excluded_resources = ["image", "font", "stylesheet", "media"]
                async def block_aggressively(route):
                    if route.request.resource_type in excluded_resources:
                        await route.abort()
                    else:
                        await route.continue_()
                await page.route("**/*", block_aggressively)

                print(f"Attempt {attempt + 1}: Navigating to Amazon...")
                await page.goto(product_url, timeout=60000)

                # DEBUG: Print what page we actually landed on
                page_title = await page.title()
                print(f"DEBUG: Page Title is: {page_title}")

                if "Robot Check" in page_title or "CAPTCHA" in page_title:
                    print("Hit Amazon CAPTCHA. Retrying...")
                    raise Exception("Amazon CAPTCHA detected")

                # UPDATED: Increased timeout to 30 seconds (Render is slow)
                await page.locator("span#productTitle").wait_for(timeout=30000)
                
                title = await page.locator("span#productTitle").inner_text()
                title = title.strip()

                # ... (Price and Image logic stays the same) ...
                price_locator = page.locator("span.a-price-whole").first
                if await price_locator.count() > 0:
                    raw_price = await price_locator.inner_text()
                    price = clean_price(raw_price)
                else:
                    price = 0.0

                image_locator = page.locator("#landingImage, #imgBlkFront").first
                image_url = await image_locator.get_attribute("src") if await image_locator.count() > 0 else None

                print(f"Success! Found: {title[:30]}... | Price: {price}")
                return {"title": title, "price": price, "image_url": image_url}

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
            
            finally:
                if browser:
                    await browser.close()

    print("All retry attempts failed.")
    return {"title": None, "price": 0.0, "image_url": None}

# if __name__ == "__main__":
#     url = "https://www.amazon.in/OnePlus-Snapdragon%C2%AE-7300mAh-Personalised-Game-Changing/dp/B0FTR2PJTV/?_encoding=UTF8&pd_rd_w=Ox8Bw&content-id=amzn1.sym.eb64ff86-b345-4426-98d6-57bdc23df42d&pf_rd_p=eb64ff86-b345-4426-98d6-57bdc23df42d&pf_rd_r=NRZ2ZYEDGXSTSC9Q7SP0&pd_rd_wg=TGDgs&pd_rd_r=d452d36d-3b4c-4a8d-bbc9-8e53283d6915&th=1"
#     print(asyncio.run((get_amazon_price(url))))