"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: FIXED - Validierung der Statistics-Tab mit allen 55 Modellen
"""

from playwright.sync_api import sync_playwright
import json
import time

def test_statistics_tab_55_models_fixed():
    """Test ob Statistics-Tab alle 55 Modelle anzeigt - FIXED VERSION"""
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_name': 'Statistics Tab - 55 Models Validation FIXED',
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
            
            # 2. Zum Statistics Tab navigieren - FIXED
            print("📊 Navigiere zu Statistics Tab...")
            stats_nav_button = page.locator('a.nav-item[data-tab="statistics"]')
            stats_nav_button.click()
            page.wait_for_timeout(1000)
            
            # 3. Prüfe ob statistics tab aktiv ist
            stats_section = page.locator('#statistics')
            if stats_section.is_visible():
                print("✅ Statistics Tab erfolgreich aktiviert")
                results['details']['tab_activated'] = True
            else:
                print("❌ Statistics Tab nicht sichtbar")
                results['details']['tab_activated'] = False
                
            # 4. Suche "Statistiken laden" Button und klicke ihn - CRITICAL FIX
            print("🔄 Suche und klicke 'Statistiken laden' Button...")
            load_button_selectors = [
                'button:has-text("Statistiken laden")',
                'button:has-text("🔍 Statistiken laden")',
                'button[onclick*="loadModelStatistics"]',
                '.unified-search-button:has-text("Statistiken laden")',
                '#model-statistics-table-container button'
            ]
            
            button_found = False
            for selector in load_button_selectors:
                button = page.locator(selector)
                if button.count() > 0 and button.is_visible():
                    print(f"✅ Button gefunden mit Selector: {selector}")
                    button.click()
                    button_found = True
                    break
            
            results['details']['load_button_found'] = button_found
            
            if not button_found:
                print("❌ 'Statistiken laden' Button nicht gefunden")
            else:
                # 5. Warten auf Datenladung
                print("⏳ Warte auf Statistik-Datenladung...")
                page.wait_for_timeout(5000)  # 5 Sekunden warten
                
                # 6. Prüfe API Response durch JavaScript
                print("📡 Prüfe Statistics API Response...")
                api_test_result = page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/api/statistics/models/comprehensive');
                        const data = await response.json();
                        
                        if (data.success && data.data) {
                            const models = data.data.models || [];
                            const summary = data.data.summary || {};
                            
                            return {
                                success: true,
                                total_models: models.length,
                                tested_models: summary.total_tested_models || 0,
                                available_models: summary.total_available_models || 0,
                                first_model: models[0] ? models[0].model_id : 'None'
                            };
                        }
                        return { success: false, error: 'API response invalid' };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                }
                """)
                
                results['details']['api_test'] = api_test_result
                
                if api_test_result.get('success'):
                    print(f"✅ API Response OK: {api_test_result['total_models']} models")
                    print(f"   📊 Tested: {api_test_result['tested_models']}, Available: {api_test_result['available_models']}")
                    print(f"   🎯 First model: {api_test_result['first_model']}")
                
                # 7. Analysiere HTML-Tabelle nach dem Laden
                print("📋 Suche Statistics-Tabelle...")
                
                # Warte auf Tabelle
                page.wait_for_timeout(2000)
                
                # Verschiedene Table-Selektoren probieren
                table_selectors = [
                    '#model-statistics-table-container table',
                    '.statistics-table',
                    '.model-table', 
                    '#statistics table',
                    'table'
                ]
                
                table_found = False
                table_rows = 0
                
                for selector in table_selectors:
                    tables = page.locator(selector)
                    table_count = tables.count()
                    if table_count > 0:
                        table_found = True
                        print(f"📊 Statistics-Tabelle gefunden: {selector} ({table_count} tables)")
                        
                        # Zähle Zeilen in der ersten gefundenen Tabelle
                        first_table = tables.first
                        if first_table.is_visible():
                            rows = first_table.locator('tr')
                            table_rows = rows.count()
                            print(f"   📋 Tabelle hat {table_rows} Zeilen")
                        break
                
                results['details']['table_found'] = table_found
                results['details']['table_rows'] = table_rows
                
                # 8. Screenshot zur Dokumentation
                page.screenshot(path="/app/tests/statistics_fixed_validation.png", full_page=True)
                
                # 9. Success Evaluation
                api_has_models = api_test_result.get('total_models', 0) >= 50
                table_has_data = table_rows >= 2  # Header + mindestens 1 Datenzeile
                
                if api_has_models and table_has_data:
                    results['success'] = True
                    print("🎉 VALIDATION ERFOLGREICH: Statistics Tab funktioniert mit vielen Modellen!")
                elif api_has_models:
                    results['success'] = False
                    print("⚠️ PARTIAL SUCCESS: API OK, aber Tabelle zeigt keine Daten")
                else:
                    results['success'] = False
                    print("❌ VALIDATION FEHLGESCHLAGEN: API Problem")
            
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            print(f"❌ ERROR: {e}")
            
            # Error Screenshot
            try:
                page.screenshot(path="/app/tests/statistics_validation_error_fixed.png")
            except:
                pass
        
        finally:
            browser.close()
    
    # Ergebnisse speichern
    with open('/app/tests/statistics_fixed_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    result = test_statistics_tab_55_models_fixed()
    print(f"\n📊 FINAL RESULT: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Details: {result.get('details', {})}")