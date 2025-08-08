"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Finaler Test nach Container-ID Fix
"""

import asyncio
from playwright.async_api import async_playwright

async def test_container_fix():
    """Testet ob der Container-Fix funktioniert"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type.upper()}: {msg.text}"))
        
        try:
            print("🔧 CONTAINER FIX TEST")
            print("=" * 30)
            
            await page.goto('http://localhost:8000', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Aktiviere Statistics Tab
            stats_label = await page.query_selector('label[for="method_statistics"]')
            await stats_label.click()
            await page.wait_for_timeout(1000)
            
            # Prüfe Container-Existenz
            model_stats_container = await page.query_selector('#model-statistics-table-container')
            enhanced_stats_container = await page.query_selector('#enhanced-statistics-table-container')
            
            print(f"model-statistics-table-container exists: {bool(model_stats_container)}")
            print(f"enhanced-statistics-table-container exists: {bool(enhanced_stats_container)}")
            
            if model_stats_container:
                container_html = await model_stats_container.inner_html()
                print(f"Container HTML length: {len(container_html)}")
                print(f"Container content preview: {container_html[:200]}...")
                
                # Klick auf Statistiken laden
                load_btn = await page.query_selector('#statistics_form button:has-text("Statistiken laden")')
                if load_btn:
                    await load_btn.click()
                    print("✅ Statistiken laden Button geklickt")
                    
                    await page.wait_for_timeout(10000)
                    
                    # Check updated content
                    new_html = await model_stats_container.inner_html()
                    has_table = '<table' in new_html
                    has_data = '<tbody>' in new_html and '<tr>' in new_html
                    
                    print(f"After click - Has table: {has_table}")
                    print(f"After click - Has data: {has_data}")
                    print(f"After click - HTML length: {len(new_html)}")
                    
                    await page.screenshot(path='container_fix_result.png')
                    print("📸 Screenshot: container_fix_result.png")
                
            # Console logs
            errors = [log for log in console_logs if 'ERROR:' in log]
            success = [log for log in console_logs if 'success' in log.lower() or '✅' in log]
            
            print(f"\nConsole - Errors: {len(errors)}")
            print(f"Console - Success: {len(success)}")
            
            for error in errors:
                print(f"❌ {error}")
                
            for suc in success[-3:]:
                print(f"✅ {suc}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_container_fix())