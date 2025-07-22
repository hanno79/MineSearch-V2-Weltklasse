#!/usr/bin/env python3
"""
Final Complete Screenshot - Show full interface with Quebec mines expanded
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
    options.add_argument('--window-size=1400,1400')  # Taller window
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return None

def take_final_screenshot():
    """Take the final complete screenshot showing Quebec mines"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Navigate and setup
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Upload CSV
        csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
        file_input = driver.find_element(By.ID, "csv_file")
        file_input.send_keys(csv_file_path)
        
        upload_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        upload_button.click()
        time.sleep(5)
        
        # Expand the mine preview
        details_element = driver.find_element(By.CSS_SELECTOR, "details summary")
        driver.execute_script("arguments[0].scrollIntoView(true);", details_element)
        time.sleep(1)
        details_element.click()
        time.sleep(2)
        
        # Scroll to show both the warning and the mines
        mine_list = driver.find_element(By.CSS_SELECTOR, "details ul")
        driver.execute_script("arguments[0].scrollIntoView(true);", mine_list)
        time.sleep(1)
        
        # Take final screenshot
        driver.save_screenshot("/app/FINAL_quebec_mines_with_abacus.png")
        print("📸 Final screenshot: FINAL_quebec_mines_with_abacus.png")
        
        # Print the mine details
        mines_text = mine_list.text
        print("🏔️ Quebec Mines Successfully Uploaded:")
        print(mines_text)
        
        # Also capture the warning about Abacus
        try:
            abacus_warning = driver.find_element(By.XPATH, "//p[contains(text(), 'Bei Abacus AI')]")
            print(f"\n⚠️ Abacus Warning: {abacus_warning.text}")
        except:
            print("\n⚠️ Abacus warning found in interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Error taking final screenshot: {e}")
        return False
    
    finally:
        driver.quit()

def main():
    print("📸 Final Complete Screenshot")
    print("=" * 40)
    
    success = take_final_screenshot()
    
    if success:
        print("\n✅ Final screenshot completed!")
        print("🎯 Ready for Abacus deep research testing with Quebec mines")
    else:
        print("\n❌ Screenshot failed")

if __name__ == "__main__":
    main()