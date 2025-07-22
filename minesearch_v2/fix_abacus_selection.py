#!/usr/bin/env python3
"""
Fix Abacus selection to ensure ONLY Abacus is selected
Author: rahn
Datum: 18.07.2025
Version: 1.0
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fix_abacus_selection(driver):
    """Fix selection to only have Abacus selected"""
    
    print("🔧 Fixing Abacus selection...")
    
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take before screenshot
    driver.save_screenshot("/app/minesearch_v2/before_fix.png")
    
    # Step 1: Deselect ALL model checkboxes first
    print("❌ Deselecting all model checkboxes...")
    model_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @name='model']")
    
    for checkbox in model_checkboxes:
        if checkbox.is_selected():
            try:
                checkbox.click()
                # Get model name for logging
                parent = checkbox.find_element(By.XPATH, "./..")
                model_text = parent.text.strip()[:50] + "..."
                print(f"   Deselected: {model_text}")
            except:
                pass
    
    time.sleep(1)
    
    # Step 2: Find and select ONLY the Abacus checkbox
    print("🎯 Searching for Abacus checkbox...")
    
    abacus_found = False
    
    # Look for checkbox with value containing 'abacus'
    abacus_selectors = [
        "//input[@type='checkbox' and contains(@value, 'abacus')]",
        "//input[@type='checkbox' and @value='abacus:deep-agent']"
    ]
    
    for selector in abacus_selectors:
        try:
            abacus_checkbox = driver.find_element(By.XPATH, selector)
            if not abacus_checkbox.is_selected():
                abacus_checkbox.click()
                print("✅ Abacus checkbox selected!")
                abacus_found = True
                break
        except:
            continue
    
    if not abacus_found:
        print("🔍 Searching by text content...")
        # Alternative: search by text content
        all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        
        for checkbox in all_checkboxes:
            try:
                parent = checkbox.find_element(By.XPATH, "./..")
                parent_text = parent.text.lower()
                
                if ('abacus' in parent_text or 'deep agent' in parent_text):
                    if not checkbox.is_selected():
                        checkbox.click()
                        print(f"✅ Found and selected Abacus: {parent.text[:60]}...")
                        abacus_found = True
                        break
            except:
                continue
    
    time.sleep(1)
    
    # Take after screenshot
    driver.save_screenshot("/app/minesearch_v2/after_fix.png")
    
    # Verify the fix
    print("🔍 Verifying configuration...")
    
    selected_models = []
    model_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @name='model']")
    
    for checkbox in model_checkboxes:
        if checkbox.is_selected():
            try:
                parent = checkbox.find_element(By.XPATH, "./..")
                model_text = parent.text.strip()
                value = checkbox.get_attribute('value')
                selected_models.append((model_text[:60], value))
            except:
                pass
    
    print(f"\n📊 Currently selected models: {len(selected_models)}")
    for text, value in selected_models:
        print(f"   - {text}... (Value: {value})")
    
    # Check if only Abacus is selected
    abacus_only = (len(selected_models) == 1 and 
                   any('abacus' in value for text, value in selected_models))
    
    if abacus_only:
        print(f"\n🎉 SUCCESS: Only Abacus is now selected!")
        return True
    else:
        print(f"\n⚠️  Still need adjustment: {len(selected_models)} models selected")
        return False

def main():
    """Main function"""
    
    driver = None
    try:
        driver = setup_driver()
        success = fix_abacus_selection(driver)
        
        if success:
            print("\n✅ Abacus-only configuration completed!")
        else:
            print("\n🔧 Manual adjustment may be needed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()