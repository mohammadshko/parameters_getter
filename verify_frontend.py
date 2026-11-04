import asyncio
import os
from playwright.async_api import async_playwright

async def run_verification():
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    os.makedirs("/home/jules/verification/videos", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            record_video_dir="/home/jules/verification/videos"
        )
        page = await context.new_page()

        print("Navigating to login...")
        await page.goto("http://127.0.0.1:8000/")
        await asyncio.sleep(0.5)

        print("Logging in...")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "admin")
        await page.click("button[type='submit']")
        await asyncio.sleep(0.8)

        # Step 1: Customer Profile (Name & Address only)
        print("Step 1 (EN): Filling Customer Name and Address...")
        await page.fill("input[name='customer_name']", "Acme Precision Labs")
        await page.fill("textarea[name='customer_address']", "123 Calibration Blvd, Industrial Zone")
        await page.screenshot(path="/home/jules/verification/screenshots/step1_customer_en.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 2: Choose Tool
        print("Step 2 (EN): Choosing Tool (Pressure Gauge)...")
        await page.click("button[id='tool-card-Pressure-Gauge']")
        await page.screenshot(path="/home/jules/verification/screenshots/step2_tool_en.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 3: Producer Name
        print("Step 3 (EN): Selecting Producer (.producer-badge-btn:has-text('WIKA'))...")
        await page.click(".producer-badge-btn:has-text('WIKA')")
        await page.screenshot(path="/home/jules/verification/screenshots/step3_producer_en.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 4: Tool Specifications (Model, Range, Resolution, Serial No, Location)
        print("Step 4 (EN): Filling/Verifying Model, Range, Resolution, Serial No, Location...")
        await page.fill("input[id='spec-model']", "213.53-HeavyDuty")
        await page.fill("input[id='spec-range']", "0 - 1000 mbar")
        await page.fill("input[id='spec-resolution']", "1.0 mbar")
        await page.fill("input[id='spec-serial']", "SN-WIKA-99201")
        await page.fill("input[id='spec-location']", "Calibration Lab Bay 3")
        await page.screenshot(path="/home/jules/verification/screenshots/step4_specs_en.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Step 5: Calibration Table matching image.png
        print("Step 5 (EN): Filling calibration table (Reference value [Rising, Falling] and UUC)...")
        cal_values = [
            ("0", "0.0", "0.0"),
            ("200", "199.5", "200.2"),
            ("400", "399.8", "400.1"),
            ("600", "599.9", "600.4"),
            ("800", "800.1", "800.5"),
            ("1000", "1000.2", "1000.6"),
        ]
        for i, (uuc, rising, falling) in enumerate(cal_values):
            await page.fill(f"input[id='uuc_{i}']", uuc)
            await page.fill(f"input[id='ref_rising_{i}']", rising)
            await page.fill(f"input[id='ref_falling_{i}']", falling)

        await page.screenshot(path="/home/jules/verification/screenshots/step5_table_en.png")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Arrive on Success page
        print("Success page reached (EN). Saving screenshot...")
        await page.screenshot(path="/home/jules/verification/screenshots/success_en.png")

        # Change language to Persian (فارسی)
        print("Changing language to Persian (فارسی)...")
        await page.click("text=فارسی")
        await asyncio.sleep(0.8)

        # We are on the parameters page in Persian RTL with prefill banner
        print("Testing Persian RTL & Prefill...")
        prefill_banner = page.locator("id=prefill-banner")
        if await prefill_banner.is_visible():
            print("Clicking prefill button...")
            await page.click("button[id='btn-prefill']")
            await asyncio.sleep(0.5)

        await page.screenshot(path="/home/jules/verification/screenshots/step1_customer_fa.png")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Choose Digital Manometer
        print("Step 2 (FA): Selecting Digital Manometer...")
        await page.click("button[id='tool-card-Digital-Manometer']")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Producer
        print("Step 3 (FA): Selecting Fluke...")
        await page.click(".producer-badge-btn:has-text('Fluke')")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Tool Specs in FA
        print("Step 4 (FA): Tool specs...")
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.5)

        # Calibration Table in FA
        print("Step 5 (FA): Calibration table in FA...")
        await page.fill("input[id='uuc_0']", "0")
        await page.fill("input[id='ref_rising_0']", "0.0")
        await page.fill("input[id='ref_falling_0']", "0.0")
        await page.screenshot(path="/home/jules/verification/screenshots/step5_table_fa.png")
        await page.click("button[id='submit-btn']")
        await asyncio.sleep(1.0)

        # Success in FA
        await page.screenshot(path="/home/jules/verification/screenshots/success_fa.png")

        # Submissions page
        print("Navigating to submissions page...")
        await page.goto("http://127.0.0.1:8000/submissions")
        await asyncio.sleep(0.8)
        await page.screenshot(path="/home/jules/verification/screenshots/submissions_fa.png")

        # Test CSV download
        print("Testing CSV download...")
        async with page.expect_download() as download_info:
            await page.click("text=دانلود خروجی CSV")
        download = await download_info.value
        path = await download.path()
        print(f"CSV downloaded: {path}")

        # Switch to EN on submissions
        await page.click("text=EN")
        await asyncio.sleep(0.8)
        await page.screenshot(path="/home/jules/verification/screenshots/submissions_en.png")

        # Save main screenshot for frontend_verification_complete
        await page.goto("http://127.0.0.1:8000/parameters")
        await asyncio.sleep(0.5)
        # Advance to step 5 to screenshot the new calibration table in wizard
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)
        await page.click("button[id='next-btn']")
        await asyncio.sleep(0.3)
        await page.screenshot(path="/home/jules/verification/screenshots/verification_main.png")

        await context.close()
        await browser.close()
        print("All Playwright verification tests passed!")

if __name__ == "__main__":
    asyncio.run(run_verification())
