#!/usr/bin/env python3
"""
Final verification that only Abacus provider is configured
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

def final_verification(driver):
    """Final verification of Abacus-only configuration"""
    
    print("🔍 FINAL VERIFICATION: Abacus-only configuration")
    print("=" * 50)
    
    driver.get("http://localhost:8080")
    time.sleep(3)
    
    # Take focused screenshot of Abacus section
    driver.save_screenshot("/app/minesearch_v2/FINAL_abacus_only_config.png")
    
    # Count all provider sections
    provider_sections = driver.find_elements(By.XPATH, "//div[contains(@class, 'form-group') or contains(@class, 'provider')]//input[@type='checkbox'][contains(@name, 'model')]")
    
    total_models = len(provider_sections)
    selected_models = []
    abacus_models = []
    
    for checkbox in provider_sections:
        try:
            parent = checkbox.find_element(By.XPATH, "./..")
            model_text = parent.text.strip()
            value = checkbox.get_attribute('value')
            is_selected = checkbox.is_selected()
            
            if is_selected:
                selected_models.append((model_text, value))
            
            if 'abacus' in value.lower():
                abacus_models.append((model_text, value, is_selected))
                
        except:
            continue
    
    print(f"📊 STATISTICS:")
    print(f"   Total models available: {total_models}")
    print(f"   Total models selected: {len(selected_models)}")
    print(f"   Abacus models found: {len(abacus_models)}")
    
    print(f"\n✅ SELECTED MODELS:")
    if selected_models:
        for i, (text, value) in enumerate(selected_models, 1):
            print(f"   {i}. {text[:70]}...")
            print(f"      Value: {value}")
    else:
        print("   None")
    
    print(f"\n🎯 ABACUS MODELS:")
    for text, value, selected in abacus_models:
        status = "✅ SELECTED" if selected else "❌ NOT SELECTED"
        print(f"   - {text[:70]}...")
        print(f"     Value: {value} | Status: {status}")
    
    # Determine success
    abacus_selected = any(selected for _, _, selected in abacus_models)
    only_abacus_selected = (len(selected_models) == 1 and 
                           len(abacus_models) == 1 and 
                           abacus_models[0][2])  # abacus is selected
    
    print(f"\n🏆 VERIFICATION RESULT:")
    if only_abacus_selected:
        print("✅ SUCCESS: Only Abacus provider (abacus:deep-agent) is selected!")
        print("🎉 Configuration is perfect for testing Abacus exclusively.")
        return True
    elif abacus_selected:
        print("⚠️  WARNING: Abacus is selected but other providers are also selected.")
        print("🔧 Need to deselect other providers for exclusive Abacus testing.")
        return False
    else:
        print("❌ ERROR: Abacus provider is not selected.")
        print("🔧 Need to select Abacus provider.")
        return False

def main():
    """Main verification function"""
    
    driver = None
    try:
        driver = setup_driver()
        success = final_verification(driver)
        
        print(f"\n{'='*50}")
        if success:
            print("🎯 FINAL STATUS: READY FOR ABACUS TESTING!")
        else:
            print("🔧 FINAL STATUS: Configuration needs adjustment")
        print(f"{'='*50}")
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()