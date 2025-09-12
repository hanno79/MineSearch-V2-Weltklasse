#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Bereinigung der Countries-Duplikate (Canada/Kanada)
"""

import sqlite3
import logging
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_countries():
    """Bereinigt Countries-Duplikate und normalisiert zu deutschen Namen"""
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    try:
        logger.info("🇩🇪 PHASE 2: Countries Bereinigung gestartet")

        # 1. Aktuelle Countries anzeigen
        cursor.execute("SELECT id, name FROM countries ORDER BY name")
        countries = cursor.fetchall()
        logger.info(f"Aktuelle Countries: {countries}")

        # 2. Canada (ID:1) → Kanada (ID:2) Migration
        logger.info("Merge Canada → Kanada...")

        # Prüfe Referenzen zu Canada (ID:1)
        cursor.execute("SELECT COUNT(*) FROM mines WHERE country_id = 1")
        canada_refs = cursor.fetchone()[0]
        logger.info(f"Mines mit Canada (ID:1): {canada_refs}")

        # Update alle Referenzen von Canada auf Kanada
        if canada_refs > 0:
            cursor.execute("UPDATE mines SET country_id = 2 WHERE country_id = 1")
            logger.info(f"✅ {cursor.rowcount} Mines von Canada (ID:1) auf Kanada (ID:2) migriert")

        # Prüfe weitere Tabellen mit country_id
        country_ref_tables = [
            'regions',  # kann country_id haben
            'mine_data_fields'  # kann country_id haben
        ]

        for table in country_ref_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE country_id = 1")
                ref_count = cursor.fetchone()[0]
                if ref_count > 0:
                    cursor.execute(f"UPDATE {table} SET country_id = 2 WHERE country_id = 1")
                    logger.info(f"✅ {cursor.rowcount} {table} Referenzen von Canada auf Kanada migriert")
            except sqlite3.OperationalError as e:
                if "no such column: country_id" in str(e):
                    logger.debug(f"Tabelle {table} hat keine country_id Spalte")
                else:
                    logger.warning(f"Fehler bei {table}: {e}")

        # 3. Lösche Canada (ID:1)
        cursor.execute("DELETE FROM countries WHERE id = 1 AND name = 'Canada'")
        if cursor.rowcount > 0:
            logger.info("✅ Canada (ID:1) gelöscht")

        # 4. Validierung
        logger.info("Validiere Countries Bereinigung...")
        cursor.execute("SELECT id, name FROM countries ORDER BY name")
        remaining_countries = cursor.fetchall()
        logger.info(f"Verbliebene Countries: {remaining_countries}")

        # Prüfe auf Duplikate
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM countries
            GROUP BY LOWER(name)
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            logger.warning(f"⚠️ Verbliebene Duplikate: {duplicates}")
        else:
            logger.info("✅ Keine Countries-Duplikate mehr vorhanden")

        # 5. Prüfe dass alle Referenzen korrekt sind
        cursor.execute("""
            SELECT m.id, m.name, c.name as country_name
            FROM mines m
            LEFT JOIN countries c ON m.country_id = c.id
            WHERE m.country_id IS NOT NULL
            LIMIT 5
        """)
        sample_refs = cursor.fetchall()
        logger.info(f"Sample Mine-Country Referenzen: {sample_refs}")

        # Commit alle Änderungen
        conn.commit()
        logger.info("✅ PHASE 2 KOMPLETT: Countries erfolgreich bereinigt")

        return True

    except Exception as e:
        logger.error(f"❌ Fehler bei Countries Bereinigung: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starte Countries Bereinigung...")
    success = cleanup_countries()
    if success:
        logger.info("🎉 Countries Bereinigung erfolgreich abgeschlossen!")
    else:
        logger.error("💥 Countries Bereinigung fehlgeschlagen!")
