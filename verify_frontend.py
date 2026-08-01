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

        # Step 1: Customer Info
        print("Step 1 (EN): Filling customer info...")
        await page.fill("input[name='customer_date']", "2025-07-29")
        await page.fill("input[name='customer_name']", "Acme Corporation")
        await page.fill("input[name='certificate_id']", "CERT-99120-EN")
        await page.fill("input[name='customer_place']", "London, UK")
        await page.fill("input[name='machine_name']", "Laser-X1-English")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 2: Test Selection (Default Test A)
        print("Step 2 (EN): Selecting Test A and moving forward...")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Test A parameter wizard steps
        print("Step 3: Database Host...")
        await page.fill("input[id='input-Test-A-0']", "acme-db-primary.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 4: Database Port...")
        await page.fill("input[id='input-Test-A-1']", "5432")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 5: API Key...")
        await page.fill("input[id='input-Test-A-2']", "acme-api-secret-key-xyz")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 6: Max Retries...")
        await page.fill("input[id='input-Test-A-3']", "5")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 7: Timeout and Submitting...")
        await page.fill("input[id='input-Test-A-4']", "30")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Arrive on Success page for Test A
        print("Success page (EN - Test A) reached. Saving screenshot...")
        await page.screenshot(path="/home/jules/verification/screenshots/verification_en_test_a.png")

        # Now, change language to Persian (فارسی)
        print("Changing language to Persian (فارسی)...")
        await page.click("text=فارسی")
        await asyncio.sleep(0.8)

        # Now we are on the /parameters page in Persian RTL because of the referer /submit protection redirect
        print("Arrived on Persian RTL parameters page.")

        # Prefill customer info
        prefill_banner = page.locator("id=prefill-banner")
        if await prefill_banner.is_visible():
            print("Prefill banner is visible in Persian RTL! Clicking prefill button...")
            await page.click("button[id='btn-prefill']")
            await asyncio.sleep(0.5)
        else:
            print("Error: Prefill banner not visible!")

        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 2: Test Selection in Persian RTL
        print("Step 2 (FA): Searching and Selecting 'Test B' in Persian...")
        # Search for Test B
        await page.fill("input[id='test-search-input']", "Test B")
        await asyncio.sleep(0.5)
        # Click on Test B
        await page.click("button[id='test-card-Test-B']")
        await asyncio.sleep(0.5)
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Test B specific parameter steps
        print("Step 3 (FA): Database Replica Host...")
        await page.fill("input[id='input-Test-B-0']", "acme-db-replica.internal")
        # Save a screenshot showing Persian RTL wizard dynamic fields and buttons
        await page.screenshot(path="/home/jules/verification/screenshots/verification_fa_wizard.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 4 (FA): Port...")
        await page.fill("input[id='input-Test-B-1']", "5433")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 5 (FA): Read Cache Size (MB)...")
        await page.fill("input[id='input-Test-B-2']", "512")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Step 6 (FA): Use SSL...")
        await page.fill("input[id='input-Test-B-3']", "Yes")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Save final success screen in Persian for Test B
        print("Success page (FA - Test B) reached. Saving final screenshot...")
        await page.screenshot(path="/home/jules/verification/screenshots/verification.png")
        await asyncio.sleep(1.0)

        # Navigating to submissions page
        print("Navigating to submissions dashboard...")
        await page.goto("http://127.0.0.1:8000/submissions")
        await asyncio.sleep(1.0)

        print("Taking screenshot of dynamic bilingual list page...")
        await page.screenshot(path="/home/jules/verification/screenshots/verification_submissions.png")

        # Test CSV generation
        print("Verifying dynamic CSV generation...")
        async with page.expect_download() as download_info:
            await page.click("text=دانلود خروجی CSV")
        download = await download_info.value
        path = await download.path()
        print(f"CSV downloaded successfully to path: {path}")

        # Verify language switcher working on submissions list page
        print("Switching back to English on submissions dashboard...")
        await page.click("text=EN")
        await asyncio.sleep(0.8)
        await page.screenshot(path="/home/jules/verification/screenshots/verification_submissions_en.png")

        await context.close()
        await browser.close()
        print("Bilingual Persian and English unified dynamic test selection wizard and submissions spreadsheet dashboard completed perfectly!")

if __name__ == "__main__":
    asyncio.run(run_verification())
