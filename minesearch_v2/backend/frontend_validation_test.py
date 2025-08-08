"""
Author: rahn
Datum: 30.07.2025
Version: 1.0
Beschreibung: Frontend Output Validation für konsolidierte Ergebnisse
"""

from playwright.sync_api import sync_playwright
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_frontend_output():
    """
    Teste die tatsächliche Browser-Ausgabe der konsolidierten Ergebnisse
    """
    validation_results = {
        'url_accessible': False,
        'consolidated_tab_found': False,
        'table_found': False,
        'column_count': 0,
        'required_columns_visible': {
            'Restaurationskosten': False,
            'Kostenjahr': False,
            'Dokumentenjahr': False,
            'Produktionsstart': False,
            'Minenfläche in qkm': False
        },
        'duplicate_check': {
            'total_rows': 0,
            'unique_mine_land_combinations': 0,
            'duplicates_found': False
        },
        'screenshot_taken': False
    }
    
    with sync_playwright() as p:
        try:
            # Browser starten
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Zur Frontend-URL navigieren
            logger.info("Navigiere zu http://localhost:8000")
            page.goto("http://localhost:8000", timeout=30000)
            validation_results['url_accessible'] = True
            
            # Warten bis die Seite geladen ist
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # Suche nach "Konsolidierte Ergebnisse" Tab
            logger.info("Suche nach 'Konsolidierte Ergebnisse' Tab")
            consolidated_tab = page.locator('text=Konsolidierte Ergebnisse').first
            
            if consolidated_tab.is_visible():
                logger.info("✅ Konsolidierte Ergebnisse Tab gefunden")
                validation_results['consolidated_tab_found'] = True
                
                # Klicke auf den Tab
                consolidated_tab.click()
                time.sleep(2)
                
                # Warte auf die Tabelle
                page.wait_for_selector('table', timeout=10000)
                table = page.locator('table').first
                
                if table.is_visible():
                    logger.info("✅ Tabelle gefunden")
                    validation_results['table_found'] = True
                    
                    # Zähle Spalten in der Tabelle
                    header_row = table.locator('thead tr').first
                    if header_row.is_visible():
                        headers = header_row.locator('th')
                        column_count = headers.count()
                        validation_results['column_count'] = column_count
                        logger.info(f"📊 Gefundene Spalten: {column_count}")
                        
                        # Prüfe spezifische Spalten
                        for i in range(column_count):
                            header_text = headers.nth(i).inner_text().strip()
                            logger.info(f"Spalte {i+1}: '{header_text}'")
                            
                            # Prüfe erforderliche Spalten
                            for required_col in validation_results['required_columns_visible']:
                                if required_col.lower() in header_text.lower():
                                    validation_results['required_columns_visible'][required_col] = True
                                    logger.info(f"✅ Erforderliche Spalte gefunden: {required_col}")
                    
                    # Prüfe auf Duplikate
                    body_rows = table.locator('tbody tr')
                    row_count = body_rows.count()
                    validation_results['duplicate_check']['total_rows'] = row_count
                    logger.info(f"📊 Gefundene Datenzeilen: {row_count}")
                    
                    # Sammle Mine/Land Kombinationen
                    mine_land_combinations = set()
                    for i in range(min(row_count, 50)):  # Prüfe max. 50 Zeilen
                        try:
                            row = body_rows.nth(i)
                            cells = row.locator('td')
                            if cells.count() >= 2:
                                mine_name = cells.nth(0).inner_text().strip()
                                land = cells.nth(1).inner_text().strip()
                                combination = f"{mine_name}|{land}"
                                mine_land_combinations.add(combination)
                        except Exception as e:
                            logger.warning(f"Fehler beim Lesen von Zeile {i}: {e}")
                    
                    validation_results['duplicate_check']['unique_mine_land_combinations'] = len(mine_land_combinations)
                    validation_results['duplicate_check']['duplicates_found'] = (
                        row_count > len(mine_land_combinations)
                    )
                    
                    if validation_results['duplicate_check']['duplicates_found']:
                        logger.warning("⚠️ Duplikate gefunden!")
                    else:
                        logger.info("✅ Keine Duplikate gefunden")
                    
                else:
                    logger.error("❌ Tabelle nicht sichtbar")
            else:
                logger.error("❌ Konsolidierte Ergebnisse Tab nicht gefunden")
            
            # Screenshot erstellen
            screenshot_path = "/app/minesearch_v2/backend/frontend_validation_screenshot.png"
            page.screenshot(path=screenshot_path, full_page=True)
            validation_results['screenshot_taken'] = True
            logger.info(f"📸 Screenshot gespeichert: {screenshot_path}")
            
            browser.close()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Frontend-Validierung: {e}")
    
    return validation_results

def print_validation_report(results):
    """
    Drucke einen detaillierten Validierungsbericht
    """
    print("\n" + "="*70)
    print("         FRONTEND OUTPUT VALIDATION BERICHT")
    print("="*70)
    
    print(f"\n🌐 URL Zugriff: {'✅ ERFOLGREICH' if results['url_accessible'] else '❌ FEHLGESCHLAGEN'}")
    print(f"📑 Konsolidierte Ergebnisse Tab: {'✅ GEFUNDEN' if results['consolidated_tab_found'] else '❌ NICHT GEFUNDEN'}")
    print(f"📊 Tabelle sichtbar: {'✅ JA' if results['table_found'] else '❌ NEIN'}")
    print(f"📋 Anzahl Spalten: {results['column_count']}")
    
    print("\n🔍 ERFORDERLICHE SPALTEN:")
    for col_name, found in results['required_columns_visible'].items():
        status = "✅ SICHTBAR" if found else "❌ NICHT SICHTBAR"
        print(f"   • {col_name}: {status}")
    
    print(f"\n👥 DUPLIKAT-PRÜFUNG:")
    print(f"   • Gesamtzeilen: {results['duplicate_check']['total_rows']}")
    print(f"   • Einzigartige Mine/Land: {results['duplicate_check']['unique_mine_land_combinations']}")
    duplicate_status = "❌ DUPLIKATE GEFUNDEN" if results['duplicate_check']['duplicates_found'] else "✅ KEINE DUPLIKATE"
    print(f"   • Status: {duplicate_status}")
    
    print(f"\n📸 Screenshot: {'✅ ERSTELLT' if results['screenshot_taken'] else '❌ FEHLGESCHLAGEN'}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    logger.info("🚀 Starte Frontend Output Validation")
    results = validate_frontend_output()
    print_validation_report(results)
    
    # Speichere Ergebnisse in Memory für Koordination
    try:
        import json
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        print(f"\n📊 VALIDIERUNG ABGESCHLOSSEN")
        print(f"Ergebnisse: {results_json}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Ergebnisse: {e}")