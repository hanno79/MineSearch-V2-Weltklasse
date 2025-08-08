"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Test Session Input Isolation - Find the specific parsing issue
"""

import asyncio
from playwright.async_api import async_playwright

async def test_session_input_isolation():
    """Test isolated session_id input parsing"""
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Enable console logging
            def handle_console(msg):
                print(f"[CONSOLE {msg.type}] {msg.text}")
            page.on('console', handle_console)
            
            print("🔍 Testing Isolated Session Input Parsing...")
            
            # Test 1: Simple session input
            await page.goto('data:text/html,<html><body><div id="test1"></div></body></html>')
            await page.evaluate('''
                document.getElementById('test1').innerHTML = '<input type="hidden" name="session_id" value="test123">';
                console.log('Test 1: Simple session input inserted');
            ''')
            
            test1_inputs = page.locator('#test1 input[name="session_id"]')
            test1_count = await test1_inputs.count()
            print(f"📊 Test 1 - Simple session input: {test1_count}")
            
            # Test 2: Session input inside form
            await page.evaluate('''
                document.getElementById('test1').innerHTML = '<form><input type="hidden" name="session_id" value="test123"></form>';
                console.log('Test 2: Session input inside form inserted');
            ''')
            
            test2_inputs = page.locator('#test1 input[name="session_id"]')
            test2_count = await test2_inputs.count()
            print(f"📊 Test 2 - Session input in form: {test2_count}")
            
            # Test 3: Check if the exact HTML from our API works
            test_html = '''
            <form id="batch-form" data-session-id="test-session-id">
                <input type="hidden" name="session_id" value="test-session-id">
                <input type="hidden" name="selected_models" value="">
                <button type="submit">Test</button>
            </form>
            '''
            
            await page.evaluate(f'''
                document.getElementById('test1').innerHTML = `{test_html}`;
                console.log('Test 3: Full form HTML inserted');
            ''')
            
            test3_inputs = page.locator('#test1 input[name="session_id"]')
            test3_count = await test3_inputs.count()
            print(f"📊 Test 3 - Full form HTML: {test3_count}")
            
            if test3_count > 0:
                test3_value = await test3_inputs.get_attribute('value')
                print(f"✅ Test 3 - Session value: {test3_value}")
            
            # Test 4: Let's try with exact problem HTML from our API
            import subprocess
            result = subprocess.run([
                'curl', '-X', 'POST', 
                '-F', 'csv_file=@/app/minesearch_v2/backend/csv/test_mines_quebec.csv',
                'http://localhost:8000/api/batch/upload-csv'
            ], capture_output=True, text=True)
            
            api_html = result.stdout
            
            # Let's just test the form part
            form_start = api_html.find('<form id="batch-form"')
            form_end = api_html.find('</form>') + 7
            
            if form_start >= 0 and form_end > form_start:
                form_html = api_html[form_start:form_end]
                print(f"📄 Extracted form HTML length: {len(form_html)}")
                
                await page.evaluate(f'''
                    try {{
                        document.getElementById('test1').innerHTML = `{form_html}`;
                        console.log('Test 4: API form HTML inserted successfully');
                    }} catch (e) {{
                        console.error('Test 4: Error inserting API form HTML:', e);
                    }}
                ''')
                
                test4_inputs = page.locator('#test1 input[name="session_id"]')
                test4_count = await test4_inputs.count()
                print(f"📊 Test 4 - API form HTML: {test4_count}")
                
                if test4_count > 0:
                    test4_value = await test4_inputs.get_attribute('value')
                    print(f"✅ Test 4 - Session value: {test4_value}")
                else:
                    print("❌ Test 4 - No session input found")
                    # Let's see what we actually got
                    actual_html = await page.locator('#test1').inner_html()
                    print(f"📄 Actual HTML (first 200 chars): {actual_html[:200]}...")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_session_input_isolation())