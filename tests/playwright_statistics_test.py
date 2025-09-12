"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Playwright Tests für Statistics Tab - Model Combination Issue
ÄNDERUNG 16.08.2025: Tests für Statistics-Tab Modell-Kombination vs. Einzelmodell-Problem
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, Browser, Page

class StatisticsTabTester:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"
        self.browser = None
        self.page = None

    async def setup(self):
        """Browser und Page initialisieren"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False, slow_mo=500)
        self.page = await self.browser.new_page()

        # Console-Logs abfangen für Debug
        self.page.on("console", lambda msg: print(f"🖥️ [BROWSER] {msg.type}: {msg.text}"))
        self.page.on("pageerror", lambda error: print(f"❌ [BROWSER-ERROR] {error}"))

    async def teardown(self):
        """Browser schließen"""
        if self.browser:
            await self.browser.close()

    async def test_current_statistics_behavior(self):
        """
        TEST 1: Dokumentiert aktuelles Verhalten - Modell-Kombinationen in Statistics Tab
        Analysiert wie model_used aktuell angezeigt wird
        """
        print("\n🧪 TEST 1: CURRENT STATISTICS BEHAVIOR")
        print("=" * 60)

        # Zur Hauptseite navigieren
        await self.page.goto(f"{self.base_url}/static/index.html")
        await self.page.wait_for_load_state("networkidle")

        # Warten auf Interface-Load
        await asyncio.sleep(2)

        # Statistics Tab aktivieren
        print("📊 [TEST] Aktiviere Statistics Tab...")
        stats_tab = await self.page.wait_for_selector("button[onclick='showStatistics()']", timeout=10000)
        await stats_tab.click()

        # Warten auf Statistics-Load
        await asyncio.sleep(3)

        # Statistics Container prüfen
        stats_container = await self.page.wait_for_selector("#model-statistics-table-container", timeout=10000)
        if stats_container:
            print("✅ [TEST] Statistics Container gefunden")

            # Alle Model Cards sammeln
            model_cards = await self.page.query_selector_all(".data-card")
            print(f"📋 [TEST] Gefundene Model Cards: {len(model_cards)}")

            # Analyse der aktuellen Modell-Namen
            for i, card in enumerate(model_cards[:5]):  # Erste 5 analysieren
                model_title = await card.query_selector(".card-title")
                if model_title:
                    title_text = await model_title.text_content()
                    print(f"   Card {i+1}: '{title_text}'")

                    # Prüfe auf Modell-Kombinationen
                    if ',' in title_text:
                        print(f"      ⚠️  MODELL-KOMBINATION ERKANNT: {title_text}")
                    else:
                        print(f"      ✅ Einzelmodell: {title_text}")

        return len(model_cards) if 'model_cards' in locals() else 0

    async def test_api_response_structure(self):
        """
        TEST 2: API Response-Struktur analysieren
        Prüft /api/consolidated/results für model_used Format
        """
        print("\n🧪 TEST 2: API RESPONSE STRUCTURE ANALYSIS")
        print("=" * 60)

        # API direkt aufrufen
        response = await self.page.evaluate("""
            async () => {
                try {
                    const response = await fetch('/api/consolidated/results?days_back=30&exclude_exa=true');
                    const data = await response.json();
                    return data;
                } catch (error) {
                    return { error: error.message };
                }
            }
        """)

        if 'data' in response and 'results' in response['data']:
            results = response['data']['results']
            print(f"📊 [TEST] API Response: {len(results)} Ergebnisse")

            # Analysiere model_used Muster
            model_used_patterns = {}
            for result in results[:10]:  # Erste 10 analysieren
                model_used = result.get("model_used", 'unknown')
                print(f"   Mine: {result.get("mine_name", 'N/A')} -> model_used: '{model_used}'")

                # Zähle Kombinations-Muster
                if ',' in model_used:
                    model_used_patterns[model_used] = model_used_patterns.get(model_used, 0) + 1
                    print(f"      🔍 KOMBINATION: {model_used}")
                else:
                    print(f"      ✅ Einzelmodell: {model_used}")

            print(f"\n📋 [TEST] Gefundene Modell-Kombinationen:")
            for pattern, count in model_used_patterns.items():
                print(f"   '{pattern}': {count}x verwendet")

            return model_used_patterns

        print("❌ [TEST] Keine API-Daten erhalten")
        return {}

    async def test_model_splitting_logic(self):
        """
        TEST 3: Model Splitting Logic validieren
        Testet die Aufspaltung von Modell-Kombinationen
        """
        print("\n🧪 TEST 3: MODEL SPLITTING LOGIC TEST")
        print("=" * 60)

        # Test-Daten für Splitting-Logic
        test_cases = [
            "openrouter:deepseek-free,perplexity:sonar",
            "openrouter:deepseek-free",
            "perplexity:sonar,tavily:search",
            "exa:neural"
        ]

        for test_case in test_cases:
            # JavaScript Model-Splitting evaluieren
            split_result = await self.page.evaluate(f"""
                () => {{
                    const modelUsed = '{test_case}';
                    const splitModels = modelUsed.split(',').map(m => m.trim());
                    return splitModels;
                }}
            """)

            print(f"   Input: '{test_case}'")
            print(f"   Split: {split_result}")
            print(f"   Count: {len(split_result)} Modelle")

        return test_cases

    async def test_statistics_tab_rendering(self):
        """
        TEST 4: Statistics Tab Rendering validieren
        Prüft wie Modell-Daten aktuell gerendert werden
        """
        print("\n🧪 TEST 4: STATISTICS TAB RENDERING")
        print("=" * 60)

        # Zur Statistics Tab navigieren
        await self.page.goto(f"{self.base_url}/static/index.html")
        await self.page.wait_for_load_state("networkidle")

        # Statistics aktivieren
        stats_tab = await self.page.wait_for_selector("button[onclick='showStatistics()']", timeout=10000)
        await stats_tab.click()
        await asyncio.sleep(3)

        # JavaScript Console-Output analysieren
        console_logs = []
        self.page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

        # Statistics erneut laden für Log-Capture
        await self.page.evaluate("window.loadStatistics()")
        await asyncio.sleep(2)

        # Relevante Logs filtern
        stats_logs = [log for log in console_logs if 'STATISTICS' in log or 'MOCK' in log]

        print("📋 [TEST] Relevante Console-Logs:")
        for log in stats_logs[-10:]:  # Letzte 10 relevante Logs
            print(f"   {log}")

        # Mock-Generierung Analyse
        mock_logs = [log for log in console_logs if 'MOCK' in log]
        if mock_logs:
            print(f"\n🔄 [TEST] Mock-Generierung: {len(mock_logs)} relevante Logs")

        return stats_logs

    async def run_comprehensive_test(self):
        """Führt alle Tests aus und erstellt Bericht"""
        print("🚀 COMPREHENSIVE STATISTICS TAB TESTING")
        print("=" * 80)

        test_results = {
            'current_behavior': None,
            'api_patterns': None,
            'splitting_logic': None,
            'rendering_logs': None
        }

        try:
            await self.setup()

            # Test 1: Current Behavior
            model_count = await self.test_current_statistics_behavior()
            test_results['current_behavior'] = {
                'model_cards_found': model_count,
                'status': 'completed'
            }

            # Test 2: API Response
            api_patterns = await self.test_api_response_structure()
            test_results['api_patterns'] = api_patterns

            # Test 3: Splitting Logic
            split_tests = await self.test_model_splitting_logic()
            test_results['splitting_logic'] = split_tests

            # Test 4: Rendering
            rendering_logs = await self.test_statistics_tab_rendering()
            test_results['rendering_logs'] = len(rendering_logs)

        except Exception as e:
            print(f"❌ [TEST-ERROR] {str(e)}")
            test_results['error'] = str(e)

        finally:
            await self.teardown()

        # Bericht erstellen
        print("\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        print(f"✅ Model Cards Found: {test_results['current_behavior']['model_cards_found'] if
test_results['current_behavior'] else 'N/A'}")
        print(f"✅ API Patterns: {len(test_results['api_patterns']) if test_results['api_patterns']
else 0} Kombinationen")
        print(f"✅ Splitting Tests: {len(test_results['splitting_logic']) if
test_results['splitting_logic'] else 0} Test-Cases")
        print(f"✅ Rendering Logs: {test_results['rendering_logs'] if test_results['rendering_logs']
else 0} relevante Logs")

        # Problem-Identifikation
        print("\n🔍 PROBLEM ANALYSIS")
        if test_results['api_patterns']:
            print("⚠️  ERKANNTES PROBLEM: API liefert Modell-Kombinationen in model_used")
            print("💡 LÖSUNG: Frontend muss model_used aufsplitten für separate Model-Cards")

        return test_results

# Test ausführen wenn direkt aufgerufen
if __name__ == "__main__":
    async def main():
        tester = StatisticsTabTester()
        results = await tester.run_comprehensive_test()

        # Ergebnisse in Datei speichern
        with open('/app/tests/statistics_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Test-Ergebnisse gespeichert: /app/tests/statistics_test_results.json")

    asyncio.run(main())
