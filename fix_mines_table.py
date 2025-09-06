#!/usr/bin/env python3
"""
Fix mines table to use foreign keys for country_id and region_id
Author: rahn
Datum: 06.09.2025
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_mines_table():
    """Aktualisiert die mines Tabelle um Foreign Keys zu verwenden"""
    
    conn = sqlite3.connect('/home/hanno/projects/MineSearch/backend/mines.db')
    cursor = conn.cursor()
    
    try:
        # Backup der aktuellen mines Tabelle
        logger.info("Erstelle Backup der mines Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mines_backup AS 
            SELECT * FROM mines
        """)
        
        # Prüfe ob country_id und region_id bereits existieren
        cursor.execute("PRAGMA table_info(mines)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'country_id' not in column_names:
            logger.info("Füge country_id Spalte hinzu...")
            cursor.execute("ALTER TABLE mines ADD COLUMN country_id INTEGER")
        
        if 'region_id' not in column_names:
            logger.info("Füge region_id Spalte hinzu...")
            cursor.execute("ALTER TABLE mines ADD COLUMN region_id INTEGER")
        
        # Update country_id basierend auf country Namen
        logger.info("Update country_id basierend auf country Namen...")
        cursor.execute("""
            UPDATE mines 
            SET country_id = (
                SELECT id FROM countries 
                WHERE LOWER(countries.name) = LOWER(mines.country)
                LIMIT 1
            )
            WHERE country IS NOT NULL
        """)
        
        # Update region_id basierend auf region Namen und country
        logger.info("Update region_id basierend auf region Namen...")
        cursor.execute("""
            UPDATE mines 
            SET region_id = (
                SELECT regions.id FROM regions 
                WHERE LOWER(regions.name) = LOWER(mines.region)
                AND regions.country_id = mines.country_id
                LIMIT 1
            )
            WHERE region IS NOT NULL AND country_id IS NOT NULL
        """)
        
        # Füge fehlende Länder hinzu
        logger.info("Füge fehlende Länder hinzu...")
        cursor.execute("""
            INSERT INTO countries (name, created_at, updated_at)
            SELECT DISTINCT country, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM mines
            WHERE country IS NOT NULL 
            AND country NOT IN (SELECT name FROM countries)
        """)
        
        # Update country_id für neue Länder
        cursor.execute("""
            UPDATE mines 
            SET country_id = (
                SELECT id FROM countries 
                WHERE LOWER(countries.name) = LOWER(mines.country)
                LIMIT 1
            )
            WHERE country IS NOT NULL AND country_id IS NULL
        """)
        
        # Füge fehlende Regionen hinzu
        logger.info("Füge fehlende Regionen hinzu...")
        cursor.execute("""
            INSERT INTO regions (name, country_id, created_at, updated_at)
            SELECT DISTINCT m.region, m.country_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM mines m
            WHERE m.region IS NOT NULL 
            AND m.country_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM regions r 
                WHERE LOWER(r.name) = LOWER(m.region) 
                AND r.country_id = m.country_id
            )
        """)
        
        # Update region_id für neue Regionen
        cursor.execute("""
            UPDATE mines 
            SET region_id = (
                SELECT regions.id FROM regions 
                WHERE LOWER(regions.name) = LOWER(mines.region)
                AND regions.country_id = mines.country_id
                LIMIT 1
            )
            WHERE region IS NOT NULL AND country_id IS NOT NULL AND region_id IS NULL
        """)
        
        # Zeige Statistiken
        cursor.execute("SELECT COUNT(*) FROM mines WHERE country_id IS NOT NULL")
        mines_with_country = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM mines WHERE region_id IS NOT NULL")
        mines_with_region = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM mines")
        total_mines = cursor.fetchone()[0]
        
        logger.info(f"Statistiken:")
        logger.info(f"  - Total Mines: {total_mines}")
        logger.info(f"  - Mines mit country_id: {mines_with_country}")
        logger.info(f"  - Mines mit region_id: {mines_with_region}")
        
        conn.commit()
        logger.info("✅ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_mines_table()