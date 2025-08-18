#!/usr/bin/env python3
"""
Debug what the frontend actually sees from the statistics API
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_frontend_api():
    """Debug what the frontend sees"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to statistics tab
            await page.goto("http://localhost:8000/static/index.html#statistics")
            await page.wait_for_selector('[data-tab="statistics"]', timeout=10000)
            await page.click('[data-tab="statistics"]')
            
            # Wait for API call and intercept the response
            print("🔍 Waiting for statistics API call...")
            
            # Listen for the API request
            async def handle_response(response):
                if "/api/statistics/models/comprehensive" in response.url:
                    return response
                return None
            
            # Wait for page to make the API call
            await page.wait_for_timeout(5000)
            
            # Make a direct API call to get the data
            import requests
            response = requests.get("http://localhost:8000/api/statistics/models/comprehensive")
            response_data = response.json()
            
            # Data is already loaded from requests call above
            
            print(f"📊 API Response Summary:")
            print(f"  Success: {response_data.get('success')}")
            print(f"  Data keys: {list(response_data.get('data', {}).keys())}")
            
            if 'models' in response_data.get('data', {}):
                models = response_data['data']['models']
                print(f"  Total models: {len(models)}")
                
                # Count by status
                tested = [m for m in models if m.get('status') != 'available']
                available = [m for m in models if m.get('status') == 'available']
                
                print(f"  Tested models: {len(tested)}")
                print(f"  Available models: {len(available)}")
                
                # Show first few available models
                if available:
                    print(f"\n📋 First 5 available models:")
                    for model in available[:5]:
                        print(f"    - {model['model_id']} (Status: {model.get('status', 'N/A')})")
                
                # Check what frontend console shows
                print(f"\n🔍 Checking frontend console logs...")
                
                # Wait a bit for frontend processing
                await page.wait_for_timeout(3000)
                
                # Check if the models are being processed correctly
                console_logs = []
                page.on("console", lambda msg: console_logs.append(msg.text))
                
                # Trigger a reload to see console
                await page.reload()
                await page.wait_for_selector('[data-tab="statistics"]', timeout=10000)
                await page.click('[data-tab="statistics"]')
                await page.wait_for_timeout(5000)
                
                # Show relevant console logs
                stats_logs = [log for log in console_logs if 'STATISTICS' in log or 'DISPLAY' in log]
                if stats_logs:
                    print(f"\n📝 Frontend logs:")
                    for log in stats_logs[-10:]:  # Last 10 relevant logs
                        print(f"    {log}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_frontend_api())