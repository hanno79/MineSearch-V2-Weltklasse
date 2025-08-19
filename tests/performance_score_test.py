"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test für neue Performance-Score Berechnung mit 4-Komponenten-System
"""

import asyncio
import json
from playwright.async_api import async_playwright

class PerformanceScoreSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.browser = None
        self.page = None
    
    async def setup(self):
        """Browser initialisieren"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
        self.page = await self.browser.new_page()
        
        # Console-Logs für Score-Berechnung abfangen
        self.console_logs = []
        self.page.on("console", lambda msg: self.console_logs.append(f"{msg.type}: {msg.text}"))
        
    async def teardown(self):
        """Browser schließen"""
        if self.browser:
            await self.browser.close()
    
    async def test_new_score_calculation(self):
        """Test the new 4-component score system"""
        print("\n🧪 TEST: Neue 4-Komponenten Score-Berechnung")
        print("=" * 60)
        
        # Navigate to Statistics tab
        await self.page.goto(f"{self.base_url}/static/index.html")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Clear console logs
        self.console_logs = []
        
        # Activate Statistics tab
        print("📊 Aktiviere Statistics Tab...")
        await self.page.click('header nav a[href="#statistics"]')
        await asyncio.sleep(5)  # Mehr Zeit für neue Score-Berechnung
        
        # Check for score calculation logs
        score_logs = [log for log in self.console_logs if 'SCORE' in log]
        split_logs = [log for log in self.console_logs if 'SPLIT' in log]
        
        print(f"\n📊 Score-Calculation Logs: {len(score_logs)}")
        for log in score_logs[:5]:  # Erste 5 Score-Logs
            print(f"   {log}")
        
        print(f"\n🔧 Model-Splitting Logs: {len(split_logs)}")
        for log in split_logs[:3]:  # Erste 3 Split-Logs
            print(f"   {log}")
        
        return len(score_logs) > 0
    
    async def test_score_breakdown_display(self):
        """Test the detailed score breakdown on model cards"""
        print("\n🧪 TEST: Score-Breakdown auf Model-Cards")
        print("=" * 60)
        
        # Navigate to Statistics tab if not already there
        await self.page.goto(f"{self.base_url}/static/index.html")
        await self.page.wait_for_load_state("networkidle")
        
        # Activate Statistics tab
        await self.page.click('header nav a[href="#statistics"]')
        await asyncio.sleep(4)
        
        # Wait for model cards to load
        await self.page.wait_for_selector(".data-card", timeout=10000)
        
        # Check for score breakdown sections
        breakdown_sections = await self.page.query_selector_all(".score-breakdown-section")
        print(f"📋 Score-Breakdown Sections gefunden: {len(breakdown_sections)}")
        
        if breakdown_sections:
            # Analyze first breakdown section
            first_section = breakdown_sections[0]
            section_text = await first_section.text_content()
            print(f"\n📊 Erste Score-Breakdown:")
            print(f"   {section_text[:200]}...")
            
            # Check for specific components
            components = ['Feldqualität', 'Konsistenz', 'Geschwindigkeit', 'Kosten']
            found_components = []
            for component in components:
                if component in section_text:
                    found_components.append(component)
            
            print(f"\n✅ Gefundene Score-Komponenten: {found_components}")
            return len(found_components) >= 4
        else:
            print("❌ Keine Score-Breakdown Sections gefunden")
            return False
    
    async def test_confidence_display(self):
        """Test confidence percentage display"""
        print("\n🧪 TEST: Konfidenz-Anzeige")
        print("=" * 60)
        
        # Look for confidence indicators in performance scores
        confidence_elements = await self.page.query_selector_all("small:has-text('Konfidenz')")
        print(f"📊 Konfidenz-Anzeigen gefunden: {len(confidence_elements)}")
        
        if confidence_elements:
            # Analyze confidence texts
            for i, element in enumerate(confidence_elements[:3]):
                text = await element.text_content()
                print(f"   Konfidenz {i+1}: {text}")
            return True
        else:
            print("❌ Keine Konfidenz-Anzeigen gefunden")
            return False
    
    async def test_score_consistency_fix(self):
        """Test that score inconsistencies are resolved"""
        print("\n🧪 TEST: Score-Konsistenz (10/10 + 0% Bug-Fix)")
        print("=" * 60)
        
        # Get all model cards
        model_cards = await self.page.query_selector_all(".model-stats-card")
        print(f"📋 Model Cards analysiert: {len(model_cards)}")
        
        inconsistencies_found = 0
        for i, card in enumerate(model_cards[:5]):  # Erste 5 Cards
            try:
                # Extract score and success rate
                score_element = await card.query_selector(".performance-score")
                success_element = await card.query_selector(".data-row:has-text('Erfolgsrate') .data-value")
                
                if score_element and success_element:
                    score_text = await score_element.text_content()
                    success_text = await success_element.text_content()
                    
                    print(f"   Card {i+1}: Score={score_text.strip()}, Erfolgsrate={success_text.strip()}")
                    
                    # Check for impossible combinations
                    if "10.0/10" in score_text and "0.0%" in success_text:
                        inconsistencies_found += 1
                        print(f"      ⚠️  INKONSISTENZ GEFUNDEN: Score 10/10 + 0% Erfolgsrate")
                    elif "0.0%" in success_text and any(x in score_text for x in ["8.", "9.", "10."]):
                        inconsistencies_found += 1
                        print(f"      ⚠️  INKONSISTENZ: Hoher Score + 0% Erfolgsrate")
                    else:
                        print(f"      ✅ Konsistent")
                        
            except Exception as e:
                print(f"   Card {i+1}: Fehler beim Analysieren - {e}")
        
        print(f"\n📊 KONSISTENZ-ANALYSE:")
        print(f"   Inkonsistenzen gefunden: {inconsistencies_found}")
        print(f"   Status: {'REPARIERT' if inconsistencies_found == 0 else 'NOCH PROBLEME'}")
        
        return inconsistencies_found == 0
    
    async def run_comprehensive_test(self):
        """Run all performance score tests"""
        print("🚀 COMPREHENSIVE PERFORMANCE-SCORE SYSTEM TEST")
        print("=" * 80)
        
        test_results = {}
        
        try:
            await self.setup()
            
            # Test 1: Score Calculation
            test_results['score_calculation'] = await self.test_new_score_calculation()
            
            # Test 2: Score Breakdown Display
            test_results['breakdown_display'] = await self.test_score_breakdown_display()
            
            # Test 3: Confidence Display
            test_results['confidence_display'] = await self.test_confidence_display()
            
            # Test 4: Score Consistency Fix
            test_results['consistency_fix'] = await self.test_score_consistency_fix()
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            test_results['error'] = str(e)
        
        finally:
            await self.teardown()
        
        # Final Report
        print("\n📊 FINAL PERFORMANCE-SCORE TEST REPORT")
        print("=" * 80)
        passed_tests = sum(1 for result in test_results.values() if result is True)
        total_tests = len([k for k in test_results.keys() if k != 'error'])
        
        print(f"✅ Score Calculation: {'PASSED' if test_results.get('score_calculation') else 'FAILED'}")
        print(f"✅ Breakdown Display: {'PASSED' if test_results.get('breakdown_display') else 'FAILED'}")
        print(f"✅ Confidence Display: {'PASSED' if test_results.get('confidence_display') else 'FAILED'}")
        print(f"✅ Consistency Fix: {'PASSED' if test_results.get('consistency_fix') else 'FAILED'}")
        print(f"\n🎯 GESAMTERGEBNIS: {passed_tests}/{total_tests} Tests bestanden")
        
        if passed_tests == total_tests:
            print("🎉 PERFORMANCE-SCORE REVOLUTION ERFOLGREICH!")
        else:
            print("⚠️  Einige Tests fehlgeschlagen - weitere Optimierung nötig")
        
        return test_results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = PerformanceScoreSystemTester()
        results = await tester.run_comprehensive_test()
        
        # Save results
        with open('/app/tests/performance_score_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved: /app/tests/performance_score_results.json")
    
    asyncio.run(main())