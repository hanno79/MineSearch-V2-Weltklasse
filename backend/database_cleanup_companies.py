#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Bereinigung der Companies-Duplikate (Inc/non-Inc Varianten)
"""

import sqlite3
import logging
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_company_name(name):
    """Normalisiert Company-Namen für Duplikat-Erkennung"""
    if not name:
        return ""
    
    normalized = name.strip().lower()
    # Entferne Inc, Inc., Ltd, etc. für Vergleich
    suffixes_to_remove = [' inc', ' inc.', ' ltd', ' ltd.', ' limited', ' corp', ' corp.', ' corporation']
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized

def cleanup_companies():
    """Bereinigt Companies-Duplikate - behält die Inc-Version"""
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    try:
        logger.info("🏢 PHASE 3: Companies Bereinigung gestartet")
        
        # 1. Alle Companies laden
        cursor.execute("SELECT id, name FROM companies ORDER BY name")
        companies = cursor.fetchall()
        logger.info(f"Total Companies: {len(companies)}")
        
        # 2. Duplikate finden
        company_groups = {}
        for id, name in companies:
            if name:
                normalized = normalize_company_name(name)
                if normalized not in company_groups:
                    company_groups[normalized] = []
                company_groups[normalized].append((id, name))
        
        duplicates = {k: v for k, v in company_groups.items() if len(v) > 1}
        logger.info(f"Gefundene Duplikat-Gruppen: {len(duplicates)}")
        
        merge_operations = []
        
        for norm_name, entries in duplicates.items():
            logger.info(f"\n🔍 Duplikat-Gruppe '{norm_name}': {entries}")
            
            # Wähle die beste Version (bevorzuge Inc/Ltd Varianten)
            best_entry = None
            entries_to_merge = []
            
            # Priorisierung: Inc > Ltd > Corporation > plain name
            for id, name in entries:
                if any(suffix in name.lower() for suffix in [' inc', ' inc.', ' ltd', ' ltd.', ' limited']):
                    if best_entry is None:
                        best_entry = (id, name)
                    else:
                        entries_to_merge.append((id, name))
                else:
                    entries_to_merge.append((id, name))
            
            # Falls kein Inc/Ltd gefunden, nimm den ersten
            if best_entry is None:
                best_entry = entries[0]
                entries_to_merge = entries[1:]
            
            if entries_to_merge:
                merge_operations.append((best_entry, entries_to_merge))
                logger.info(f"  ✅ Behalte: {best_entry}")
                logger.info(f"  🔄 Merge: {entries_to_merge}")
        
        # 3. Führe Merges durch
        total_merged = 0
        for (keep_id, keep_name), merge_list in merge_operations:
            logger.info(f"\n🔄 Merge Operation: Behalte '{keep_name}' (ID {keep_id})")
            
            for merge_id, merge_name in merge_list:
                logger.info(f"  Lösche '{merge_name}' (ID {merge_id})")
                
                # Update alle Referenzen auf die Company
                ref_tables = [
                    ('mines', 'company_id'),
                    ('mine_data_fields', 'company_id'),
                    ('mine_owners', 'company_id'),
                    ('mine_operators', 'company_id'),
                    ('company_type_associations', 'company_id')
                ]
                
                for table, column in ref_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (merge_id,))
                        ref_count = cursor.fetchone()[0]
                        if ref_count > 0:
                            cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (keep_id, merge_id))
                            logger.info(f"    ✅ {cursor.rowcount} {table} Referenzen aktualisiert")
                    except sqlite3.OperationalError as e:
                        if "no such column" in str(e):
                            logger.debug(f"    Tabelle {table} hat keine {column} Spalte")
                        else:
                            logger.warning(f"    Fehler bei {table}: {e}")
                
                # Lösche die Duplikat-Company
                cursor.execute("DELETE FROM companies WHERE id = ?", (merge_id,))
                if cursor.rowcount > 0:
                    logger.info(f"    ✅ Company '{merge_name}' (ID {merge_id}) gelöscht")
                    total_merged += 1
        
        # 4. Validierung
        logger.info(f"\n📊 Validiere Companies Bereinigung...")
        logger.info(f"Total Companies gelöscht: {total_merged}")
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        remaining_count = cursor.fetchone()[0]
        logger.info(f"Verbleibende Companies: {remaining_count}")
        
        # Prüfe auf weitere Duplikate
        cursor.execute("""
            SELECT normalized_name, COUNT(*) as count 
            FROM (
                SELECT 
                    LOWER(REPLACE(REPLACE(REPLACE(name, ' Inc', ''), ' inc', ''), ' Ltd', '')) as normalized_name
                FROM companies
            ) 
            GROUP BY normalized_name 
            HAVING COUNT(*) > 1
        """)
        remaining_duplicates = cursor.fetchall()
        if remaining_duplicates:
            logger.warning(f"⚠️ Möglicherweise verbliebene Duplikate: {remaining_duplicates}")
        else:
            logger.info("✅ Keine erkennbaren Companies-Duplikate mehr vorhanden")
        
        # Sample der bereinigten Companies
        cursor.execute("SELECT id, name FROM companies ORDER BY name LIMIT 10")
        sample_companies = cursor.fetchall()
        logger.info(f"Sample Companies: {sample_companies}")
        
        # Commit alle Änderungen
        conn.commit()
        logger.info("✅ PHASE 3 KOMPLETT: Companies erfolgreich bereinigt")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Companies Bereinigung: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starte Companies Bereinigung...")
    success = cleanup_companies()
    if success:
        logger.info("🎉 Companies Bereinigung erfolgreich abgeschlossen!")
    else:
        logger.error("💥 Companies Bereinigung fehlgeschlagen!")