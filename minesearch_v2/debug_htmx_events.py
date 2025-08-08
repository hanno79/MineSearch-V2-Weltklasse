"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Debug HTMX Events - Check if HTMX events are triggering
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

async def debug_htmx_events():
    """Debug HTMX events to see if they trigger progress loading"""
    
    test_csv_content = """Name;Country;Region
Eleonore Mine;Canada;Quebec
Canadian Malartic;Canada;Quebec"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv_content)
        csv_file_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Monitor console messages
            def handle_console(msg):
                print(f"[{msg.type.upper()}] {msg.text}")
            page.on('console', handle_console)
            
            print("🔍 Debug HTMX Events Test...")
            
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Add HTMX event listeners for debugging
            await page.evaluate('''
                // Add global HTMX event listeners for debugging
                document.addEventListener('htmx:beforeRequest', function(evt) {
                    console.log('🚀 [HTMX-DEBUG] beforeRequest:', evt.detail.requestConfig.path);
                    if (evt.detail.requestConfig.path === '/api/batch-search') {
                        console.log('🎯 [HTMX-DEBUG] Batch search beforeRequest triggered!');
                        console.log('🔍 [HTMX-DEBUG] Form element:', evt.target);
                        console.log('🔍 [HTMX-DEBUG] Event details:', evt.detail);
                    }
                });
                
                document.addEventListener('htmx:afterRequest', function(evt) {
                    console.log('✅ [HTMX-DEBUG] afterRequest:', evt.detail.requestConfig.path);
                });
                
                document.addEventListener('htmx:responseError', function(evt) {
                    console.log('❌ [HTMX-DEBUG] responseError:', evt.detail.requestConfig.path);
                });
                
                document.addEventListener('htmx:configRequest', function(evt) {
                    console.log('⚙️ [HTMX-DEBUG] configRequest:', evt.detail.path);
                });
                
                console.log('🔧 [HTMX-DEBUG] Global HTMX event listeners added');
            ''')
            
            # Upload CSV
            print("📤 Uploading CSV...")
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
            
            await page.wait_for_timeout(1000)
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_file_path)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            await page.wait_for_timeout(3000)
            
            # Select model
            print("🎯 Selecting model...")
            model_checkbox = page.locator('input[value="openrouter:deepseek-free"]').first
            if await model_checkbox.count() > 0:
                await model_checkbox.check()
            
            # Check batch form state before clicking
            batch_form_info = await page.evaluate('''
                const form = document.getElementById('batch-form');
                if (form) {
                    const sessionInput = form.querySelector('input[name="session_id"]');
                    const modelsInput = form.querySelector('input[name="selected_models"]');
                    return {
                        formExists: true,
                        sessionId: sessionInput ? sessionInput.value : 'not found',
                        selectedModels: modelsInput ? modelsInput.value : 'not found',
                        formHTML: form.outerHTML.substring(0, 500)
                    };
                } else {
                    return {formExists: false};
                }
            ''')
            print(f"Batch form info: {batch_form_info}")
            
            # Start batch search
            print("🚀 Clicking batch search button...")
            batch_start_button = page.locator('#batch-search-start')
            if await batch_start_button.count() > 0:
                await batch_start_button.click()
                
                # Wait for HTMX events
                print("⏳ Waiting for HTMX events to trigger...")
                await page.wait_for_timeout(5000)
                
                # Check if any progress elements appeared
                progress_check = await page.evaluate('''
                    ({
                        progressContainers: document.querySelectorAll('.progress-container').length,
                        enhancedLoading: document.querySelectorAll('.enhanced-loading-container').length,
                        loadingSpinners: document.querySelectorAll('.loading-spinner').length,
                        resultsHTML: document.getElementById('results').innerHTML.substring(0, 300)
                    })
                ''')
                print(f"Progress check after click: {progress_check}")
            
            await page.screenshot(path='/app/minesearch_v2/debug_htmx_events.png')
            await browser.close()
            
    finally:
        os.unlink(csv_file_path)
        print("✅ HTMX events debug completed")

if __name__ == "__main__":
    asyncio.run(debug_htmx_events())