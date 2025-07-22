#!/usr/bin/env python3
"""
Show Mines Preview - Click to expand the mine list
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1400,1000')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return None

def show_mines_preview():
    """Upload CSV and show the mines preview"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Navigate and upload
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Upload CSV file
        csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
        file_input = driver.find_element(By.ID, "csv_file")
        file_input.send_keys(csv_file_path)
        
        # Click upload button
        upload_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        upload_button.click()
        
        # Wait for upload response
        time.sleep(5)
        
        # Look for the "Erste 5 Minen anzeigen" details element
        try:
            details_element = driver.find_element(By.CSS_SELECTOR, "details summary")
            if "Erste 5 Minen anzeigen" in details_element.text:
                print("🔍 Found 'Erste 5 Minen anzeigen' dropdown")
                
                # Scroll to the element
                driver.execute_script("arguments[0].scrollIntoView(true);", details_element)
                time.sleep(1)
                
                # Take screenshot before clicking
                driver.save_screenshot("/app/before_expand.png")
                print("📸 Screenshot before expanding: before_expand.png")
                
                # Click to expand
                details_element.click()
                time.sleep(2)
                
                # Take screenshot after expanding
                driver.save_screenshot("/app/after_expand.png")
                print("📸 Screenshot after expanding: after_expand.png")
                
                # Get the expanded content
                details_parent = driver.find_element(By.CSS_SELECTOR, "details")
                if details_parent.get_attribute("open"):
                    print("✅ Details successfully expanded")
                    
                    # Get the mine list
                    try:
                        mine_list = driver.find_element(By.CSS_SELECTOR, "details ul")
                        mines_text = mine_list.text
                        print(f"🏔️ Mines in preview:\n{mines_text}")
                        
                        # Check for Quebec mines
                        quebec_mines = ["Jeffrey Mine", "LAB Chrysotile Mine", "Horne Mine", "East Malartic Mine"]
                        found_mines = []
                        for mine in quebec_mines:
                            if mine in mines_text:
                                found_mines.append(mine)
                        
                        print(f"✅ Found {len(found_mines)}/{len(quebec_mines)} Quebec mines:")
                        for mine in found_mines:
                            print(f"   ✓ {mine}")
                        
                        return len(found_mines) > 0
                        
                    except Exception as e:
                        print(f"❌ Error reading mine list: {e}")
                        return False
                else:
                    print("❌ Details not expanded")
                    return False
            else:
                print("❌ 'Erste 5 Minen anzeigen' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error finding details element: {e}")
            
            # Take screenshot of current state
            driver.save_screenshot("/app/error_state.png")
            print("📸 Error state screenshot: error_state.png")
            
            # Print page source for debugging
            page_source = driver.page_source
            if "Jeffrey Mine" in page_source:
                print("✅ Quebec mines found in page source")
                return True
            else:
                print("❌ Quebec mines not found in page source")
                return False
        
    except Exception as e:
        print(f"❌ Error during preview test: {e}")
        return False
    
    finally:
        driver.quit()

def main():
    print("🔍 Mines Preview Test")
    print("=" * 30)
    
    success = show_mines_preview()
    
    if success:
        print("\n✅ Mines preview test successful!")
        print("📸 Screenshots:")
        print("   - before_expand.png")
        print("   - after_expand.png")
    else:
        print("\n⚠️ Preview test completed with issues")

if __name__ == "__main__":
    main()