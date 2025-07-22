#!/usr/bin/env python3
"""
CSV Upload Test Script for MineSearch v2
Automated testing of CSV upload functionality with screenshots
"""

import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1200,800')
    
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

def test_csv_upload():
    """Test the CSV upload functionality"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Navigate to the frontend
        frontend_url = "http://localhost:8080"
        print(f"🌐 Navigating to: {frontend_url}")
        driver.get(frontend_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Take initial screenshot
        take_screenshot(driver, "01_initial_interface.png", "Initial MineSearch interface")
        
        # Check if CSV upload tab is visible and active
        csv_tab = driver.find_element(By.ID, "method_csv")
        if csv_tab.is_selected():
            print("✅ CSV upload tab is already selected")
        else:
            print("🔄 Selecting CSV upload tab")
            csv_tab.click()
            time.sleep(1)
        
        # Take screenshot after tab selection
        take_screenshot(driver, "02_csv_tab_selected.png", "CSV upload tab selected")
        
        # Find the file input element
        print("🔍 Looking for file input element...")
        file_input = driver.find_element(By.ID, "csv_file")
        
        # Check if Quebec CSV file exists
        csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return False
        
        print(f"📁 CSV file found: {csv_file_path}")
        
        # Upload the CSV file
        print("📤 Uploading CSV file...")
        file_input.send_keys(csv_file_path)
        
        # Take screenshot after file selection
        take_screenshot(driver, "03_file_selected.png", "CSV file selected")
        
        # Find and click the upload button
        upload_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print("🚀 Clicking upload button...")
        upload_button.click()
        
        # Wait for upload to complete and response to appear
        print("⏳ Waiting for upload response...")
        try:
            # Wait for the csv-info div to be updated with content
            wait.until(lambda d: d.find_element(By.ID, "csv-info").text.strip() != "")
            print("✅ Upload response received")
            
            # Take screenshot after upload
            take_screenshot(driver, "04_upload_response.png", "Upload response received")
            
            # Get the upload response content
            csv_info = driver.find_element(By.ID, "csv-info")
            response_text = csv_info.text
            print(f"📄 Upload response:\n{response_text}")
            
            # Look for mine preview data
            if "Jeffrey Mine" in response_text or "Quebec" in response_text:
                print("✅ Quebec mines data detected in response")
            else:
                print("⚠️ Quebec mines not clearly visible in response")
            
            # Take final screenshot
            take_screenshot(driver, "05_final_state.png", "Final state after upload")
            
            return True
            
        except TimeoutException:
            print("⏰ Timeout waiting for upload response")
            take_screenshot(driver, "04_timeout_error.png", "Timeout error during upload")
            return False
        
    except Exception as e:
        print(f"❌ Error during CSV upload test: {e}")
        take_screenshot(driver, "error_state.png", f"Error state: {e}")
        return False
    
    finally:
        print("🔄 Closing browser...")
        driver.quit()

def verify_csv_content():
    """Verify the CSV file content before upload"""
    csv_file_path = "/app/minesearch_v2/test_mines_quebec.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print(f"📋 CSV file content preview:")
    try:
        with open(csv_file_path, 'r') as f:
            content = f.read()
            print(content)
            
        # Check for expected mines
        expected_mines = ["Jeffrey Mine", "LAB Chrysotile Mine", "Horne Mine", "East Malartic Mine"]
        found_mines = []
        
        for mine in expected_mines:
            if mine in content:
                found_mines.append(mine)
        
        print(f"✅ Found {len(found_mines)}/{len(expected_mines)} expected Quebec mines:")
        for mine in found_mines:
            print(f"   - {mine}")
        
        return len(found_mines) == len(expected_mines)
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False

def main():
    """Main function"""
    print("🎯 MineSearch CSV Upload Test")
    print("=" * 50)
    
    # First verify CSV content
    print("\n1. Verifying CSV file content...")
    if not verify_csv_content():
        print("❌ CSV verification failed")
        return
    
    # Test CSV upload
    print("\n2. Testing CSV upload functionality...")
    success = test_csv_upload()
    
    if success:
        print("\n✅ CSV upload test completed successfully!")
        print("\n📸 Screenshots taken:")
        for i, desc in enumerate([
            "01_initial_interface.png - Initial MineSearch interface",
            "02_csv_tab_selected.png - CSV upload tab selected", 
            "03_file_selected.png - CSV file selected",
            "04_upload_response.png - Upload response received",
            "05_final_state.png - Final state after upload"
        ], 1):
            print(f"   {desc}")
    else:
        print("\n❌ CSV upload test failed!")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    main()