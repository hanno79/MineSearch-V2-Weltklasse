"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Direct Progress Test - Simple CSV upload and progress check
"""

import asyncio
import tempfile
import os
from playwright.async_api import async_playwright

async def test_progress_direct():
    """Direct test of progress functionality after fixing HTMX syntax errors"""
    
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
            
            # Monitor console for errors
            errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    errors.append(msg.text)
                    print(f"[ERROR] {msg.text}")
                elif 'progress' in msg.text.lower() or 'batch' in msg.text.lower():
                    print(f"[PROGRESS] {msg.text}")
            
            page.on('console', handle_console)
            
            print("🚀 Testing direct progress functionality...")
            
            # Navigate to site
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
            
            # Check if form was created without errors
            form_check = await page.evaluate('''
                const form = document.getElementById('batch-form');
                return {
                    formExists: !!form,
                    sessionId: form ? form.querySelector('input[name="session_id"]')?.value : null,
                    scriptErrors: document.querySelectorAll('script').length
                };
            ''')
            
            print(f"Form check: {form_check}")
            
            # Select a model
            print("🎯 Selecting model...")
            model_checkbox = page.locator('input[value="openrouter:deepseek-free"]').first
            if await model_checkbox.count() > 0:
                await model_checkbox.check()
                await page.wait_for_timeout(1000)
            
            # Check if progress functions are available
            progress_functions = await page.evaluate('''
                ({
                    showEnhanced: typeof window.showEnhancedLoadingMessage,
                    hideEnhanced: typeof window.hideEnhancedLoadingMessage,
                    progressTracker: typeof window.progressTracker
                })
            ''')
            print(f"Progress functions: {progress_functions}")
            
            # Try clicking search button
            print("🚀 Testing batch search...")
            batch_button = page.locator('#batch-search-start')
            if await batch_button.count() > 0:
                await batch_button.click()
                
                # Monitor for 10 seconds
                for i in range(10):
                    await page.wait_for_timeout(1000)
                    
                    # Check results container content
                    results_content = await page.locator('#results').inner_html()
                    if 'progress' in results_content.lower() or 'loading' in results_content.lower():
                        print(f"✅ Progress content detected at second {i+1}")
                        if len(results_content) > 100:
                            print(f"Results preview: {results_content[:200]}...")
                        break
                    elif i == 5 and len(results_content) > 50:
                        print(f"Results at 5s: {results_content[:200]}...")
                        
            # Final error check
            if errors:
                print(f"\n❌ JavaScript errors found: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"  - {error}")
            else:
                print("✅ No JavaScript errors detected")
            
            await page.screenshot(path='/app/minesearch_v2/test_progress_direct.png')
            await browser.close()
            
    finally:
        os.unlink(csv_path)
        print("✅ Direct progress test completed")

if __name__ == "__main__":
    asyncio.run(test_progress_direct())