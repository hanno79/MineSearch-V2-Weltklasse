"""
Author: Database Schema Specialist (Swarm Agent)
Datum: 30.07.2025
Version: 1.0
Beschreibung: Sichere Migration der Feldnamen in search_results Tabelle
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class FieldNameMigrator:
    """Sichere Migration von Feldnamen in structured_data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path = f"{db_path}_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Master-Mapping aus Swarm-Koordination
        self.FIELD_CONSOLIDATION_MAP = {
            'Name': 'Mine',
            'Country': 'Land'
        }
        
        self.FIELD_RENAME_MAP = {
            'Jahr der Aufnahme der Kosten': 'Kostenjahr',
            'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr', 
            'Fläche der Mine in qkm': 'Minenfläche in qkm',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
            'Minentyp (Untertage/ Open-Pit/ usw.)': 'Minentyp'
        }
        
        # Kombiniertes Master-Mapping
        self.COMPLETE_FIELD_MAPPING = {**self.FIELD_CONSOLIDATION_MAP, **self.FIELD_RENAME_MAP}
    
    def create_backup(self) -> bool:
        """Erstelle Sicherheitskopie der Datenbank"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"✅ Backup erstellt: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Backup fehlgeschlagen: {e}")
            return False
    
    def analyze_current_fields(self) -> Dict[str, int]:
        """Analysiere aktuelle Feldverteilung"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        field_counts = {}
        cursor.execute("SELECT structured_data FROM search_results WHERE structured_data IS NOT NULL")
        
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                if isinstance(data, dict):
                    for field_name in data.keys():
                        if field_name == '_source_mapping':
                            continue
                        field_counts[field_name] = field_counts.get(field_name, 0) + 1
            except Exception as e:
                logger.warning(f"Fehler beim Parsen von structured_data: {e}")
        
        conn.close()
        return field_counts
    
    def migrate_single_record(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migriere ein einzelnes structured_data Dictionary"""
        if not isinstance(structured_data, dict):
            return structured_data
        
        migrated_data = {}
        
        for old_field, value in structured_data.items():
            # Spezialbehandlung für _source_mapping - behalten
            if old_field == '_source_mapping':
                migrated_data[old_field] = value
                continue
            
            # Prüfe Mapping
            new_field = self.COMPLETE_FIELD_MAPPING.get(old_field, old_field)
            
            # Verhindere leere oder ungültige Werte
            if value and str(value).strip() and str(value).strip() not in ['X', 'N/A', '-', 'null']:
                migrated_data[new_field] = value
                
                # Logging für kritische Feldänderungen
                if new_field != old_field:
                    logger.debug(f"Feld migriert: '{old_field}' → '{new_field}' = '{value}'")
        
        return migrated_data
    
    def perform_migration(self, dry_run: bool = True) -> Dict[str, Any]:
        """Führe Migration durch"""
        if not dry_run and not self.create_backup():
            return {"success": False, "error": "Backup fehlgeschlagen"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hole alle Einträge mit structured_data
        cursor.execute("SELECT id, structured_data FROM search_results WHERE structured_data IS NOT NULL")
        records = cursor.fetchall()
        
        migration_stats = {
            "total_records": len(records),
            "migrated_records": 0,
            "field_changes": {},
            "errors": []
        }
        
        for record_id, structured_data_raw in records:
            try:
                # Parse structured_data
                if isinstance(structured_data_raw, str):
                    structured_data = json.loads(structured_data_raw)
                else:
                    structured_data = structured_data_raw
                
                # Migriere Felder
                migrated_data = self.migrate_single_record(structured_data)
                
                # Zähle Änderungen
                for old_field in structured_data.keys():
                    if old_field in self.COMPLETE_FIELD_MAPPING:
                        new_field = self.COMPLETE_FIELD_MAPPING[old_field]
                        migration_stats["field_changes"][f"{old_field} → {new_field}"] = \
                            migration_stats["field_changes"].get(f"{old_field} → {new_field}", 0) + 1
                
                # Update Datenbank (nur wenn nicht dry_run)
                if not dry_run:
                    cursor.execute(
                        "UPDATE search_results SET structured_data = ? WHERE id = ?",
                        (json.dumps(migrated_data, ensure_ascii=False), record_id)
                    )
                
                migration_stats["migrated_records"] += 1
                
            except Exception as e:
                error_msg = f"Fehler bei Record {record_id}: {e}"
                migration_stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        if not dry_run:
            conn.commit()
            logger.info(f"✅ Migration abgeschlossen: {migration_stats['migrated_records']} Records aktualisiert")
        else:
            logger.info(f"🔍 Dry-Run abgeschlossen: {migration_stats['migrated_records']} Records würden migriert")
        
        conn.close()
        migration_stats["success"] = True
        return migration_stats
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verifiziere erfolgreiche Migration"""
        field_counts = self.analyze_current_fields()
        
        verification_result = {
            "old_fields_remaining": 0,
            "new_fields_present": 0,
            "field_distribution": field_counts,
            "migration_complete": True
        }
        
        # Prüfe ob alte Felder noch vorhanden sind
        for old_field in self.COMPLETE_FIELD_MAPPING.keys():
            if old_field in field_counts:
                verification_result["old_fields_remaining"] += field_counts[old_field]
                verification_result["migration_complete"] = False
        
        # Prüfe ob neue Felder vorhanden sind
        for new_field in self.COMPLETE_FIELD_MAPPING.values():
            if new_field in field_counts:
                verification_result["new_fields_present"] += field_counts[new_field]
        
        return verification_result


def main():
    """Hauptfunktion für Migration"""
    db_path = "/app/minesearch_v2/backend/mines.db"
    migrator = FieldNameMigrator(db_path)
    
    print("🗄️ Datenbank-Feldmigration gestartet...")
    
    # 1. Aktuelle Feldverteilung analysieren
    print("\n📊 Aktuelle Feldverteilung:")
    current_fields = migrator.analyze_current_fields()
    for field, count in sorted(current_fields.items()):
        if field in migrator.COMPLETE_FIELD_MAPPING:
            print(f"❌ {field}: {count} (MUSS MIGRIERT WERDEN)")
        else:
            print(f"✅ {field}: {count}")
    
    # 2. Dry-Run durchführen
    print("\n🔍 Dry-Run Migration...")
    dry_run_result = migrator.perform_migration(dry_run=True)
    print(f"Dry-Run Ergebnis: {dry_run_result}")
    
    # 3. Echte Migration (falls erwünscht)
    print("\n⚠️  Starte echte Migration in 3 Sekunden... (Ctrl+C zum Abbrechen)")
    import time
    time.sleep(3)
    
    migration_result = migrator.perform_migration(dry_run=False)
    print(f"Migration Ergebnis: {migration_result}")
    
    # 4. Verifikation
    print("\n✅ Verifikation...")
    verification = migrator.verify_migration()
    print(f"Verifikation: {verification}")
    
    if verification["migration_complete"]:
        print("✅ Migration erfolgreich abgeschlossen!")
    else:
        print("❌ Migration unvollständig - manuelle Prüfung erforderlich")


if __name__ == "__main__":
    main()