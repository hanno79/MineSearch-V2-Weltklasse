"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Test Direct HTML Insert - Browser HTML Parsing Issue
"""

import asyncio
from playwright.async_api import async_playwright

async def test_direct_html_insert():
    """Test directly inserting the problematic HTML to see if browser parses it"""
    
    # Get the raw HTML from API
    import subprocess
    result = subprocess.run([
        'curl', '-X', 'POST', 
        '-F', 'csv_file=@/app/minesearch_v2/backend/csv/test_mines_quebec.csv',
        'http://localhost:8000/api/batch/upload-csv'
    ], capture_output=True, text=True)
    
    raw_html = result.stdout
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Enable console logging
            def handle_console(msg):
                print(f"[CONSOLE {msg.type}] {msg.text}")
            page.on('console', handle_console)
            
            # Create a minimal test page
            await page.goto('data:text/html,<html><body><div id="csv-info"></div></body></html>')
            
            print("🔍 Direct HTML Insert Test...")
            print(f"📄 Raw HTML length: {len(raw_html)} chars")
            print(f"📄 Session_id in raw HTML: {'session_id' in raw_html}")
            
            # Insert the HTML directly
            await page.evaluate(f'''
                document.getElementById('csv-info').innerHTML = `{raw_html}`;
                console.log('HTML inserted directly into #csv-info');
            ''')
            
            # Check if inputs are parsed
            await page.wait_for_timeout(1000)
            
            session_inputs = page.locator('input[name="session_id"]')
            session_count = await session_inputs.count()
            print(f"📊 Session inputs after direct insert: {session_count}")
            
            if session_count > 0:
                session_value = await session_inputs.get_attribute('value')
                print(f"✅ Session ID value: {session_value}")
            else:
                print("❌ No session inputs found even with direct HTML insert")
                
                # Try to understand what's in the DOM
                csv_info_content = await page.locator('#csv-info').inner_html()
                print(f"📄 DOM content length: {len(csv_info_content)}")
                print(f"📄 'session_id' in DOM: {'session_id' in csv_info_content}")
                print(f"📄 '<input' in DOM: {'<input' in csv_info_content}")
                
                # Check for any inputs at all
                all_inputs = page.locator('input')
                all_input_count = await all_inputs.count()
                print(f"📊 Total inputs in page: {all_input_count}")
            
            await page.screenshot(path='/app/minesearch_v2/test_direct_html_insert.png')
            await browser.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_html_insert())