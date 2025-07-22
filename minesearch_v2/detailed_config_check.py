#!/usr/bin/env python3
"""
Detailed configuration check for Abacus provider
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

def detailed_analysis(driver):
    """Detailed analysis of provider configuration"""
    
    print("🔍 Performing detailed configuration analysis...")
    
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take screenshot
    driver.save_screenshot("/app/minesearch_v2/detailed_analysis.png")
    
    # Find all checkboxes
    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
    
    print(f"\n📊 Found {len(checkboxes)} total checkboxes")
    
    selected_count = 0
    abacus_selected = False
    
    for i, checkbox in enumerate(checkboxes):
        try:
            # Get parent element text to identify the model
            parent = checkbox.find_element(By.XPATH, "./..")
            parent_text = parent.text.strip()
            
            # Get checkbox attributes
            checkbox_id = checkbox.get_attribute('id')
            checkbox_name = checkbox.get_attribute('name')
            checkbox_value = checkbox.get_attribute('value')
            is_selected = checkbox.is_selected()
            
            if is_selected:
                selected_count += 1
                print(f"\n✅ Selected #{selected_count}:")
                print(f"   Text: {parent_text}")
                print(f"   ID: {checkbox_id}")
                print(f"   Name: {checkbox_name}")
                print(f"   Value: {checkbox_value}")
                
                # Check if this is Abacus
                if ('abacus' in parent_text.lower() or 
                    'deep agent' in parent_text.lower() or
                    'abacus' in str(checkbox_value).lower()):
                    abacus_selected = True
                    print(f"   🎯 THIS IS ABACUS!")
        
        except Exception as e:
            continue
    
    print(f"\n📈 SUMMARY:")
    print(f"Total selected: {selected_count}")
    print(f"Abacus selected: {'✅ YES' if abacus_selected else '❌ NO'}")
    
    if selected_count == 1 and abacus_selected:
        print(f"\n🎉 PERFECT: Only Abacus is selected!")
    elif abacus_selected:
        print(f"\n⚠️  WARNING: Abacus is selected but {selected_count-1} other models are also selected")
    else:
        print(f"\n❌ ERROR: Abacus is not selected")
    
    return abacus_selected and selected_count == 1

def main():
    """Main function"""
    
    driver = None
    try:
        driver = setup_driver()
        success = detailed_analysis(driver)
        
        if success:
            print("\n🎯 Configuration is correct!")
        else:
            print("\n🔧 Configuration needs fixing...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()