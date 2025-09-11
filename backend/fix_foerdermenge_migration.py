#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 2.0
Beschreibung: Korrigierte Migration zur Aufteilung von Fördermenge/Jahr in Mine_Data_Fields

KORRIGIERTE FELDNAMEN-AUFTEILUNG:
=================================
1. "Fördermenge/Jahr" → "Fördermenge/Jahr Rohstoff" (für Rohstoff-Produktion)
2. "Fördermenge/Jahr" → "Fördermenge/Jahr Abraum" (für Gesamtextraktion/Abraum)

Dieses Script:
- Arbeitet mit Mine_Data_Fields Tabelle (nicht field_values)
- Analysiert vorhandene Fördermenge-Daten intelligent
- Klassifiziert basierend auf Einheiten und Kontext
- Stellt sicher, dass alle Constraints erhalten bleiben
"""

import sqlite3
import re
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FoerdermengeMigrationFixed:
    """Korrigierte Migration für die Aufteilung des Fördermenge/Jahr Feldes"""
    
    def __init__(self, db_path="mines.db"):
        self.db_path = db_path
        logger.info(f"Using database: {self.db_path}")
        
        # Unit patterns for intelligent classification
        self.rohstoff_patterns = [
            r'\b(\d+[,.]?\d*)\s*(oz|ounces?|unzen)\b',  # Gold/Silver ounces
            r'\b(\d+[,.]?\d*)\s*(tonnes?|tons?|t)\s+(of\s+)?(gold|copper|silver|zinc|lead|nickel|platinum|palladium)\b',  # Metal tonnes
            r'\b(\d+[,.]?\d*)\s*(grams?|g)\s+(gold|au|silver|ag)\b',  # Grams of precious metals
            r'\b(\d+[,.]?\d*)\s*(pounds?|lbs?)\s+(copper|cu|zinc|zn)\b',  # Pounds of metals
            r'\b(\d+[,.]?\d*)\s*(carats?)\b',  # Diamond carats
            r'\b(\d+[,.]?\d*)\s*(kg|kilogram)\s+(gold|silver|copper)\b',  # Kg of metals
            r'\bgold.*(\d+[,.]?\d*)\s*(oz|tonnes?)\b',  # Gold production
            r'\bcopper.*(\d+[,.]?\d*)\s*(tonnes?|lbs?)\b',  # Copper production
        ]
        
        self.abraum_patterns = [
            r'\b(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?|mt)\s*(per\s+year|annually|total|material|rock|ore|waste)?\b',
            r'\b(\d+[,.]?\d*)\s*(mt|million\s+tonnes?)\b',  # Million tonnes general
            r'\b(\d+[,.]?\d*)\s*(bcm|million\s+cubic\s*meters?|million\s+m³)\b',  # Cubic meters
            r'\btotal.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
            r'\bmaterial.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
            r'\bwaste.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
            r'\boverburden.*?(\d+[,.]?\d*)\s*(million\s+)?(tonnes?|tons?)\b',
        ]
    
    def analyze_existing_data(self):
        """Analysiert vorhandene Fördermenge/Jahr Daten in Mine_Data_Fields"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Hole alle Fördermenge/Jahr Einträge aus Mine_Data_Fields
            cursor.execute("""
                SELECT id, mine_id, field_name, primitive_value, numeric_value, unit
                FROM Mine_Data_Fields 
                WHERE field_name = 'Fördermenge/Jahr'
                AND (primitive_value IS NOT NULL OR numeric_value IS NOT NULL)
                AND primitive_value != 'X'
                AND primitive_value != ''
                ORDER BY id
            """)
            
            entries = cursor.fetchall()
            logger.info(f"Found {len(entries)} existing Fördermenge/Jahr entries in Mine_Data_Fields")
            
            # Klassifiziere die Werte
            rohstoff_entries = []
            abraum_entries = []
            ambiguous_entries = []
            
            for entry_id, mine_id, field_name, primitive_value, numeric_value, unit in entries:
                classification = self.classify_production_value(primitive_value, unit)
                entry_data = {
                    'id': entry_id,
                    'mine_id': mine_id,
                    'primitive_value': primitive_value,
                    'numeric_value': numeric_value,
                    'unit': unit,
                    'classification': classification
                }
                
                if classification == 'rohstoff':
                    rohstoff_entries.append(entry_data)
                elif classification == 'abraum':
                    abraum_entries.append(entry_data)
                else:
                    ambiguous_entries.append(entry_data)
            
            logger.info(f"Classification results:")
            logger.info(f"  - Rohstoff entries: {len(rohstoff_entries)}")
            logger.info(f"  - Abraum entries: {len(abraum_entries)}")
            logger.info(f"  - Ambiguous entries: {len(ambiguous_entries)}")
            
            return rohstoff_entries, abraum_entries, ambiguous_entries
    
    def classify_production_value(self, value_text, unit_text=None):
        """Klassifiziert einen Fördermenge-Wert als Rohstoff oder Abraum"""
        if not value_text:
            return 'unknown'
        
        combined_text = f"{value_text} {unit_text or ''}".lower()
        
        # Check for rohstoff indicators
        for pattern in self.rohstoff_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return 'rohstoff'
        
        # Check for abraum indicators
        for pattern in self.abraum_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return 'abraum'
        
        # Default logic: smaller numbers likely rohstoff, larger likely abraum
        # Extract numeric values
        numbers = re.findall(r'(\d+[,.]?\d*)', combined_text)
        if numbers:
            try:
                max_num = max([float(n.replace(',', '')) for n in numbers])
                # Heuristic: numbers > 1000 are likely total material (abraum)
                # numbers < 1000 are likely commodity production (rohstoff)
                if max_num > 1000:
                    return 'abraum'
                else:
                    return 'rohstoff'
            except ValueError:
                pass
        
        return 'unknown'
    
    def execute_migration(self):
        """Führt die Migration aus"""
        logger.info("🔄 STARTING CORRECTED FÖRDERMENGE MIGRATION")
        logger.info("=" * 60)
        
        # Analyze existing data
        rohstoff_entries, abraum_entries, ambiguous_entries = self.analyze_existing_data()
        
        migration_report = {
            'start_time': datetime.now().isoformat(),
            'original_entries': len(rohstoff_entries) + len(abraum_entries) + len(ambiguous_entries),
            'rohstoff_entries': len(rohstoff_entries),
            'abraum_entries': len(abraum_entries),
            'ambiguous_entries': len(ambiguous_entries),
            'created_entries': 0,
            'updated_entries': 0,
            'errors': []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Create rohstoff entries
                logger.info(f"Creating {len(rohstoff_entries)} Rohstoff entries...")
                for entry in rohstoff_entries:
                    # Duplicate entry with new field_name
                    cursor.execute("""
                        INSERT INTO Mine_Data_Fields (
                            search_result_id, mine_id, field_name, field_type, 
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, updated_at, normalized_value
                        )
                        SELECT 
                            search_result_id, mine_id, 'Fördermenge/Jahr Rohstoff', field_type,
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, ?, normalized_value
                        FROM Mine_Data_Fields 
                        WHERE id = ?
                    """, (datetime.now(), entry['id']))
                    migration_report['created_entries'] += 1
                
                # Create abraum entries
                logger.info(f"Creating {len(abraum_entries)} Abraum entries...")
                for entry in abraum_entries:
                    cursor.execute("""
                        INSERT INTO Mine_Data_Fields (
                            search_result_id, mine_id, field_name, field_type, 
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, updated_at, normalized_value
                        )
                        SELECT 
                            search_result_id, mine_id, 'Fördermenge/Jahr Abraum', field_type,
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, ?, normalized_value
                        FROM Mine_Data_Fields 
                        WHERE id = ?
                    """, (datetime.now(), entry['id']))
                    migration_report['created_entries'] += 1
                
                # Handle ambiguous entries (default to abraum for safety)
                logger.info(f"Creating {len(ambiguous_entries)} Ambiguous entries as Abraum (default)...")
                for entry in ambiguous_entries:
                    cursor.execute("""
                        INSERT INTO Mine_Data_Fields (
                            search_result_id, mine_id, field_name, field_type, 
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, updated_at, normalized_value
                        )
                        SELECT 
                            search_result_id, mine_id, 'Fördermenge/Jahr Abraum', field_type,
                            commodity_id, company_id, activity_status_id, mine_type_id,
                            country_id, region_id, primitive_value, numeric_value, unit,
                            confidence_score, is_template_value, validation_status,
                            source_name, model_used, session_id, extraction_timestamp,
                            model_id, source_id, created_at, ?, normalized_value
                        FROM Mine_Data_Fields 
                        WHERE id = ?
                    """, (datetime.now(), entry['id']))
                    migration_report['created_entries'] += 1
                
                conn.commit()
                logger.info("✅ Migration successful - all entries created")
                
                # Validation
                cursor.execute('SELECT COUNT(*) FROM Mine_Data_Fields WHERE field_name = "Fördermenge/Jahr Rohstoff"')
                rohstoff_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM Mine_Data_Fields WHERE field_name = "Fördermenge/Jahr Abraum"')
                abraum_count = cursor.fetchone()[0]
                
                logger.info(f"Validation results:")
                logger.info(f"  - Fördermenge/Jahr Rohstoff: {rohstoff_count} entries")
                logger.info(f"  - Fördermenge/Jahr Abraum: {abraum_count} entries")
                
                migration_report['final_rohstoff_count'] = rohstoff_count
                migration_report['final_abraum_count'] = abraum_count
                migration_report['success'] = True
                
            except Exception as e:
                migration_report['errors'].append(str(e))
                migration_report['success'] = False
                logger.error(f"Migration failed: {e}")
                raise
        
        # Save migration report
        report_path = f'migration_foerdermenge_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(migration_report, f, indent=2)
        
        logger.info(f"Migration report saved: {report_path}")
        return migration_report

def main():
    """Main execution"""
    migration = FoerdermengeMigrationFixed()
    report = migration.execute_migration()
    
    print("🎯 MIGRATION SUMMARY:")
    print(f"  Original entries: {report['original_entries']}")
    print(f"  Created entries: {report['created_entries']}")
    print(f"  Final Rohstoff: {report.get('final_rohstoff_count', 0)}")
    print(f"  Final Abraum: {report.get('final_abraum_count', 0)}")
    print(f"  Success: {report['success']}")
    
    if report['errors']:
        print(f"  Errors: {', '.join(report['errors'])}")
    
    return report

if __name__ == "__main__":
    main()