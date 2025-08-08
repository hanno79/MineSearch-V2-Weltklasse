"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Debug CSV-Info Content - Was passiert mit dem HTML?
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

async def debug_csv_info_content():
    """Debug what happens to CSV upload HTML content in #csv-info"""
    
    test_csv_content = """Name;Country;Region;Eigentümer
Test Mine;Canada;Quebec;Test Owner"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv_content)
        csv_file_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Enable console logging
            def handle_console(msg):
                print(f"[CONSOLE {msg.type}] {msg.text}")
            page.on('console', handle_console)
            
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            print("🔍 Checking #csv-info BEFORE upload...")
            csv_info_before = page.locator('#csv-info')
            if await csv_info_before.count() > 0:
                content_before = await csv_info_before.inner_html()
                print(f"📄 #csv-info BEFORE: '{content_before[:100]}...'")
            else:
                print("❌ #csv-info element not found BEFORE upload")
            
            # Upload CSV
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
            
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_file_path)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            
            # Wait for upload
            await page.wait_for_timeout(5000)
            
            print("\n🔍 Checking #csv-info AFTER upload...")
            csv_info_after = page.locator('#csv-info')
            if await csv_info_after.count() > 0:
                content_after = await csv_info_after.inner_html()
                print(f"📄 #csv-info AFTER length: {len(content_after)} chars")
                print(f"📄 #csv-info AFTER preview: '{content_after[:200]}...'")
                
                # Check specifically for batch-form
                if 'batch-form' in content_after:
                    print("✅ batch-form found in #csv-info")
                    
                    # Check for session_id in csv-info
                    if 'session_id' in content_after:
                        print("✅ session_id found in #csv-info content")
                        
                        # Find all session_id inputs in csv-info
                        session_inputs_in_csv_info = csv_info_after.locator('input[name="session_id"]')
                        session_count = await session_inputs_in_csv_info.count()
                        print(f"📊 Session inputs in #csv-info: {session_count}")
                        
                        if session_count > 0:
                            session_value = await session_inputs_in_csv_info.get_attribute('value')
                            print(f"✅ Session ID in #csv-info: {session_value}")
                        else:
                            print("❌ No session input elements in #csv-info despite HTML containing session_id")
                    else:
                        print("❌ session_id NOT found in #csv-info content")
                else:
                    print("❌ batch-form NOT found in #csv-info")
            else:
                print("❌ #csv-info element not found AFTER upload")
            
            # Also check entire page for any session_id inputs
            print("\n🔍 Checking entire page for session_id inputs...")
            all_session_inputs = page.locator('input[name="session_id"]')
            total_session_count = await all_session_inputs.count()
            print(f"📊 Total session inputs on page: {total_session_count}")
            
            for i in range(total_session_count):
                input_element = all_session_inputs.nth(i)
                parent_info = await input_element.evaluate('el => el.parentElement.id || el.parentElement.className || "no-parent-id"')
                session_value = await input_element.get_attribute('value')
                print(f"  Input {i+1}: parent='{parent_info}', value='{session_value}'")
            
            await page.screenshot(path='/app/minesearch_v2/debug_csv_info_content.png')
            await browser.close()
            
    finally:
        os.unlink(csv_file_path)

if __name__ == "__main__":
    asyncio.run(debug_csv_info_content())