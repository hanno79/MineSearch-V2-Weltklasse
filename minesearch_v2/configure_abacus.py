#!/usr/bin/env python3
"""
Script to configure MineSearch interface to select only Abacus provider
Author: rahn
Datum: 18.07.2025
Version: 1.0
"""

import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os

def setup_driver():
    """Setup Chrome driver for automation"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def take_screenshot(driver, filename, description=""):
    """Take a screenshot and save it"""
    screenshot_path = f"/app/minesearch_v2/{filename}"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path} - {description}")
    return screenshot_path

def configure_abacus_only(driver):
    """Configure interface to select only Abacus provider"""
    
    print("🚀 Starting Abacus configuration...")
    
    # Navigate to the interface
    print("📱 Navigating to MineSearch interface...")
    driver.get("http://localhost:8080")
    
    # Wait for page to load
    wait = WebDriverWait(driver, 10)
    time.sleep(3)
    
    # Take initial screenshot
    take_screenshot(driver, "01_initial_interface.png", "Initial MineSearch interface")
    
    try:
        # Look for provider selection area
        print("🔍 Looking for provider selection area...")
        
        # Try to find the provider section - multiple possible selectors
        provider_sections = [
            "//div[contains(@class, 'provider')]",
            "//div[contains(@class, 'model')]", 
            "//div[contains(@id, 'provider')]",
            "//div[contains(@id, 'model')]",
            "//section[contains(@class, 'provider')]",
            "//fieldset[contains(@class, 'provider')]"
        ]
        
        provider_area = None
        for selector in provider_sections:
            try:
                provider_area = driver.find_element(By.XPATH, selector)
                print(f"✅ Found provider area with selector: {selector}")
                break
            except:
                continue
        
        if not provider_area:
            print("⚠️  Could not find provider selection area, looking for checkboxes...")
            
        # Take screenshot of current state
        take_screenshot(driver, "02_searching_providers.png", "Searching for provider options")
        
        # Look for all checkboxes or radio buttons
        print("🔍 Looking for all provider checkboxes...")
        
        # Multiple strategies to find provider inputs
        checkbox_selectors = [
            "//input[@type='checkbox']",
            "//input[@type='radio']", 
            "//input[contains(@name, 'provider')]",
            "//input[contains(@name, 'model')]",
            "//input[contains(@id, 'abacus')]",
            "//label[contains(text(), 'abacus')]//input",
            "//div[contains(text(), 'abacus')]//input"
        ]
        
        all_inputs = []
        abacus_input = None
        
        for selector in checkbox_selectors:
            try:
                inputs = driver.find_elements(By.XPATH, selector)
                all_inputs.extend(inputs)
                print(f"Found {len(inputs)} inputs with selector: {selector}")
            except:
                continue
        
        # Remove duplicates
        all_inputs = list(set(all_inputs))
        print(f"📊 Total unique inputs found: {len(all_inputs)}")
        
        # Look specifically for Abacus
        print("🎯 Searching for Abacus provider...")
        
        abacus_selectors = [
            "//input[contains(@id, 'abacus')]",
            "//input[contains(@value, 'abacus')]",
            "//input[contains(@name, 'abacus')]",
            "//label[contains(text(), 'abacus')]//input",
            "//label[contains(text(), 'deep-agent')]//input",
            "//div[contains(text(), 'abacus')]//input",
            "//*[contains(text(), 'abacus:deep-agent')]//input",
            "//*[contains(text(), 'abacus')]/input",
            "//*[contains(text(), 'abacus')]/..//input"
        ]
        
        for selector in abacus_selectors:
            try:
                abacus_candidates = driver.find_elements(By.XPATH, selector)
                if abacus_candidates:
                    abacus_input = abacus_candidates[0]
                    print(f"✅ Found Abacus input with selector: {selector}")
                    break
            except:
                continue
        
        # If still not found, examine page source
        if not abacus_input:
            print("🔍 Examining page source for 'abacus'...")
            page_source = driver.page_source.lower()
            if 'abacus' in page_source:
                print("✅ 'abacus' found in page source")
                # Look for any element containing abacus
                abacus_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'abacus')]")
                print(f"Found {len(abacus_elements)} elements containing 'abacus'")
                
                for element in abacus_elements:
                    print(f"Abacus element: {element.tag_name} - {element.text}")
            else:
                print("❌ 'abacus' not found in page source")
        
        # Take screenshot before configuration
        take_screenshot(driver, "03_before_configuration.png", "Before provider configuration")
        
        # Strategy 1: If we found Abacus input, select it and deselect others
        if abacus_input:
            print("🎯 Configuring Abacus provider...")
            
            # First, deselect all other providers
            print("❌ Deselecting all other providers...")
            for input_elem in all_inputs:
                try:
                    if input_elem != abacus_input and input_elem.is_selected():
                        input_elem.click()
                        print(f"Deselected: {input_elem.get_attribute('id') or input_elem.get_attribute('name')}")
                except:
                    pass
            
            # Now select Abacus
            print("✅ Selecting Abacus provider...")
            if not abacus_input.is_selected():
                abacus_input.click()
                print("Abacus provider selected!")
            
        else:
            # Strategy 2: Look for any element containing "abacus" and try to click it
            print("🔄 Alternative strategy: Looking for clickable Abacus elements...")
            
            clickable_selectors = [
                "//*[contains(text(), 'abacus')]",
                "//*[contains(text(), 'deep-agent')]",
                "//button[contains(text(), 'abacus')]",
                "//div[contains(text(), 'abacus')]",
                "//span[contains(text(), 'abacus')]",
                "//label[contains(text(), 'abacus')]"
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            element.click()
                            print(f"✅ Clicked Abacus element: {element.text}")
                            break
                        except:
                            continue
                except:
                    continue
        
        # Take screenshot after configuration
        take_screenshot(driver, "04_after_configuration.png", "After Abacus configuration")
        
        # Look for confirmation or status indicators
        print("🔍 Looking for confirmation indicators...")
        
        status_selectors = [
            "//*[contains(@class, 'selected')]",
            "//*[contains(@class, 'active')]",
            "//*[contains(@class, 'checked')]",
            "//*[contains(text(), 'selected')]",
            "//*[contains(text(), 'active')]"
        ]
        
        for selector in status_selectors:
            try:
                status_elements = driver.find_elements(By.XPATH, selector)
                for element in status_elements:
                    if 'abacus' in element.text.lower():
                        print(f"✅ Status indicator: {element.text}")
            except:
                continue
        
        # Final screenshot
        take_screenshot(driver, "05_final_configuration.png", "Final configuration state")
        
        print("✅ Abacus configuration completed!")
        
    except Exception as e:
        print(f"❌ Error during configuration: {str(e)}")
        take_screenshot(driver, "error_configuration.png", f"Error state: {str(e)}")
    
    return True

def main():
    """Main execution function"""
    
    print("🚀 Starting MineSearch Abacus Configuration...")
    
    # Start servers if not running
    print("🔧 Checking servers...")
    
    driver = None
    try:
        # Setup driver
        driver = setup_driver()
        
        # Configure Abacus only
        configure_abacus_only(driver)
        
        print("✅ Configuration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if driver:
            take_screenshot(driver, "final_error.png", f"Final error: {str(e)}")
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Driver closed")

if __name__ == "__main__":
    main()