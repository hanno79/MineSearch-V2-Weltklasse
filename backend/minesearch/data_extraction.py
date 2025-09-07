"""
Author: rahn
Datum: 05.07.2025
Version: 2.0
Beschreibung: Refactorierte Datenextraktion für MineSearch - Hauptmodul
"""

import re
import logging
from typing import Dict, List, Any, Optional
from minesearch.config import config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.utils import clean_extracted_value, get_country_config
from minesearch.source_discovery import extract_sources_from_content

# Importiere neue Module
from minesearch.extraction_patterns import get_extraction_patterns, get_enhanced_coordinate_patterns
from minesearch.extraction_validators import (
    is_placeholder_value, validate_coordinate, 
    validate_restoration_cost, validate_year, validate_area
)
from minesearch.extraction_processors import (
    process_restoration_costs, process_activity_status,
    split_country_region, find_region_from_content,
    process_sources, post_process_data, clean_field_value,
    is_template_or_dummy_value, extract_core_value
)
from minesearch.source_manager import SourceManager
from minesearch.field_name_blacklist import is_field_name_value
from minesearch.database.normalized_manager import NormalizedDatabaseManager

logger = logging.getLogger(__name__)


class DataExtractor:
    """Klasse für strukturierte Datenextraktion aus Mining-Suchergebnissen"""
    
    def __init__(self):
        self.patterns = get_extraction_patterns()
        self.coordinate_patterns = get_enhanced_coordinate_patterns()
        self.source_manager = SourceManager()
        self.normalized_db = NormalizedDatabaseManager()
    
    def _get_field_status_marker(self, field: str, activity_status: str) -> str:
        """
        CONDITIONAL-FIELDS-FIX 15.07.2025: Generiert aussagekräftige Status-Marker
        
        Args:
            field: Feldname
            activity_status: Aktivitätsstatus der Mine
            
        Returns:
            Passender Status-Marker für das Feld
        """
        if not activity_status:
            # REGEL 10 KONFORM: Leeres Feld lassen statt ausgedachten Marker
            return ''  # Echte "nicht gefunden" - kein Dummy-Marker
            
        activity_lower = activity_status.lower()
        
        # Produktionsende bei aktiven Minen
        if field == 'Produktionsende':
            if any(status in activity_lower for status in ['aktiv', 'explorativ', 'geplant', 'entwicklung']):
                return 'noch aktiv'
                
        # Fördermenge bei inaktiven Minen
        if field == 'Fördermenge/Jahr':
            if any(status in activity_lower for status in ['geschlossen', 'explorativ', 'geplant', 'entwicklung']):
                if 'geschlossen' in activity_lower:
                    return 'Mine geschlossen'
                elif 'explorativ' in activity_lower:
                    return 'nur Exploration'
                elif 'geplant' in activity_lower:
                    return 'noch geplant'
                elif 'entwicklung' in activity_lower:
                    return 'in Entwicklung'
                    
        # REGEL 10 KONFORM: Kein Fallback-Marker - leer lassen wenn unbekannt  
        return ''  # Echte "nicht gefunden" - kein Dummy-Marker
    
    def _should_set_status_marker(self, field: str, activity_status: str) -> bool:
        """
        CLEAN DATA AT SOURCE FIX 20.08.2025: Prüft ob ein Feld einen Status-Marker braucht
        
        Nur bei logischen Ausschlüssen (z.B. "Produktionsende" bei aktiver Mine) 
        werden Status-Marker gesetzt. Normale "nicht gefunden" Felder bleiben leer.
        
        Args:
            field: Feldname
            activity_status: Aktivitätsstatus der Mine
            
        Returns:
            True wenn Status-Marker gesetzt werden soll, False für normale leere Felder
        """
        if not activity_status:
            return False  # Keine Status-Marker wenn Aktivitätsstatus unbekannt
            
        activity_lower = activity_status.lower()
        
        # Produktionsende bei aktiven Minen → "noch aktiv" 
        if field == 'Produktionsende':
            if any(status in activity_lower for status in ['aktiv', 'explorativ', 'geplant', 'entwicklung']):
                return True
                
        # Fördermenge bei inaktiven Minen → spezifische Status-Marker
        if field == 'Fördermenge/Jahr':
            if any(status in activity_lower for status in ['geschlossen', 'explorativ', 'geplant', 'entwicklung']):
                return True
        
        # Alle anderen Felder: keine Status-Marker, bleiben leer
        return False
    
    def _is_valid_data_value(self, value: str, field: str) -> bool:
        """
        RULE 10 COMPLIANCE 26.08.2025: ULTRA-VERSCHÄRFTES Quality Gate für alle Felder
        
        Prüft JEDES Datenfeld gegen alle bekannten Template/Schätzungs/Dummy-Muster.
        ABSOLUT NULL-TOLERANZ für verdächtige Werte.
        
        Args:
            value: Zu prüfender Wert  
            field: Feldname für spezifische Validierung
            
        Returns:
            True nur bei 100% verifizierten echten Datenwerten
        """
        if not value or not str(value).strip():
            return False
            
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        logger.debug(f"[ULTRA QUALITY GATE] Validiere Wert '{value_str}' für Feld '{field}'")
        
        # 0. KRITISCHER FELDNAMEN-CHECK (HÖCHSTE PRIORITÄT) 
        if is_field_name_value(value_str, field):
            logger.error(f"[CRITICAL FIELD-NAME-CHECK] Feldname als Wert: '{value_str}' für '{field}' → BLOCKIERT")
            return False
        
        # 1. TEMPLATE/DUMMY DETECTION (verschärft durch extraction_processors.py)
        if is_template_or_dummy_value(value_str, field):
            logger.warning(f"[ULTRA QUALITY GATE] Template/Dummy-Wert: '{value_str}' → ABGELEHNT")
            return False
        
        # 2. RULE 10 COMPLIANCE CHECKS - NEUE VERSCHÄRFUNGEN
        
        # 2.1: NULL-NORMALISIERUNG Integration
        from minesearch.null_normalizer import NullNormalizer
        null_normalizer = NullNormalizer()
        if null_normalizer.is_null_equivalent(value_str, field):
            logger.warning(f"[ULTRA QUALITY GATE] NULL-äquivalenter Wert: '{value_str}' → ABGELEHNT")
            return False
        
        # 2.2: Koordinaten-Validierung (Integration mit extraction_validators.py)
        if field in ['x-Koordinate', 'y-Koordinate']:
            from minesearch.extraction_validators import validate_coordinate
            coord_type = 'x' if field == 'x-Koordinate' else 'y'
            validated_coord = validate_coordinate(value_str, coord_type)
            if not validated_coord:
                logger.warning(f"[ULTRA QUALITY GATE] Ungültige Koordinate: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.3: Restaurationskosten-Validierung  
        if field == 'Restaurationskosten':
            from minesearch.extraction_validators import validate_restoration_cost
            validated_cost = validate_restoration_cost(value_str)
            if not validated_cost:
                logger.warning(f"[ULTRA QUALITY GATE] Ungültige Restaurationskosten: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.4: Jahr-Validierung
        if field in ['Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes', 
                    'Produktionsstart', 'Produktionsende', 'Kostenjahr', 'Dokumentenjahr']:
            from minesearch.extraction_validators import validate_year
            field_type = 'costs' if 'kosten' in field.lower() else 'document' if 'dokument' in field.lower() else 'production'
            validated_year = validate_year(value_str, field_type)
            if not validated_year:
                logger.warning(f"[ULTRA QUALITY GATE] Ungültiges Jahr: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.5: Flächenvalidierung
        if field in ['Fläche der Mine in qkm', 'Minenfläche in qkm']:
            from minesearch.extraction_validators import validate_area
            validated_area = validate_area(value_str)
            if not validated_area:
                logger.warning(f"[ULTRA QUALITY GATE] Ungültige Fläche: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.6: Firmenname-Validierung (Eigentümer/Betreiber)
        if field in ['Eigentümer', 'Betreiber']:
            # Koordinaten in Firmennamen-Feldern
            if re.match(r'^[\d\.\-\s,°\'\"]+$', value_str):
                logger.warning(f"[ULTRA QUALITY GATE] Koordinaten in {field}: '{value_str}' → ABGELEHNT")
                return False
                
            # Generic company names 
            generic_company_patterns = [
                r'^mining company$', r'^bergbauunternehmen$', r'^mining corp$',
                r'^the company$', r'^das unternehmen$', r'^operator$', r'^betreiber$',
                r'^owner$', r'^eigentümer$', r'^local company$', r'^private company$'
            ]
            if any(re.match(pattern, value_lower) for pattern in generic_company_patterns):
                logger.warning(f"[ULTRA QUALITY GATE] Generischer Firmenname: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.7: Rohstoff-Validierung
        if field in ['Rohstoff', 'Rohstoffe']:
            # Template-Strukturen mit "usw."
            if 'usw.' in value_lower or 'etc.' in value_lower:
                logger.warning(f"[ULTRA QUALITY GATE] Template-Rohstoff mit 'usw.': '{value_str}' → ABGELEHNT")
                return False
                
        # 2.8: Status-Validierung
        if field == 'Aktivitätsstatus':
            # Template-Status mit Optionen
            if '/' in value_str and any(word in value_lower for word in ['sonstiges', 'usw.', 'etc.']):
                logger.warning(f"[ULTRA QUALITY GATE] Template-Status: '{value_str}' → ABGELEHNT")
                return False
        
        # 2.9: AI-Entschuldigung Detection (erweitert)
        ai_excuse_patterns = [
            'ohne spezifische', 'mangels konkreter', 'keine verlässlichen',
            'no specific', 'without specific', 'lacking concrete',
            'based on similar', 'typical for', 'generally ranges',
            'fachwissen', 'allgemeines fachwissen', 'expert knowledge'
        ]
        if any(pattern in value_lower for pattern in ai_excuse_patterns):
            logger.warning(f"[ULTRA QUALITY GATE] AI-Entschuldigung erkannt: '{value_str}' → ABGELEHNT")
            return False
        
        # 2.10: Zu kurze Werte (aber "-" als legitimier empty marker erlauben)
        if len(value_str) <= 2 and value_str not in ['-']:
            logger.warning(f"[ULTRA QUALITY GATE] Zu kurzer Wert: '{value_str}' → ABGELEHNT")
            return False
            
        # ALLE CHECKS BESTANDEN - Wert ist echt und kann gespeichert werden
        logger.debug(f"[ULTRA QUALITY GATE] Wert '{value_str}' für Feld '{field}' → AKZEPTIERT (alle Prüfungen bestanden)")
        return True
    
    def extract_structured_data(self, content: str, mine_name: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrahiere strukturierte Daten aus dem Perplexity-Response
        
        CLEAN DATA AT SOURCE FIX 20.08.2025: Keine Dummy-Werte in DB - nur echte Daten oder NULL
        
        Args:
            content: Perplexity API Antwort
            mine_name: Name der Mine
            country: Land (optional)
            
        Returns:
            Dict mit extrahierten Daten und Quellen-Mapping
        """
        try:
            # Reset SourceManager für neue Extraktion
            self.source_manager = SourceManager()
            
            # Extrahiere Quellen aus Response
            response_sources = self.source_manager.extract_sources_from_response(content)
            
            data = {col: '' for col in CSV_COLUMNS}
            data['Name'] = mine_name
            
            # Hole länderspezifische Währung
            country_config = get_country_config(country) if country else {}
            currency = country_config.get('currency', 'USD')
            
            # KOORDINATEN-FIX 03.09.2025: Extrahiere Country ZUERST und setze globalen Kontext
            country_extracted = False
            from minesearch.extraction_validators import validate_coordinate
            
            # Setze Länder-Kontext aus Parameter wenn verfügbar
            if country:
                validate_coordinate._country_context = country
                logger.debug(f"[COORD-CONTEXT] Globaler Länder-Kontext aus Parameter gesetzt: {country}")
                country_extracted = True
            
            # Extrahiere Daten mit Patterns
            for field, field_patterns in self.patterns.items():
                # Setze Länder-Kontext sobald Country extrahiert wurde
                if field == 'Country' and not country_extracted:
                    value = self._extract_field(field, field_patterns, content, currency)
                    if value:
                        clean_value, field_sources = self.source_manager.parse_field_with_sources(value)
                        if self._is_valid_data_value(clean_value, field):
                            data[field] = clean_value
                            # Setze Länder-Kontext für Koordinaten-Validierung
                            from minesearch.extraction_validators import validate_coordinate
                            if hasattr(validate_coordinate, '_country_context'):
                                delattr(validate_coordinate, '_country_context')
                            validate_coordinate._country_context = clean_value
                            country_extracted = True
                            logger.debug(f"[COORD-CONTEXT] Länder-Kontext früh gesetzt: {clean_value}")
                            
                            # Standard monitoring und source assignment
                            from minesearch.template_monitor import monitor_extraction_result
                            source_values = [s.get('value', '') for s in field_sources] if field_sources else []
                            try:
                                monitor_extraction_result(field, clean_value, mine_name, source_values)
                            except Exception as e:
                                logger.exception(f"[TEMPLATE MONITOR] Fehler beim Monitoring für Feld '{field}' in Mine '{mine_name}' mit Quellen {source_values}: {e}")
                            
                            if field_sources:
                                self.source_manager.assign_field_sources(field, field_sources)
                            elif response_sources and clean_value not in ['X', '']:
                                self.source_manager.assign_field_sources(field, response_sources)
                    continue  # Country bereits verarbeitet
                    
                value = self._extract_field(field, field_patterns, content, currency)
                if value:
                    # ÄNDERUNG 07.07.2025: Debug-Logging vor Platzhalter-Check
                    logger.debug(f"[EXTRACTION-PRE] Feld '{field}' extrahiert: '{value[:100]}...'")
                    
                    # QUELLENREFERENZEN-FIX 19.07.2025: Parse Quellen aus Feld-Text
                    clean_value, field_sources = self.source_manager.parse_field_with_sources(value)
                    
                    # CLEAN DATA AT SOURCE FIX 20.08.2025: Rigorose Data Quality Gate
                    if self._is_valid_data_value(clean_value, field):
                        logger.debug(f"[EXTRACTION-POST] Feld '{field}' behalten: '{clean_value[:100]}...'")
                        data[field] = clean_value
                        
                        # PHASE 8: Template-Monitoring Integration
                        from minesearch.template_monitor import monitor_extraction_result
                        source_values = [s.get('value', '') for s in field_sources] if field_sources else []
                        try:
                            monitor_extraction_result(field, clean_value, mine_name, source_values)
                        except Exception as e:
                            logger.exception(f"[TEMPLATE MONITOR] Fehler beim Monitoring für Feld '{field}' in Mine '{mine_name}' mit Quellen {source_values}: {e}")
                        
                        # Wenn Feldquellen gefunden, zuordnen; sonst alle Response-Quellen verwenden
                        if field_sources:
                            self.source_manager.assign_field_sources(field, field_sources)
                        elif response_sources and clean_value not in ['X', '']:
                            # Für alle Felder mit echten Daten: alle gefundenen Quellen zuordnen
                            self.source_manager.assign_field_sources(field, response_sources)
                    else:
                        # CLEAN DATA AT SOURCE FIX: Template/Dummy-Werte → NULL statt X
                        logger.info(f"[DATA QUALITY GATE] Template/Dummy-Wert '{clean_value}' für Feld '{field}' abgelehnt - bleibt leer")
                        data[field] = ""  # Leer lassen - wird später zu NULL in DB
            
            # Spezielle Behandlung für Koordinaten mit erweiterten Patterns
            data = self._extract_coordinates(content, data)
            
            # FIX 02.09.2025: Fallback-Extraction für unlabeled/slash-getrennte Daten
            data = self._extract_unlabeled_data(content, data)
            
            # FIX 02.09.2025: Post-Processing für verpasste Daten - Raw Content nochmal durchsuchen
            data = self._post_process_missed_data(content, data, mine_name)
            
            # Post-Processing
            data = post_process_data(data, content, country_config)
            
            # Validierung spezifischer Felder
            data = self._validate_fields(data, currency)
            
            # QUELLENREFERENZEN-FIX 19.07.2025: Erstelle Quellenangaben mit neuer Logik
            data['Quellenangaben'] = self.source_manager.get_sources_summary()
            
            # SYSTEM-FELD FILTER 05.09.2025: _source_mapping wird NICHT mehr als Feld gespeichert
            # da es JSON-Strukturen enthält und die Datenbank kontaminiert.
            # Source-Mappings werden über separate Tabellen/Relationen verwaltet.
            
            # KERNWERTE-EXTRAKTION 27.08.2025: Extrahiere atomare Werte aus Sätzen
            # Bereinige alle Feldwerte NACH Quellen-Zuordnung
            for field in CSV_COLUMNS:
                if field in data and data[field] and field not in FIELDS_WITHOUT_SOURCES:
                    if isinstance(data[field], str):  # Nur String-Werte bereinigen
                        # 1. Extrahiere Kernwert (atomare Daten statt Sätze)
                        data[field] = extract_core_value(data[field], field)
                        # 2. Zusätzliche Bereinigung
                        data[field] = clean_field_value(data[field], field)
            
            # ARCHITEKTUR-FIX 03.09.2025: Quellenreferenzen [1,2,3] NICHT in DB-Felder!
            # format_field_with_sources wird nur noch für CSV-Export verwendet
            # Hier bleiben die Felder sauber ohne [1,2,3] - Quellenreferenzen sind im _source_mapping
            logger.debug("[CLEAN DB] Quellenreferenzen werden NICHT in DB-Felder eingefügt - nur in _source_mapping gespeichert")
            
            # CLEAN DATA AT SOURCE FIX 20.08.2025: Markiere nur logisch ausgeschlossene Felder
            # Leere Felder bleiben leer (NULL) - keine X-Marker für einfache "nicht gefunden"
            activity_status = data.get('Aktivitätsstatus', '')
            
            for field in CSV_COLUMNS:
                if field != 'Name' and field != 'Quellenangaben':  # Name und Quellenangaben ausschließen
                    if not data.get(field) or str(data[field]).strip() == '':
                        # NUR bei logischen Ausschlüssen Status-Marker setzen
                        if self._should_set_status_marker(field, activity_status):
                            status_marker = self._get_field_status_marker(field, activity_status)
                            data[field] = status_marker
                            logger.debug(f"[FIELD MARKER] Feld '{field}' als '{status_marker}' markiert (logischer Ausschluss)")
                        else:
                            # Feld bleibt leer - wird zu NULL in DB
                            logger.debug(f"[CLEAN DATA] Feld '{field}' bleibt leer - nicht gefunden")
            
            # ÄNDERUNG 15.07.2025: Detailliertes Logging der extrahierten Felder
            filled_fields = [(k, v) for k, v in data.items() if v and str(v).strip() and str(v).strip() not in ['X', 'noch aktiv', 'Mine geschlossen', 'nur Exploration', 'noch geplant', 'in Entwicklung']]
            x_marked_fields = [(k, v) for k, v in data.items() if str(v).strip() == 'X']
            status_marked_fields = [(k, v) for k, v in data.items() if str(v).strip() in ['noch aktiv', 'Mine geschlossen', 'nur Exploration', 'noch geplant', 'in Entwicklung']]
            logger.info(f"[DATA EXTRACTION] {len(filled_fields)} Felder mit Daten, {len(x_marked_fields)} als 'X' markiert, {len(status_marked_fields)} Status-Marker")
            
            # Log die ersten gefüllten Felder
            for field, value in filled_fields[:10]:
                logger.debug(f"[DATA EXTRACTION] {field}: '{str(value)[:80]}...'")
            
            # Warne bei kritischen fehlenden Feldern
            critical_fields = ['Eigentümer', 'Betreiber', 'Aktivitätsstatus', 'Rohstoff']            
            missing_critical = [f for f in critical_fields if not data.get(f)]
            if missing_critical:
                logger.warning(f"[DATA EXTRACTION] Kritische Felder fehlen: {missing_critical}")
            
            return data
            
        except Exception as e:
            logger.error(f"[DATA EXTRACTION ERROR] Fehler bei Datenextraktion: {str(e)}")
            return {col: '' for col in CSV_COLUMNS}
    
    def _extract_field(self, field: str, patterns: List[str], content: str, currency: str) -> Optional[str]:
        """Extrahiere ein spezifisches Feld mit den gegebenen Patterns"""
        # ÄNDERUNG 07.07.2025: Debug-Logging für Feld-Extraktion
        logger.debug(f"[EXTRACT-FIELD] Versuche '{field}' mit {len(patterns)} Patterns zu extrahieren")
        
        # FALLBACK 09.08.2025: Spezialbehandlung für Restaurationskosten ohne externes Modul
        if field == 'Restaurationskosten':
            try:
                from extraction_restoration_costs import RestorationCostExtractor
                extractor = RestorationCostExtractor()
                result = extractor.extract_restoration_costs(content)
                if result and 'restoration_costs' in result:
                    logger.debug(f"[EXTRACT-FIELD] Restaurationskosten gefunden: {result['restoration_costs']}")
                    return result['restoration_costs']
            except ImportError:
                # FALLBACK: Nutze Standard-Patterns statt spezialisiertes Modul
                logger.debug("[EXTRACT-FIELD] FALLBACK: extraction_restoration_costs Modul nicht verfügbar - nutze Standard-Patterns")
                pass  # Continue with standard extraction patterns
        
        for pattern in patterns:
            try:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    
                    # Spezialbehandlung für Restaurationskosten
                    if field == 'Restaurationskosten':
                        value = process_restoration_costs(value, match.group(0), currency)
                    
                    # Bereinigung
                    value = clean_extracted_value(value)
                    
                    if value:
                        logger.debug(f"[EXTRACTION] {field}: '{value}' gefunden mit Pattern: {pattern[:50]}...")
                        return value
                        
            except re.error as e:
                logger.error(f"[REGEX ERROR] Fehler bei Pattern für {field}: {e}")
                continue
        
        # ÄNDERUNG 07.07.2025: Log wenn kein Pattern matched
        logger.debug(f"[EXTRACT-FIELD] Kein Pattern hat für '{field}' gematched")
        return None
    
    def _extract_coordinates(self, content: str, data: Dict[str, str]) -> Dict[str, str]:
        """
        KOORDINATEN-FIX 03.09.2025: Extrahiere Koordinaten mit Länder-Kontext für automatische Korrektur
        """
        # Setze Länder-Kontext für validate_coordinate
        country = data.get('Country', data.get('Land', ''))
        if country:
            validate_coordinate._country_context = country
            logger.debug(f"[COORD-CONTEXT] Länder-Kontext gesetzt: {country}")
        
        # Versuche zuerst mit Standard-Patterns
        if not data.get('x-Koordinate'):
            for pattern in self.coordinate_patterns['latitude']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    if 'DMS' in pattern or '°' in pattern:
                        # Handle DMS format
                        coord = validate_coordinate(match.group(0), 'x')
                    else:
                        coord = validate_coordinate(match.group(1), 'x')
                    
                    if coord:
                        data['x-Koordinate'] = coord
                        logger.info(f"[COORDINATES] Latitude gefunden: {coord}")
                        break
        
        if not data.get('y-Koordinate'):
            for pattern in self.coordinate_patterns['longitude']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    logger.debug(f"[COORD-MATCH] Longitude Pattern matched: '{pattern[:50]}...' → '{match.group()}'")
                    if 'DMS' in pattern or '°' in pattern:
                        # Handle DMS format
                        raw_value = match.group(0)
                        logger.debug(f"[COORD-DEBUG] DMS Raw value: '{raw_value}'")
                        coord = validate_coordinate(raw_value, 'y')
                        logger.debug(f"[COORD-DEBUG] DMS After validation: '{coord}'")
                    else:
                        raw_value = match.group(1)
                        logger.debug(f"[COORD-DEBUG] Decimal Raw value: '{raw_value}'")
                        coord = validate_coordinate(raw_value, 'y')
                        logger.debug(f"[COORD-DEBUG] Decimal After validation: '{coord}'")
                    
                    if coord:
                        data['y-Koordinate'] = coord
                        logger.info(f"[COORDINATES] Longitude gefunden: {coord} (Land: {country})")
                        break
        
        # Lösche Länder-Kontext nach Nutzung
        if hasattr(validate_coordinate, '_country_context'):
            delattr(validate_coordinate, '_country_context')
        
        return data
    
    def _extract_unlabeled_data(self, content: str, data: Dict[str, str]) -> Dict[str, str]:
        """
        FIX 02.09.2025: Fallback-Extraction für unlabeled/slash-getrennte Formate
        
        Verarbeitet Formate wie:
        "Casa Berardi Mine / Kanada / Quebec / 49.5731083 / -79.2369972 / $61.4M restoration costs"
        
        Args:
            content: Roher Content
            data: Bisherige extrahierte Daten
            
        Returns:
            Ergänzte Daten mit unlabeled Extraktion
        """
        logger.debug("[UNLABELED] Starte Fallback-Extraktion für unlabeled/slash-getrennte Formate")
        
        # Pattern für typische slash-getrennte Formate (Perplexity-Style)
        slash_patterns = [
            # Format: Mine / Land / Region / Latitude / Longitude / weitere Infos
            r'([^/]+\s*(?:mine|Mine))\s*/\s*([^/]+)\s*/\s*([^/]+)\s*/\s*([-+]?\d{2}\.?\d+)\s*/\s*([-+]?\d{2,3}\.?\d+)(?:\s*/\s*(.*))?',
            # Format ohne "Mine": Name / Land / Region / Lat / Long / Info
            r'([^/]+)\s*/\s*([Kk]anada|[Cc]anada|[Cc]hile|[Pp]eru|[Mm]exico|[Uu]SA)\s*/\s*([^/]+)\s*/\s*([-+]?\d{2}\.?\d+)\s*/\s*([-+]?\d{2,3}\.?\d+)(?:\s*/\s*(.*))?',
            # Nur Koordinaten mit zusätzlichen Infos
            r'([-+]?\d{2}\.?\d+)\s*/\s*([-+]?\d{2,3}\.?\d+)\s*/\s*(.+?)(?:\$\s*[\d,]+(?:\.\d+)?(?:M|million))?'
        ]
        
        extracted_data = {}
        
        for i, pattern in enumerate(slash_patterns):
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                logger.debug(f"[UNLABELED] Pattern {i+1} gefunden: {groups}")
                
                try:
                    if i == 0:  # Vollständiges Format mit Mine-Name
                        mine_name, country, region, lat, lng = groups[:5]
                        extra_info = groups[5] if len(groups) > 5 and groups[5] else ""
                        
                        if not data.get('Country'):
                            extracted_data['Country'] = country.strip()
                        if not data.get('Region'):
                            extracted_data['Region'] = region.strip()
                        if not data.get('x-Koordinate'):
                            validated_lat = validate_coordinate(lat.strip(), 'x')
                            if validated_lat:
                                extracted_data['x-Koordinate'] = validated_lat
                        if not data.get('y-Koordinate'):
                            validated_lng = validate_coordinate(lng.strip(), 'y')
                            if validated_lng:
                                extracted_data['y-Koordinate'] = validated_lng
                        
                        # Extrahiere Restaurationskosten aus extra_info
                        if extra_info and not data.get('Restaurationskosten'):
                            cost_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)', extra_info, re.IGNORECASE)
                            if cost_match:
                                extracted_data['Restaurationskosten'] = f"${cost_match.group(1)}M"
                    
                    elif i == 1:  # Format ohne expliziten "Mine"
                        name, country, region, lat, lng = groups[:5]
                        extra_info = groups[5] if len(groups) > 5 and groups[5] else ""
                        
                        if not data.get('Country'):
                            extracted_data['Country'] = country.strip()
                        if not data.get('Region'):
                            extracted_data['Region'] = region.strip()
                        if not data.get('x-Koordinate'):
                            validated_lat = validate_coordinate(lat.strip(), 'x')
                            if validated_lat:
                                extracted_data['x-Koordinate'] = validated_lat
                        if not data.get('y-Koordinate'):
                            validated_lng = validate_coordinate(lng.strip(), 'y')
                            if validated_lng:
                                extracted_data['y-Koordinate'] = validated_lng
                    
                    elif i == 2:  # Nur Koordinaten mit Infos
                        lat, lng, info = groups
                        if not data.get('x-Koordinate'):
                            validated_lat = validate_coordinate(lat.strip(), 'x')
                            if validated_lat:
                                extracted_data['x-Koordinate'] = validated_lat
                        if not data.get('y-Koordinate'):
                            validated_lng = validate_coordinate(lng.strip(), 'y')
                            if validated_lng:
                                extracted_data['y-Koordinate'] = validated_lng
                        
                        # Extrahiere weitere Infos aus info
                        if info and not data.get('Restaurationskosten'):
                            cost_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)', info, re.IGNORECASE)
                            if cost_match:
                                extracted_data['Restaurationskosten'] = f"${cost_match.group(1)}M"
                
                except Exception as e:
                    logger.debug(f"[UNLABELED] Fehler bei Pattern {i+1}: {e}")
                    continue
        
        # Weitere unlabeled Patterns für spezifische Felder
        self._extract_unlabeled_restoration_costs(content, extracted_data, data)
        self._extract_unlabeled_ownership(content, extracted_data, data)
        
        # Übertrage extrahierte Daten
        for field, value in extracted_data.items():
            if value and self._is_valid_data_value(value, field):
                data[field] = value
                logger.info(f"[UNLABELED] Feld '{field}' ergänzt: '{value}'")
        
        return data
    
    def _extract_unlabeled_restoration_costs(self, content: str, extracted_data: Dict[str, str], existing_data: Dict[str, str]):
        """Extrahiert Restaurationskosten aus unlabeled Textstellen"""
        if existing_data.get('Restaurationskosten'):
            return
            
        # Pattern für unlabeled Millionen-Beträge in Kontexten
        patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:M|million)\s*(?:CAD|USD)?\s*(?:for|zur|pour|para)?\s*(?:restoration|closure|reclamation|fermeture|cierre)',
            r'(?:restoration|closure|reclamation)\s*(?:costs?|coûts?)?\s*(?:of|de)?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)\s*(?:environmental|restoration|closure)',
            # Direkte Beträge nach Koordinaten
            r'[-+]?\d{2}\.?\d+\s*/\s*[-+]?\d{2,3}\.?\d+.*?\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cost_value = match.group(1)
                # Validiere den Betrag
                if cost_value and cost_value.replace(',', '').replace('.', '').isdigit():
                    extracted_data['Restaurationskosten'] = f"${cost_value}M"
                    logger.debug(f"[UNLABELED] Restaurationskosten unlabeled gefunden: ${cost_value}M")
                    break
    
    def _extract_unlabeled_ownership(self, content: str, extracted_data: Dict[str, str], existing_data: Dict[str, str]):
        """Extrahiert Eigentümer/Betreiber aus unlabeled Kontexten"""
        # Pattern für Unternehmensstrukturen in unlabeled Texten
        company_patterns = [
            r'(?:owned|operated|managed)\s+by\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|SA|Ltda)\.?)',
            r'([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|SA|Ltda)\.?)\s+(?:owns|operates|manages)',
            r'subsidiary\s+of\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|SA|Ltda)\.?)',
            # Französische Patterns für Quebec
            r'(?:détenu|exploité|géré)\s+par\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltée|SA)\.?)',
            r'filiale\s+(?:de|d\')\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltée|SA)\.?)'
        ]
        
        if not existing_data.get('Eigentümer'):
            for pattern in company_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    owner = match.group(1).strip()
                    if len(owner) > 3 and not any(word in owner.lower() for word in ['mining', 'mine', 'minerals']):
                        extracted_data['Eigentümer'] = owner
                        logger.debug(f"[UNLABELED] Eigentümer unlabeled gefunden: {owner}")
                        break
        
        if not existing_data.get('Betreiber'):
            operator_patterns = [
                r'operated\s+by\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|SA|Ltda)\.?)',
                r'operator:\s*([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|SA|Ltda)\.?)',
                r'exploité\s+par\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltée|SA)\.?)'
            ]
            
            for pattern in operator_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    operator = match.group(1).strip()
                    if len(operator) > 3:
                        extracted_data['Betreiber'] = operator
                        logger.debug(f"[UNLABELED] Betreiber unlabeled gefunden: {operator}")
                        break
    
    def _post_process_missed_data(self, content: str, data: Dict[str, str], mine_name: str) -> Dict[str, str]:
        """
        FIX 02.09.2025: Post-Processing für verpasste Daten - Raw Content nochmal durchsuchen
        
        Sucht systematisch nach Daten die in ersten Extraction-Runden verpasst wurden.
        Konzentriert sich auf kritische Felder wie Restaurationskosten.
        
        Args:
            content: Raw Content
            data: Bereits extrahierte Daten
            mine_name: Name der Mine
            
        Returns:
            Ergänzte Daten mit verpassten Informationen
        """
        logger.debug("[POST-PROCESS] Starte systematische Nachsuche nach verpassten Daten")
        
        # Kritische Felder priorisiert nachbearbeiten
        critical_fields = [
            'Restaurationskosten',
            'Eigentümer', 
            'Betreiber',
            'x-Koordinate',
            'y-Koordinate',
            'Aktivitätsstatus',
            'Rohstoff'
        ]
        
        recovered_data = {}
        
        for field in critical_fields:
            if not data.get(field) or data[field] in ['', 'X']:
                logger.debug(f"[POST-PROCESS] Feld '{field}' ist leer - starte Nachsuche")
                
                # Spezialisierte Nachsuche je Feld
                if field == 'Restaurationskosten':
                    recovery_value = self._recover_restoration_costs(content, mine_name)
                    if recovery_value:
                        recovered_data[field] = recovery_value
                        
                elif field in ['Eigentümer', 'Betreiber']:
                    recovery_value = self._recover_ownership_data(content, field)
                    if recovery_value:
                        recovered_data[field] = recovery_value
                        
                elif field in ['x-Koordinate', 'y-Koordinate']:
                    recovery_value = self._recover_coordinates(content, field)
                    if recovery_value:
                        recovered_data[field] = recovery_value
                        
                elif field == 'Aktivitätsstatus':
                    recovery_value = self._recover_activity_status(content)
                    if recovery_value:
                        recovered_data[field] = recovery_value
                        
                elif field == 'Rohstoff':
                    recovery_value = self._recover_commodity_data(content)
                    if recovery_value:
                        recovered_data[field] = recovery_value
        
        # Brute-Force-Ansatz für verpasste numerische Daten
        if not data.get('Fördermenge/Jahr'):
            production_data = self._recover_production_data(content)
            if production_data:
                recovered_data['Fördermenge/Jahr'] = production_data
        
        if not data.get('Fläche der Mine in qkm'):
            area_data = self._recover_area_data(content)
            if area_data:
                recovered_data['Fläche der Mine in qkm'] = area_data
        
        # Übertrage alle erfolgreichen Wiederherstellungen
        for field, value in recovered_data.items():
            if value and self._is_valid_data_value(value, field):
                data[field] = value
                logger.info(f"[POST-PROCESS] Verpasste Daten wiederhergestellt - {field}: '{value}'")
        
        return data
    
    def _recover_restoration_costs(self, content: str, mine_name: str) -> Optional[str]:
        """Aggressive Wiederherstellung von Restaurationskosten"""
        logger.debug("[RECOVERY] Suche aggressiv nach Restaurationskosten...")
        
        # Sehr breite Pattern für Zahlen + Währung + Kontext
        broad_patterns = [
            # Millionen-Beträge mit Mining-Kontext
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|Mio)\s*(?:CAD|USD|EUR)?.*?(?:mine|mining|closure|restoration|environmental|rehabilitation|reclamation)',
            r'(?:mine|mining|closure|restoration|environmental|rehabilitation|reclamation).*?\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|Mio)',
            # ARO/Asset Retirement in beliebigem Kontext
            r'(?:ARO|Asset.*?Retirement|environmental.*?liability).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million).*?(?:ARO|Asset.*?Retirement|environmental.*?liability)',
            # Zahlen mit Mine-Name-Verbindung
            fr'{re.escape(mine_name)}.*?\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million)',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million).*?' + re.escape(mine_name),
            # Sehr allgemeine Pattern für große Beträge in Mining-Kontexten
            r'(?:costs?|coûts?|costos?).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|Mio)',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|Mio).*?(?:costs?|coûts?|costos?)',
            # Französische Patterns (Quebec)
            r'(?:fermeture|restauration|réhabilitation).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:M|millions?|Mio)',
            # Patterns für kleinere Beträge (Tausende)
            r'\$\s*([\d,]+)\s*(?:k|K|thousand).*?(?:closure|restoration|rehabilitation|environmental)',
            r'(?:closure|restoration|rehabilitation|environmental).*?\$\s*([\d,]+)\s*(?:k|K|thousand)'
        ]
        
        for pattern in broad_patterns:
            try:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    cost_value = match.group(1)
                    # Validiere, dass es eine sinnvolle Zahl ist
                    if cost_value and cost_value.replace(',', '').replace('.', '').isdigit():
                        # Konvertiere zu Standard-Format
                        cost_float = float(cost_value.replace(',', ''))
                        if cost_float > 0.1 and cost_float < 10000:  # Zwischen 100k und 10 Milliarden
                            unit = "M" if "k" not in pattern.lower() else "k" 
                            result = f"${cost_value}{unit}"
                            logger.info(f"[RECOVERY] Restaurationskosten aggressive gefunden: {result}")
                            return result
            except Exception as e:
                logger.debug(f"[RECOVERY] Pattern-Fehler bei Restaurationskosten: {e}")
                continue
        
        return None
    
    def _recover_ownership_data(self, content: str, field: str) -> Optional[str]:
        """Wiederherstellung von Eigentümer/Betreiber-Daten"""
        # Breite Unternehmens-Pattern ohne Feldlabels
        company_patterns = [
            r'([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Corporation|Ltd|Limited|SA|Ltée|LLC|GmbH|AG)\.?)(?:\s+(?:owns|operates|manages|controls))?',
            r'(?:owned|operated|managed|controlled)\s+by\s+([A-Z][A-Za-z\s&,.-]+)',
            r'([A-Z][A-Za-z\s&,.-]+)\s+(?:is the|owns|operates|manages|controls)',
            # Französische Pattern
            r'([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltée|SA)\.?)\s+(?:détient|exploite|gère)',
            r'(?:détenu|exploité|géré)\s+par\s+([A-Z][A-Za-z\s&,.-]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                company = match.group(1).strip().rstrip('.,')
                # Filter out generic terms
                if (len(company) > 5 and 
                    not any(word in company.lower() for word in ['mining', 'mine', 'project', 'property', 'site', 'area']) and
                    any(suffix in company for suffix in ['Inc', 'Corp', 'Ltd', 'SA', 'Ltée', 'LLC', 'GmbH', 'AG'])):
                    logger.info(f"[RECOVERY] {field} aggressiv gefunden: {company}")
                    return company
        
        return None
    
    def _recover_coordinates(self, content: str, coord_type: str) -> Optional[str]:
        """Aggressive Koordinaten-Wiederherstellung"""
        # Sehr breite Pattern für Zahlen die wie Koordinaten aussehen
        if coord_type == 'x-Koordinate':
            coord_patterns = [
                r'(4[0-9]\.[\d]+)',    # 40-49.xxx (Nordamerika)
                r'(5[0-9]\.[\d]+)',    # 50-59.xxx (Kanada)
                r'([+-]?[4-6]\d\.[\d]{4,})',  # Präzise Latitude-Range
            ]
        else:  # y-Koordinate
            coord_patterns = [
                r'(-[6-9]\d\.[\d]+)',  # -60 bis -99 (Nordamerika West)
                r'(-1[0-2]\d\.[\d]+)', # -100 bis -129 (Westkanada)
                r'([+-]?[6-9]\d\.[\d]{4,})',  # Präzise Longitude-Range
            ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, content)
            if match:
                coord_value = match.group(1)
                # Validiere mit bestehender Funktion
                validated = validate_coordinate(coord_value, 'x' if coord_type == 'x-Koordinate' else 'y')
                if validated:
                    logger.info(f"[RECOVERY] {coord_type} aggressiv gefunden: {validated}")
                    return validated
        
        return None
    
    def _recover_activity_status(self, content: str) -> Optional[str]:
        """Wiederherstellung des Aktivitätsstatus"""
        status_patterns = [
            r'((?:currently\s+)?(?:active|operational|operating|in\s+operation))',
            r'((?:temporarily\s+)?(?:closed|shut\s+down|suspended))',
            r'((?:under\s+)?(?:development|construction))',
            r'((?:in\s+)?(?:exploration|planning\s+stage))',
            # Deutsch
            r'((?:derzeit\s+)?(?:aktiv|in\s+Betrieb|operativ))',
            r'((?:temporär\s+)?(?:geschlossen|stillgelegt|eingestellt))',
            r'((?:in\s+)?(?:Entwicklung|Bau|Planung))',
            r'((?:in\s+)?(?:Exploration|Erkundung))'
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                status = match.group(1).strip()
                logger.info(f"[RECOVERY] Aktivitätsstatus aggressiv gefunden: {status}")
                return status
        
        return None
    
    def _recover_commodity_data(self, content: str) -> Optional[str]:
        """Wiederherstellung von Rohstoff-Daten"""
        commodity_patterns = [
            r'((?:gold|copper|silver|zinc|lead|iron|nickel|coal)(?:\s+(?:and|und|,)\s+(?:gold|copper|silver|zinc|lead|iron|nickel|coal))*)',
            r'((?:Gold|Kupfer|Silber|Zink|Blei|Eisen|Nickel|Kohle)(?:\s+(?:und|,)\s+(?:Gold|Kupfer|Silber|Zink|Blei|Eisen|Nickel|Kohle))*)',
            r'(?:primary|main|haupt)\s+(?:commodity|mineral|rohstoff):\s*([^.\n]+)',
            r'(?:produces|produziert|fördert):\s*([^.\n]+(?:gold|copper|silver|zinc|lead|iron|nickel|coal)[^.\n]*)'
        ]
        
        for pattern in commodity_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                commodity = match.group(1).strip()
                if len(commodity) > 3 and len(commodity) < 100:
                    logger.info(f"[RECOVERY] Rohstoffabbau aggressiv gefunden: {commodity}")
                    return commodity
        
        return None
    
    def _recover_production_data(self, content: str) -> Optional[str]:
        """Wiederherstellung von Produktionsdaten"""
        production_patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:oz|ounces|tonnes?|tons?|pounds?)\s*(?:of\s+)?(?:gold|copper|silver|zinc|lead)',
            r'(?:annual\s+)?(?:production|output):\s*([\d,]+(?:\.\d+)?)\s*(?:oz|ounces|tonnes?|tons?|pounds?)',
            r'(?:produces|produziert)\s*(?:jährlich\s+)?([\d,]+(?:\.\d+)?)\s*(?:oz|ounces|tonnes?|tons?|pounds?)'
        ]
        
        for pattern in production_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                production = match.group(0)  # Full match for context
                logger.info(f"[RECOVERY] Fördermenge aggressiv gefunden: {production}")
                return production
        
        return None
    
    def _recover_area_data(self, content: str) -> Optional[str]:
        """Wiederherstellung von Flächen-Daten"""
        area_patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2|square\s+kilometers)',
            r'(?:area|fläche):\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2|square\s+kilometers)',
            r'(?:covers|umfasst)\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2|square\s+kilometers)'
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                area = f"{match.group(1)} km²"
                logger.info(f"[RECOVERY] Fläche aggressiv gefunden: {area}")
                return area
        
        return None
    
    def _validate_fields(self, data: Dict[str, str], currency: str) -> Dict[str, str]:
        """Validiere spezifische Felder"""
        # Restaurationskosten
        if data.get('Restaurationskosten'):
            validated = validate_restoration_cost(data['Restaurationskosten'], currency)
            if validated:
                data['Restaurationskosten'] = validated
            else:
                data['Restaurationskosten'] = ""
        
        # Jahre
        if data.get('Jahr der Aufnahme der Kosten'):
            validated = validate_year(data['Jahr der Aufnahme der Kosten'], 'costs')
            data['Jahr der Aufnahme der Kosten'] = validated or ""
        
        if data.get('Jahr der Erstellung des Dokumentes'):
            validated = validate_year(data['Jahr der Erstellung des Dokumentes'], 'document')
            data['Jahr der Erstellung des Dokumentes'] = validated or ""
        
        if data.get('Produktionsstart'):
            validated = validate_year(data['Produktionsstart'], 'production')
            data['Produktionsstart'] = validated or ""
        
        if data.get('Produktionsende'):
            validated = validate_year(data['Produktionsende'], 'production')
            data['Produktionsende'] = validated or ""
        
        # KOORDINATEN-FIX 03.09.2025: Strikte Koordinaten-Validierung mit korrektem Länder-Kontext
        # Setze Länder-Kontext für Koordinaten-Korrektur in _validate_fields
        country_context = data.get('Country', data.get('Land', ''))
        if country_context:
            validate_coordinate._country_context = country_context
            logger.debug(f"[VALIDATE-FIELDS] Länder-Kontext für Koordinaten-Korrektur gesetzt: {country_context}")
        
        # Validiere x-Koordinate (Latitude)
        if data.get('x-Koordinate'):
            validated = validate_coordinate(data['x-Koordinate'], 'x')
            if validated:
                data['x-Koordinate'] = validated
            else:
                logger.warning(f"Ungültige x-Koordinate entfernt: {data['x-Koordinate']}")
                data['x-Koordinate'] = ""
        
        # Validiere y-Koordinate (Longitude)
        if data.get('y-Koordinate'):
            validated = validate_coordinate(data['y-Koordinate'], 'y')
            if validated:
                data['y-Koordinate'] = validated
            else:
                logger.warning(f"Ungültige y-Koordinate entfernt: {data['y-Koordinate']}")
                data['y-Koordinate'] = ""
        
        # Bereinige Länder-Kontext nach Koordinaten-Validierung
        if hasattr(validate_coordinate, '_country_context'):
            delattr(validate_coordinate, '_country_context')
            logger.debug("[VALIDATE-FIELDS] Länder-Kontext bereinigt nach Koordinaten-Validierung")
        
        # Fläche
        if data.get('Fläche der Mine in qkm'):
            validated = validate_area(data['Fläche der Mine in qkm'])
            data['Fläche der Mine in qkm'] = validated or ""
        
        # ÄNDERUNG 07.07.2025: Erweiterte Betreiber-Validierung
        if data.get('Betreiber'):
            betreiber = str(data['Betreiber']).strip()
            
            # Liste ungültiger Betreiber-Werte
            invalid_operators = [
                'koordinaten', 'coordinates', 'coords', 'koordinate',
                'dhilmar', 'unknown', 'unbekannt', 'nicht verfügbar', 
                'n/a', 'n.a.', '-', 'keine daten', 'keine angabe',
                'tbd', 'placeholder', 'dummy', 'test'
            ]
            
            # Prüfe auf ungültige Werte
            if betreiber.lower() in invalid_operators:
                logger.warning(f"Ungültiger Betreiber entfernt: {betreiber}")
                data['Betreiber'] = ""
            # Prüfe auf Koordinaten-Muster (z.B. "Koordinaten: 45.123, -78.456")
            elif re.search(r'koordinaten\s*:?\s*[\d\.,\-\s]+', betreiber, re.IGNORECASE):
                logger.warning(f"Betreiber enthält Koordinaten-Muster: {betreiber}")
                data['Betreiber'] = ""
            # Prüfe auf reine Zahlen (könnten Koordinaten sein)
            elif re.match(r'^[\d\.,\-\s]+$', betreiber):
                logger.warning(f"Betreiber besteht nur aus Zahlen: {betreiber}")
                data['Betreiber'] = ""
        
        # ÄNDERUNG 07.07.2025: Erweiterte Validierung verdächtiger Restaurationskosten
        if data.get('Restaurationskosten'):
            resto = str(data['Restaurationskosten']).strip()
            
            # Liste aller verdächtigen Dummy-Werte
            dummy_values = [
                'USD$1.0 million', 'CAD$1.0 million', '$1.0 million', '1.0 million',
                'USD$1 million', 'CAD$1 million', '$1 million', '1 million',
                'USD$2.0 million', 'CAD$2.0 million', '$2.0 million', '2.0 million',
                'USD$10000.0 million', 'CAD$10000.0 million', '$10000.0 million',
                'USD$0.0 million', 'CAD$0.0 million', '$0.0 million', '0.0 million',
                'USD$1.0', 'CAD$1.0', '$1.0', '1.0',
                'USD$1', 'CAD$1', '$1', '1',
                'TBD', 'N/A', 'n/a', 'Unknown', 'unbekannt', '-', 'keine Angabe'
            ]
            
            # Prüfe auf exakte Übereinstimmung
            if str(resto).lower() in [dv.lower() for dv in dummy_values]:
                logger.warning(f"Dummy-Restaurationskostenwert entfernt: {resto}")
                data['Restaurationskosten'] = ""
            # Prüfe auf Muster wie "$X.0 million" wo X eine einzelne Ziffer ist
            elif re.match(r'^[\$€£]?\s*\d{1,2}\.0+\s*(million|mio|m)?\s*(USD|CAD|EUR|AUD)?$', resto, re.IGNORECASE):
                logger.warning(f"Verdächtiges Restaurationskosten-Muster entfernt: {resto}")
                data['Restaurationskosten'] = ""
            # Prüfe auf unrealistische Werte
            elif 'CAD$10000' in resto or 'USD$10000' in resto:
                logger.warning(f"Unrealistischer Restaurationskostenwert entfernt: {resto}")
                data['Restaurationskosten'] = ""
            # BUGFIX 23.08.2025: Verbesserte Validierung - echte Kosten nicht mehr entfernen  
            # Prüfe nur auf offensichtliche Dummy-Patterns ohne Jahresangabe
            elif (not any(year in resto for year in ['20', '19']) and 'million' in resto.lower() 
                  and re.match(r'^[\$€£]?\s*[1-9]\.0+\s*(million|mio|millionen)\s*(USD|CAD|EUR|AUD)?$', resto, re.IGNORECASE)):
                # Nur offensichtliche Dummy-Pattern wie "$1.0 million", "$2.0 million" ohne Jahresangabe
                logger.warning(f"Dummy-Restaurationskosten-Pattern ohne Zeitangabe entfernt: {resto}")
                data['Restaurationskosten'] = ""
            # ERLAUBT: Echte Werte wie "150.0 Millionen CAD" werden NICHT mehr gefiltert
        
        return data
    
    def extract_structured_data_with_sources(self, content: str, mine_name: str, 
                                           country: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrahiere strukturierte Daten mit Quellenzuordnung
        
        Args:
            content: Perplexity API Antwort
            mine_name: Name der Mine
            country: Land (optional)
            
        Returns:
            Dict mit extrahierten Daten und Quellenreferenzen
        """
        # QUELLENREFERENZEN-FIX 24.08.2025: Verwende SourceManager für konsistente Nummerierung
        # Basis-Extraktion (bereits mit SourceManager-Integration)
        data = self.extract_structured_data(content, mine_name, country)
        
        # SourceManager wurde bereits in extract_structured_data verwendet
        # Erstelle data_with_sources basierend auf den nummerierten Quellen
        data_with_sources = {}
        source_mapping = data.get('_source_mapping', {})
        field_sources = source_mapping.get('field_sources', {})
        
        for field, value in data.items():
            if field == '_source_mapping':  # Interne Datenstruktur überspringen
                continue
                
            if not value or field in FIELDS_WITHOUT_SOURCES:
                data_with_sources[field] = {'value': value, 'sources': []}
                continue
            
            # Verwende die vom SourceManager zugeordneten Quellen
            source_ids = field_sources.get(field, [])
            
            data_with_sources[field] = {
                'value': value,
                'sources': source_ids
            }
        
        # Extrahiere Quellen-Index aus SourceManager
        sources_dict = source_mapping.get('sources', {})
        source_index = []
        for source_id, source_data in sources_dict.items():
            source_index.append({
                'id': int(source_id),
                'url': source_data['url'],
                'title': source_data['title'],
                'type': source_data['type'],
                'reliability': source_data['reliability']
            })
        
        # RULE 10 COMPLIANCE 26.08.2025: NULL-Normalisierung der extrahierten Daten
        from minesearch.null_normalizer import NullNormalizer
        null_normalizer = NullNormalizer()
        
        # Normalisiere Daten (konvertiert "-", "unknown", etc. zu NULL)
        normalized_data = null_normalizer.normalize_structured_data(data)
        
        # Normalisiere auch data_with_sources
        normalized_data_with_sources = {}
        for field, field_data in data_with_sources.items():
            normalized_value = null_normalizer.normalize_value(field_data['value'], field)
            normalized_data_with_sources[field] = {
                'value': normalized_value,
                'sources': field_data['sources']
            }
        
        logger.info(f"[NULL-NORMALIZER] Datenextraktion für '{mine_name}' - NULL-Normalisierung angewendet")
        
        return {
            'data': normalized_data,
            'data_with_sources': normalized_data_with_sources,
            'source_index': source_index,
            'source_mapping': source_mapping  # QUELLENREFERENZEN-FIX: Für DB-Speicherung
        }
    
    def save_to_normalized_database(self, mine_name: str, model_used: str, 
                                  structured_data: Dict[str, Any], sources: List[Dict[str, Any]],
                                  session_id: Optional[str] = None, country: Optional[str] = None,
                                  search_duration: Optional[float] = None) -> int:
        """
        NEUE FUNKTION 03.09.2025: Speichere extrahierte Daten direkt in normalisierte Datenbank
        
        Args:
            mine_name: Name der Mine
            model_used: Verwendetes AI-Modell
            structured_data: Extrahierte strukturierte Daten
            sources: Liste der Quellen
            session_id: Session-ID (optional)
            country: Land (optional)
            search_duration: Suchdauer in Sekunden (optional)
            
        Returns:
            search_result_id aus der normalisierten Datenbank
        """
        try:
            logger.info(f"[NORMALIZED-SAVE] Speichere Daten für Mine '{mine_name}' mit Modell '{model_used}'")
            
            # Verwende den NormalizedDatabaseManager
            search_result_id = self.normalized_db.save_search_result_normalized(
                mine_name=mine_name,
                model_used=model_used,
                structured_data=structured_data,
                sources=sources,
                session_id=session_id,
                country=country,
                search_duration=search_duration
            )
            
            logger.info(f"✅ [NORMALIZED-SAVE] Erfolgreich gespeichert - Search Result ID: {search_result_id}")
            return search_result_id
            
        except Exception as e:
            logger.error(f"❌ [NORMALIZED-SAVE] Fehler beim Speichern: {e}")
            raise


# Hilfsfunktionen für Quellenzuordnung
def assign_sources_to_data(data: Dict[str, str], content: str, 
                          all_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ordne Quellen zu extrahierten Datenwerten zu
    
    Args:
        data: Extrahierte Daten
        content: Original-Content mit Quellenreferenzen
        all_sources: Liste aller extrahierten Quellen
        
    Returns:
        Dict mit Daten und zugeordneten Quellenreferenzen
    """
    data_with_sources = {}
    
    for field, value in data.items():
        if not value or field in FIELDS_WITHOUT_SOURCES:
            data_with_sources[field] = {'value': value, 'sources': []}
            continue
        
        # BUGFIX 20.07.2025: Skip dictionary values (z.B. _source_mapping)
        if isinstance(value, dict):
            data_with_sources[field] = {'value': value, 'sources': []}
            continue
        
        # Finde Quellenreferenzen für diesen Wert
        source_numbers = _find_source_references(value, content, all_sources)
        
        data_with_sources[field] = {
            'value': value,
            'sources': source_numbers
        }
    
    return data_with_sources


def _find_source_references(value: str, content: str, 
                           all_sources: List[Dict[str, Any]]) -> List[int]:
    """Finde Quellenreferenzen für einen bestimmten Wert"""
    source_numbers = []
    
    # Suche nach direkten Quellenreferenzen [1], [2,3] etc.
    patterns = _get_source_patterns_for_value(value)
    
    for pattern in patterns:
        try:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                for num in match.split(','):
                    try:
                        source_num = int(num.strip())
                        if source_num not in source_numbers and source_num <= len(all_sources):
                            source_numbers.append(source_num)
                    except ValueError:
                        continue
        except re.error:
            continue
    
    # Kontext-basierte Zuordnung wenn keine expliziten Quellen
    if not source_numbers:
        contexts = _find_value_in_context(value, content)
        sorted_sources = [s for s in all_sources if s['type'] == 'url'] + \
                        [s for s in all_sources if s['type'] == 'document'] + \
                        [s for s in all_sources if s['type'] == 'organization']
        
        for ctx in contexts[:3]:
            ctx_sources = _find_sources_in_context(ctx['context'], sorted_sources)
            source_numbers.extend(ctx_sources)
        
        source_numbers = sorted(list(set(source_numbers)))
    
    return source_numbers


def _get_source_patterns_for_value(value: str) -> List[str]:
    """Erstelle Regex-Patterns für Quellensuche"""
    patterns = []
    escaped_value = re.escape(value)
    
    if re.match(r'[\d,.$]+', value):
        # Für Zahlen
        base_number = re.sub(r'[,$]', '', value)
        patterns.extend([
            rf'{re.escape(base_number)}[^\n]*?\[(\d+(?:,\s*\d+)*)\]',
            rf'\[(\d+(?:,\s*\d+)*)\][^\n]*?{re.escape(base_number)}'
        ])
    else:
        # Für Text
        search_value = escaped_value[:50] if len(escaped_value) > 50 else escaped_value
        patterns.extend([
            rf'{search_value}[^\n]*?\[(\d+(?:,\s*\d+)*)\]',
            rf'\[(\d+(?:,\s*\d+)*)\][^\n]*?{search_value}'
        ])
        
        if ' ' in value:
            try:
                first_word = value.split()[0]
                escaped_first_word = re.escape(first_word)
                patterns.append(rf'{escaped_first_word}[^\n]*?\[(\d+(?:,\s*\d+)*)\]')
            except (IndexError, ValueError) as e:
                logger.debug(f"[DATA_EXTRACTION] Fehler beim Splitten von '{value}': {e}")
            except Exception as e:
                logger.warning(f"[DATA_EXTRACTION] Unerwarteter Fehler bei Pattern-Generierung: {e}")
    
    return patterns


def _find_value_in_context(value: str, content: str, context_size: int = 200) -> List[Dict[str, Any]]:
    """Finde alle Vorkommen eines Wertes im Content mit Kontext"""
    contexts = []
    value_lower = value.lower()
    content_lower = content.lower()
    
    start = 0
    while True:
        pos = content_lower.find(value_lower, start)
        if pos == -1:
            break
        
        context_start = max(0, pos - context_size)
        context_end = min(len(content), pos + len(value) + context_size)
        context = content[context_start:context_end]
        
        contexts.append({
            'position': pos,
            'context': context,
            'before': content[context_start:pos],
            'after': content[pos + len(value):context_end]
        })
        
        start = pos + 1
    
    return contexts


def _find_sources_in_context(context: str, all_sources: List[Dict[str, Any]]) -> List[int]:
    """Finde Quellen-Referenzen in einem Kontext-String"""
    found_sources = []
    context_lower = context.lower()
    
    # Suche nach Quellen-Keywords
    source_keywords = [
        'according to', 'per ', 'from ', 'source:', 'quelle:', 'laut ', 'gemäß ',
        'based on', 'as reported', 'states that', 'indicates', 'shows'
    ]
    
    # Prüfe jede Quelle
    for idx, source in enumerate(all_sources, 1):
        source_value = str(source.get('value', '')).lower()
        
        # Direkte Erwähnung
        if source_value in context_lower:
            found_sources.append(idx)
            continue
        
        # Teilweise Übereinstimmung
        if len(source_value) > 20:
            key_parts = source_value.split()[:3]
            if all(part in context_lower for part in key_parts):
                found_sources.append(idx)
    
    return sorted(list(set(found_sources)))