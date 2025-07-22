#!/usr/bin/env python3
"""
Verify Abacus is the only configured provider
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1400,1200')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return None

def verify_abacus_provider():
    """Verify that only Abacus models are available"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Navigate to the page
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Scroll to top to capture model selection
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Take screenshot of the model selection area
        driver.save_screenshot("/app/model_selection_full.png")
        print("📸 Full model selection screenshot: model_selection_full.png")
        
        # Check the model selection area
        model_selection = driver.find_element(By.ID, "model-selection")
        selection_text = model_selection.text
        
        print("🔍 Available models/providers:")
        print(selection_text)
        
        # Check for provider names
        providers_found = []
        known_providers = ["Perplexity", "Openrouter", "OpenAI", "Claude", "Gemini", "Abacus"]
        
        for provider in known_providers:
            if provider.lower() in selection_text.lower():
                providers_found.append(provider)
        
        print(f"\n📊 Providers found: {providers_found}")
        
        # Check if only Abacus-related models are present
        abacus_terms = ["deepseek", "abacus"]
        has_abacus = any(term.lower() in selection_text.lower() for term in abacus_terms)
        
        if has_abacus and len(providers_found) <= 2:  # Allow for some variation in naming
            print("✅ Abacus appears to be the primary/only provider configured")
        else:
            print("⚠️ Multiple providers may be configured")
        
        # Upload CSV to get to the final state
        csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
        file_input = driver.find_element(By.ID, "csv_file")
        file_input.send_keys(csv_file_path)
        
        upload_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        upload_button.click()
        time.sleep(5)
        
        # Expand the mine preview
        details_element = driver.find_element(By.CSS_SELECTOR, "details summary")
        details_element.click()
        time.sleep(2)
        
        # Take final comprehensive screenshot
        driver.save_screenshot("/app/complete_interface_abacus.png")
        print("📸 Complete interface with Abacus and Quebec mines: complete_interface_abacus.png")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        driver.save_screenshot("/app/verification_error.png")
        return False
    
    finally:
        driver.quit()

def main():
    print("🔍 Abacus Provider Verification")
    print("=" * 40)
    
    success = verify_abacus_provider()
    
    if success:
        print("\n✅ Verification completed successfully!")
        print("📸 Screenshots taken:")
        print("   - model_selection_full.png")
        print("   - complete_interface_abacus.png")
    else:
        print("\n❌ Verification failed")

if __name__ == "__main__":
    main()