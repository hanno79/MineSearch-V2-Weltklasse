"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Debug Frontend 422 Fehler - Unterschied Browser vs. API
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

async def debug_frontend_422_error():
    """Debug the 422 error that occurs in browser but not in direct API calls"""
    
    # Create test CSV with multiple entries (similar to the large one)
    test_csv_content = """Name;Country;Region;Eigentümer
Lac Expanse;Canada;Quebec;Unknown Owner
Mine Test 1;Canada;Quebec;Test Owner
Mine Test 2;Canada;Quebec;Another Owner"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv_content)
        csv_file_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            
            # Enable console logging to catch frontend errors
            page = await context.new_page()
            
            # Capture console messages
            console_messages = []
            def handle_console(msg):
                console_messages.append(f"[{msg.type}] {msg.text}")
            page.on('console', handle_console)
            
            # Capture network requests
            network_requests = []
            def handle_request(request):
                if 'batch' in request.url:
                    network_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'post_data': request.post_data if request.method == 'POST' else None
                    })
            page.on('request', handle_request)
            
            # Capture network responses
            network_responses = []
            def handle_response(response):
                if 'batch' in response.url:
                    network_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers)
                    })
            page.on('response', handle_response)
            
            print("🔍 Testing Frontend 422 Error...")
            
            # Navigate and upload CSV
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Upload CSV
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
            
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_file_path)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            
            # Wait for upload response
            await page.wait_for_timeout(3000)
            
            # Check session_id in hidden input
            session_inputs = page.locator('input[name="session_id"]')
            session_count = await session_inputs.count()
            print(f"📊 Session inputs found: {session_count}")
            
            if session_count > 0:
                session_value = await session_inputs.get_attribute('value')
                print(f"✅ Session ID: {session_value}")
            else:
                print("❌ No session_id input found!")
                return
            
            # Select model
            model_checkbox = page.locator('input[value="openrouter:deepseek-free"]').first
            if await model_checkbox.count() > 0:
                await model_checkbox.check()
                print("✅ Model selected")
            
            # Click batch search button and capture the form data
            batch_button = page.locator('#batch-search-start')
            if await batch_button.count() > 0:
                print("🚀 Clicking batch search button...")
                
                # Capture the form before submission
                form = page.locator('#batch-form')
                form_data = await form.evaluate('''
                    (form) => {
                        const formData = new FormData(form);
                        const data = {};
                        for (let [key, value] of formData.entries()) {
                            data[key] = value;
                        }
                        return data;
                    }
                ''')
                print(f"📋 Form data being sent: {form_data}")
                
                await batch_button.click()
                
                # Wait for response
                await page.wait_for_timeout(5000)
                
                # Check for error messages
                error_messages = page.locator('.error, [class*="error"], text*="422", text*="Unprocessable"')
                error_count = await error_messages.count()
                
                if error_count > 0:
                    for i in range(error_count):
                        error_text = await error_messages.nth(i).text_content()
                        print(f"❌ Error {i+1}: {error_text}")
                else:
                    print("✅ No errors found in DOM")
                
                # Print captured network activity
                print(f"\n📡 Network Requests: {len(network_requests)}")
                for req in network_requests:
                    print(f"  {req['method']} {req['url']}")
                    if req['post_data']:
                        print(f"  POST data length: {len(req['post_data'])} chars")
                
                print(f"\n📡 Network Responses: {len(network_responses)}")
                for resp in network_responses:
                    print(f"  {resp['status']} {resp['url']}")
                
                # Print console messages
                print(f"\n🖥️ Console Messages: {len(console_messages)}")
                for msg in console_messages:
                    print(f"  {msg}")
            
            await page.screenshot(path='/app/minesearch_v2/debug_422_error.png')
            await browser.close()
            
    finally:
        os.unlink(csv_file_path)
        print("✅ Debug completed")

if __name__ == "__main__":
    asyncio.run(debug_frontend_422_error())