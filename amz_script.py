import re
import asyncio # <--- Import this for the delay
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
    RETRY_DELAY = 5 # seconds

    async with async_playwright() as playwright:
        
        # RETRY LOOP STARTS HERE
        for attempt in range(MAX_RETRIES):
            browser = None
            try:
                # 1. SETUP BROWSER (Same stealth logic as before)
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()

                # Stealth Script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                # Resource Blocking
                excluded_resources = ["image", "font", "stylesheet", "media"]
                async def block_aggressively(route):
                    if route.request.resource_type in excluded_resources:
                        await route.abort()
                    else:
                        await route.continue_()
                await page.route("**/*", block_aggressively)

                # 2. NAVIGATE & SCRAPE
                print(f"Attempt {attempt + 1}: Navigating to Amazon...")
                await page.goto(product_url, timeout=60000)

                await page.locator("span#productTitle").wait_for(timeout=10000)
                title = await page.locator("span#productTitle").inner_text()
                title = title.strip()

                price_locator = page.locator("span.a-price-whole").first
                if await price_locator.count() > 0:
                    raw_price = await price_locator.inner_text()
                    price = clean_price(raw_price)
                else:
                    price = 0.0
                    print("Warning: Could not find price element.")

                image_locator = page.locator("#landingImage, #imgBlkFront").first
                image_url = None
                if await image_locator.count() > 0:
                    image_url = await image_locator.get_attribute("src")

                print(f"Success! Found: {title[:30]}... | Price: {price}")
                
                # IMPORTANT: If successful, return immediately (breaking the loop)
                return {
                    "title": title, 
                    "price": price, 
                    "image_url": image_url
                }

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                
                # Wait before retrying (unless it's the last attempt)
                if attempt < MAX_RETRIES - 1:
                    print(f"Waiting {RETRY_DELAY} seconds before retrying...")
                    await asyncio.sleep(RETRY_DELAY)
            
            finally:
                # Always close the browser instance for this attempt
                if browser:
                    await browser.close()

    # If the loop finishes all 3 attempts without returning, we failed.
    print("All retry attempts failed.")
    return {"title": None, "price": 0.0, "image_url": None}

if __name__ == "__main__":
    url = "https://www.amazon.in/OnePlus-Snapdragon%C2%AE-7300mAh-Personalised-Game-Changing/dp/B0FTR2PJTV/?_encoding=UTF8&pd_rd_w=Ox8Bw&content-id=amzn1.sym.eb64ff86-b345-4426-98d6-57bdc23df42d&pf_rd_p=eb64ff86-b345-4426-98d6-57bdc23df42d&pf_rd_r=NRZ2ZYEDGXSTSC9Q7SP0&pd_rd_wg=TGDgs&pd_rd_r=d452d36d-3b4c-4a8d-bbc9-8e53283d6915&th=1"
    print(asyncio.run((get_amazon_price(url))))