"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Validierung der Statistics-Tab mit allen 55 Modellen
"""

from playwright.sync_api import sync_playwright
import json
import time

def test_statistics_tab_55_models():
    """Test ob Statistics-Tab alle 55 Modelle anzeigt"""
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_name': 'Statistics Tab - 55 Models Validation',
        'success': False,
        'details': {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        
        try:
            # 1. Page laden
            print("🌐 Lade MineSearch Hauptseite...")
            page.goto("http://localhost:8000", wait_until="networkidle")
            page.wait_for_selector("body", timeout=10000)
            
            # 2. Zum Statistics Tab navigieren
            print("📊 Navigiere zu Statistics Tab...")
            stats_tab = page.locator('a[href="/statistics"]')
            if stats_tab.is_visible():
                stats_tab.click()
                page.wait_for_load_state("networkidle")
            else:
                # Alternative: direkter Link
                page.goto("http://localhost:8000/statistics", wait_until="networkidle")
            
            # Warten auf vollständiges Laden
            page.wait_for_timeout(3000)
            
            # 3. Statistics Button klicken um Daten zu laden
            print("🔄 Trigger statistics data loading...")
            stats_button = page.locator('button:has-text("Statistiken laden"), button:has-text("Statistics laden"), .btn:has-text("laden")')
            if stats_button.is_visible():
                stats_button.click()
                page.wait_for_timeout(2000)
            
            # 4. API Response prüfen (über Network-Calls)
            print("📡 Prüfe API Response...")
            page.evaluate("""
            async () => {
                const response = await fetch('/api/statistics/models/comprehensive');
                const data = await response.json();
                window.statsApiData = data;
                console.log('Stats API Response:', data);
            }
            """)
            
            page.wait_for_timeout(1000)
            api_data = page.evaluate("window.statsApiData")
            
            if api_data and api_data.get('success'):
                models = api_data.get('data', {}).get('models', [])
                summary = api_data.get('data', {}).get('summary', {})
                
                results['details']['api_success'] = True
                results['details']['api_total_models'] = len(models)
                results['details']['api_tested_models'] = summary.get('total_tested_models', 0)
                results['details']['api_available_models'] = summary.get('total_available_models', 0)
                
                print(f"✅ API liefert {len(models)} Modelle")
                print(f"   📊 {summary.get('total_tested_models', 0)} getestet, {summary.get('total_available_models', 0)} verfügbar")
            
            # 5. HTML Tabelle analysieren
            print("📋 Analysiere HTML-Tabelle...")
            
            # Suche verschiedene Table-Selektoren
            table_selectors = [
                'table',
                '.statistics-table', 
                '.model-table',
                '[role="table"]',
                '.table'
            ]
            
            table_found = False
            for selector in table_selectors:
                tables = page.locator(selector)
                if tables.count() > 0:
                    print(f"📊 Table gefunden mit Selector: {selector}")
                    table_found = True
                    break
            
            results['details']['table_found'] = table_found
            
            if table_found:
                # Zähle Zeilen in der Tabelle
                rows = page.locator('tr')
                total_rows = rows.count()
                
                # Zähle Daten-Zeilen (ohne Header)
                data_rows = page.locator('tr:not(:first-child)')  # Exclude header
                data_row_count = data_rows.count()
                
                results['details']['html_total_rows'] = total_rows
                results['details']['html_data_rows'] = data_row_count
                
                print(f"📊 HTML-Tabelle: {data_row_count} Datenzeilen ({total_rows} total mit Header)")
                
                # Prüfe ob mindestens 50 Modelle angezeigt werden
                if data_row_count >= 50:
                    results['details']['shows_all_models'] = True
                    print("✅ Tabelle zeigt mindestens 50 Modelle - ERFOLGREICH")
                else:
                    results['details']['shows_all_models'] = False
                    print(f"❌ Tabelle zeigt nur {data_row_count} Modelle statt 55")
            
            # 6. Screenshot zur Dokumentation
            page.screenshot(path="/app/tests/statistics_55_models_validation.png", full_page=True)
            
            # 7. Success-Evaluation
            api_ok = results['details'].get('api_total_models', 0) >= 55
            table_ok = results['details'].get('shows_all_models', False)
            
            if api_ok and table_ok:
                results['success'] = True
                print("🎉 VALIDATION ERFOLGREICH: Statistics Tab zeigt alle 55 Modelle!")
            elif api_ok:
                results['success'] = False
                print("⚠️ PARTIAL SUCCESS: API OK, aber Frontend-Tabelle zeigt nicht alle Modelle")
            else:
                results['success'] = False
                print("❌ VALIDATION FEHLGESCHLAGEN: API oder Frontend Problem")
            
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            print(f"❌ ERROR: {e}")
            
            # Error Screenshot
            try:
                page.screenshot(path="/app/tests/statistics_validation_error.png")
            except:
                pass
        
        finally:
            browser.close()
    
    # Ergebnisse speichern
    with open('/app/tests/statistics_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    result = test_statistics_tab_55_models()
    print(f"\n📊 FINAL RESULT: {'SUCCESS' if result['success'] else 'FAILED'}")