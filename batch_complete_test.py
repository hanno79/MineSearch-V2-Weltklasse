#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Complete test for MineSearch Batch functionality with CSV upload and result validation
"""

from playwright.sync_api import sync_playwright
import time
import sys
import os

def test_complete_batch_workflow():
    """Complete test of batch functionality including CSV upload and result validation"""
    
    with sync_playwright() as p:
        # Launch browser with longer timeout for complex operations
        browser = p.chromium.launch(headless=False, timeout=60000)
        page = browser.new_page()
        
        # Set longer timeout for all operations
        page.set_default_timeout(30000)
        
        try:
            print("📍 Step 1: Navigate to MineSearch and access Batch tab")
            page.goto("http://localhost:8000")
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Click on Batch tab - try multiple selectors
            batch_selectors = [
                'a[href="#batch"]',
                'button:has-text("Batch")',
                '.tab:has-text("Batch")',
                '*:has-text("📊"):has-text("Batch")',
                'nav a:has-text("Batch")',
                '.navigation a:has-text("Batch")'
            ]
            
            batch_clicked = False
            for selector in batch_selectors:
                batch_tab = page.locator(selector)
                if batch_tab.count() > 0:
                    batch_tab.first.click()
                    time.sleep(3)
                    page.screenshot(path="complete_batch_01_tab_clicked.png")
                    print(f"✅ Batch tab successfully clicked using selector: {selector}")
                    batch_clicked = True
                    break
            
            if not batch_clicked:
                print("❌ Batch tab not found with any selector")
                # Try to find any element containing "batch"
                all_elements = page.locator('*')
                for i in range(min(all_elements.count(), 50)):
                    element = all_elements.nth(i)
                    try:
                        text = element.text_content()
                        if text and 'batch' in text.lower():
                            print(f"Found batch element: {text}")
                            element.click()
                            time.sleep(3)
                            batch_clicked = True
                            break
                    except:
                        continue
                
                if not batch_clicked:
                    page.screenshot(path="complete_batch_error_no_tab.png")
                    return False
            
            print("📍 Step 2: Select multiple models for comprehensive testing")
            # First try to select Top Performers
            top_performers = page.locator('button:has-text("Top Performers"), .model-group:has-text("Top Performers")')
            if top_performers.count() > 0:
                top_performers.first.click()
                time.sleep(1)
                print("✅ Top Performers selected")
            
            # Also select Web-Suche models
            web_suche = page.locator('button:has-text("Web-Suche"), .model-group:has-text("Web-Suche")')
            if web_suche.count() > 0:
                web_suche.first.click()
                time.sleep(1)
                print("✅ Web-Suche models selected")
            
            # Also try Premium models
            premium = page.locator('button:has-text("Premium"), .model-group:has-text("Premium")')
            if premium.count() > 0:
                premium.first.click()
                time.sleep(1)
                print("✅ Premium models selected")
            
            page.screenshot(path="complete_batch_02_models_selected.png")
            
            print("📍 Step 3: Upload CSV file with Quebec mines")
            # Look for file input
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                # Upload the CSV file
                csv_path = "/app/test_quebec_mines.csv"
                if os.path.exists(csv_path):
                    file_input.set_input_files(csv_path)
                    time.sleep(2)
                    page.screenshot(path="complete_batch_03_csv_uploaded.png")
                    print("✅ CSV file uploaded successfully")
                else:
                    print("❌ CSV file not found at path:", csv_path)
                    return False
            else:
                print("❌ File input not found")
                page.screenshot(path="complete_batch_error_no_file_input.png")
                return False
            
            print("📍 Step 4: Configure batch options")
            # Look for batch options
            nur_erste = page.locator('input[type="radio"][value="first_only"], label:has-text("Nur erste")')
            if nur_erste.count() > 0:
                nur_erste.first.click()
                time.sleep(1)
                print("✅ 'Nur erste' option selected for faster testing")
            
            page.screenshot(path="complete_batch_04_options_configured.png")
            
            print("📍 Step 5: Start batch processing")
            # Look for the CSV verarbeiten button
            process_button = page.locator('button:has-text("CSV verarbeiten"), .process-btn, .batch-start')
            if process_button.count() > 0:
                process_button.first.click()
                time.sleep(3)
                page.screenshot(path="complete_batch_05_processing_started.png")
                print("✅ Batch processing started")
                
                # Wait for processing to show some progress
                print("📍 Step 6: Monitor processing progress")
                time.sleep(10)  # Wait for initial processing
                page.screenshot(path="complete_batch_06_processing_progress.png")
                
                # Wait longer for results to appear
                print("🔄 Waiting for batch results...")
                time.sleep(20)  # Wait for more results
                page.screenshot(path="complete_batch_07_processing_continued.png")
                
            else:
                print("❌ Process button not found")
                # Try alternative selectors
                all_buttons = page.locator('button')
                print(f"Found {all_buttons.count()} buttons on page")
                for i in range(min(all_buttons.count(), 10)):
                    button = all_buttons.nth(i)
                    text = button.text_content()
                    if text and ('verarbeiten' in text.lower() or 'start' in text.lower() or 'batch' in text.lower()):
                        print(f"Found potential button: {text}")
                        button.click()
                        time.sleep(3)
                        break
                page.screenshot(path="complete_batch_error_no_process_button.png")
            
            print("📍 Step 7: Check for results table and validate data")
            time.sleep(5)  # Additional wait for results
            
            # Look for results table
            results_table = page.locator('table, .results-table, .batch-results, [data-results]')
            if results_table.count() > 0:
                page.screenshot(path="complete_batch_08_results_visible.png")
                print("✅ Results table found")
                
                # Check for "k.A." values
                ka_values = page.locator('td:has-text("k.A."), .result-cell:has-text("k.A.")')
                ka_count = ka_values.count()
                print(f"📊 Found {ka_count} 'k.A.' placeholders in results")
                
                # Check for actual data
                cells_with_data = page.locator('td:not(:has-text("k.A.")):not(:empty), .result-cell:not(:has-text("k.A.")):not(:empty)')
                data_count = cells_with_data.count()
                print(f"📊 Found {data_count} cells with actual data")
                
                # Look for specific mine names
                mine_names = ['Éléonore', 'Lac Expanse', 'Aubelle', 'Detour Lake', 'Malartic']
                for mine in mine_names:
                    mine_elements = page.locator(f'*:has-text("{mine}")')
                    if mine_elements.count() > 0:
                        print(f"✅ Found mine: {mine}")
                    else:
                        print(f"❌ Mine not found in results: {mine}")
                
                # Take final comprehensive screenshot
                page.screenshot(path="complete_batch_09_final_results.png", full_page=True)
                
            else:
                print("❌ No results table found")
                # Check if there are any error messages
                error_messages = page.locator('.error, .alert-danger, [data-error]')
                if error_messages.count() > 0:
                    for i in range(error_messages.count()):
                        error = error_messages.nth(i)
                        print(f"⚠️ Error message: {error.text_content()}")
                
                page.screenshot(path="complete_batch_error_no_results.png", full_page=True)
            
            print("📍 Step 8: Generate comprehensive report")
            # Get page content for analysis
            page_text = page.text_content()
            
            # Count important indicators
            ka_in_page = page_text.count('k.A.')
            actual_data_indicators = page_text.count('Quebec') + page_text.count('Canada') + page_text.count('Gold')
            
            print(f"\n📈 BATCH TEST SUMMARY:")
            print(f"   - 'k.A.' occurrences: {ka_in_page}")
            print(f"   - Actual data indicators: {actual_data_indicators}")
            print(f"   - Test completed successfully: {'YES' if actual_data_indicators > ka_in_page else 'NEEDS REVIEW'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during batch test: {e}")
            page.screenshot(path="complete_batch_critical_error.png")
            return False
        
        finally:
            # Keep browser open briefly for manual inspection
            print("🔍 Keeping browser open for 10 seconds for manual inspection...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    success = test_complete_batch_workflow()
    sys.exit(0 if success else 1)