#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Bereinigung aller Test-Einträge aus der Datenbank
"""

import sqlite3
import logging
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_test_entries():
    """Entfernt alle Test-Einträge aus der Datenbank"""
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    try:
        logger.info("🧹 PHASE 1: Test-Einträge Bereinigung gestartet")
        
        # 1. Test Mine löschen (ID 33)
        logger.info("Lösche Test Mine (ID 33)...")
        
        # Prüfe Referenzen zur Test Mine
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE mine_name = 'Test Mine'")
        search_results_count = cursor.fetchone()[0]
        logger.info(f"Search Results mit Test Mine: {search_results_count}")
        
        # Lösche Search Results für Test Mine
        if search_results_count > 0:
            cursor.execute("DELETE FROM search_results WHERE mine_name = 'Test Mine'")
            logger.info(f"✅ {search_results_count} Search Results für Test Mine gelöscht")
        
        # Lösche Test Mine
        cursor.execute("DELETE FROM mines WHERE id = 33 AND name = 'Test Mine'")
        if cursor.rowcount > 0:
            logger.info("✅ Test Mine (ID 33) gelöscht")
        
        # 2. Test Country löschen (ID 9)
        logger.info("Lösche Test Country (ID 9)...")
        
        # Update Mines die Test Country verwenden zu NULL
        cursor.execute("UPDATE mines SET country_id = NULL WHERE country_id = 9")
        if cursor.rowcount > 0:
            logger.info(f"✅ {cursor.rowcount} Mines von Test Country getrennt")
        
        # Lösche Test Country
        cursor.execute("DELETE FROM countries WHERE id = 9 AND name = 'Test Country'")
        if cursor.rowcount > 0:
            logger.info("✅ Test Country (ID 9) gelöscht")
        
        # 3. TEST_ field_definitions löschen
        logger.info("Lösche TEST_ field_definitions...")
        
        # Finde TEST_ Felder
        cursor.execute("SELECT id, field_name FROM field_definitions WHERE field_name LIKE 'TEST_%'")
        test_fields = cursor.fetchall()
        logger.info(f"Gefundene TEST_ Felder: {test_fields}")
        
        for field_id, field_name in test_fields:
            # Lösche zugehörige mine_data_fields (basierend auf field_name)
            cursor.execute("DELETE FROM mine_data_fields WHERE field_name = ?", (field_name,))
            data_count = cursor.rowcount
            
            # Lösche zugehörige field_values (basierend auf field_name)
            cursor.execute("DELETE FROM field_values WHERE field_name = ?", (field_name,))
            values_count = cursor.rowcount
            
            # Lösche field_definition
            cursor.execute("DELETE FROM field_definitions WHERE id = ?", (field_id,))
            
            logger.info(f"✅ TEST Feld '{field_name}' (ID {field_id}) gelöscht - {data_count} mine_data_fields + {values_count} field_values entfernt")
        
        # 4. Validierung: Prüfe ob Test-Einträge entfernt wurden
        logger.info("Validiere Bereinigung...")
        
        cursor.execute("SELECT COUNT(*) FROM mines WHERE name LIKE '%test%'")
        test_mines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM countries WHERE name LIKE '%test%'") 
        test_countries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM field_definitions WHERE field_name LIKE 'TEST_%'")
        test_fields_remaining = cursor.fetchone()[0]
        
        logger.info(f"Verbliebene Test-Einträge: Mines={test_mines}, Countries={test_countries}, Fields={test_fields_remaining}")
        
        if test_mines == 0 and test_countries == 0 and test_fields_remaining == 0:
            logger.info("✅ Validierung erfolgreich: Alle Test-Einträge entfernt")
        else:
            logger.warning("⚠️ Einige Test-Einträge könnten noch vorhanden sein")
        # Commit alle Änderungen
        conn.commit()
        logger.info("✅ PHASE 1 KOMPLETT: Alle Test-Einträge erfolgreich bereinigt")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Test-Einträge Bereinigung: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starte Test-Einträge Bereinigung...")
    success = cleanup_test_entries()
    if success:
        logger.info("🎉 Test-Einträge Bereinigung erfolgreich abgeschlossen!")
    else:
        logger.error("💥 Test-Einträge Bereinigung fehlgeschlagen!")