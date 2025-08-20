#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Simplified batch test focusing on starting batch process and validating results
"""

from playwright.sync_api import sync_playwright
import time
import sys
import os

def test_batch_results():
    """Test batch processing and validate results for 'k.A.' values"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(60000)  # Longer timeout
        
        try:
            print("📍 Step 1: Navigate and setup")
            page.goto("http://localhost:8000")
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Click batch tab
            batch_elements = page.locator('*:has-text("📊"):has-text("Batch")')
            if batch_elements.count() > 0:
                batch_elements.first.click()
                time.sleep(2)
                print("✅ Batch tab clicked")
            
            page.screenshot(path="batch_results_01_setup.png")
            
            print("📍 Step 2: Quick model selection")
            # Select Top Performers (should be fastest)
            top_perf = page.locator('button:has-text("Top Performers")')
            if top_perf.count() > 0:
                top_perf.first.click()
                time.sleep(1)
                print("✅ Top Performers selected")
            
            print("📍 Step 3: Upload CSV")
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                csv_path = "/app/test_quebec_mines.csv"
                file_input.set_input_files(csv_path)
                time.sleep(2)
                print("✅ CSV uploaded")
            
            page.screenshot(path="batch_results_02_ready.png")
            
            print("📍 Step 4: Start batch process (simple approach)")
            # Try different button selectors for starting batch
            button_selectors = [
                'button:has-text("CSV verarbeiten")',
                'button:has-text("verarbeiten")',
                'button:has-text("Start")',
                '.process-btn',
                '.batch-start',
                'button[type="submit"]'
            ]
            
            started = False
            for selector in button_selectors:
                buttons = page.locator(selector)
                if buttons.count() > 0:
                    try:
                        buttons.first.click()
                        time.sleep(3)
                        print(f"✅ Clicked button with selector: {selector}")
                        started = True
                        break
                    except:
                        continue
            
            if not started:
                # Try clicking any button with relevant text
                all_buttons = page.locator('button')
                for i in range(all_buttons.count()):
                    try:
                        button = all_buttons.nth(i)
                        text = button.text_content()
                        if text and any(word in text.lower() for word in ['verarbeiten', 'start', 'batch', 'suche']):
                            print(f"Trying button: {text}")
                            button.click()
                            time.sleep(3)
                            started = True
                            break
                    except:
                        continue
            
            page.screenshot(path="batch_results_03_started.png")
            
            print("📍 Step 5: Wait for initial results")
            time.sleep(15)  # Wait for some processing
            page.screenshot(path="batch_results_04_processing.png")
            
            print("📍 Step 6: Check for any results or progress")
            # Scroll down to see if there are results
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            page.screenshot(path="batch_results_05_scrolled.png", full_page=True)
            
            print("📍 Step 7: Analyze page content for validation")
            page_text = page.text_content()
            
            # Count key indicators
            ka_count = page_text.count('k.A.')
            mine_names_found = 0
            mine_names = ['Éléonore', 'Lac Expanse', 'Aubelle', 'Detour Lake', 'Malartic']
            
            for mine in mine_names:
                if mine in page_text:
                    mine_names_found += 1
                    print(f"✅ Found mine name: {mine}")
            
            # Look for actual data patterns
            data_indicators = [
                'Quebec', 'Canada', 'Gold', 'Mining', 'Exploration',
                'tonnes', 'oz', 'g/t', 'million', 'resource'
            ]
            
            data_found = 0
            for indicator in data_indicators:
                if indicator.lower() in page_text.lower():
                    data_found += 1
            
            print(f"\n📊 BATCH RESULTS ANALYSIS:")
            print(f"   - Mine names found in results: {mine_names_found}/{len(mine_names)}")
            print(f"   - 'k.A.' placeholder count: {ka_count}")
            print(f"   - Data indicators found: {data_found}/{len(data_indicators)}")
            
            # Check for results table
            tables = page.locator('table')
            if tables.count() > 0:
                print(f"   - Results tables found: {tables.count()}")
                
                # Get table content
                for i in range(min(tables.count(), 3)):  # Check first 3 tables
                    table = tables.nth(i)
                    table_text = table.text_content()
                    if table_text:
                        ka_in_table = table_text.count('k.A.')
                        print(f"   - Table {i+1}: {ka_in_table} 'k.A.' values")
            else:
                print("   - No results tables found yet")
            
            # Final assessment
            if mine_names_found > 0 and data_found > ka_count:
                print("\n✅ SUCCESS: Real data found in batch results!")
            elif ka_count > data_found:
                print(f"\n⚠️  WARNING: Too many 'k.A.' placeholders ({ka_count}) vs real data indicators ({data_found})")
            else:
                print("\n🔍 REVIEW NEEDED: Mixed results - check screenshots")
            
            page.screenshot(path="batch_results_06_final.png", full_page=True)
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="batch_results_error.png")
            return False
        
        finally:
            time.sleep(5)  # Brief pause for inspection
            browser.close()

if __name__ == "__main__":
    success = test_batch_results()
    sys.exit(0 if success else 1)