#!/usr/bin/env python3
"""
Test to check form visibility and button state
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def test_visibility():
    print("🔍 Testing Form Visibility and Button States")
    print("=" * 60)
    
    driver = create_driver()
    
    try:
        # Load page
        driver.get("http://localhost:8000/static/index.html")
        time.sleep(3)
        
        # Check all radio buttons
        print("\n📍 Checking radio buttons...")
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[name="search_method"]')
        for radio in radio_buttons:
            print(f"   Radio {radio.get_attribute('id')}: checked={radio.is_selected()}, value={radio.get_attribute('value')}")
        
        # Check all forms
        print("\n📍 Checking forms visibility...")
        forms = driver.find_elements(By.CSS_SELECTOR, '.search-form')
        for form in forms:
            form_id = form.get_attribute('id')
            is_visible = form.is_displayed()
            has_active_class = 'active' in form.get_attribute('class')
            print(f"   Form {form_id}: visible={is_visible}, has_active_class={has_active_class}")
        
        # Click on statistics radio button
        print("\n📍 Clicking Statistics radio button...")
        stats_radio = driver.find_element(By.ID, "method_statistics")
        driver.execute_script("arguments[0].click();", stats_radio)
        time.sleep(2)
        
        # Check forms after click
        print("\n📍 Checking forms after statistics click...")
        forms = driver.find_elements(By.CSS_SELECTOR, '.search-form')
        for form in forms:
            form_id = form.get_attribute('id')
            is_visible = form.is_displayed()
            has_active_class = 'active' in form.get_attribute('class')
            print(f"   Form {form_id}: visible={is_visible}, has_active_class={has_active_class}")
        
        # Check if statistics form is visible
        stats_form = driver.find_element(By.ID, "statistics_form")
        if stats_form.is_displayed():
            print("✅ Statistics form is now visible")
            
            # Find buttons within statistics form
            print("\n📍 Checking buttons in statistics form...")
            buttons = stats_form.find_elements(By.TAG_NAME, "button")
            for i, button in enumerate(buttons):
                text = button.text.strip()
                onclick = button.get_attribute('onclick')
                is_visible = button.is_displayed()
                is_enabled = button.is_enabled()
                print(f"   Button {i+1}: text='{text}', onclick='{onclick}', visible={is_visible}, enabled={is_enabled}")
                
                # Try to click if it's the field statistics button
                if "loadFieldStatistics" in str(onclick):
                    print(f"   🖱️ Trying to click Field Statistics button...")
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(3)
                        print("   ✅ Field Statistics button clicked successfully")
                        
                        # Check result container
                        container = driver.find_element(By.ID, "statistics-table-container")
                        content = container.text
                        print(f"   📊 Results: {content[:150]}...")
                        
                    except Exception as e:
                        print(f"   ❌ Error clicking Field Statistics button: {e}")
                
                # Try to click if it's the field comparison button
                if "loadFieldComparison" in str(onclick):
                    print(f"   🖱️ Trying to click Field Comparison button...")
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(3)
                        print("   ✅ Field Comparison button clicked successfully")
                        
                        # Check result container
                        container = driver.find_element(By.ID, "statistics-table-container")
                        content = container.text
                        print(f"   📈 Results: {content[:150]}...")
                        
                    except Exception as e:
                        print(f"   ❌ Error clicking Field Comparison button: {e}")
        else:
            print("❌ Statistics form is NOT visible")
        
        # Save final screenshot
        driver.save_screenshot("/tmp/visibility_test.png")
        print("\n✅ Screenshot saved to /tmp/visibility_test.png")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_visibility()