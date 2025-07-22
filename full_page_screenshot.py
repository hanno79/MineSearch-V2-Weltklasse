#!/usr/bin/env python3
"""
Get full page screenshot showing statistics section
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def get_full_page_screenshots():
    driver = create_driver()
    
    try:
        # Load page
        driver.get("http://localhost:8000/static/index.html")
        time.sleep(2)
        
        # Scroll down to see tabs
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        # Save screenshot showing tabs
        driver.save_screenshot("/tmp/page_with_tabs.png")
        print("✅ Page with tabs screenshot saved")
        
        # Click on statistics tab
        stats_radio = driver.find_element(By.ID, "method_statistics")
        driver.execute_script("arguments[0].click();", stats_radio)
        time.sleep(2)
        
        # Scroll to statistics section
        driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(1)
        
        # Save screenshot of statistics section
        driver.save_screenshot("/tmp/statistics_section.png")
        print("✅ Statistics section screenshot saved")
        
        # Click Field Statistics button
        field_stats_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'loadFieldStatistics')]")
        driver.execute_script("arguments[0].click();", field_stats_button)
        time.sleep(5)
        
        # Scroll to results
        driver.execute_script("window.scrollTo(0, 1600);")
        time.sleep(1)
        
        # Save screenshot of results
        driver.save_screenshot("/tmp/field_statistics_results.png")
        print("✅ Field statistics results screenshot saved")
        
        # Click Field Comparison button
        field_comparison_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'loadFieldComparison')]")
        driver.execute_script("arguments[0].click();", field_comparison_button)
        time.sleep(5)
        
        # Save screenshot of comparison results
        driver.save_screenshot("/tmp/field_comparison_results.png")
        print("✅ Field comparison results screenshot saved")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    get_full_page_screenshots()