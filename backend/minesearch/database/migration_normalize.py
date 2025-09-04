#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Migration Script für Datenbank-Normalisierung
"""

import sqlite3
import logging
import os
from pathlib import Path
from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _parse_decimal_value(raw: Any) -> Optional[float]:
    """Parst einen numerischen Dezimalwert robust aus diversen Eingabeformaten.

    Regeln:
    - Entfernt Whitespace und alle nicht-numerischen Zeichen außer Ziffern, Vorzeichen, Punkt und Komma
    - Handhabt Tausendertrennzeichen und unterschiedliche Dezimaltrennzeichen
    - Ersetzt Komma erst nach Sicherstellung, dass höchstens ein Dezimaltrennzeichen übrig bleibt
    - Gibt bei ungültigen/leerem Input None zurück
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return float(raw)

        text = str(raw).strip()
        if not text:
            return None

        # Entferne Whitespaces und alle Zeichen außer Ziffern, +, -, ., ,
        cleaned = re.sub(r"\s+", "", text)
        cleaned = re.sub(r"[^0-9+\-\.,]", "", cleaned)

        # Muss mindestens eine Ziffer enthalten
        if not re.search(r"\d", cleaned or ""):
            return None

        # Behalte optionales Vorzeichen nur am Anfang
        sign = ""
        if cleaned and cleaned[0] in "+-":
            sign = "-" if cleaned[0] == "-" else ""
        # Entferne alle Vorzeichen im restlichen String
        numeric_part = re.sub(r"[+\-]", "", cleaned)

        # Bestimme Dezimaltrennzeichen-Strategie
        dot_pos = numeric_part.rfind(".")
        comma_pos = numeric_part.rfind(",")

        if dot_pos != -1 and comma_pos != -1:
            # Beide vorhanden: der letzte Separator ist das Dezimaltrennzeichen, die anderen sind Tausender
            decimal_pos = dot_pos if dot_pos > comma_pos else comma_pos
            result_chars = []
            for idx, ch in enumerate(numeric_part):
                if ch.isdigit():
                    result_chars.append(ch)
                elif ch in ",.":
                    if idx == decimal_pos:
                        result_chars.append(".")  # Normalisiere auf Punkt
                    # alle anderen Separatoren werden ignoriert (Tausender)
            normalized = "".join(result_chars)
        else:
            # Nur ein Separator-Typ oder keiner vorhanden
            if comma_pos != -1:
                # Nur Kommas vorhanden
                if numeric_part.count(",") == 1:
                    normalized = numeric_part.replace(",", ".")
                else:
                    # Mehrere Kommas: als Tausendertrennzeichen betrachten
                    normalized = numeric_part.replace(",", "")
            else:
                # Nur Punkte vorhanden (oder keiner)
                if numeric_part.count(".") == 1:
                    normalized = numeric_part
                else:
                    # Mehrere Punkte: als Tausendertrennzeichen betrachten
                    normalized = numeric_part.replace(".", "")

        # Füge Vorzeichen wieder an den Anfang an (falls negativ)
        if sign:
            normalized = sign + normalized

        # Final: validiere Format (maximal eine Dezimalstelle)
        if normalized.count(".") > 1:
            # Sollte durch obige Logik nicht vorkommen; als ungültig behandeln
            return None

        # Konvertiere zu float
        return float(normalized)
    except (ValueError, TypeError) as e:
        logger.debug(f"Ungültiges Dezimalformat '{raw}': {e}")
        return None

class DatabaseNormalizer:
    """
    Migriert die bestehende JSON-basierte Datenbank zu einem normalisierten Schema
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.schema_path = Path(__file__).parent / "normalized_schema.sql"
        
    def connect(self):
        """Verbinde zur Datenbank"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
            logger.info(f"✅ Verbunden zu: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
            return False
    
    def create_normalized_tables(self):
        """Erstelle die neuen normalisierten Tabellen"""
        try:
            # Lade Schema
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Führe Schema-Kommandos aus
            cursor = self.connection.cursor()
            
            # Aufsplitten in einzelne Statements (SQLite kann nicht mehrere auf einmal)
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        logger.debug(f"✅ SQL Statement ausgeführt: {statement[:50]}...")
                    except Exception as e:
                        logger.warning(f"⚠️ Statement failed: {e} - {statement[:100]}")
            
            self.connection.commit()
            logger.info("✅ Normalisierte Tabellen erstellt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema-Erstellung fehlgeschlagen: {e}")
            return False
    
    def analyze_existing_data(self):
        """Analysiere bestehende Daten für Migration"""
        try:
            cursor = self.connection.cursor()
            
            # Hole alle search_results
            cursor.execute("""
                SELECT id, mine_name, country, structured_data, structured_data_with_sources, model_used, search_timestamp
                FROM search_results 
                ORDER BY id
            """)
            
            results = cursor.fetchall()
            logger.info(f"📊 Zu migrierende Suchergebnisse: {len(results)}")
            
            # Analysiere Mine-Namen für Normalisierung
            mine_names = set()
            mine_countries = {}
            field_names = set()
            
            for row in results:
                search_id, mine_name, country, structured_data, structured_data_with_sources, model_used, timestamp = row
                
                if mine_name:
                    normalized_name = self.normalize_mine_name(mine_name)
                    mine_names.add((mine_name, normalized_name, country))
                    mine_countries[normalized_name] = country
                
                # Analysiere JSON-Felder
                if structured_data:
                    try:
                        if isinstance(structured_data, str):
                            data = json.loads(structured_data)
                        else:
                            data = structured_data
                            
                        if isinstance(data, dict):
                            field_names.update(data.keys())
                    except Exception as e:
                        logger.warning(f"JSON Parse Error für Result {search_id}: {e}")
            
            logger.info(f"📋 Unique Mine-Namen: {len(mine_names)}")
            logger.info(f"📋 Unique Feld-Namen: {len(field_names)}")
            
            # Zeige potentielle Duplikate
            normalized_counts = {}
            for original, normalized, country in mine_names:
                if normalized not in normalized_counts:
                    normalized_counts[normalized] = []
                normalized_counts[normalized].append((original, country))
            
            duplicates = {k: v for k, v in normalized_counts.items() if len(v) > 1}
            if duplicates:
                logger.warning("⚠️ Potentielle Mine-Duplikate gefunden:")
                for normalized, variants in duplicates.items():
                    logger.warning(f"  {normalized}: {variants}")
            
            return {
                'mine_names': mine_names,
                'field_names': field_names,
                'total_results': len(results),
                'duplicates': duplicates
            }
            
        except Exception as e:
            logger.error(f"❌ Datenanalyse fehlgeschlagen: {e}")
            return None
    
    def normalize_mine_name(self, name: str) -> str:
        """Normalisiere Mine-Namen für Konsistenz"""
        if not name:
            return ""
        
        # Basis-Normalisierung
        normalized = name.strip().lower()
        
        # Akzente entfernen (éléonore → eleonore)
        accent_map = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ñ': 'n', 'ç': 'c'
        }
        
        for accented, normal in accent_map.items():
            normalized = normalized.replace(accented, normal)
        
        # Entferne Sonderzeichen außer Zahlen und Buchstaben
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Entferne doppelte Leerzeichen
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def migrate_companies(self, mine_data):
        """Migriere Unternehmensdaten"""
        try:
            cursor = self.connection.cursor()
            companies = set()
            
            # Sammle alle Unternehmen aus den Daten
            cursor.execute("""
                SELECT structured_data FROM search_results 
                WHERE structured_data IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                structured_data = row[0]
                try:
                    if isinstance(structured_data, str):
                        data = json.loads(structured_data)
                    else:
                        data = structured_data
                    
                    # Eigentümer und Betreiber sammeln
                    if isinstance(data, dict):
                        owner = data.get('Eigentümer') or data.get('Owner') or data.get('owner')
                        operator = data.get('Betreiber') or data.get('Operator') or data.get('operator')
                        
                        if owner and owner != 'Nicht gefunden':
                            companies.add((owner, 'owner'))
                        if operator and operator != 'Nicht gefunden':
                            companies.add((operator, 'operator'))
                            
                except Exception as e:
                    logger.debug(f"JSON Parse Error: {e}")
            
            # Füge Unternehmen in companies Tabelle ein
            company_id_map = {}
            for company_name, company_type in companies:
                normalized = self.normalize_mine_name(company_name)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO companies (name, normalized_name, company_type) 
                    VALUES (?, ?, ?)
                """, (company_name, normalized, company_type))
                
                # Hole ID für Mapping
                cursor.execute("SELECT id FROM companies WHERE normalized_name = ?", (normalized,))
                result = cursor.fetchone()
                if result:
                    company_id_map[normalized] = result[0]
            
            self.connection.commit()
            logger.info(f"✅ {len(companies)} Unternehmen migriert")
            return company_id_map
            
        except Exception as e:
            logger.error(f"❌ Unternehmensmigration fehlgeschlagen: {e}")
            return {}
    
    def migrate_mines(self, mine_data, company_id_map):
        """Migriere Mine-Stammdaten"""
        try:
            cursor = self.connection.cursor()
            mine_id_map = {}
            
            # Verarbeite alle einzigartigen Minen
            mines_processed = set()
            
            for original_name, normalized_name, country in mine_data['mine_names']:
                if normalized_name in mines_processed:
                    continue
                
                # Standard-Werte
                region = None
                latitude = None  
                longitude = None
                status = 'active'
                mine_type = 'open_pit'
                primary_commodity = 'gold'
                owner_id = None
                operator_id = None
                
                # Suche zusätzliche Daten aus search_results
                cursor.execute("""
                    SELECT structured_data FROM search_results 
                    WHERE mine_name = ? LIMIT 1
                """, (original_name,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    try:
                        if isinstance(result[0], str):
                            data = json.loads(result[0])
                        else:
                            data = result[0]
                            
                        if isinstance(data, dict):
                            # Extrahiere zusätzliche Daten
                            region = data.get('Region') or data.get('region')
                            
                            # Koordinaten
                            lat_raw = data.get('x-Koordinate') or data.get('latitude') or data.get('lat')
                            lon_raw = data.get('y-Koordinate') or data.get('longitude') or data.get('lon')
                            
                            if lat_raw is not None:
                                latitude = _parse_decimal_value(lat_raw)
                                if latitude is None:
                                    logger.debug(f"Latitude konnte nicht geparst werden: {lat_raw!r}")
                            if lon_raw is not None:
                                longitude = _parse_decimal_value(lon_raw)
                                if longitude is None:
                                    logger.debug(f"Longitude konnte nicht geparst werden: {lon_raw!r}")
                            
                            # Status
                            status_raw = data.get('Aktivitätsstatus') or data.get('status')
                            if status_raw and 'aktiv' in str(status_raw).lower():
                                status = 'active'
                            elif status_raw and 'inaktiv' in str(status_raw).lower():
                                status = 'inactive'
                            
                            # Eigentümer/Betreiber IDs
                            owner_name = data.get('Eigentümer') or data.get('Owner')
                            operator_name = data.get('Betreiber') or data.get('Operator')
                            
                            if owner_name:
                                owner_normalized = self.normalize_mine_name(owner_name)
                                owner_id = company_id_map.get(owner_normalized)
                            
                            if operator_name:
                                operator_normalized = self.normalize_mine_name(operator_name)
                                operator_id = company_id_map.get(operator_normalized)
                    
                    except Exception as e:
                        logger.debug(f"Datenextraktion für {original_name}: {e}")
                
                # Füge Mine ein
                cursor.execute("""
                    INSERT OR REPLACE INTO mines_normalized 
                    (name, normalized_name, country, region, latitude, longitude, 
                     status, owner_company_id, operator_company_id, mine_type, primary_commodity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (original_name, normalized_name, country, region, latitude, longitude,
                     status, owner_id, operator_id, mine_type, primary_commodity))
                
                # Hole ID für Mapping
                cursor.execute("SELECT id FROM mines_normalized WHERE normalized_name = ?", (normalized_name,))
                result = cursor.fetchone()
                if result:
                    mine_id_map[normalized_name] = result[0]
                
                mines_processed.add(normalized_name)
            
            self.connection.commit()
            logger.info(f"✅ {len(mines_processed)} Minen migriert")
            return mine_id_map
            
        except Exception as e:
            logger.error(f"❌ Mine-Migration fehlgeschlagen: {e}")
            return {}
    
    def run_migration(self):
        """Führe komplette Migration aus"""
        logger.info("🚀 STARTE DATENBANK-NORMALISIERUNG")
        logger.info("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Schritt 1: Erstelle neue Tabellen
            logger.info("📋 SCHRITT 1: Erstelle normalisierte Tabellen")
            if not self.create_normalized_tables():
                return False
            
            # Schritt 2: Analysiere bestehende Daten
            logger.info("📋 SCHRITT 2: Analysiere bestehende Daten")
            mine_data = self.analyze_existing_data()
            if not mine_data:
                return False
            
            # Schritt 3: Migriere Unternehmen
            logger.info("📋 SCHRITT 3: Migriere Unternehmen")
            company_id_map = self.migrate_companies(mine_data)
            
            # Schritt 4: Migriere Minen
            logger.info("📋 SCHRITT 4: Migriere Mine-Stammdaten")
            mine_id_map = self.migrate_mines(mine_data, company_id_map)
            
            logger.info("🎉 MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
            logger.info(f"   📊 {len(company_id_map)} Unternehmen")
            logger.info(f"   🏔️ {len(mine_id_map)} Minen")
            logger.info(f"   📋 {mine_data['total_results']} Suchergebnisse")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration fehlgeschlagen: {e}")
            import traceback
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
            traceback.print_exc()
            return False
        
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main Entry Point"""
    # Finde Datenbank
    db_paths = [
        get_normalized_db_path(),
        get_normalized_db_path(),
        get_normalized_db_path(),
        "./minesearch.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        logger.error("❌ Keine Datenbank gefunden!")
        return False
    
    logger.info(f"🎯 Verwende Datenbank: {db_path}")
    
    # Starte Migration
    migrator = DatabaseNormalizer(db_path)
    return migrator.run_migration()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)