import asyncio
import os
from playwright.async_api import async_playwright

async def run_verification():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        # Create context with video recording
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="/home/jules/verification/videos"
        )
        page = await context.new_page()

        print("Navigating to home page, redirecting to login...")
        await page.goto("http://127.0.0.1:8000/")
        await asyncio.sleep(0.5)

        print("Filling login details...")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "admin")
        await page.click("button[type='submit']")
        await asyncio.sleep(0.8)

        # Now directly on the consolidated parameters wizard page in English
        print("Step 1 (EN): Filling customer info...")
        await page.fill("input[name='customer_date']", "2025-07-29")
        await page.fill("input[name='customer_name']", "Acme Corporation")
        await page.fill("input[name='certificate_id']", "CERT-99120-EN")
        await page.fill("input[name='customer_place']", "London, UK")
        await page.fill("input[name='machine_name']", "Laser-X1-English")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 2: Entering Database Host...")
        await page.fill("input[id='input-0']", "acme-db-primary.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 3: Entering Database Port...")
        await page.fill("input[id='input-1']", "5432")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 4: Entering API Key...")
        await page.fill("input[id='input-2']", "acme-api-secret-key-xyz")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 5: Entering Max Retries...")
        await page.fill("input[id='input-3']", "5")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 6: Entering Timeout and Submitting...")
        await page.fill("input[id='input-4']", "30")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Arrive on Success page
        print("Success page (EN) reached. Saving screenshot...")
        await page.screenshot(path="/home/jules/verification/screenshots/verification_en.png")

        # Now, change language to Persian (فارسی)
        print("Changing language to Persian (فارسی)...")
        await page.click("text=فارسی")
        await asyncio.sleep(0.8)

        # Now we are on the /parameters page in Persian because of the referer /submit protection redirect
        print("Arrived on Persian RTL parameters page.")

        # Checking if Prefill Banner is visible and clicking it
        prefill_banner = page.locator("id=prefill-banner")
        if await prefill_banner.is_visible():
            print("Prefill banner is visible in Persian RTL! Clicking prefill button...")
            await page.click("button[id='btn-prefill']")
            await asyncio.sleep(0.5)
        else:
            print("Error: Prefill banner not visible!")

        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 2 (FA): Database Host...")
        await page.fill("input[id='input-0']", "acme-db-replica.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 3 (FA): Database Port...")
        await page.fill("input[id='input-1']", "5433")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 4 (FA): API Key...")
        await page.fill("input[id='input-2']", "acme-api-replica-key-abc")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 5 (FA): Max Retries...")
        await page.fill("input[id='input-3']", "10")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        print("Step 6 (FA): Timeout and Submitting...")
        await page.fill("input[id='input-4']", "60")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Save final screen in Persian
        print("Success page (FA) reached. Saving final screenshot...")
        await page.screenshot(path="/home/jules/verification/screenshots/verification.png")
        await asyncio.sleep(1.0)

        await context.close()
        await browser.close()
        print("Bilingual Persian and English unified wizard verification completed perfectly!")

if __name__ == "__main__":
    asyncio.run(run_verification())
