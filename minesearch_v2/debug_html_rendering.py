"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Debug HTML-Rendering Problem - Session-ID im Browser vs. API
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

async def debug_html_rendering():
    """Debug HTML rendering difference between browser and direct API call"""
    
    test_csv_content = """Name;Country;Region;Eigentümer
Test Mine;Canada;Quebec;Test Owner"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv_content)
        csv_file_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture the actual HTML content after CSV upload
            html_content = None
            
            def handle_response(response):
                nonlocal html_content
                if 'batch/upload-csv' in response.url and response.status == 200:
                    # This will be called when CSV upload response is received
                    print(f"📨 CSV Upload Response: {response.status}")
            
            page.on('response', handle_response)
            
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Upload CSV
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
            
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_file_path)
            
            # Intercept the upload response
            async def handle_upload_response(response):
                if 'batch/upload-csv' in response.url:
                    html_content = await response.text()
                    print(f"📄 Raw HTML Response Length: {len(html_content)} chars")
                    
                    # Check if session_id is in the raw HTML
                    if 'session_id' in html_content:
                        print("✅ session_id found in raw HTML response")
                        # Extract session_id value
                        import re
                        match = re.search(r'name="session_id" value="([^"]+)"', html_content)
                        if match:
                            session_id = match.group(1)
                            print(f"✅ Extracted session_id: {session_id}")
                        else:
                            print("❌ session_id attribute found but no value extracted")
                    else:
                        print("❌ session_id NOT found in raw HTML response")
                        # Show first 500 chars of HTML for debugging
                        print(f"📄 HTML Preview: {html_content[:500]}...")
            
            page.on('response', handle_upload_response)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            
            # Wait for upload response
            await page.wait_for_timeout(5000)
            
            # Now check what's actually in the DOM
            print("\n🔍 Checking DOM content after upload...")
            
            # Get the HTML content that was inserted into the DOM
            results_div = page.locator('#results')
            if await results_div.count() > 0:
                dom_html = await results_div.inner_html()
                print(f"📋 DOM Content Length: {len(dom_html)} chars")
                
                if 'session_id' in dom_html:
                    print("✅ session_id found in DOM")
                    # Extract session_id from DOM
                    session_inputs = page.locator('input[name="session_id"]')
                    session_count = await session_inputs.count()
                    print(f"📊 Session input elements found: {session_count}")
                    
                    if session_count > 0:
                        session_value = await session_inputs.get_attribute('value')
                        print(f"✅ DOM session_id value: {session_value}")
                    else:
                        print("❌ session_id in HTML but no input elements found")
                else:
                    print("❌ session_id NOT found in DOM")
                    print(f"📄 DOM Preview: {dom_html[:500]}...")
            else:
                print("❌ No #results div found")
            
            # Take a screenshot for visual debugging
            await page.screenshot(path='/app/minesearch_v2/debug_html_rendering.png')
            
            await browser.close()
            
    finally:
        os.unlink(csv_file_path)

if __name__ == "__main__":
    asyncio.run(debug_html_rendering())