#!/usr/bin/env python3
"""
Comprehensive Eleonore Mine Test mit Playwright
Prüft alle Fixes: Loading, Normalisierung, Scores, Statistiken
"""

import asyncio
import time
import sys
from playwright.async_api import async_playwright

async def comprehensive_eleonore_test():
    print("🚀 STARTE UMFASSENDEN ELEONORE MINE TEST")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Browser mit Desktop-Größe starten
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-web-security']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # SCHRITT 1: Navigation zur MineSearch Oberfläche
            print("\n📡 SCHRITT 1: Navigation zur MineSearch...")
            await page.goto('http://localhost:8000/static/index.html', wait_until='networkidle')
            await asyncio.sleep(3)
            
            # SCHRITT 2: Einzelsuche-Tab sicherstellen
            print("🔍 SCHRITT 2: Einzelsuche-Tab aktivieren...")
            await page.click('.nav-item[data-tab="single"]')
            await asyncio.sleep(2)
            
            # SCHRITT 3: Mine-Name eingeben
            print("⛏️ SCHRITT 3: 'Eleonore' eingeben...")
            await page.fill('input[name="mine_name"]', 'Eleonore')
            await asyncio.sleep(1)
            
            # SCHRITT 4: Alle Modelle auswählen
            print("🤖 SCHRITT 4: Alle Modelle auswählen...")
            
            # Versuche "Alle auswählen" Button
            select_all_buttons = [
                'button:has-text("Alle auswählen")',
                'button:has-text("Select All")', 
                '.select-all-btn',
                '[onclick*="selectAll"]'
            ]
            
            selected_all = False
            for btn_selector in select_all_buttons:
                try:
                    if await page.locator(btn_selector).count() > 0:
                        await page.click(btn_selector)
                        await asyncio.sleep(1)
                        print("   ✅ 'Alle auswählen' Button gefunden und geklickt")
                        selected_all = True
                        break
                except:
                    continue
            
            if not selected_all:
                # Manuell Modelle auswählen
                checkboxes = page.locator('input[type="checkbox"][name="selected_models"]')
                count = await checkboxes.count()
                print(f"   📋 {count} Modell-Checkboxen gefunden - wähle alle aus...")
                
                for i in range(count):
                    checkbox = checkboxes.nth(i)
                    if not await checkbox.is_checked():
                        await checkbox.check()
                        await asyncio.sleep(0.1)
                print(f"   ✅ {count} Modelle ausgewählt")
            
            # SCHRITT 5: Suche starten
            print("🚀 SCHRITT 5: Suche starten...")
            search_selectors = [
                'button[type="submit"]',
                'button:has-text("Search")',
                'button:has-text("Suchen")',
                '.search-btn',
                '#search-button'
            ]
            
            search_started = False
            for selector in search_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        print(f"   ✅ Suche gestartet mit Selector: {selector}")
                        search_started = True
                        break
                except:
                    continue
            
            if not search_started:
                print("   ❌ Konnte keinen Such-Button finden!")
                return
            
            # SCHRITT 6: Warten auf Suchabschluss
            print("⏳ SCHRITT 6: Warte auf Suchabschluss (max 4 Minuten)...")
            start_time = time.time()
            max_wait = 240  # 4 Minuten
            
            while time.time() - start_time < max_wait:
                # Prüfe Loading-Indikatoren
                loading_selectors = [
                    '.loading', '.spinner', '[class*="loading"]', 
                    '[class*="spinner"]', '.progress'
                ]
                
                loading_active = False
                for selector in loading_selectors:
                    if await page.locator(selector).count() > 0:
                        loading_active = True
                        break
                
                # Prüfe Ergebnisse
                result_selectors = [
                    '#results', '.results-container', '.mine-card',
                    '.field-based-card', '.result-card'
                ]
                
                results_content = ""
                for selector in result_selectors:
                    if await page.locator(selector).count() > 0:
                        results_content = await page.locator(selector).first.text_content()
                        break
                
                elapsed = int(time.time() - start_time)
                print(f"   ⏱️ {elapsed}s - Loading: {loading_active}, Results: {len(results_content)} chars")
                
                # Suche abgeschlossen?
                if not loading_active and len(results_content) > 100:
                    print("   ✅ Suche erfolgreich abgeschlossen!")
                    break
                
                await asyncio.sleep(3)
            
            # SCHRITT 7: Detaillierte Ergebnis-Analyse
            print("\n" + "=" * 60)
            print("📊 SCHRITT 7: UMFASSENDE ERGEBNIS-ANALYSE")
            print("=" * 60)
            
            # Screenshot erstellen
            await page.screenshot(path='/app/eleonore_search_complete.png', full_page=True)
            print("📸 Screenshot gespeichert: /app/eleonore_search_complete.png")
            
            # Analysiere Suchergebnisse
            await analyze_search_results_detailed(page)
            
            # SCHRITT 8: Statistik-Tab prüfen
            print("\n📈 SCHRITT 8: Statistik-Tab Analyse...")
            await page.click('.nav-item[data-tab="statistics"]')
            await asyncio.sleep(4)  # Warte auf Statistics Loading
            
            await analyze_statistics_tab_detailed(page)
            
            # SCHRITT 9: Ergebnis-Tab prüfen (der ursprünglich nicht funktionierte)
            print("\n📋 SCHRITT 9: Ergebnis-Tab prüfen (Loading-Fix)...")
            await page.click('.nav-item[data-tab="consolidated"]')
            await asyncio.sleep(5)  # Warte auf Consolidated Results Loading
            
            await analyze_consolidated_tab(page)
            
            print("\n" + "=" * 60)
            print("✅ UMFASSENDER TEST ABGESCHLOSSEN!")
            print("=" * 60)
            
            # Browser offen lassen für manuelle Inspektion
            print("\n🌐 Browser bleibt für manuelle Inspektion geöffnet...")
            print("   Schließen Sie das Browserfenster, wenn Sie fertig sind.")
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            await page.screenshot(path='/app/error_eleonore_test.png')
            raise

async def analyze_search_results_detailed(page):
    """Detaillierte Analyse der Eleonore-Suchergebnisse"""
    print("\n🔍 DETAILLIERTE SUCHERGEBNIS-ANALYSE:")
    
    # Suche nach Ergebnis-Containern
    result_found = False
    result_containers = [
        '#results', '.results-container', '.mine-card',
        '.field-based-card', '.result-card', '.search-results'
    ]
    
    main_result_text = ""
    
    for selector in result_containers:
        elements = await page.locator(selector).count()
        if elements > 0:
            main_result_text = await page.locator(selector).first.text_content()
            print(f"✅ Ergebnisse gefunden: {elements} Container mit '{selector}'")
            print(f"   📊 Inhalt: {len(main_result_text)} Zeichen")
            result_found = True
            break
    
    if not result_found:
        print("❌ KEINE SUCHERGEBNISSE GEFUNDEN!")
        # Suche nach Fehlermeldungen
        error_text = await page.locator('body').text_content()
        if 'error' in error_text.lower() or 'fehler' in error_text.lower():
            print(f"⚠️ Mögliche Fehlermeldung: {error_text[:200]}...")
        return
    
    # KRITISCHE QUALITÄTSPRÜFUNGEN
    print("\n🔍 KRITISCHE QUALITÄTSPRÜFUNGEN:")
    
    quality_results = {
        "❌ Rohstoff-Extraktion": check_commodity_extraction(main_result_text),
        "❌ Land-Normalisierung": check_country_normalization(main_result_text),
        "❌ Dummy-Daten": check_dummy_data(main_result_text),
        "❌ Template-Phrasen": check_template_phrases(main_result_text),
        "❌ Koordinaten-Format": check_coordinates_format(main_result_text)
    }
    
    for test_name, result in quality_results.items():
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {test_name.split(' ', 1)[1]}: {result['message']}")
        if result["details"]:
            for detail in result["details"][:3]:  # Max 3 Details
                print(f"      → {detail}")
    
    # SPEZIFISCHE FELD-ANALYSE
    await analyze_specific_fields(page, main_result_text)

def check_commodity_extraction(text):
    """Prüft ob Rohstoffe korrekt extrahiert wurden"""
    good_indicators = ["Gold", "Kupfer", "Silber", "Copper", "Silver"]
    bad_indicators = [
        "Eleonore ist die größte", "größte Goldmine", 
        "Mine produziert", "..produziert Gold", "Hauptrohstoff ist"
    ]
    
    good_found = [g for g in good_indicators if g in text]
    bad_found = [b for b in bad_indicators if b.lower() in text.lower()]
    
    if good_found and not bad_found:
        return {"passed": True, "message": f"Korrekt extrahiert: {', '.join(good_found)}", "details": []}
    elif bad_found:
        return {"passed": False, "message": f"Template-Phrasen gefunden: {len(bad_found)}", "details": bad_found}
    else:
        return {"passed": False, "message": "Keine Rohstoff-Daten gefunden", "details": []}

def check_country_normalization(text):
    """Prüft Land-Normalisierung (Kanada/Canada)"""
    if "Kanada" in text:
        return {"passed": True, "message": "Land als 'Kanada' normalisiert", "details": []}
    elif "Canada" in text:
        return {"passed": True, "message": "Land als 'Canada' gefunden", "details": []}
    else:
        return {"passed": False, "message": "Kein Land gefunden", "details": []}

def check_dummy_data(text):
    """Prüft auf Dummy-Daten"""
    dummy_indicators = ["DUMMY", "FALLBACK", "Nichts gefunden", "noch aktiv", "Mine geschlossen"]
    found = [d for d in dummy_indicators if d in text]
    
    if found:
        return {"passed": False, "message": f"Dummy-Daten gefunden: {len(found)}", "details": found}
    else:
        return {"passed": True, "message": "Keine Dummy-Daten gefunden", "details": []}

def check_template_phrases(text):
    """Prüft auf Template-Phrasen"""
    templates = [
        "ist eine Mine", "befindet sich in", "wird betrieben von",
        "ca. X Tonnen", "ungefähr X", "schätzungsweise"
    ]
    found = [t for t in templates if t.lower() in text.lower()]
    
    if found:
        return {"passed": False, "message": f"Template-Phrasen: {len(found)}", "details": found}
    else:
        return {"passed": True, "message": "Keine Template-Phrasen", "details": []}

def check_coordinates_format(text):
    """Prüft Koordinaten-Format"""
    import re
    # Suche nach Koordinaten-Mustern
    coord_patterns = [r'-?\d+\.\d+', r'\d+°\d+', r'49\.\d+', r'-79\.\d+']
    
    found_coords = []
    for pattern in coord_patterns:
        matches = re.findall(pattern, text)
        found_coords.extend(matches)
    
    if found_coords:
        return {"passed": True, "message": f"Koordinaten gefunden: {len(found_coords)}", "details": found_coords[:5]}
    else:
        return {"passed": False, "message": "Keine Koordinaten gefunden", "details": []}

async def analyze_specific_fields(page, main_text):
    """Analysiert spezifische Felder im Detail"""
    print("\n📋 SPEZIFISCHE FELD-ANALYSE:")
    
    # Suche nach strukturierten Feldern
    field_selectors = [
        '.field-item', '.structured-field', '[class*="field"]',
        'dt', 'dd', '.field-display'
    ]
    
    all_fields = {}
    
    for selector in field_selectors:
        elements = await page.locator(selector).count()
        if elements > 0:
            print(f"   📊 {elements} Felder mit '{selector}':")
            
            for i in range(min(elements, 15)):  # Max 15 Felder
                try:
                    field_elem = page.locator(selector).nth(i)
                    field_text = await field_elem.text_content()
                    
                    if ':' in field_text and len(field_text) < 200:
                        parts = field_text.split(':', 1)
                        if len(parts) == 2:
                            field_name = parts[0].strip()
                            field_value = parts[1].strip()
                            
                            quality = evaluate_field_quality(field_name, field_value)
                            print(f"      {quality['status']} {field_name}: '{field_value[:50]}{'...' if len(field_value) > 50 else ''}'")
                            
                            if quality['issues']:
                                for issue in quality['issues'][:2]:
                                    print(f"         ⚠️ {issue}")
                            
                            all_fields[field_name] = field_value
                            
                except Exception as e:
                    continue
            
            break  # Nur einen Selector verwenden
    
    print(f"\n📈 GESAMT: {len(all_fields)} strukturierte Felder analysiert")
    return all_fields

def evaluate_field_quality(field_name, field_value):
    """Bewertet einzelne Feldwerte auf Qualität"""
    issues = []
    field_lower = field_name.lower()
    value_lower = field_value.lower()
    
    # Rohstoff-Prüfung
    if 'rohstoff' in field_lower or 'commodity' in field_lower:
        if value_lower in ['gold', 'kupfer', 'silber', 'copper', 'silver']:
            status = "✅"
        elif any(bad in value_lower for bad in ['größte', 'mine produziert', 'hauptrohstoff']):
            status = "❌"
            issues.append("Template-Phrase statt Rohstoff-Name")
        else:
            status = "⚪"
    
    # Land-Prüfung
    elif 'land' in field_lower or 'country' in field_lower:
        if value_lower in ['kanada', 'canada']:
            status = "✅"
        else:
            status = "⚪"
    
    # Koordinaten-Prüfung  
    elif 'koordinate' in field_lower:
        if any(char in field_value for char in ['-', '°', '49', '79']):
            status = "✅"
        elif any(word in value_lower for word in ['ungefähr', 'ca.', 'etwa']):
            status = "❌"
            issues.append("Ungenaue Koordinaten-Angabe")
        else:
            status = "⚪"
    
    # Allgemeine Dummy-Prüfung
    elif any(dummy in value_lower for dummy in ['dummy', 'fallback', 'nichts gefunden']):
        status = "❌"
        issues.append("Dummy-Daten gefunden")
    
    else:
        status = "⚪"
    
    return {"status": status, "issues": issues}

async def analyze_statistics_tab_detailed(page):
    """Analysiert den Statistik-Tab auf Search-Performance Integration"""
    print("\n📈 STATISTIK-TAB DETAILANALYSE:")
    
    # Prüfe auf Search-Performance Sektion (neue Implementierung)
    search_performance = await page.locator('#search-performance-section').count()
    if search_performance > 0:
        print("✅ Search-Performance Sektion gefunden! (Phase 2 Fix erfolgreich)")
        
        performance_text = await page.locator('#search-performance-section').text_content()
        
        # Suche nach Modell-Karten in Performance-Sektion
        model_cards = await page.locator('#search-performance-section [style*="rgba(255,255,255,0.15)"]').count()
        print(f"   🤖 {model_cards} Modell-Performance-Karten gefunden")
        
        # Analysiere Performance-Details
        if "✅" in performance_text and "ERFOLG" in performance_text:
            success_count = performance_text.count("ERFOLG")
            print(f"   ✅ {success_count} erfolgreiche Modell-Ausführungen erkannt")
        
        if "❌" in performance_text and "FEHLER" in performance_text:
            error_count = performance_text.count("FEHLER")
            print(f"   ❌ {error_count} Modell-Fehler erkannt")
        
        # Prüfe auf Feld-Statistiken
        if "Felder gefüllt" in performance_text:
            print("   📊 Feld-Statistiken in Performance-Karten gefunden")
        
    else:
        print("❌ Search-Performance Sektion NICHT gefunden (Phase 2 Fix fehlgeschlagen)")
    
    # Prüfe normale Statistiken
    stats_container = await page.locator('#statistics-table-container').count()
    if stats_container > 0:
        print("✅ Hauptstatistik-Container gefunden")
        
        # Prüfe ULTRAFIX Statistiken  
        ultrafix_stats = await page.locator('.statistics-grid, [class*="statistics"]').count()
        print(f"   📊 {ultrafix_stats} Statistik-Komponenten gefunden")
    else:
        print("❌ Hauptstatistik-Container NICHT gefunden")

async def analyze_consolidated_tab(page):
    """Analysiert den Ergebnis-Tab (ursprünglich defekt)"""
    print("\n📋 ERGEBNIS-TAB ANALYSE (Loading-Fix Test):")
    
    # Warte und prüfe auf Loading-Indikatoren
    await asyncio.sleep(2)
    loading_indicators = await page.locator('.loading, .spinner, [class*="loading"]').count()
    print(f"   ⏳ Loading-Indikatoren aktiv: {loading_indicators}")
    
    # Prüfe auf Ergebnis-Container
    result_containers = [
        '#consolidated-table-container',
        '.field-display-container', 
        '.mine-card',
        '.field-based-card'
    ]
    
    results_found = False
    for selector in result_containers:
        elements = await page.locator(selector).count()
        if elements > 0:
            content = await page.locator(selector).first.text_content()
            print(f"✅ Konsolidierte Ergebnisse gefunden: {elements} Container mit '{selector}'")
            print(f"   📊 Inhalt: {len(content)} Zeichen")
            
            # Prüfe auf spezifische Eleonore-Ergebnisse
            if 'eleonore' in content.lower() or 'éléonore' in content.lower():
                print("   ✅ Eleonore-Daten in konsolidierten Ergebnissen gefunden")
            
            # Prüfe auf Normalisierung (Gold vs gold)
            if 'Gold' in content and 'gold' not in content:
                print("   ✅ Rohstoff-Normalisierung erfolgreich (nur 'Gold', kein 'gold')")
            elif 'Gold' in content and 'gold' in content:
                print("   ⚠️ Beide Varianten gefunden: 'Gold' und 'gold'")
            
            results_found = True
            break
    
    if not results_found:
        print("❌ KEINE konsolidierten Ergebnisse gefunden!")
        
        # Prüfe auf Fehlermeldungen
        error_selectors = ['.error', '[class*="error"]', '.no-data']
        for selector in error_selectors:
            if await page.locator(selector).count() > 0:
                error_text = await page.locator(selector).first.text_content()
                print(f"   ⚠️ Fehlermeldung: {error_text}")
    else:
        print("✅ Ergebnis-Tab Loading-Fix erfolgreich!")

# Test starten
if __name__ == "__main__":
    print("🔧 Installiere Playwright Browser falls nötig...")
    import subprocess
    try:
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True, capture_output=True)
    except:
        print("⚠️ Playwright Installation fehlgeschlagen - versuche trotzdem...")
    
    print("🚀 Starte umfassenden Test...")
    asyncio.run(comprehensive_eleonore_test())