import asyncio
import os
from playwright.async_api import async_playwright

async def run_verification():
    async with async_playwright() as p:
        # Launch browser headless or headful (headless for testing)
        browser = await p.chromium.launch(headless=True)
        # 1280x800 for nice screenshots
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        print("Navigating to home page, redirecting to login...")
        await page.goto("http://127.0.0.1:8000/")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_01_login_page.png")

        print("Filling login details...")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "admin")
        await page.screenshot(path="screenshot_02_login_filled.png")

        print("Clicking login...")
        # Clicking sign in button
        await page.click("button[type='submit']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_03_wizard_step1.png")

        # Step through wizard
        # Parameter 1: Database Host
        print("Editing Database Host and pressing Forward...")
        await page.fill("input[id='input-0']", "production-db.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_04_wizard_step2.png")

        # Parameter 2: Database Port
        print("Editing Database Port and pressing Forward...")
        await page.fill("input[id='input-1']", "5439")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_05_wizard_step3.png")

        # Parameter 3: API Key
        print("Editing API Key and pressing Forward...")
        await page.fill("input[id='input-2']", "prod-key-xyz-789")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_06_wizard_step4.png")

        # Let's test Back button from step 4
        print("Testing Back button...")
        await page.click("button[id='back-btn']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_07_wizard_back_step3.png")

        # Go forward again to step 4
        print("Going Forward again to step 4...")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Parameter 4: Max Retries
        print("Editing Max Retries and pressing Forward...")
        await page.fill("input[id='input-3']", "10")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_08_wizard_step5.png")

        # Parameter 5: Timeout (seconds)
        print("Editing Timeout and checking Submit button visibility...")
        await page.fill("input[id='input-4']", "60")
        await page.screenshot(path="screenshot_09_wizard_step5_filled.png")

        print("Submitting the configuration...")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_10_success.png")

        print("Testing logout...")
        await page.click("a[href='/logout']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_11_after_logout.png")

        print("Frontend verification flow completed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
