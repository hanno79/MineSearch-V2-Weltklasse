"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: NULL-Normalisierung für konsistente leere Werte

NULL-NORMALISIERUNG 25.08.2025: Konvertiert verschiedene leere Werte zu NULL
Löst das Problem mit 84 "-" Werten die zu NULL normalisiert werden müssen
"""

import logging
import json
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class NullNormalizer:
    """
    NULL-NORMALIZER 25.08.2025
    Standardisiert leere Werte zu echten NULL-Werten in der Datenbank
    """
    
    def __init__(self):
        """Initialisiert den NULL-Normalizer mit konfigurierten leeren Werten"""
        
        # KONFIGURIERTE LEERE WERTE 25.08.2025
        # Diese Werte werden alle zu NULL konvertiert
        self.null_equivalent_values: Set[str] = {
            # Explizite leere Marker
            '-', '_', 'X', 
            
            # Deutsche leere Marker  
            'nicht gefunden', 'nichts gefunden', 'keine Angaben', 'keine Information',
            'unbekannt', 'nicht verfügbar', 'nicht vorhanden', 'keine Daten',
            'nicht angegeben', 'keine Angabe', 'nicht ermittelt',
            
            # Englische leere Marker
            'not found', 'not available', 'unknown', 'N/A', 'n/a', 'n.a.',
            'not specified', 'no data', 'no information', 'TBD', 'tbd',
            'not applicable', 'not determined', 'none', 'null', 'NULL',
            
            # Leer/Whitespace (wird separat behandelt)
            '', ' ', '  ', '   ',
            
            # Spezielle Mining-spezifische leere Werte
            'still active', 'noch aktiv', 'mine closed', 'mine geschlossen',
            'nur exploration', 'only exploration', 'noch geplant', 'still planned',
            'in entwicklung', 'in development'
        }
        
        # CONDITIONAL NULL VALUES 25.08.2025
        # Diese sind nur in bestimmten Feldern als NULL zu behandeln
        self.conditional_null_values: Dict[str, Set[str]] = {
            'Produktionsende': {'noch aktiv', 'still active', 'currently active', 'aktiv'},
            'Fördermenge/Jahr': {'mine geschlossen', 'mine closed', 'geschlossen', 'closed'},
            'Kostenjahr': {'nicht verfügbar', 'not available', 'unbekannt', 'unknown'},
            'Dokumentenjahr': {'nicht verfügbar', 'not available', 'unbekannt', 'unknown'}
        }
    
    def is_null_equivalent(self, value: Any, field_name: Optional[str] = None) -> bool:
        """
        PRÜFT OB EIN WERT NULL-ÄQUIVALENT IST 25.08.2025
        
        Args:
            value: Zu prüfender Wert
            field_name: Feldname für kontextspezifische Prüfung (optional)
            
        Returns:
            True wenn Wert zu NULL konvertiert werden soll
        """
        if value is None:
            return True
            
        # Konvertiere zu String und normalisiere
        value_str = str(value).strip().lower()
        
        # Leerer String ist immer NULL
        if not value_str:
            return True
        
        # Prüfe explizite NULL-äquivalente Werte
        if value_str in {v.lower() for v in self.null_equivalent_values}:
            logger.debug(f"[NULL-NORMALIZER] NULL-äquivalenter Wert erkannt: '{value_str}'")
            return True
        
        # Prüfe feldspezifische NULL-Werte
        if field_name and field_name in self.conditional_null_values:
            conditional_nulls = {v.lower() for v in self.conditional_null_values[field_name]}
            if value_str in conditional_nulls:
                logger.debug(f"[NULL-NORMALIZER] Feldspezifischer NULL-Wert für '{field_name}': '{value_str}'")
                return True
        
        return False
    
    def normalize_value(self, value: Any, field_name: Optional[str] = None) -> Optional[str]:
        """
        NORMALISIERT EINEN EINZELNEN WERT 25.08.2025
        
        Args:
            value: Zu normalisierender Wert
            field_name: Feldname für kontextspezifische Normalisierung
            
        Returns:
            Normalisierter Wert (None für NULL, String für echte Werte)
        """
        if self.is_null_equivalent(value, field_name):
            logger.debug(f"[NULL-NORMALIZER] Wert '{value}' → NULL")
            return None
        
        # Echter Wert - bereinigen aber behalten
        cleaned_value = str(value).strip()
        logger.debug(f"[NULL-NORMALIZER] Wert '{value}' → '{cleaned_value}' (bereinigt)")
        return cleaned_value
    
    def normalize_structured_data(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        NORMALISIERT STRUKTURIERTE DATEN 25.08.2025
        
        Args:
            structured_data: Dictionary mit strukturierten Daten
            
        Returns:
            Normalisiertes Dictionary mit NULL-Werten
        """
        if not structured_data:
            return structured_data
        
        normalized_data = {}
        null_conversions = 0
        
        for field_name, field_value in structured_data.items():
            # Skip meta fields
            if field_name.startswith('_') or field_name in ['sources', 'source_mapping']:
                normalized_data[field_name] = field_value
                continue
            
            # Normalisiere Wert
            normalized_value = self.normalize_value(field_value, field_name)
            normalized_data[field_name] = normalized_value
            
            # Zähle NULL-Konvertierungen
            if field_value is not None and normalized_value is None:
                null_conversions += 1
                logger.debug(f"[NULL-NORMALIZER] Feld '{field_name}': '{field_value}' → NULL")
        
        if null_conversions > 0:
            logger.info(f"[NULL-NORMALIZER] {null_conversions} Werte zu NULL konvertiert")
        
        return normalized_data
    
    def normalize_database_entry(self, entry_id: int, structured_data_json: str, 
                                db_path: str = "/app/backend/minesearch/database/mines.db") -> bool:
        """
        NORMALISIERT EINZELNEN DATENBANK-EINTRAG 25.08.2025
        
        Args:
            entry_id: ID des Datenbank-Eintrags
            structured_data_json: JSON-String der strukturierten Daten
            db_path: Pfad zur Datenbank
            
        Returns:
            True wenn Eintrag normalisiert wurde
        """
        try:
            # Parse JSON
            structured_data = json.loads(structured_data_json)
            
            # Normalisiere Daten
            normalized_data = self.normalize_structured_data(structured_data)
            
            # Prüfe ob Änderungen vorgenommen wurden
            if normalized_data == structured_data:
                logger.debug(f"[NULL-NORMALIZER] Eintrag {entry_id}: Keine Normalisierung nötig")
                return False
            
            # Speichere normalisierte Daten zurück in DB
            normalized_json = json.dumps(normalized_data, ensure_ascii=False)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE search_results SET structured_data = ? WHERE id = ?",
                (normalized_json, entry_id)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"[NULL-NORMALIZER] Eintrag {entry_id} erfolgreich normalisiert")
            return True
            
        except Exception as e:
            logger.error(f"[NULL-NORMALIZER] Fehler bei Eintrag {entry_id}: {e}")
            return False
    
    def normalize_database(self, db_path: str = "/app/backend/minesearch/database/mines.db", 
                          batch_size: int = 100) -> Dict[str, int]:
        """
        NORMALISIERT KOMPLETTE DATENBANK 25.08.2025
        
        Args:
            db_path: Pfad zur Datenbank
            batch_size: Anzahl Einträge pro Batch
            
        Returns:
            Statistiken der Normalisierung
        """
        try:
            logger.info("[NULL-NORMALIZER] Starte Datenbank-NULL-Normalisierung...")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Hole alle Einträge mit structured_data
            cursor.execute("""
                SELECT id, mine_name, structured_data 
                FROM search_results 
                WHERE structured_data IS NOT NULL AND structured_data != ''
            """)
            
            all_entries = cursor.fetchall()
            conn.close()
            
            stats = {
                'total_entries': len(all_entries),
                'processed_entries': 0,
                'normalized_entries': 0,
                'skipped_entries': 0,
                'error_entries': 0
            }
            
            logger.info(f"[NULL-NORMALIZER] {stats['total_entries']} Einträge zu verarbeiten")
            
            # Verarbeite in Batches
            for i in range(0, len(all_entries), batch_size):
                batch = all_entries[i:i + batch_size]
                
                logger.info(f"[NULL-NORMALIZER] Verarbeite Batch {i//batch_size + 1} ({len(batch)} Einträge)...")
                
                for entry_id, mine_name, structured_data_json in batch:
                    try:
                        stats['processed_entries'] += 1
                        
                        if self.normalize_database_entry(entry_id, structured_data_json, db_path):
                            stats['normalized_entries'] += 1
                            logger.debug(f"[NULL-NORMALIZER] {mine_name} (ID: {entry_id}) normalisiert")
                        else:
                            stats['skipped_entries'] += 1
                            logger.debug(f"[NULL-NORMALIZER] {mine_name} (ID: {entry_id}) übersprungen")
                            
                    except Exception as e:
                        stats['error_entries'] += 1
                        logger.error(f"[NULL-NORMALIZER] Fehler bei {mine_name} (ID: {entry_id}): {e}")
            
            # Finale Statistiken
            logger.info(f"[NULL-NORMALIZER] ✅ NULL-Normalisierung abgeschlossen:")
            logger.info(f"[NULL-NORMALIZER]   📊 {stats['total_entries']} Einträge insgesamt")
            logger.info(f"[NULL-NORMALIZER]   ✅ {stats['normalized_entries']} Einträge normalisiert") 
            logger.info(f"[NULL-NORMALIZER]   ⏭️ {stats['skipped_entries']} Einträge übersprungen")
            logger.info(f"[NULL-NORMALIZER]   ❌ {stats['error_entries']} Fehler")
            
            return stats
            
        except Exception as e:
            logger.error(f"[NULL-NORMALIZER] Kritischer Fehler bei Datenbank-Normalisierung: {e}")
            return {'error': str(e)}
    
    def get_null_statistics(self, db_path: str = "/app/backend/minesearch/database/mines.db") -> Dict[str, Any]:
        """
        ANALYSIERT NULL-WERTE IN DER DATENBANK 25.08.2025
        
        Args:
            db_path: Pfad zur Datenbank
            
        Returns:
            Statistiken über NULL-Werte und normalisierbare Werte
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Hole alle Einträge
            cursor.execute("""
                SELECT id, mine_name, structured_data 
                FROM search_results 
                WHERE structured_data IS NOT NULL AND structured_data != ''
            """)
            
            entries = cursor.fetchall()
            conn.close()
            
            stats = {
                'total_entries': len(entries),
                'null_normalizable_fields': {},
                'fields_with_nulls': {},
                'total_null_normalizable': 0
            }
            
            for entry_id, mine_name, structured_data_json in entries:
                try:
                    structured_data = json.loads(structured_data_json)
                    
                    for field_name, field_value in structured_data.items():
                        if field_name.startswith('_') or field_name in ['sources']:
                            continue
                        
                        # Prüfe ob Wert NULL-normalisierbar ist
                        if self.is_null_equivalent(field_value, field_name):
                            if field_name not in stats['null_normalizable_fields']:
                                stats['null_normalizable_fields'][field_name] = 0
                            stats['null_normalizable_fields'][field_name] += 1
                            stats['total_null_normalizable'] += 1
                        
                        # Zähle bereits vorhandene NULL-Werte  
                        if field_value is None or field_value == '':
                            if field_name not in stats['fields_with_nulls']:
                                stats['fields_with_nulls'][field_name] = 0
                            stats['fields_with_nulls'][field_name] += 1
                
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"[NULL-STATISTICS] {stats['total_null_normalizable']} normalisierbare NULL-Werte gefunden")
            return stats
            
        except Exception as e:
            logger.error(f"[NULL-STATISTICS] Fehler bei NULL-Statistik-Analyse: {e}")
            return {'error': str(e)}

def main():
    """
    MAIN-FUNKTION 25.08.2025: Führt NULL-Normalisierung durch
    """
    print("🔄 NULL-NORMALISIERUNG TOOL")
    print("=" * 50)
    
    normalizer = NullNormalizer()
    
    # Analysiere aktuelle NULL-Situation
    print("📊 Analysiere aktuelle NULL-Werte...")
    stats = normalizer.get_null_statistics()
    
    if 'error' in stats:
        print(f"❌ Fehler bei Analyse: {stats['error']}")
        return False
    
    print(f"📈 {stats['total_entries']} Einträge analysiert")
    print(f"🔄 {stats['total_null_normalizable']} normalisierbare NULL-Werte gefunden")
    
    if stats['null_normalizable_fields']:
        print("\n🔍 Normalisierbare Felder:")
        for field, count in sorted(stats['null_normalizable_fields'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {field}: {count} Werte")
    
    if stats['total_null_normalizable'] == 0:
        print("✅ Keine NULL-Normalisierung nötig - alle Werte bereits korrekt!")
        return True
    
    # Sicherheitsabfrage  
    response = input(f"\n⚠️ {stats['total_null_normalizable']} Werte normalisieren? (ja/nein): ").lower().strip()
    
    if response not in ['ja', 'j', 'yes', 'y']:
        print("❌ NULL-Normalisierung abgebrochen.")
        return False
    
    # Führe Normalisierung durch
    print("\n🔄 Starte NULL-Normalisierung...")
    result_stats = normalizer.normalize_database()
    
    if 'error' in result_stats:
        print(f"❌ Fehler bei Normalisierung: {result_stats['error']}")
        return False
    
    print(f"\n✅ NULL-NORMALISIERUNG ABGESCHLOSSEN!")
    print(f"   📊 {result_stats['normalized_entries']} Einträge normalisiert")
    print(f"   ⏭️ {result_stats['skipped_entries']} Einträge übersprungen")
    print(f"   ❌ {result_stats['error_entries']} Fehler")
    
    return True

if __name__ == "__main__":
    main()