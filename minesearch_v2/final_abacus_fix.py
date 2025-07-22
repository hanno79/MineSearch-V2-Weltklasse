#!/usr/bin/env python3
"""
Final fix to configure ONLY Abacus provider
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

def configure_abacus_exclusive(driver):
    """Configure ONLY Abacus provider"""
    
    print("🎯 FINAL ABACUS CONFIGURATION")
    print("=" * 50)
    
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take before screenshot
    driver.save_screenshot("/app/minesearch_v2/before_final_fix.png")
    
    print("Step 1: Deselecting ALL model checkboxes...")
    # Deselect all model checkboxes
    model_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @name='model']")
    deselected_count = 0
    
    for checkbox in model_checkboxes:
        if checkbox.is_selected():
            try:
                checkbox.click()
                deselected_count += 1
            except:
                pass
    
    print(f"   ❌ Deselected {deselected_count} model checkboxes")
    
    print("\nStep 2: Ensuring Abacus provider is enabled...")
    # Enable Abacus provider if not already
    abacus_provider = driver.find_elements(By.XPATH, "//input[@id='provider_abacus']")
    if abacus_provider:
        if not abacus_provider[0].is_selected():
            abacus_provider[0].click()
            print("   ✅ Enabled Abacus provider")
        else:
            print("   ✅ Abacus provider already enabled")
    
    print("\nStep 3: Selecting ONLY the Abacus model...")
    # Select only the Abacus model
    abacus_model = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @value='abacus:deep-agent']")
    if abacus_model:
        if not abacus_model[0].is_selected():
            abacus_model[0].click()
            print("   ✅ Selected abacus:deep-agent model")
        else:
            print("   ✅ abacus:deep-agent already selected")
    else:
        print("   ❌ Could not find abacus:deep-agent checkbox")
    
    time.sleep(2)
    
    # Take after screenshot
    driver.save_screenshot("/app/minesearch_v2/FINAL_abacus_exclusive.png")
    
    print("\nStep 4: Final verification...")
    # Verify configuration
    all_model_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @name='model']")
    selected_models = []
    
    for checkbox in all_model_checkboxes:
        if checkbox.is_selected():
            value = checkbox.get_attribute('value')
            selected_models.append(value)
    
    abacus_provider_enabled = False
    abacus_provider_checkboxes = driver.find_elements(By.XPATH, "//input[@id='provider_abacus']")
    if abacus_provider_checkboxes:
        abacus_provider_enabled = abacus_provider_checkboxes[0].is_selected()
    
    print(f"\n📊 FINAL VERIFICATION:")
    print(f"   Abacus provider enabled: {'✅ YES' if abacus_provider_enabled else '❌ NO'}")
    print(f"   Total models selected: {len(selected_models)}")
    print(f"   Selected models: {selected_models}")
    
    # Check success criteria
    success = (len(selected_models) == 1 and 
              'abacus:deep-agent' in selected_models and
              abacus_provider_enabled)
    
    if success:
        print(f"\n🎉 SUCCESS: Abacus is now the ONLY selected provider!")
        print(f"   ✅ Provider: Abacus enabled")
        print(f"   ✅ Model: abacus:deep-agent selected")
        print(f"   ✅ All other models: deselected")
        print(f"\n🚀 Ready for exclusive Abacus testing!")
    else:
        print(f"\n⚠️  Configuration incomplete:")
        if not abacus_provider_enabled:
            print(f"   ❌ Abacus provider not enabled")
        if 'abacus:deep-agent' not in selected_models:
            print(f"   ❌ abacus:deep-agent not selected")
        if len(selected_models) > 1:
            print(f"   ❌ Multiple models selected (should be only 1)")
    
    return success

def main():
    """Main configuration function"""
    
    driver = None
    try:
        driver = setup_driver()
        success = configure_abacus_exclusive(driver)
        
        print(f"\n{'='*50}")
        if success:
            print("🎯 CONFIGURATION COMPLETE: Ready for Abacus testing!")
            print("🔍 Only the Abacus provider (abacus:deep-agent) is selected.")
            print("🚀 You can now proceed with testing the Abacus provider exclusively.")
        else:
            print("🔧 CONFIGURATION INCOMPLETE: Manual verification needed")
        print(f"{'='*50}")
            
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()