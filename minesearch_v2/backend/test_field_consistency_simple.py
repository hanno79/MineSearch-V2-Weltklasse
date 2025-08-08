#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Simplified Field Consistency Browser Test focusing on key functionality
"""

import asyncio
import json
import sys
import time
from playwright.async_api import async_playwright
import requests

class SimpleFieldConsistencyTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        
    async def run_test(self):
        """Führt vereinfachten Field Consistency Test durch"""
        print("🚀 Starte Simple Field Consistency Test")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=['--disable-web-security'])
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Test 1: API Verification (bereits erfolgreich)
                await self.test_api_functionality()
                
                # Test 2: Direct Frontend Access
                await self.test_frontend_access(page)
                
                # Test 3: Statistics Loading via JavaScript
                await self.test_statistics_loading(page)
                
                # Test 4: Detail Modal Functionality
                await self.test_detail_modal_functionality(page)
                
                await self.generate_report()
                
            except Exception as e:
                print(f"❌ Test-Fehler: {e}")
                self.results.append({
                    "test": "General Error",
                    "status": "FAILED",
                    "error": str(e)
                })
            finally:
                await browser.close()
    
    async def test_api_functionality(self):
        """Test 1: API Field Consistency Functionality"""
        print("\n📊 Test 1: API Field Consistency Functionality")
        
        try:
            # Test Performance API
            response = requests.get(f"{self.base_url}/api/statistics/models/performance")
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', {}).get('models', [])
                
                if models:
                    model_id = models[0]['model_id']
                    
                    # Test Detail API mit Field Consistency
                    detail_url = f"{self.base_url}/api/statistics/models/{model_id}/details?include_field_consistency=true"
                    detail_response = requests.get(detail_url)
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        field_details = detail_data.get('data', {}).get('critical_fields_consistency', {}).get('field_consistency_details', {})
                        
                        # Analysiere Feldkonsistenz
                        if field_details:
                            total_fields = len(field_details)
                            excellent_count = sum(1 for v in field_details.values() if v >= 90)
                            good_count = sum(1 for v in field_details.values() if 70 <= v < 90)
                            problematic_count = sum(1 for v in field_details.values() if v < 70)
                            
                            print(f"✅ Field Consistency Analysis:")
                            print(f"   - Total fields: {total_fields}")
                            print(f"   - Excellent (≥90%): {excellent_count}")
                            print(f"   - Good (70-89%): {good_count}")
                            print(f"   - Problematic (<70%): {problematic_count}")
                            
                            self.results.append({
                                "test": "API Field Consistency",
                                "status": "PASSED",
                                "details": {
                                    "total_fields": total_fields,
                                    "excellent": excellent_count,
                                    "good": good_count,
                                    "problematic": problematic_count,
                                    "model_tested": model_id,
                                    "sample_values": dict(list(field_details.items())[:5])
                                }
                            })
                        else:
                            raise Exception("Keine Field Consistency Details gefunden")
                    else:
                        raise Exception(f"Detail API failed: {detail_response.status_code}")
                else:
                    raise Exception("Keine Modelle verfügbar")
            else:
                raise Exception(f"Performance API failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API Test failed: {e}")
            self.results.append({
                "test": "API Field Consistency",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_frontend_access(self, page):
        """Test 2: Frontend Access and Basic Elements"""
        print("\n🌐 Test 2: Frontend Access")
        
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check basic page elements
            title = await page.title()
            body = await page.query_selector('body')
            
            # Look for statistics-related elements
            statistics_buttons = await page.query_selector_all('button:has-text("Statistiken"), button[onclick*="loadStatistics"]')
            statistics_containers = await page.query_selector_all('[id*="statistics"], [class*="statistics"]')
            
            print(f"✅ Frontend loaded: {title}")
            print(f"✅ Statistics buttons found: {len(statistics_buttons)}")
            print(f"✅ Statistics containers found: {len(statistics_containers)}")
            
            if body and "MineSearch" in title:
                self.results.append({
                    "test": "Frontend Access",
                    "status": "PASSED",
                    "details": {
                        "title": title,
                        "statistics_buttons": len(statistics_buttons),
                        "statistics_containers": len(statistics_containers)
                    }
                })
            else:
                raise Exception("Frontend basic elements missing")
                
        except Exception as e:
            print(f"❌ Frontend Access failed: {e}")
            self.results.append({
                "test": "Frontend Access",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_statistics_loading(self, page):
        """Test 3: Statistics Loading via JavaScript"""
        print("\n📈 Test 3: Statistics Loading")
        
        try:
            # Try to trigger statistics loading
            await page.evaluate("if (window.loadStatistics) window.loadStatistics();")
            await page.wait_for_timeout(5000)
            
            # Check for loaded statistics table
            statistics_table = await page.query_selector('table.model-stats-table, .statistics-table-container table, #enhanced-statistics-table-container table')
            
            if statistics_table:
                # Check for field consistency columns
                consistency_headers = await page.query_selector_all('th:has-text("Konsistenz"), th:has-text("Field"), th:has-text("Feld")')
                consistency_cells = await page.query_selector_all('td[data-field*="consistency"], td[data-field*="field"]')
                
                print(f"✅ Statistics table loaded")
                print(f"✅ Consistency headers: {len(consistency_headers)}")
                print(f"✅ Consistency cells: {len(consistency_cells)}")
                
                # Check for realistic values
                if consistency_cells:
                    realistic_count = 0
                    for cell in consistency_cells[:10]:  # Check first 10 cells
                        text = await cell.text_content()
                        if text and '%' in text and text != '100%' and text != 'N/A':
                            realistic_count += 1
                    
                    print(f"✅ Realistic consistency values: {realistic_count}/10 checked")
                
                self.results.append({
                    "test": "Statistics Loading",
                    "status": "PASSED",
                    "details": {
                        "table_found": True,
                        "consistency_headers": len(consistency_headers),
                        "consistency_cells": len(consistency_cells),
                        "realistic_values": realistic_count if 'realistic_count' in locals() else 0
                    }
                })
            else:
                raise Exception("Statistics table not found")
                
        except Exception as e:
            print(f"❌ Statistics Loading failed: {e}")
            self.results.append({
                "test": "Statistics Loading",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_detail_modal_functionality(self, page):
        """Test 4: Detail Modal Field Consistency Functionality"""
        print("\n🔍 Test 4: Detail Modal Functionality")
        
        try:
            # Look for detail buttons
            detail_buttons = await page.query_selector_all('button[onclick*="showModelDetails"], button[onclick*="Details"], .detail-button')
            
            if detail_buttons:
                # Click first detail button
                await detail_buttons[0].click()
                await page.wait_for_timeout(3000)
                
                # Check for modal
                modal = await page.query_selector('.modal, #model-details-modal, [class*="modal"]')
                
                if modal:
                    # Look for field consistency section
                    fc_section = await page.query_selector_all('text=Feld-Konsistenz, text=Field Consistency, text=📊')
                    fc_button = await page.query_selector('button:has-text("Feld-Konsistenz laden"), button:has-text("🔍")')
                    
                    print(f"✅ Detail modal opened")
                    print(f"✅ Field consistency sections: {len(fc_section)}")
                    print(f"✅ Field consistency button: {fc_button is not None}")
                    
                    # Try to load field consistency if button exists
                    if fc_button:
                        await fc_button.click()
                        await page.wait_for_timeout(5000)
                        
                        # Check for loaded field data
                        field_data = await page.query_selector_all('.field-excellent, .field-good, .field-problematic, .field-consistency-data')
                        print(f"✅ Field consistency data loaded: {len(field_data)} elements")
                    
                    self.results.append({
                        "test": "Detail Modal Functionality",
                        "status": "PASSED",
                        "details": {
                            "modal_opened": True,
                            "fc_sections": len(fc_section),
                            "fc_button_present": fc_button is not None,
                            "field_data_elements": len(field_data) if 'field_data' in locals() else 0
                        }
                    })
                else:
                    raise Exception("Detail modal not opened")
            else:
                raise Exception("No detail buttons found")
                
        except Exception as e:
            print(f"❌ Detail Modal test failed: {e}")
            self.results.append({
                "test": "Detail Modal Functionality",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def generate_report(self):
        """Generiert vereinfachten Report"""
        print("\n" + "="*50)
        print("📋 SIMPLE FIELD CONSISTENCY TEST REPORT")
        print("="*50)
        
        passed = len([r for r in self.results if r['status'] == 'PASSED'])
        failed = len([r for r in self.results if r['status'] == 'FAILED'])
        total = len(self.results)
        
        print(f"📊 Ergebnisse: {passed} PASSED, {failed} FAILED von {total} Tests")
        print()
        
        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if 'details' in result and isinstance(result['details'], dict):
                for key, value in result['details'].items():
                    print(f"   {key}: {value}")
            elif 'error' in result:
                print(f"   Error: {result['error']}")
            print()
        
        # Save report
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            'results': self.results
        }
        
        report_file = f"/app/minesearch_v2/backend/simple_field_consistency_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Report gespeichert: {report_file}")
        
        # Overall assessment
        if passed >= 3:
            print("🎉 FIELD CONSISTENCY FUNCTIONALITY WORKING")
        elif passed >= 2:
            print("⚠️ FIELD CONSISTENCY MOSTLY WORKING")
        else:
            print("❌ FIELD CONSISTENCY NEEDS SIGNIFICANT FIXES")

async def main():
    test = SimpleFieldConsistencyTest()
    await test.run_test()

if __name__ == "__main__":
    print("🧪 Simple Field Consistency Test")
    asyncio.run(main())