#!/usr/bin/env python3
"""
Debug page structure to understand the interface
Author: rahn
Datum: 18.07.2025
Version: 1.0
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def debug_structure(driver):
    """Debug the page structure"""
    
    print("🔍 DEBUGGING PAGE STRUCTURE")
    print("=" * 50)
    
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take screenshot
    driver.save_screenshot("/app/minesearch_v2/debug_structure.png")
    
    # Check if page loaded
    title = driver.title
    print(f"Page title: {title}")
    
    # Look for main content
    body = driver.find_element(By.TAG_NAME, "body")
    print(f"Page has content: {len(body.text) > 100}")
    
    # Find all checkboxes
    all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
    print(f"Total checkboxes found: {len(all_checkboxes)}")
    
    # Count selected checkboxes
    selected_count = 0
    abacus_checkbox = None
    
    print(f"\nALL CHECKBOXES ANALYSIS:")
    for i, checkbox in enumerate(all_checkboxes):
        try:
            # Get surrounding context
            parent = checkbox.find_element(By.XPATH, "./..")
            grandparent = parent.find_element(By.XPATH, "./..")
            
            text_content = parent.text.strip() or grandparent.text.strip()
            checkbox_id = checkbox.get_attribute('id')
            checkbox_name = checkbox.get_attribute('name') 
            checkbox_value = checkbox.get_attribute('value')
            is_selected = checkbox.is_selected()
            
            if is_selected:
                selected_count += 1
                
            # Check if this could be Abacus
            is_abacus = ('abacus' in text_content.lower() or 
                        'abacus' in str(checkbox_value).lower() or
                        'deep agent' in text_content.lower())
            
            if is_abacus:
                abacus_checkbox = checkbox
                print(f"🎯 ABACUS FOUND #{i+1}:")
            elif is_selected:
                print(f"✅ SELECTED #{i+1}:")
            else:
                continue  # Skip unselected non-Abacus
                
            print(f"   Text: {text_content[:80]}...")
            print(f"   ID: {checkbox_id}")
            print(f"   Name: {checkbox_name}")
            print(f"   Value: {checkbox_value}")
            print(f"   Selected: {is_selected}")
            print()
            
        except Exception as e:
            continue
    
    print(f"📊 SUMMARY:")
    print(f"   Total checkboxes: {len(all_checkboxes)}")
    print(f"   Selected checkboxes: {selected_count}")
    print(f"   Abacus found: {'✅ YES' if abacus_checkbox else '❌ NO'}")
    
    if abacus_checkbox:
        print(f"   Abacus selected: {'✅ YES' if abacus_checkbox.is_selected() else '❌ NO'}")
    
    # Check for specific Abacus value
    abacus_specific = driver.find_elements(By.XPATH, "//input[@value='abacus:deep-agent']")
    print(f"   Specific abacus:deep-agent found: {len(abacus_specific)}")
    
    if abacus_specific:
        specific_selected = abacus_specific[0].is_selected()
        print(f"   abacus:deep-agent selected: {'✅ YES' if specific_selected else '❌ NO'}")

def main():
    """Main debug function"""
    
    driver = None
    try:
        driver = setup_driver()
        debug_structure(driver)
        
    except Exception as e:
        print(f"❌ Debug error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()