#!/usr/bin/env python3
"""
Author: rahn
Datum: 30.07.2025
Version: 1.0
Beschreibung: Frontend Table Analysis - Überprüfe die tatsächliche Darstellung der konsolidierten Ergebnisse Tabelle
"""

import asyncio
from playwright.async_api import async_playwright
import json
import sys
import os

async def analyze_consolidated_table():
    """Analysiere die konsolidierte Ergebnisse Tabelle im Browser"""
    
    async with async_playwright() as p:
        # Browser starten (headless=False für sichtbare Analyse)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🌐 Öffne http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # Warte auf das Interface
            await page.wait_for_selector('#method_consolidated', timeout=10000)
            
            print("📊 Navigiere zu 'Konsolidierte Ergebnisse' Tab...")
            await page.click('#method_consolidated')
            await page.wait_for_timeout(2000)  # Warte auf Tab-Wechsel
            
            # Versuche die Daten zu laden
            print("🔄 Versuche konsolidierte Daten zu laden...")
            
            # Prüfe ob bereits Daten vorhanden sind
            table_container = await page.query_selector('#consolidated-table-container')
            if table_container:
                content = await table_container.inner_text()
                if "Keine konsolidierten Ergebnisse" in content:
                    print("⚠️ Keine Daten vorhanden - lade Test-Daten...")
                    
                    # Gehe zum Search Tab und führe eine Testsuche durch
                    await page.click('#method_search')
                    await page.wait_for_timeout(1000)
                    
                    # Fülle Testdaten ein
                    await page.fill('#mineName', 'Abacus')
                    await page.fill('#country', 'Canada')
                    await page.fill('#region', 'Ontario')
                    
                    # Klicke Search
                    await page.click('#searchBtn')
                    print("🔍 Starte Testsuche für 'Abacus'...")
                    
                    # Warte auf Ergebnis
                    await page.wait_for_timeout(10000)
                    
                    # Zurück zu konsolidierten Ergebnissen
                    await page.click('#method_consolidated')
                    await page.wait_for_timeout(2000)
            
            # Analysiere die Tabelle
            print("📋 Analysiere Tabellen-Struktur...")
            
            # Hole alle Header-Zellen
            headers = await page.query_selector_all('.table-header-row .table-cell')
            header_texts = []
            
            for header in headers:
                text = await header.inner_text()
                header_texts.append(text.strip())
            
            print(f"📊 Gefundene Spaltenköpfe ({len(header_texts)}):")
            for i, header in enumerate(header_texts):
                print(f"  {i+1:2d}. {header}")
            
            # Prüfe auf Duplikate
            print("\n🔍 Duplikat-Analyse:")
            seen = set()
            duplicates = []
            for header in header_texts:
                clean_header = header.replace('▲', '').replace('▼', '').replace('↕️', '').strip()
                if clean_header in seen:
                    duplicates.append(clean_header)
                seen.add(clean_header)
            
            if duplicates:
                print(f"❌ DUPLIKATE GEFUNDEN: {duplicates}")
            else:
                print("✅ Keine Duplikate gefunden")
            
            # Prüfe spezifische Spalten
            print("\n🎯 Prüfe spezifische Spalten:")
            target_columns = ['Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr']
            
            for target in target_columns:
                found = any(target in header for header in header_texts)
                status = "✅ SICHTBAR" if found else "❌ NICHT SICHTBAR"
                print(f"  💰 {target}: {status}")
            
            # Screenshot machen
            screenshot_path = "/app/minesearch_v2/backend/consolidated_table_analysis.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot gespeichert: {screenshot_path}")
            
            # Detaillierte Tabellen-Struktur speichern
            analysis_data = {
                "timestamp": page.evaluate("() => new Date().toISOString()"),
                "total_columns": len(header_texts),
                "headers": header_texts,
                "duplicates": duplicates,
                "target_columns_visibility": {
                    col: any(col in header for header in header_texts) 
                    for col in target_columns
                },
                "has_data_rows": bool(await page.query_selector('.table-row'))
            }
            
            # Analysiere auch Datenzeilen falls vorhanden
            data_rows = await page.query_selector_all('.table-row')
            if data_rows:
                print(f"\n📊 Gefundene Datenzeilen: {len(data_rows)}")
                
                # Analysiere erste Zeile
                if len(data_rows) > 0:
                    first_row_cells = await data_rows[0].query_selector_all('.table-cell')
                    first_row_data = []
                    for cell in first_row_cells:
                        text = await cell.inner_text()
                        first_row_data.append(text.strip())
                    
                    analysis_data["first_row_sample"] = first_row_data
                    print("📋 Erste Datenzeile:")
                    for i, data in enumerate(first_row_data):
                        header_name = header_texts[i] if i < len(header_texts) else f"Spalte {i+1}"
                        print(f"  {header_name}: {data}")
            else:
                print("⚠️ Keine Datenzeilen gefunden")
                analysis_data["first_row_sample"] = []
            
            # Speichere detaillierte Analyse
            analysis_path = "/app/minesearch_v2/backend/table_analysis_results.json"
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Detaillierte Analyse gespeichert: {analysis_path}")
            
            # Browser offen lassen für manuelle Inspektion
            print("\n🔍 Browser bleibt für 30 Sekunden offen für manuelle Inspektion...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"❌ Fehler bei der Analyse: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_consolidated_table())