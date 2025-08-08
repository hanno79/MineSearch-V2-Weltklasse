"""
Author: rahn
Datum: 05.08.2025
Version: 1.0
Beschreibung: Test Progress Tracking Workflow - Complete CSV Upload + Batch Search mit Progress-Bar
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import os
import json

async def test_progress_workflow():
    """Test complete progress tracking workflow"""
    
    test_csv_content = """Name;Country;Region;Eigentümer
Eleonore Mine;Canada;Quebec;Newmont
Canadian Malartic;Canada;Quebec;Agnico Eagle"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_csv_content)
        csv_file_path = f.name
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Enable console logging for progress tracking
            def handle_console(msg):
                if any(keyword in msg.text for keyword in ['PROGRESS', 'Enhanced Loading', 'WebSocket', 'Progress session', 'batch']):
                    print(f"[CONSOLE {msg.type}] {msg.text}")
            page.on('console', handle_console)
            
            print("🚀 Progress Workflow Test: CSV Upload + Batch Search mit Progress-Bar")
            
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Step 1: Upload CSV
            print("📤 Step 1: Uploading CSV...")
            csv_tab = page.locator('[data-tab="csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
                await page.wait_for_timeout(1000)
            
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(csv_file_path)
            
            upload_button = page.locator('button:has-text("CSV hochladen")')
            await upload_button.click()
            
            await page.wait_for_timeout(3000)
            
            # Step 2: Verify CSV upload and batch form
            print("🔍 Step 2: Verifying CSV upload and batch form...")
            
            batch_form = page.locator('#batch-form')
            batch_form_count = await batch_form.count()
            print(f"Batch form found: {batch_form_count > 0}")
            
            if batch_form_count > 0:
                session_input = batch_form.locator('input[name="session_id"]')
                session_value = await session_input.get_attribute('value')
                print(f"✅ Session ID: {session_value}")
                
                # Step 3: Select a model
                print("🎯 Step 3: Selecting model...")
                model_checkbox = page.locator('input[value="openrouter:deepseek-free"]').first
                if await model_checkbox.count() > 0:
                    await model_checkbox.check()
                    print("✅ Model selected: openrouter:deepseek-free")
                
                # Step 4: Start batch search and monitor progress
                print("🚀 Step 4: Starting batch search...")
                
                # Check if progress tracking is loaded
                progress_check = await page.evaluate('''
                    window.progressTracker && window.showEnhancedLoadingMessage
                ''')
                print(f"Progress tracking system loaded: {progress_check}")
                
                # Start batch search
                batch_start_button = page.locator('#batch-search-start')
                if await batch_start_button.count() > 0:
                    print("📊 Clicking batch search button and monitoring progress...")
                    await batch_start_button.click()
                    
                    # Monitor for progress bar appearance
                    print("⏳ Waiting for progress bar to appear...")
                    await page.wait_for_timeout(2000)
                    
                    # Check for progress elements
                    progress_container = page.locator('.progress-container')
                    progress_bar = page.locator('.progress-fill')
                    enhanced_loading = page.locator('.enhanced-loading-container')
                    
                    progress_container_count = await progress_container.count()
                    progress_bar_count = await progress_bar.count()
                    enhanced_loading_count = await enhanced_loading.count()
                    
                    print(f"📊 Progress elements found:")
                    print(f"  - Progress container: {progress_container_count}")
                    print(f"  - Progress bar: {progress_bar_count}")
                    print(f"  - Enhanced loading: {enhanced_loading_count}")
                    
                    if progress_container_count > 0:
                        print("✅ Progress container found!")
                        
                        # Monitor progress for a few seconds
                        for i in range(10):
                            await page.wait_for_timeout(1000)
                            
                            # Check progress bar value if visible
                            if await progress_bar.count() > 0:
                                progress_text = await progress_bar.locator('span').text_content()
                                print(f"Progress: {progress_text}")
                            
                            # Check for completion
                            results = page.locator('#results')
                            results_content = await results.inner_html()
                            if 'Eleonore Mine' in results_content or 'Canadian Malartic' in results_content:
                                print("✅ Search completed with results!")
                                break
                    else:
                        print("❌ No progress container found - investigating...")
                        
                        # Check what elements exist in #results
                        results_html = await page.locator('#results').inner_html()
                        print(f"Results HTML length: {len(results_html)}")
                        
                        if 'progress' in results_html.lower():
                            print("Progress-related content found in results")
                        
                        if 'enhanced-loading' in results_html:
                            print("Enhanced loading HTML found")
                    
                    # Wait for final results
                    print("⏳ Waiting for final results...")
                    await page.wait_for_timeout(15000)
                    
                    # Check final state
                    final_results = await page.locator('#results').inner_html()
                    if len(final_results) > 1000:
                        print(f"✅ Final results received: {len(final_results)} characters")
                        
                        if 'Eleonore Mine' in final_results:
                            print("✅ Eleonore Mine found in results")
                        if 'Canadian Malartic' in final_results:
                            print("✅ Canadian Malartic found in results")
                    else:
                        print(f"⚠️ Minimal results: {len(final_results)} characters")
                
                else:
                    print("❌ Batch search button not found")
            else:
                print("❌ No batch form found after CSV upload")
            
            await page.screenshot(path='/app/minesearch_v2/test_progress_workflow.png')
            await browser.close()
            
    finally:
        os.unlink(csv_file_path)
        print("✅ Progress workflow test completed")

if __name__ == "__main__":
    asyncio.run(test_progress_workflow())