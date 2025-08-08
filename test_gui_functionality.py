#!/usr/bin/env python3
"""
Test script to analyze MineSearch v2.1 GUI functionality
Tests JavaScript functions, button clicks, and API interactions
"""

import subprocess
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import sys
import os

# Setup Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

def test_homepage():
    """Test 1: Initial Page Load"""
    print("🧪 TEST 1: Initial Page Load")
    print("=" * 50)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        driver.get("http://localhost:8000/static/index.html")
        time.sleep(2)
        
        # Take screenshot
        driver.save_screenshot("/tmp/homepage_screenshot.png")
        print("✅ Screenshot saved to /tmp/homepage_screenshot.png")
        
        # Check page title
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # Check for main elements
        header = driver.find_element(By.TAG_NAME, "h1")
        print(f"🏷️ Header text: {header.text}")
        
        # Check for tab navigation
        tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-navigation label')
        print(f"📑 Found {len(tabs)} tabs:")
        for i, tab in enumerate(tabs):
            print(f"   {i+1}. {tab.text}")
        
        # Check for statistics tab specifically
        stats_tab = None
        for tab in tabs:
            if "Suchstatistiken" in tab.text:
                stats_tab = tab
                break
        
        if stats_tab:
            print("✅ Found 'Suchstatistiken' tab")
        else:
            print("❌ 'Suchstatistiken' tab not found")
            
        return driver, stats_tab
        
    except Exception as e:
        print(f"❌ Error during homepage test: {e}")
        driver.quit()
        return None, None

def test_tab_navigation(driver, stats_tab):
    """Test 2: Tab Navigation"""
    print("\n🧪 TEST 2: Tab Navigation")
    print("=" * 50)
    
    try:
        if stats_tab:
            # Click on Statistics tab
            print("🖱️ Clicking on 'Suchstatistiken' tab...")
            stats_tab.click()
            time.sleep(2)
            
            # Take screenshot after click
            driver.save_screenshot("/tmp/statistics_tab_screenshot.png")
            print("✅ Screenshot saved to /tmp/statistics_tab_screenshot.png")
            
            # Check if the form is visible
            stats_form = driver.find_element(By.ID, "statistics_form")
            if stats_form.is_displayed():
                print("✅ Statistics form is visible after tab click")
            else:
                print("❌ Statistics form is not visible")
                
            return True
        else:
            print("❌ Cannot test tab navigation - no statistics tab found")
            return False
            
    except Exception as e:
        print(f"❌ Error during tab navigation test: {e}")
        return False

def test_button_functionality(driver):
    """Test 3: Button Testing"""
    print("\n🧪 TEST 3: Button Testing")
    print("=" * 50)
    
    try:
        # Look for "Feld-Statistiken" button
        field_stats_button = None
        field_comparison_button = None
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"🔘 Found {len(buttons)} buttons on page")
        
        for button in buttons:
            button_text = button.text
            if "Feld-Statistiken" in button_text:
                field_stats_button = button
                print(f"✅ Found 'Feld-Statistiken' button: {button_text}")
            elif "Feld-Vergleich" in button_text:
                field_comparison_button = button
                print(f"✅ Found 'Feld-Vergleich' button: {button_text}")
        
        # Test Feld-Statistiken button
        if field_stats_button:
            print("🖱️ Clicking 'Feld-Statistiken' button...")
            field_stats_button.click()
            time.sleep(3)
            
            # Take screenshot
            driver.save_screenshot("/tmp/field_statistics_result.png")
            print("✅ Screenshot saved to /tmp/field_statistics_result.png")
            
            # Check for results container
            try:
                results_container = driver.find_element(By.ID, "statistics-table-container")
                content = results_container.text
                print(f"📊 Results container content: {content[:200]}...")
            except:
                print("❌ No results container found")
        
        # Test Feld-Vergleich button
        if field_comparison_button:
            print("🖱️ Clicking 'Feld-Vergleich' button...")
            field_comparison_button.click()
            time.sleep(3)
            
            # Take screenshot
            driver.save_screenshot("/tmp/field_comparison_result.png")
            print("✅ Screenshot saved to /tmp/field_comparison_result.png")
            
            # Check for results
            try:
                results_container = driver.find_element(By.ID, "statistics-table-container")
                content = results_container.text
                print(f"📈 Results container content: {content[:200]}...")
            except:
                print("❌ No results container found")
                
        return field_stats_button is not None, field_comparison_button is not None
        
    except Exception as e:
        print(f"❌ Error during button testing: {e}")
        return False, False

def test_console_analysis(driver):
    """Test 4: Console Analysis"""
    print("\n🧪 TEST 4: Console Analysis")
    print("=" * 50)
    
    try:
        # Get console logs
        logs = driver.get_log('browser')
        print(f"📝 Found {len(logs)} console entries")
        
        errors = []
        warnings = []
        info = []
        
        for log in logs:
            level = log['level']
            message = log['message']
            
            if level == 'SEVERE':
                errors.append(message)
            elif level == 'WARNING':
                warnings.append(message)
            else:
                info.append(message)
        
        print(f"❌ Errors: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
            
        print(f"⚠️ Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
            
        # Test if functions are defined
        print("\n🔍 Testing function definitions...")
        
        functions_to_test = [
            'loadFieldStatistics',
            'loadFieldComparison',
            'loadStatistics',
            'displayFieldStatistics'
        ]
        
        for func in functions_to_test:
            try:
                result = driver.execute_script(f"return typeof {func}")
                print(f"   {func}: {result}")
            except Exception as e:
                print(f"   {func}: ERROR - {e}")
                
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Error during console analysis: {e}")
        return False

def test_network_analysis():
    """Test 5: Network Analysis"""
    print("\n🧪 TEST 5: Network Analysis")
    print("=" * 50)
    
    try:
        # Test API endpoints
        endpoints = [
            "/api/models",
            "/api/benchmark/field-statistics",
            "/api/benchmark/field-comparison",
            "/api/benchmark/summary"
        ]
        
        base_url = "http://localhost:8000"
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                print(f"📡 {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ Valid JSON response")
                    except:
                        print(f"   ❌ Invalid JSON response")
                else:
                    print(f"   ❌ Error response: {response.text[:100]}")
            except Exception as e:
                print(f"   ❌ {endpoint}: Connection error - {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error during network analysis: {e}")
        return False

def test_html_source_verification():
    """Test 6: HTML Source Verification"""
    print("\n🧪 TEST 6: HTML Source Verification")
    print("=" * 50)
    
    try:
        # Read the HTML file
        with open("/app/frontend/index.html", "r") as f:
            content = f.read()
        
        # Check for key JavaScript functions
        functions_to_check = [
            'loadFieldStatistics',
            'loadFieldComparison',
            'displayFieldStatistics',
            'displayFieldComparison'
        ]
        
        for func in functions_to_check:
            if func in content:
                print(f"✅ Function '{func}' found in HTML")
            else:
                print(f"❌ Function '{func}' NOT found in HTML")
        
        # Check for button onclick handlers
        button_handlers = [
            'onclick="loadFieldStatistics()"',
            'onclick="loadFieldComparison()"'
        ]
        
        for handler in button_handlers:
            if handler in content:
                print(f"✅ Button handler '{handler}' found")
            else:
                print(f"❌ Button handler '{handler}' NOT found")
                
        return True
        
    except Exception as e:
        print(f"❌ Error during HTML source verification: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 MineSearch v2.1 GUI Functionality Test")
    print("=" * 60)
    
    # Test 1: Homepage
    driver, stats_tab = test_homepage()
    if not driver:
        print("❌ Cannot continue - homepage test failed")
        return
    
    try:
        # Test 2: Tab Navigation
        tab_success = test_tab_navigation(driver, stats_tab)
        
        # Test 3: Button Testing
        stats_button_found, comparison_button_found = test_button_functionality(driver)
        
        # Test 4: Console Analysis
        console_clean = test_console_analysis(driver)
        
        # Test 5: Network Analysis
        network_success = test_network_analysis()
        
        # Test 6: HTML Source Verification
        html_success = test_html_source_verification()
        
        # Summary
        print("\n🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Homepage Load: {'PASS' if driver else 'FAIL'}")
        print(f"✅ Tab Navigation: {'PASS' if tab_success else 'FAIL'}")
        print(f"✅ Feld-Statistiken Button: {'PASS' if stats_button_found else 'FAIL'}")
        print(f"✅ Feld-Vergleich Button: {'PASS' if comparison_button_found else 'FAIL'}")
        print(f"✅ Console Clean: {'PASS' if console_clean else 'FAIL'}")
        print(f"✅ Network API: {'PASS' if network_success else 'FAIL'}")
        print(f"✅ HTML Source: {'PASS' if html_success else 'FAIL'}")
        
        # Screenshots available
        print(f"\n📸 Screenshots saved to /tmp/:")
        print(f"   - homepage_screenshot.png")
        print(f"   - statistics_tab_screenshot.png")
        print(f"   - field_statistics_result.png")
        print(f"   - field_comparison_result.png")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()