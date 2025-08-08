"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Manual Progress Test - Simple test to check if progress system works
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

async def manual_test_progress():
    """Manual test - just check if the system works without complex evaluation"""
    
    test_csv = """Name;Country;Region
Eleonore Mine;Canada;Quebec
Canadian Malartic;Canada;Quebec"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv)
        csv_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Just monitor console
            def handle_console(msg):
                if 'BATCH' in msg.text or 'progress' in msg.text.lower() or 'error' in msg.text.lower():
                    print(f"[{msg.type.upper()}] {msg.text}")
            
            page.on('console', handle_console)
            
            print("🚀 Manual progress test...")
            
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Upload CSV
            print("📤 Uploading CSV...")
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
                await page.wait_for_timeout(1000)
            
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_path)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            await page.wait_for_timeout(3000)
            
            # Select model
            print("🎯 Selecting model...")
            model_checkbox = page.locator('input[value="openrouter:deepseek-free"]').first
            if await model_checkbox.count() > 0:
                await model_checkbox.check()
                await page.wait_for_timeout(1000)
            
            # Check if batch form exists
            batch_form_exists = await page.locator('#batch-form').count() > 0
            print(f"Batch form exists: {batch_form_exists}")
            
            # Try clicking search
            print("🚀 Clicking batch search...")
            batch_button = page.locator('#batch-search-start')
            if await batch_button.count() > 0:
                await batch_button.click()
                
                # Wait and watch for 15 seconds
                print("⏳ Watching for 15 seconds...")
                for i in range(15):
                    await page.wait_for_timeout(1000)
                    
                    # Check results element content
                    results_content = await page.locator('#results').inner_html()
                    if i == 0:
                        print(f"Initial results length: {len(results_content)}")
                    elif i == 5:
                        print(f"Results at 5s: {len(results_content)} chars")
                        if 'progress' in results_content.lower():
                            print("✅ Progress detected!")
                    elif i == 10:
                        print(f"Results at 10s: {len(results_content)} chars")
                    
                    # Check for progress containers
                    progress_count = await page.locator('.progress-container').count()
                    enhanced_count = await page.locator('.enhanced-loading-container').count()
                    
                    if progress_count > 0 or enhanced_count > 0:
                        print(f"📊 Progress elements found: containers={progress_count}, enhanced={enhanced_count}")
                        break
            
            await page.screenshot(path='/app/minesearch_v2/manual_test_progress.png')
            await browser.close()
            
    finally:
        os.unlink(csv_path)
        print("✅ Manual test completed")

if __name__ == "__main__":
    asyncio.run(manual_test_progress())