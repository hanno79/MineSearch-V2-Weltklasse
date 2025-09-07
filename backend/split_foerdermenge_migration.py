"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Migration script zum Aufteilen des Feldes 'Fördermenge/Jahr' in zwei separate Felder
"""

import sqlite3
import re
import json
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FoerdermengeMigration:
    """Migration für die Aufteilung des Fördermenge/Jahr Feldes"""
    
    def __init__(self, db_path="backend/mines.db"):
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            # Alternative Pfade probieren
            alt_paths = [
                Path("mines.db"),
                Path("../mines.db"),
                Path("backend/mines.db")
            ]
            for alt_path in alt_paths:
                if alt_path.exists():
                    self.db_path = alt_path
                    break
        
        logger.info(f"Using database: {self.db_path}")
        
        # Unit patterns for classification
        self.commodity_units = [
            r'\b(\d+[,.]?\d*)\s*(oz|ounces?|unzen)\b',  # Gold/Silver ounces
            r'\b(\d+[,.]?\d*)\s*(tonnes?|tons?|t)\s+(of\s+)?(gold|copper|silver|zinc|lead|nickel)\b',  # Metal tons
            r'\b(\d+[,.]?\d*)\s*(grams?|g)\s+(gold|au)\b',  # Grams of gold
            r'\b(\d+[,.]?\d*)\s*(pounds?|lbs?)\s+(copper|cu)\b',  # Pounds of copper
            r'\b(\d+[,.]?\d*)\s*(carats?)\b',  # Diamond carats
        ]
        
        self.total_extraction_units = [
            r'\b(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?|mt|t)\s+(per\s+year|annually|total|material|rock|ore)\b',
            r'\b(\d+[,.]?\d*)\s*(mt|million\s+tonnes?)\b',  # Million tonnes
            r'\b(\d+[,.]?\d*)\s*(bcm|million\s+m³)\b',  # Cubic meters
            r'\btotal.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
            r'\bmaterial.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
        ]
    
    def analyze_existing_data(self):
        """Analysiert vorhandene Fördermenge/Jahr Daten"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Hole alle Fördermenge/Jahr Einträge
            cursor.execute("""
                SELECT id, mine_id, field_name, field_value 
                FROM field_values 
                WHERE field_name = 'Fördermenge/Jahr'
                AND field_value IS NOT NULL 
                AND field_value != 'X'
                AND field_value != ''
            """)
            
            entries = cursor.fetchall()
            logger.info(f"Found {len(entries)} existing Fördermenge/Jahr entries")
            
            # Klassifiziere die Werte
            commodity_values = []
            total_extraction_values = []
            ambiguous_values = []
            
            for entry_id, mine_id, field_name, field_value in entries:
                classification = self.classify_production_value(field_value)
                entry_data = {
                    'id': entry_id,
                    'mine_id': mine_id,
                    'value': field_value,
                    'classification': classification
                }
                
                if classification == 'commodity':
                    commodity_values.append(entry_data)
                elif classification == 'total_extraction':
                    total_extraction_values.append(entry_data)
                else:
                    ambiguous_values.append(entry_data)
            
            logger.info(f"Classification results:")
            logger.info(f"  Commodity values: {len(commodity_values)}")
            logger.info(f"  Total extraction values: {len(total_extraction_values)}")
            logger.info(f"  Ambiguous values: {len(ambiguous_values)}")
            
            return {
                'commodity': commodity_values,
                'total_extraction': total_extraction_values,
                'ambiguous': ambiguous_values
            }
    
    def classify_production_value(self, value):
        """Klassifiziert einen Produktionswert"""
        if not value or value in ['X', '', 'nicht verfügbar']:
            return 'empty'
        
        value_lower = value.lower()
        
        # Check for commodity patterns
        for pattern in self.commodity_units:
            if re.search(pattern, value_lower):
                return 'commodity'
        
        # Check for total extraction patterns
        for pattern in self.total_extraction_units:
            if re.search(pattern, value_lower):
                return 'total_extraction'
        
        # Additional heuristics
        if any(word in value_lower for word in ['ounces', 'oz', 'unzen', 'grams', 'carats']):
            return 'commodity'
        
        if any(word in value_lower for word in ['million', 'total material', 'ore and waste', 'overburden']):
            return 'total_extraction'
        
        # Check for pure numbers with mining context
        if re.search(r'\b(\d+[,.]?\d*)\s*(tonnes?|tons?|t)$', value_lower):
            # Pure tonnage without context - likely total extraction
            return 'total_extraction'
        
        return 'ambiguous'
    
    def create_backup(self):
        """Erstellt Backup der field_values Tabelle"""
        backup_file = f"field_values_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = Path(__file__).parent / backup_file
        
        with sqlite3.connect(self.db_path) as conn:
            with open(backup_path, 'w') as f:
                for line in conn.iterdump():
                    if 'field_values' in line:
                        f.write('%s\n' % line)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def perform_migration(self, dry_run=True):
        """Führt die Migration durch"""
        logger.info(f"Starting migration (dry_run={dry_run})")
        
        # Erst Backup erstellen
        if not dry_run:
            self.create_backup()
        
        # Analysiere vorhandene Daten
        analysis = self.analyze_existing_data()
        
        migration_stats = {
            'commodity_migrated': 0,
            'total_extraction_migrated': 0,
            'ambiguous_kept': 0,
            'errors': []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Migriere Commodity-Werte
            for entry in analysis['commodity']:
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update entry {entry['id']} to 'Fördermenge/Jahr Rohstoff': {entry['value']}")
                    else:
                        cursor.execute("""
                            UPDATE field_values 
                            SET field_name = 'Fördermenge/Jahr Rohstoff'
                            WHERE id = ?
                        """, (entry['id'],))
                    migration_stats['commodity_migrated'] += 1
                except Exception as e:
                    error_msg = f"Error migrating commodity entry {entry['id']}: {e}"
                    logger.error(error_msg)
                    migration_stats['errors'].append(error_msg)
            
            # Migriere Total Extraction Werte
            for entry in analysis['total_extraction']:
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update entry {entry['id']} to 'Fördermenge/Jahr Abraum': {entry['value']}")
                    else:
                        cursor.execute("""
                            UPDATE field_values 
                            SET field_name = 'Fördermenge/Jahr Abraum'
                            WHERE id = ?
                        """, (entry['id'],))
                    migration_stats['total_extraction_migrated'] += 1
                except Exception as e:
                    error_msg = f"Error migrating total extraction entry {entry['id']}: {e}"
                    logger.error(error_msg)
                    migration_stats['errors'].append(error_msg)
            
            # Ambige Werte behalten das alte Feld zunächst
            migration_stats['ambiguous_kept'] = len(analysis['ambiguous'])
            
            if not dry_run:
                conn.commit()
                logger.info("Migration committed to database")
        
        # Zeige Zusammenfassung
        logger.info("Migration Summary:")
        logger.info(f"  Commodity values migrated: {migration_stats['commodity_migrated']}")
        logger.info(f"  Total extraction values migrated: {migration_stats['total_extraction_migrated']}")
        logger.info(f"  Ambiguous values kept as original: {migration_stats['ambiguous_kept']}")
        logger.info(f"  Errors: {len(migration_stats['errors'])}")
        
        if analysis['ambiguous']:
            logger.info("\nAmbiguous values requiring manual review:")
            for entry in analysis['ambiguous']:
                logger.info(f"  Mine ID {entry['mine_id']}: '{entry['value']}'")
        
        return migration_stats
    
    def verify_migration(self):
        """Überprüft das Ergebnis der Migration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Zähle neue Felder
            cursor.execute("SELECT COUNT(*) FROM field_values WHERE field_name = 'Fördermenge/Jahr Rohstoff'")
            commodity_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM field_values WHERE field_name = 'Fördermenge/Jahr Abraum'")
            abraum_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM field_values WHERE field_name = 'Fördermenge/Jahr'")
            old_count = cursor.fetchone()[0]
            
            logger.info("Post-migration verification:")
            logger.info(f"  Fördermenge/Jahr Rohstoff entries: {commodity_count}")
            logger.info(f"  Fördermenge/Jahr Abraum entries: {abraum_count}")
            logger.info(f"  Original Fördermenge/Jahr entries remaining: {old_count}")
            
            return {
                'commodity_count': commodity_count,
                'abraum_count': abraum_count,
                'original_remaining': old_count
            }

def main():
    """Hauptfunktion für die Migration"""
    migration = FoerdermengeMigration()
    
    # Erst Dry Run
    logger.info("=== DRY RUN ===")
    migration.perform_migration(dry_run=True)
    
    # Bestätigung für echte Migration
    print("\nDry run complete. Do you want to proceed with the actual migration? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        logger.info("=== ACTUAL MIGRATION ===")
        migration.perform_migration(dry_run=False)
        migration.verify_migration()
    else:
        logger.info("Migration cancelled by user")

if __name__ == "__main__":
    main()