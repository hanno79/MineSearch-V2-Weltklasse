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
    is_template_or_dummy_value
)
from minesearch.source_manager import SourceManager

logger = logging.getLogger(__name__)


class DataExtractor:
    """Klasse für strukturierte Datenextraktion aus Mining-Suchergebnissen"""
    
    def __init__(self):
        self.patterns = get_extraction_patterns()
        self.coordinate_patterns = get_enhanced_coordinate_patterns()
        self.source_manager = SourceManager()
    
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
            # FALLBACK: X-Marker wenn Aktivitätsstatus unbekannt - REGEL 10 KONFORM
            return 'X'  # Fallback für "nicht gefunden"
            
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
                    
        # FALLBACK: X-Marker für unbehandelte Status-Kombinationen - REGEL 10 KONFORM  
        return 'X'  # Fallback wenn kein spezifischer Status-Marker passt
    
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
        CLEAN DATA AT SOURCE - Data Quality Gate
        
        Prüft ob ein extrahierter Wert ein echter Datenwert ist oder ein Template/Dummy-Wert.
        Template/Dummy-Werte werden abgelehnt und als NULL in die DB gespeichert.
        
        Args:
            value: Zu prüfender Wert
            field: Feldname für spezifische Validierung
            
        Returns:
            True wenn echter Datenwert, False wenn Template/Dummy
        """
        if not value or not str(value).strip():
            return False
            
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        logger.debug(f"[DATA QUALITY GATE] Validiere Wert '{value_str}' für Feld '{field}'")
        
        # 1. PRE-EXTRACTION TEMPLATE/DUMMY DETECTION - ABSOLUTE PRIORITY
        # Nutze die dedizierte Template-Detection aus extraction_processors.py
        if is_template_or_dummy_value(value_str, field):
            logger.warning(f"[DATA QUALITY GATE] Template/Dummy-Wert über extraction_processors erkannt: '{value_str}' → ABGELEHNT")
            return False
        
        # 2. ADDITIONAL QUALITY CHECKS (nur noch spezifische Prüfungen nach Template-Detection)
        
        # Coordinates appearing in wrong fields 
        if field in ['Betreiber', 'Eigentümer'] and re.match(r'^[\d\.\-\s,°\'\"]+$', value_str):
            logger.warning(f"[DATA QUALITY GATE] Koordinaten in Betreiber/Eigentümer-Feld: '{value_str}' → ABGELEHNT")
            return False
        
        # Very short values that are likely AI artifacts (but allow "-" as legitimate empty marker)
        if len(value_str) <= 2 and value_str not in ['-']:
            logger.warning(f"[DATA QUALITY GATE] Zu kurzer Wert: '{value_str}' → ABGELEHNT")
            return False
        
        # Value passed all checks
        logger.debug(f"[DATA QUALITY GATE] Wert '{value_str}' für Feld '{field}' → AKZEPTIERT")
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
            
            # Extrahiere Daten mit Patterns
            for field, field_patterns in self.patterns.items():
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
            
            # Post-Processing
            data = post_process_data(data, content, country_config)
            
            # Validierung spezifischer Felder
            data = self._validate_fields(data, currency)
            
            # QUELLENREFERENZEN-FIX 19.07.2025: Erstelle Quellenangaben mit neuer Logik
            data['Quellenangaben'] = self.source_manager.get_sources_summary()
            
            # Füge Quellen-Mapping für JSON-Speicherung hinzu
            data['_source_mapping'] = self.source_manager.get_sources_dict()
            
            # Bereinige alle Feldwerte NACH Quellen-Zuordnung
            for field in CSV_COLUMNS:
                if field in data and data[field] and field not in FIELDS_WITHOUT_SOURCES:
                    if isinstance(data[field], str):  # Nur String-Werte bereinigen
                        data[field] = clean_field_value(data[field], field)
            
            # QUELLENREFERENZEN-FIX 19.07.2025: Formatiere Felder mit Quellen-Referenzen NACH Bereinigung
            for field in CSV_COLUMNS:
                if field not in ['Name', 'Quellenangaben'] and data.get(field) and data[field] not in ['X', '']:
                    formatted_value = self.source_manager.format_field_with_sources(data[field], field)
                    if formatted_value != data[field]:
                        logger.debug(f"[SOURCE] Feld '{field}' mit Quellen formatiert: '{formatted_value}'")
                        data[field] = formatted_value
            
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
            critical_fields = ['Eigentümer', 'Betreiber', 'Aktivitätsstatus', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)']            
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
        """Extrahiere Koordinaten mit erweiterten Patterns"""
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
                    if 'DMS' in pattern or '°' in pattern:
                        # Handle DMS format
                        coord = validate_coordinate(match.group(0), 'y')
                    else:
                        coord = validate_coordinate(match.group(1), 'y')
                    
                    if coord:
                        data['y-Koordinate'] = coord
                        logger.info(f"[COORDINATES] Longitude gefunden: {coord}")
                        break
        
        return data
    
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
        
        # ÄNDERUNG 05.07.2025: Strikte Koordinaten-Validierung
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
            # Prüfe auf Werte ohne Quellennachweis (wenn kein Jahr oder keine Details)
            elif not any(year in resto for year in ['20', '19']) and 'million' in resto.lower():
                # Wenn keine Jahreszahl (20xx oder 19xx) vorhanden ist, ist es wahrscheinlich ein Dummy
                logger.warning(f"Restaurationskosten ohne Zeitangabe entfernt: {resto}")
                data['Restaurationskosten'] = ""
        
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
        # Basis-Extraktion
        data = self.extract_structured_data(content, mine_name, country)
        
        # Quellen extrahieren
        all_sources = extract_sources_from_content(content)
        
        # Quellen zu Daten zuordnen
        data_with_sources = assign_sources_to_data(data, content, all_sources)
        
        return {
            'data': data,
            'data_with_sources': data_with_sources,
            'source_index': all_sources
        }


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