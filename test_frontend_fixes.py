#!/usr/bin/env python3
"""
Test script to verify the frontend JavaScript fixes for field statistics and field comparison
"""
import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sys
import os

def test_api_endpoints():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Test field statistics API
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-statistics")
        field_stats = response.json()
        print(f"✅ Field Statistics API: {len(field_stats.get('by_field', {}))} fields found")
        
        # Check if data structure matches expected format
        if 'by_field' in field_stats:
            sample_field = next(iter(field_stats['by_field'].values()))
            print(f"   Sample field data: {sample_field[0]['field_name']} with {len(sample_field)} models")
        else:
            print("❌ Field Statistics API: Missing 'by_field' key")
            
    except Exception as e:
        print(f"❌ Field Statistics API failed: {e}")
    
    # Test field comparison API
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-comparison")
        field_comparison = response.json()
        print(f"✅ Field Comparison API: {len(field_comparison.get('hardest_fields', []))} hardest fields, {len(field_comparison.get('easiest_fields', []))} easiest fields")
        
        # Check if data structure matches expected format
        if 'hardest_fields' in field_comparison and 'easiest_fields' in field_comparison:
            if field_comparison['hardest_fields']:
                print(f"   Hardest field: {field_comparison['hardest_fields'][0]['field_name']} ({field_comparison['hardest_fields'][0]['avg_success_rate']:.1%})")
            if field_comparison['easiest_fields']:
                print(f"   Easiest field: {field_comparison['easiest_fields'][0]['field_name']} ({field_comparison['easiest_fields'][0]['avg_success_rate']:.1%})")
        else:
            print("❌ Field Comparison API: Missing required keys")
            
    except Exception as e:
        print(f"❌ Field Comparison API failed: {e}")

def test_frontend_with_selenium():
    """Test the frontend with Selenium"""
    print("\nTesting frontend with Selenium...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:8000/static/index.html")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Switch to Statistics tab
        print("Switching to Statistics tab...")
        stats_radio = wait.until(EC.element_to_be_clickable((By.ID, "method_statistics")))
        stats_radio.click()
        
        # Wait for statistics form to be active
        wait.until(EC.presence_of_element_located((By.ID, "statistics_form")))
        
        # Test Field Statistics button
        print("Testing Field Statistics button...")
        field_stats_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Feld-Statistiken')]")))
        field_stats_button.click()
        
        # Wait for table to load and check for data
        time.sleep(2)
        table_container = driver.find_element(By.ID, "statistics-table-container")
        table_html = table_container.get_attribute("innerHTML")
        
        if "Feld-Statistiken" in table_html and "Gefunden" in table_html:
            print("✅ Field Statistics table loaded successfully")
            # Check if actual data is displayed (not just zeros)
            if "100.0%" in table_html or "92.8%" in table_html:
                print("✅ Field Statistics shows actual data (not zeros)")
            else:
                print("❌ Field Statistics might still show zeros")
        else:
            print("❌ Field Statistics table not loaded properly")
            
        # Test Field Comparison button
        print("Testing Field Comparison button...")
        field_comp_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Feld-Vergleich')]")))
        field_comp_button.click()
        
        # Wait for comparison to load
        time.sleep(2)
        table_container = driver.find_element(By.ID, "statistics-table-container")
        table_html = table_container.get_attribute("innerHTML")
        
        if "Feld-Vergleich" in table_html and "Schwierigste Felder" in table_html:
            print("✅ Field Comparison loaded successfully")
            # Check if actual data is displayed
            if "92.8%" in table_html or "100.0%" in table_html:
                print("✅ Field Comparison shows actual data")
            else:
                print("❌ Field Comparison might not show proper data")
        else:
            print("❌ Field Comparison not loaded properly")
            
        # Check for JavaScript errors
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if js_errors:
            print(f"❌ JavaScript errors found: {len(js_errors)}")
            for error in js_errors:
                print(f"   {error['message']}")
        else:
            print("✅ No JavaScript errors found")
            
        driver.quit()
        
    except Exception as e:
        print(f"❌ Frontend testing failed: {e}")
        if 'driver' in locals():
            driver.quit()

def main():
    print("🧪 Testing MineSearch v2.1 Frontend Fixes")
    print("=" * 50)
    
    # Test API endpoints first
    test_api_endpoints()
    
    # Test frontend functionality
    try:
        test_frontend_with_selenium()
    except Exception as e:
        print(f"Selenium test failed: {e}")
        print("Note: Selenium testing requires Chrome/Chromium browser")
    
    print("\n" + "=" * 50)
    print("✅ Testing completed! Please manually verify the frontend works correctly.")
    print("Navigate to: http://localhost:8000/static/index.html")
    print("1. Click on 'Database' tab (📈 Suchstatistiken)")
    print("2. Click 'Field Statistics' button")
    print("3. Click 'Field Comparison' button")
    print("4. Verify tables show actual data, not zeros")

if __name__ == "__main__":
    main()