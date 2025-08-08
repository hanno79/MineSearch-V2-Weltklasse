#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025  
Version: 1.0
Beschreibung: Prüft sources-Tabelle in der Datenbank
"""

import sqlite3
import json

def check_sources_database():
    """Analysiert die sources-Tabelle in der Datenbank"""
    try:
        conn = sqlite3.connect('mines.db')
        cursor = conn.cursor()
        
        # Anzahl sources prüfen
        cursor.execute('SELECT COUNT(*) FROM sources')
        count = cursor.fetchone()[0]
        print(f"Sources count: {count}")
        
        if count > 0:
            # Sample sources anzeigen
            cursor.execute('SELECT id, url, domain, source_type, reliability_score FROM sources LIMIT 10')
            sources = cursor.fetchall()
            print("\nSample sources:")
            for s in sources:
                print(f"ID: {s[0]}, URL: {s[1]}, Domain: {s[2]}, Type: {s[3]}, Score: {s[4]}")
                
            # Weitere Statistiken
            cursor.execute('SELECT source_type, COUNT(*) FROM sources GROUP BY source_type')
            types = cursor.fetchall()
            print("\nSource types:")
            for t in types:
                print(f"  {t[0]}: {t[1]}")
                
        # Prüfe auch consolidated_results für Testdaten
        cursor.execute('SELECT COUNT(*) FROM consolidated_results')
        results_count = cursor.fetchone()[0]
        print(f"\nConsolidated results count: {results_count}")
        
        if results_count > 0:
            cursor.execute('SELECT DISTINCT sources_used FROM consolidated_results LIMIT 5')
            sources_used = cursor.fetchall()
            print("\nSample sources_used from consolidated_results:")
            for su in sources_used:
                if su[0]:
                    try:
                        sources_list = json.loads(su[0])
                        print(f"  {sources_list}")
                    except:
                        print(f"  {su[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Fehler beim Datenbankzugriff: {e}")

if __name__ == "__main__":
    check_sources_database()