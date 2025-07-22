#!/usr/bin/env python3
"""
Detailed CSV Upload Test - Focus on data preview
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def setup_driver():
    """Setup Chrome driver with appropriate options"""
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

def take_screenshot(driver, filename, description=""):
    """Take a screenshot and save it"""
    try:
        screenshot_path = f"/app/{filename}"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        if description:
            print(f"   Description: {description}")
        return screenshot_path
    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
        return None

def test_detailed_upload():
    """Test CSV upload with detailed inspection"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Navigate to frontend
        frontend_url = "http://localhost:8080"
        print(f"🌐 Navigating to: {frontend_url}")
        driver.get(frontend_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        # Take full page screenshot
        take_screenshot(driver, "detailed_01_initial.png", "Initial page")
        
        # Upload CSV file
        csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
        file_input = driver.find_element(By.ID, "csv_file")
        file_input.send_keys(csv_file_path)
        print("📤 CSV file selected")
        
        # Click upload button
        upload_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        upload_button.click()
        print("🚀 Upload button clicked")
        
        # Wait for response
        time.sleep(5)
        
        # Take screenshot after upload
        take_screenshot(driver, "detailed_02_after_upload.png", "After upload response")
        
        # Scroll down to see any response content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        take_screenshot(driver, "detailed_03_scrolled_down.png", "Scrolled down view")
        
        # Check csv-info content
        try:
            csv_info = driver.find_element(By.ID, "csv-info")
            info_text = csv_info.text
            print(f"📄 CSV Info Content:\n{info_text}")
            
            # Get HTML content too
            info_html = csv_info.get_attribute('innerHTML')
            print(f"🔍 CSV Info HTML:\n{info_html}")
            
            if info_text.strip():
                print("✅ Upload response received")
            else:
                print("⚠️ No response text found")
            
        except Exception as e:
            print(f"❌ Error reading csv-info: {e}")
        
        # Look for any mine data in the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        quebec_mines = ["Jeffrey Mine", "LAB Chrysotile Mine", "Horne Mine", "East Malartic Mine"]
        found_mines = []
        
        for mine in quebec_mines:
            if mine in page_text:
                found_mines.append(mine)
        
        print(f"🏔️ Found {len(found_mines)}/{len(quebec_mines)} Quebec mines in page:")
        for mine in found_mines:
            print(f"   ✓ {mine}")
        
        # Take final full page screenshot
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        take_screenshot(driver, "detailed_04_final_top.png", "Final view - top of page")
        
        return len(found_mines) > 0
        
    except Exception as e:
        print(f"❌ Error during detailed upload test: {e}")
        take_screenshot(driver, "detailed_error.png", f"Error state: {e}")
        return False
    
    finally:
        driver.quit()

def check_backend_response():
    """Check if backend is responding properly"""
    import requests
    
    try:
        response = requests.get("http://localhost:8000/api/models", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is responding")
            data = response.json()
            if 'models' in data:
                print(f"📊 {len(data['models'])} models available")
            return True
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not responding: {e}")
        return False

def main():
    print("🔍 Detailed CSV Upload Test")
    print("=" * 50)
    
    # Check backend
    print("\n1. Checking backend connection...")
    if not check_backend_response():
        print("❌ Backend check failed")
        return
    
    # Run detailed upload test
    print("\n2. Running detailed upload test...")
    success = test_detailed_upload()
    
    if success:
        print("\n✅ Upload test completed - mines found in response!")
    else:
        print("\n⚠️ Upload completed but mines not clearly visible")
    
    print("\n📸 Detailed screenshots taken:")
    screenshots = [
        "detailed_01_initial.png - Initial page",
        "detailed_02_after_upload.png - After upload response", 
        "detailed_03_scrolled_down.png - Scrolled down view",
        "detailed_04_final_top.png - Final view top"
    ]
    for screenshot in screenshots:
        print(f"   {screenshot}")

if __name__ == "__main__":
    main()