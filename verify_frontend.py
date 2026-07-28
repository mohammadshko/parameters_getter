import asyncio
import os
from playwright.async_api import async_playwright

async def run_verification():
    async with async_playwright() as p:
        # Launch browser headless or headful (headless for testing)
        browser = await p.chromium.launch(headless=True)
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
        await page.click("button[type='submit']")
        await asyncio.sleep(1)
        # We are now on the dashboard
        await page.screenshot(path="screenshot_03_dashboard.png")

        print("Clicking 'Customer Info' button...")
        await page.click("a[id='btn-customer-info']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_04_new_customer_page.png")

        print("Filling customer details...")
        await page.fill("input[name='name']", "Apex Systems LLC")
        await page.fill("input[name='email']", "contact@apexsystems.com")
        await page.click("button[id='btn-save-customer']")
        await asyncio.sleep(1)
        # Redirected back to dashboard with Apex Systems LLC as active
        await page.screenshot(path="screenshot_05_dashboard_with_customer.png")

        print("Clicking 'Already Form' wizard button...")
        await page.click("a[id='btn-already-form']")
        await asyncio.sleep(0.5)
        await page.screenshot(path="screenshot_06_wizard1_step1.png")

        # Step through wizard - 1st Service configuration
        print("Editing Database Host (Service 1) and pressing Forward...")
        await page.fill("input[id='input-0']", "apex-db-primary.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Database Port (Service 1) and pressing Forward...")
        await page.fill("input[id='input-1']", "5432")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing API Key (Service 1) and pressing Forward...")
        await page.fill("input[id='input-2']", "apex-api-secret-abc")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Max Retries (Service 1) and pressing Forward...")
        await page.fill("input[id='input-3']", "3")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Timeout (Service 1) and pressing Submit...")
        await page.fill("input[id='input-4']", "15")
        await page.screenshot(path="screenshot_07_wizard1_step5.png")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1)
        # Now on Success page for first service
        await page.screenshot(path="screenshot_08_success_first_service.png")

        # Fill form twice: Configure Another Service
        print("Clicking 'Configure Another Service' to fill form twice...")
        await page.click("a[id='btn-configure-another']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_09_wizard2_step1.png")

        # Step through wizard - 2nd Service configuration
        print("Editing Database Host (Service 2) and pressing Forward...")
        await page.fill("input[id='input-0']", "apex-db-replica.internal")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Database Port (Service 2) and pressing Forward...")
        await page.fill("input[id='input-1']", "5433")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing API Key (Service 2) and pressing Forward...")
        await page.fill("input[id='input-2']", "apex-api-replica-xyz")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Max Retries (Service 2) and pressing Forward...")
        await page.fill("input[id='input-3']", "5")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)

        print("Editing Timeout (Service 2) and pressing Submit...")
        await page.fill("input[id='input-4']", "30")
        await page.screenshot(path="screenshot_10_wizard2_step5.png")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1)
        # Success page showing BOTH services configured!
        await page.screenshot(path="screenshot_11_success_both_services.png")

        print("Going back to dashboard...")
        await page.click("a[id='btn-go-dashboard']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_12_dashboard_completed.png")

        print("Testing logout...")
        await page.click("a[href='/logout']")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshot_13_after_logout.png")

        print("Pristine customer and multi-service wizard verification flow completed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
