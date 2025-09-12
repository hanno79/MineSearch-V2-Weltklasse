#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Comprehensive browser test for MineSearch field split implementation
              Tests the new "Fördermenge/Jahr Rohstoff" and "Fördermenge/Jahr Abraum" fields
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class MineSearchFieldTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"
        self.test_results = {
            "navigation": None,
            "search_execution": None,
            "field_validation": None,
            "data_validation": None,
            "screenshots": [],
            "errors": []
        }

    async def run_comprehensive_test(self):
        """Run complete browser test for MineSearch field split validation"""
        print("🚀 Starte umfassenden MineSearch Field Split Test")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                # Step 1: Navigate to MineSearch
                await self.step_1_navigate(page)

                # Step 2: Perform search for Mont Wright
                await self.step_2_perform_search(page)

                # Step 3: Monitor and wait for results
                await self.step_3_wait_for_results(page)

                # Step 4: Validate field names
                await self.step_4_validate_field_names(page)

                # Step 5: Validate data_dict content
                await self.step_5_validate_data_content(page)

                # Step 6: Take final screenshots and document
                await self.step_6_final_documentation(page)

            except Exception as e:
                self.test_results["errors"].append(f"Critical test error: {str(e)}")
                print(f"❌ Critical test error: {str(e)}")
                await page.screenshot(path='error_screenshot.png')

            finally:
                await browser.close()

        return self.test_results

    async def step_1_navigate(self, page):
        """Step 1: Navigate to MineSearch and access single search"""
        print("📍 Step 1: Navigating to MineSearch...")

        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')

            # Take initial screenshot
            await page.screenshot(path='01_homepage.png')
            self.test_results["screenshots"].append('01_homepage.png')

            # Check if page loaded correctly
            title = await page.title()
            print(f"✅ Page loaded: {title}")

            # Look for single search functionality
            # The interface should have search input fields
            mine_input = await page.query_selector('input[placeholder*="Mine"], input[id*="mine"], input[name*="mine"]')
            if mine_input:
                print("✅ Mine search input field found")
            else:
                print("⚠️ Mine search input not immediately visible, checking page structure...")

            self.test_results["navigation"] = "SUCCESS"

        except Exception as e:
            self.test_results["navigation"] = f"FAILED: {str(e)}"
            self.test_results["errors"].append(f"Navigation error: {str(e)}")
            print(f"❌ Navigation failed: {str(e)}")

    async def step_2_perform_search(self, page):
        """Step 2: Perform search for Mont Wright mine"""
        print("🔍 Step 2: Performing search for Mont Wright...")

        try:
            # Wait a bit for page to fully load
            await asyncio.sleep(2)

            # Look for search input fields - try different selectors
            selectors_to_try = [
                'input[placeholder*="Mine"]',
                'input[id*="mine"]',
                'input[name*="mine"]',
                'input[type="text"]',
                '#mine-name',
                '#mineName',
                '.search-input'
            ]

            mine_input = None
            for selector in selectors_to_try:
                mine_input = await page.query_selector(selector)
                if mine_input:
                    print(f"✅ Found mine input with selector: {selector}")
                    break

            if not mine_input:
                # Get all input elements to debug
                all_inputs = await page.query_selector_all('input')
                print(f"🔍 Found {len(all_inputs)} input elements on page")
                for i, input_elem in enumerate(all_inputs):
                    placeholder = await input_elem.get_attribute('placeholder') or ''
                    input_id = await input_elem.get_attribute('id') or ''
                    input_name = await input_elem.get_attribute('name') or ''
                    print(f"  Input {i}: placeholder='{placeholder}', id='{input_id}', name='{input_name}'")

                # Try first text input as fallback
                if all_inputs:
                    mine_input = all_inputs[0]
                    print("⚠️ Using first input element as fallback")

            if mine_input:
                # Enter mine name
                await mine_input.clear()
                await mine_input.fill("Mont Wright")
                print("✅ Entered 'Mont Wright' in mine field")

                # Look for country field
                country_selectors = [
                    'input[placeholder*="Country"]',
                    'input[placeholder*="Land"]',
                    'input[id*="country"]',
                    'input[name*="country"]'
                ]

                country_input = None
                for selector in country_selectors:
                    country_input = await page.query_selector(selector)
                    if country_input:
                        print(f"✅ Found country input with selector: {selector}")
                        break

                if country_input:
                    await country_input.clear()
                    await country_input.fill("Kanada")
                    print("✅ Entered 'Kanada' in country field")
                else:
                    print("⚠️ Country input not found, continuing...")

                # Look for model selection
                await self.select_ai_models(page)

                # Look for search/submit button
                search_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Search")',
                    'button:has-text("Suchen")',
                    'button:has-text("Start")',
                    '.search-button',
                    '#search-btn'
                ]

                search_button = None
                for selector in search_selectors:
                    try:
                        search_button = await page.query_selector(selector)
                        if search_button:
                            print(f"✅ Found search button with selector: {selector}")
                            break
                    except:
                        continue

                if search_button:
                    await page.screenshot(path='02_before_search.png')
                    self.test_results["screenshots"].append('02_before_search.png')

                    await search_button.click()
                    print("✅ Clicked search button")

                    self.test_results["search_execution"] = "SUCCESS"
                else:
                    # Try pressing Enter in the mine input field
                    print("⚠️ Search button not found, trying Enter key...")
                    await mine_input.press('Enter')
                    self.test_results["search_execution"] = "SUCCESS_FALLBACK"

            else:
                raise Exception("Could not find mine input field")

        except Exception as e:
            self.test_results["search_execution"] = f"FAILED: {str(e)}"
            self.test_results["errors"].append(f"Search execution error: {str(e)}")
            print(f"❌ Search execution failed: {str(e)}")

    async def select_ai_models(self, page):
        """Select AI models for the search"""
        print("🤖 Selecting AI models...")

        try:
            # Look for model selection checkboxes or dropdowns
            model_selectors = [
                'input[type="checkbox"]',
                'select',
                '.model-selector',
                '[data-model]'
            ]

            # Try to find and select some good models
            target_models = [
                'openrouter:deepseek-free',
                'openrouter:claude-3.5-sonnet',
                'openrouter:gpt-4o-mini'
            ]

            checkboxes = await page.query_selector_all('input[type="checkbox"]')
            selected_models = 0

            for checkbox in checkboxes:
                # Get associated label or value
                checkbox_id = await checkbox.get_attribute('id') or ''
                checkbox_value = await checkbox.get_attribute('value') or ''

                # Check if this checkbox corresponds to one of our target models
                for target_model in target_models:
                    if target_model in checkbox_id or target_model in checkbox_value:
                        is_checked = await checkbox.is_checked()
                        if not is_checked:
                            await checkbox.check()
                            print(f"✅ Selected model: {target_model}")
                            selected_models += 1
                        break

                # Limit to 2-3 models
                if selected_models >= 3:
                    break

            if selected_models == 0:
                # Fallback: select first few checkboxes
                print("⚠️ Target models not found, selecting first available models...")
                for i, checkbox in enumerate(checkboxes[:3]):
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.check()
                        selected_models += 1
                        print(f"✅ Selected model checkbox {i+1}")

            print(f"✅ Total models selected: {selected_models}")

        except Exception as e:
            print(f"⚠️ Model selection error (non-critical): {str(e)}")

    async def step_3_wait_for_results(self, page):
        """Step 3: Wait for search results to complete"""
        print("⏳ Step 3: Waiting for search results...")

        try:
            # Wait for results to appear - look for various result indicators
            result_selectors = [
                '.results-table',
                '.search-results',
                'table',
                '[data-results]',
                '.result'
            ]

            max_wait_time = 120  # 2 minutes max
            start_time = time.time()

            results_found = False
            while not results_found and (time.time() - start_time) < max_wait_time:
                for selector in result_selectors:
                    results_element = await page.query_selector(selector)
                    if results_element:
                        print(f"✅ Results found with selector: {selector}")
                        results_found = True
                        break

                if not results_found:
                    await asyncio.sleep(2)
                    print(f"⏳ Still waiting for results... ({int(time.time() - start_time)}s)")

            if results_found:
                # Wait a bit more for results to fully load
                await asyncio.sleep(5)
                await page.screenshot(path='03_results_loaded.png')
                self.test_results["screenshots"].append('03_results_loaded.png')
                print("✅ Search results loaded successfully")
            else:
                raise Exception("Search results did not appear within timeout period")

        except Exception as e:
            self.test_results["errors"].append(f"Results loading error: {str(e)}")
            print(f"❌ Results loading failed: {str(e)}")

    async def step_4_validate_field_names(self, page):
        """Step 4: Validate new field names are present and old ones are removed"""
        print("🏷️ Step 4: Validating field names...")

        try:
            # Look for table headers or field names
            header_selectors = [
                'th',
                '.column-header',
                '.field-name',
                'thead tr',
                '.table-header'
            ]

            all_headers = []
            for selector in header_selectors:
                headers = await page.query_selector_all(selector)
                for header in headers:
                    header_text = await header.inner_text()
                    if header_text.strip():
                        all_headers.append(header_text.strip())

            print(f"📋 Found {len(all_headers)} headers: {all_headers}")

            # Check for new field names
            target_new_fields = [
                "Fördermenge/Jahr Rohstoff",
                "Fördermenge/Jahr Abraum"
            ]

            found_new_fields = []
            for field in target_new_fields:
                found = any(field in header for header in all_headers)
                if found:
                    found_new_fields.append(field)
                    print(f"✅ NEW FIELD FOUND: {field}")
                else:
                    print(f"❌ NEW FIELD MISSING: {field}")

            # Check that old field name is NOT present
            old_field = "Fördermenge/Jahr"
            old_field_found = any(old_field == header for header in all_headers)

            if old_field_found:
                print(f"❌ OLD FIELD STILL PRESENT: {old_field}")
            else:
                print(f"✅ OLD FIELD CORRECTLY REMOVED: {old_field}")

            # Validation summary
            validation_result = {
                "new_fields_found": found_new_fields,
                "new_fields_expected": target_new_fields,
                "old_field_removed": not old_field_found,
                "all_headers": all_headers
            }

            self.test_results["field_validation"] = validation_result

            success_score = len(found_new_fields) / len(target_new_fields)
            if success_score >= 1.0 and not old_field_found:
                print("🎉 FIELD VALIDATION: COMPLETE SUCCESS")
            elif success_score >= 0.5:
                print("⚠️ FIELD VALIDATION: PARTIAL SUCCESS")
            else:
                print("❌ FIELD VALIDATION: FAILED")

        except Exception as e:
            self.test_results["field_validation"] = f"FAILED: {str(e)}"
            self.test_results["errors"].append(f"Field validation error: {str(e)}")
            print(f"❌ Field validation failed: {str(e)}")

    async def step_5_validate_data_content(self, page):
        """Step 5: Validate actual data_dict content in the new fields"""
        print("📊 Step 5: Validating data_dict content...")

        try:
            # Look for data_dict rows in results table
            row_selectors = [
                'tr',
                '.data-row',
                '.result-row'
            ]

            all_data = []
            for selector in row_selectors:
                rows = await page.query_selector_all(selector)
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        cell_text = await cell.inner_text()
                        row_data.append(cell_text.strip())
                    if row_data and any(cell for cell in row_data):  # Skip empty rows
                        all_data.append(row_data)

            print(f"📊 Found {len(all_data)} data_dict rows")

            # Analyze data_dict for Mont Wright mine
            mont_wright_data = []
            for row in all_data:
                row_text = ' '.join(row).lower()
                if 'mont wright' in row_text:
                    mont_wright_data.append(row)
                    print(f"🎯 Mont Wright row: {row}")

            # Look for production values in the data
            production_indicators = [
                'ton', 'tonnes', 'mt', 'million', 'thousand',
                'eisenerz', 'iron ore', 'ore'
            ]

            data_validation = {
                "mont_wright_rows_found": len(mont_wright_data),
                "production_data_found": False,
                "sample_data": mont_wright_data[:3] if mont_wright_data else [],
                "total_rows": len(all_data)
            }

            for row in mont_wright_data:
                row_text = ' '.join(row).lower()
                if any(indicator in row_text for indicator in production_indicators):
                    data_validation["production_data_found"] = True
                    break

            self.test_results["data_validation"] = data_validation

            if mont_wright_data:
                print(f"✅ Found {len(mont_wright_data)} Mont Wright entries")
                if data_validation["production_data_found"]:
                    print("✅ Production data_dict indicators found")
                else:
                    print("⚠️ No clear production data_dict indicators found")
            else:
                print("❌ No Mont Wright entries found in results")

        except Exception as e:
            self.test_results["data_validation"] = f"FAILED: {str(e)}"
            self.test_results["errors"].append(f"Data validation error: {str(e)}")
            print(f"❌ Data validation failed: {str(e)}")

    async def step_6_final_documentation(self, page):
        """Step 6: Take final screenshots and document findings"""
        print("📸 Step 6: Final documentation...")

        try:
            # Final full page screenshot
            await page.screenshot(path='04_final_results.png', full_page=True)
            self.test_results["screenshots"].append('04_final_results.png')

            # Try to get page content for analysis
            page_content = await page.content()

            # Save page content to file for further analysis
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(page_content)

            print("✅ Final documentation completed")

        except Exception as e:
            self.test_results["errors"].append(f"Documentation error: {str(e)}")
            print(f"⚠️ Documentation error: {str(e)}")


async def main():
    """Main test execution"""
    print("=" * 80)
    print("🔍 MINESEARCH FIELD SPLIT COMPREHENSIVE TEST")
    print("🎯 Testing new 'Fördermenge/Jahr Rohstoff' and 'Fördermenge/Jahr Abraum' fields")
    print("🏭 Target mine: Mont Wright (Quebec, Canada)")
    print("=" * 80)

    test = MineSearchFieldTest()
    results = await test.run_comprehensive_test()

    # Print comprehensive test report
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE TEST REPORT")
    print("=" * 80)

    print(f"🌐 Navigation: {results['navigation']}")
    print(f"🔍 Search Execution: {results['search_execution']}")
    print(f"🏷️ Field Validation: {results['field_validation']}")
    print(f"📊 Data Validation: {results['data_validation']}")
    print(f"📸 Screenshots: {len(results['screenshots'])} files")

    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   - {error}")

    # Field validation details
    if isinstance(results['field_validation'], dict):
        print(f"\n🏷️ FIELD VALIDATION DETAILS:")
        fv = results['field_validation']
        print(f"   New fields found: {fv.get("new_fields_found", [])}")
        print(f"   New fields expected: {fv.get("new_fields_expected", [])}")
        print(f"   Old field removed: {fv.get("old_field_removed", 'Unknown')}")
        print(f"   All headers found: {fv.get("all_headers", [])}")

    # Data validation details
    if isinstance(results['data_validation'], dict):
        print(f"\n📊 DATA VALIDATION DETAILS:")
        dv = results['data_validation']
        print(f"   Mont Wright rows: {dv.get("mont_wright_rows_found", 0)}")
        print(f"   Production data_dict found: {dv.get("production_data_found", False)}")
        print(f"   Total data_dict rows: {dv.get("total_rows", 0)}")
        if dv.get('sample_data'):
            print("   Sample Mont Wright data:")
            for i, row in enumerate(dv['sample_data'][:2]):
                print(f"     Row {i+1}: {row}")

    # Save detailed results to JSON
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Detailed results saved to: test_results.json")
    print(f"📸 Screenshots saved: {', '.join(results['screenshots'])}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
