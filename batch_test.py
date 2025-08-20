#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Automated test for MineSearch Batch functionality
"""

from playwright.sync_api import sync_playwright
import time
import sys

def test_batch_functionality():
    """Test the batch functionality of MineSearch interface"""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("📍 Navigating to MineSearch interface...")
            page.goto("http://localhost:8000")
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Take initial screenshot
            page.screenshot(path="batch_test_01_initial.png")
            print("✅ Initial page loaded and screenshot taken")
            
            # Click on Batch tab
            print("📍 Clicking on Batch tab...")
            batch_tab = page.locator('a[href="#batch"], button:has-text("Batch"), .tab:has-text("Batch")')
            if batch_tab.count() > 0:
                batch_tab.first.click()
                time.sleep(2)
                page.screenshot(path="batch_test_02_batch_tab_clicked.png")
                print("✅ Batch tab clicked")
            else:
                print("❌ Batch tab not found - checking all navigation elements")
                # Try to find any clickable element with "batch" text
                nav_elements = page.locator('nav a, .navigation a, .tab, button')
                for i in range(nav_elements.count()):
                    element = nav_elements.nth(i)
                    text = element.text_content().lower()
                    if 'batch' in text:
                        print(f"Found batch element: {text}")
                        element.click()
                        time.sleep(2)
                        page.screenshot(path="batch_test_02_batch_tab_clicked.png")
                        break
                else:
                    print("❌ No batch tab found in navigation")
                    page.screenshot(path="batch_test_error_no_batch_tab.png")
                    return False
            
            # Check for CSV upload functionality
            print("📍 Looking for CSV upload functionality...")
            upload_elements = page.locator('input[type="file"], .upload-area, .csv-upload, [data-upload]')
            
            if upload_elements.count() > 0:
                print("✅ CSV upload functionality found")
                page.screenshot(path="batch_test_03_upload_found.png")
                
                # Look for any instructions or labels
                upload_instructions = page.locator('label, .upload-instructions, .help-text')
                for i in range(upload_instructions.count()):
                    instruction = upload_instructions.nth(i)
                    text = instruction.text_content()
                    if 'csv' in text.lower() or 'datei' in text.lower():
                        print(f"Upload instruction found: {text}")
                
            else:
                print("❌ CSV upload functionality not visible")
                # Check if we need to scroll or if it's in a different section
                page.screenshot(path="batch_test_error_no_upload.png")
                
                # Try to look for any file-related elements
                file_elements = page.locator('*:has-text("CSV"), *:has-text("Upload"), *:has-text("Datei")')
                print(f"File-related elements found: {file_elements.count()}")
                for i in range(min(file_elements.count(), 5)):
                    element = file_elements.nth(i)
                    print(f"File element {i}: {element.text_content()}")
            
            # Check current page content
            print("📍 Analyzing current page content...")
            page_content = page.content()
            
            # Look for batch-specific elements
            batch_keywords = ['batch', 'csv', 'upload', 'datei', 'masse']
            for keyword in batch_keywords:
                if keyword.lower() in page_content.lower():
                    print(f"✅ Found keyword '{keyword}' in page content")
                else:
                    print(f"❌ Keyword '{keyword}' not found in page content")
            
            # Take a full page screenshot
            page.screenshot(path="batch_test_04_full_page.png", full_page=True)
            
            # Try to identify the current active tab
            active_tabs = page.locator('.tab.active, .nav-item.active, [aria-selected="true"]')
            if active_tabs.count() > 0:
                active_tab_text = active_tabs.first.text_content()
                print(f"Current active tab: {active_tab_text}")
            
            print("📍 Test completed - check screenshots for visual verification")
            return True
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            page.screenshot(path="batch_test_error.png")
            return False
        
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_batch_functionality()
    sys.exit(0 if success else 1)