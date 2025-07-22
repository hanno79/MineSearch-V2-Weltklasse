#!/usr/bin/env python3
"""
Script to verify that only Abacus provider is selected in MineSearch
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
    """Setup Chrome driver for verification"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def verify_abacus_only(driver):
    """Verify that only Abacus is selected"""
    
    print("🔍 Verifying Abacus-only configuration...")
    
    # Navigate to interface
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take focused screenshot of provider area
    screenshot_path = "/app/minesearch_v2/abacus_provider_focus.png"
    driver.save_screenshot(screenshot_path)
    print(f"📸 Provider focus screenshot: {screenshot_path}")
    
    # Find all model checkboxes
    model_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and contains(@name, 'model')]")
    
    selected_models = []
    unselected_models = []
    
    for checkbox in model_checkboxes:
        model_id = checkbox.get_attribute('id') or checkbox.get_attribute('name')
        if checkbox.is_selected():
            selected_models.append(model_id)
        else:
            unselected_models.append(model_id)
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"✅ Selected models: {len(selected_models)}")
    for model in selected_models:
        print(f"   - {model}")
    
    print(f"\n❌ Unselected models: {len(unselected_models)}")
    print(f"   (Showing first 5: {unselected_models[:5]}...)")
    
    # Check if only Abacus is selected
    abacus_selected = any('abacus' in model.lower() for model in selected_models)
    non_abacus_selected = any('abacus' not in model.lower() for model in selected_models)
    
    if abacus_selected and not non_abacus_selected:
        print(f"\n🎯 ✅ SUCCESS: Only Abacus provider is selected!")
        return True
    elif abacus_selected and non_abacus_selected:
        print(f"\n⚠️  WARNING: Abacus is selected but other providers are also selected")
        return False
    else:
        print(f"\n❌ ERROR: Abacus is not selected")
        return False

def main():
    """Main verification function"""
    
    driver = None
    try:
        driver = setup_driver()
        success = verify_abacus_only(driver)
        
        if success:
            print("\n🎉 Configuration verified successfully!")
        else:
            print("\n⚠️  Configuration needs adjustment")
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()