"""
Author: rahn
Datum: 30.06.2025
Version: 1.0
Beschreibung: Datenextraktion aus Perplexity-Antworten für MineSearch
"""

import re
import logging
from typing import Dict, List, Any, Optional
from config import config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from utils import clean_extracted_value, get_country_config
from source_discovery import extract_sources_from_content

# ÄNDERUNG 30.06.2025: Strukturiertes Logging (Regel 16)
logger = logging.getLogger(__name__)

# ÄNDERUNG 01.07.2025: CSV_COLUMNS und FIELDS_WITHOUT_SOURCES aus config.py importiert

class DataExtractor:
    """Klasse für strukturierte Datenextraktion aus Mining-Suchergebnissen"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialisiere Regex-Patterns für alle Felder"""
        return {
            'ID': [
                r'ID:\s*([^\n]+)',
                r'Kennziffer:\s*([^\n]+)',
                r'Nummer:\s*([^\n]+)',
                r'Reference:\s*([^\n]+)'
            ],
            'Country': [
                r'Land:\s*([^\n]+)', 
                r'Country:\s*([^\n]+)', 
                r'in\s+(\w+(?:\s+\w+)?)\s*(?:gelegen|liegt)'
            ],
            'Region': [
                r'Region:\s*([^\n]+)', 
                r'Provinz:\s*([^\n]+)', 
                r'Province:\s*([^\n]+)', 
                r'in\s+(?:der\s+)?(?:Region|Provinz)\s+([^\n,]+)',
                r'in\s+(Quebec|Québec|Ontario|British Columbia|Alberta|Manitoba|Saskatchewan)[\s,]',
                r'(?:located\s+in|liegt\s+in)\s+(Quebec|Québec|Ontario|British Columbia|Alberta)[\s,]'
            ],
            'Eigentümer': [
                r'Eigentümer:\s*([^\n]+)',
                r'Owner:\s*([^\n]+)',
                r'Propriétaire:\s*([^\n]+)',
                r'Propietario:\s*([^\n]+)',
                r'Pemilik:\s*([^\n]+)',
                r'gehört\s+(?:zu|der|dem)\s+([^\n]+)',
                r'owned\s+by\s+([^\n]+)',
                r'property\s+of\s+([^\n]+)',
                r'belongs\s+to\s+([^\n]+)',
                r'possession\s+of\s+([^\n]+)',
                r'Eigentum\s+(?:von|der)\s+([^\n]+)'
            ],
            'Betreiber': [
                r'Betreiber:\s*([^\n]+)', 
                r'Operator:\s*([^\n]+)', 
                r'betrieben\s+von\s+([^\n,]+)', 
                r'operated\s+by\s+([^\n,]+)',
                r'opérateur:\s*([^\n]+)',
                r'operador:\s*([^\n]+)',
                r'dioperasikan\s+oleh\s+([^\n]+)'
            ],
            'x-Koordinate': [
                r'Latitude:\s*([-\d.]+)', 
                r'Lat:\s*([-\d.]+)', 
                r'Breitengrad:\s*([-\d.]+)'
            ],
            'y-Koordinate': [
                r'Longitude:\s*([-\d.]+)', 
                r'Long?:\s*([-\d.]+)', 
                r'Längengrad:\s*([-\d.]+)'
            ],
            'Aktivitätsstatus': [
                r'Status:\s*([^\n]+)', 
                r'Aktivitätsstatus:\s*([^\n]+)', 
                r'(?:ist\s+)?(?:derzeit\s+)?(aktiv|geschlossen|stillgelegt|in Betrieb|geplant)',
                r'(Geplant[^,\n]*)',
                r'(Akquisition\s+abgeschlossen[^,\n]*)',
                r'(In\s+Entwicklung[^,\n]*)',
                r'(Explorationsphase[^,\n]*)',
                r'(Produktion\s+eingestellt[^,\n]*)',
                r'(Temporär\s+stillgelegt[^,\n]*)'
            ],
            'Restaurationskosten': self._get_restoration_cost_patterns(),
            'Jahr der Aufnahme der Kosten': [
                r'(?:Kosten|costs?)\s+(?:von|from|Stand)\s+(\d{4})', 
                r'(?:per|as\s+of)\s+(\d{4})',
                r'(?:Stand|status|as\s+of):\s*(?:\w+\s+)?(\d{4})',
                r'(\d{4})\s+(?:Kosten|costs|liabilities)'
            ],
            'Jahr der Erstellung des Dokumentes': [
                r'(?:Dokument|Report|Bericht)\s+(?:vom|von|dated|from)\s+(\b(?:19|20)\d{2}\b)',
                r'(?:Stand|Date|Datum):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
                r'(?:erstellt|created|prepared|published)\s+(?:im|in)?\s*(\b(?:19|20)\d{2}\b)',
                r'(\b(?:19|20)\d{2}\b)\s+(?:Report|Bericht|Document|Study)',
                r'(?:Veröffentlicht|Published|Released):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
                r'(?:Technical\s+Report|NI\s*43-101).*?(\b(?:19|20)\d{2}\b)',
                r'(?:Report|Document|Bericht).*?\((\b(?:19|20)\d{2}\b)\)'
            ],
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': [
                r'Rohstoffe?:\s*([^\n]+)', 
                r'(?:produziert|fördert|abbaut)\s+([^\n]+(?:Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)[^\n]*)',
                r'Commodity:\s*([^\n]+)',
                r'Commodities:\s*([^\n]+)',
                r'Mineral(?:s|ien)?:\s*([^\n]+)',
                r'(?:haupt|main)\s*(?:rohstoff|commodity):\s*([^\n]+)'
            ],
            'Minentyp (Untertage/ Open-Pit/ usw.)': [
                r'Minentyp:\s*([^\n]+)', 
                r'Type:\s*([^\n]+)',
                r'((?:Open[- ]?Pit|Untertage|Underground|Tagebau)[^\n,]*)'
            ],
            'Produktionsstart': [
                r'Produktionsstart:\s*(\d{4})', 
                r'Start:\s*(\d{4})', 
                r'(?:in\s+Betrieb\s+seit|eröffnet)\s+(\d{4})'
            ],
            'Produktionsende': [
                r'Produktionsende:\s*(\d{4})', 
                r'Ende:\s*(\d{4})', 
                r'geschlossen\s+(?:seit\s+)?(\d{4})'
            ],
            'Fördermenge/Jahr': [
                r'Fördermenge:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
                r'Produktion:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
                r'produziert\s+(?:jährlich\s+)?([\d,]+(?:\.\d+)?)\s*([^\n]+)'
            ],
            'Fläche der Mine in qkm': [
                r'Fläche:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)', 
                r'Area:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)'
            ]
        }
    
    def _get_restoration_cost_patterns(self) -> List[str]:
        """Spezielle Patterns für Restaurationskosten"""
        return [
            # Existierende Patterns für bereits bezahlte Kosten
            r'Restaurationskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'Sanierungskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'(?:Environmental\s+)?liabilities?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            r'Closure\s+costs?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            # Neue Patterns für geplante/zukünftige Kosten
            r'(?:geplante|geschätzte|estimated|planned|future)\s+(?:Restaurations|Sanierungs|restoration|remediation|closure)kosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
            r'(?:Restaurations|Sanierungs)kosten\s+(?:werden|sind)\s+(?:auf|geschätzt)\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'Rückstellungen?\s+(?:für\s+)?(?:Rekultivierung|Sanierung|Stilllegung):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'(?:Asset\s+)?(?:Retirement|Decommissioning)\s+Obligations?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            r'(?:provision|reserve)\s+for\s+(?:site\s+)?(?:restoration|remediation|closure):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?\s*(?:CAD|CDN)?',
            # Patterns für "budgetiert" oder "veranschlagt"
            r'(?:budgetiert|veranschlagt|budgeted|allocated)\s+für\s+(?:Restauration|Sanierung|restoration):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
            # Zusätzliche flexible Patterns
            r'(?:Umwelt|Environmental).*?(?:Kosten|costs|liabilities).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:für|for)\s+(?:Restauration|Sanierung|restoration|closure)',
            r'(?:Schätzung|estimate).*?(?:Restauration|Sanierung|closure).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?'
        ]
    
    def extract_structured_data(self, content: str, mine_name: str, country: Optional[str] = None) -> Dict[str, str]:
        """
        Extrahiere strukturierte Daten aus dem Perplexity-Response
        
        Args:
            content: Perplexity API Antwort
            mine_name: Name der Mine
            country: Land (optional)
            
        Returns:
            Dict mit extrahierten Daten
        """
        # ÄNDERUNG 30.06.2025: Try-catch für Datenextraktion (Regel 13)
        try:
            data = {col: '' for col in CSV_COLUMNS}
            data['Name'] = mine_name
            
            # Hole länderspezifische Währung
            country_config = get_country_config(country) if country else {}
            currency = country_config.get('currency', 'USD')
            
            # Extrahiere Daten mit Patterns
            for field, field_patterns in self.patterns.items():
                value = self._extract_field(field, field_patterns, content, currency)
                if value:
                    data[field] = value
            
            # Spezielle Nachbearbeitung
            data = self._post_process_data(data, content, country_config)
            
            # Quellenverarbeitung
            data = self._process_sources(data, content)
            
            logger.info(f"[EXTRACTION] {mine_name}: {sum(1 for v in data.values() if v)} Felder extrahiert")
            
            return data
            
        except Exception as e:
            logger.error(f"[EXTRACTION ERROR] Fehler bei Datenextraktion für {mine_name}: {str(e)}")
            # Gib minimale Daten zurück
            return {col: '' for col in CSV_COLUMNS} | {'Name': mine_name}
    
    def _extract_field(self, field: str, patterns: List[str], content: str, currency: str) -> Optional[str]:
        """Extrahiere ein einzelnes Feld mit den gegebenen Patterns"""
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1)
                
                # Debug-Logging für wichtige Felder
                if field in ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']:
                    logger.debug(f"[PATTERN] {field}: '{value}' (Pattern: {pattern[:50]}...)")
                
                # Spezielle Verarbeitung für Restaurationskosten
                if field == 'Restaurationskosten':
                    return self._process_restoration_costs(value, match.group(0), currency)
                else:
                    return clean_extracted_value(value)
        
        return None
    
    def _process_restoration_costs(self, value: str, full_match: str, currency: str) -> str:
        """Verarbeite Restaurationskosten mit Währungskonvertierung"""
        
        value = value.replace(',', '')
        try:
            amount = float(value)
            
            # Wenn "Million" erwähnt wurde, multipliziere
            if 'million' in full_match.lower() or 'mio' in full_match.lower():
                amount *= 1_000_000
            
            # Prüfe ob es geplante/zukünftige Kosten sind
            full_match_lower = full_match.lower()
            if any(word in full_match_lower for word in [
                'geplant', 'geschätzt', 'estimated', 'planned', 
                'future', 'budgetiert', 'veranschlagt', 
                'rückstellung', 'provision', 'reserve'
            ]):
                return f"${amount:,.0f} {currency} (geplant)"
            else:
                return f"${amount:,.0f} {currency}"
        except:
            return clean_extracted_value(value)
    
    def _post_process_data(self, data: Dict[str, str], content: str, country_config: Dict) -> Dict[str, str]:
        """Nachbearbeitung der extrahierten Daten"""
        
        # Intelligentes Status-Mapping
        if data['Aktivitätsstatus']:
            data['Aktivitätsstatus'] = self._process_activity_status(data['Aktivitätsstatus'])
        
        # Intelligente Land/Region Trennung
        if data['Country'] and '(' in data['Country']:
            data = self._split_country_region(data)
        
        # Regionen basierend auf Länderkonfiguration zuordnen
        if data['Country'] and not data['Region']:
            data['Region'] = self._find_region_from_content(data['Country'], content, country_config)
        
        return data
    
    def _process_activity_status(self, status_text: str) -> str:
        """Verarbeite Aktivitätsstatus mit Kategorisierung"""
        
        status_lower = status_text.lower()
        
        # Bestimme die Kategorie
        if any(word in status_lower for word in ['aktiv', 'in betrieb', 'produziert', 'operating', 'active']):
            category = 'aktiv'
        elif any(word in status_lower for word in ['geplant', 'akquisition', 'entwicklung', 'exploration', 'planned', 'proposed']):
            category = 'geplant'
        elif any(word in status_lower for word in ['geschlossen', 'stillgelegt', 'eingestellt', 'closed', 'ceased']):
            category = 'geschlossen'
        elif any(word in status_lower for word in ['temporär', 'suspended', 'care and maintenance']):
            category = 'sonstiges'
        else:
            category = 'sonstiges'
        
        # Behalte detaillierte Beschreibung bei längeren Texten
        if len(status_text) > 20 and category != status_text.lower():
            return f"{status_text} ({category})"
        else:
            return category
    
    def _split_country_region(self, data: Dict[str, str]) -> Dict[str, str]:
        """Trenne Land und Region aus kombiniertem Feld"""
        
        match = re.match(r'^([^(]+)\s*\(([^)]+)\)', data['Country'])
        if match:
            country = match.group(1).strip()
            region = match.group(2).strip()
            data['Country'] = country
            if not data['Region']:
                data['Region'] = region
        
        return data
    
    def _find_region_from_content(self, country: str, content: str, country_config: Dict) -> str:
        """Finde Region basierend auf Länderkonfiguration"""
        
        country_lower = country.lower()
        content_lower = content.lower()
        
        # Suche passende Länderkonfiguration
        if not country_config:
            for country_key in config.COUNTRY_CONFIGS:
                if country_key.lower() in country_lower or country_lower in country_key.lower():
                    country_config = config.COUNTRY_CONFIGS[country_key]
                    break
        
        # Wenn Länderkonfiguration gefunden, suche nach Regionen
        if country_config and 'regions' in country_config:
            for region in country_config['regions']:
                if region.lower() in content_lower:
                    return region
        
        return ''
    
    def _process_sources(self, data: Dict[str, str], content: str) -> Dict[str, str]:
        """Verarbeite und formatiere Quellen"""
        
        # Extrahiere alle Quellen
        sources = extract_sources_from_content(content)
        
        # Sammle alle Quellen-Werte
        all_source_values = []
        
        # URLs zuerst
        source_urls = [s['value'] for s in sources if s['type'] == 'url']
        all_source_values.extend(source_urls)
        
        # Dann Dokumente
        source_docs = [s['value'] for s in sources if s['type'] == 'document']
        all_source_values.extend(source_docs)
        
        # Dann Organisationen
        source_orgs = [s['value'] for s in sources if s['type'] == 'organization']
        all_source_values.extend(source_orgs)
        
        # Filtere ungültige Quellen
        valid_source_values = []
        for source_value in all_source_values:
            if (source_value and 
                not any(skip in source_value.lower() for skip in [
                    'k.a.', 'k.a', 'keine', 'nicht gefunden', 'nicht verfügbar', 
                    'perplexity search', '[quelle:', 'no specific'
                ])):
                valid_source_values.append(source_value)
        
        if valid_source_values:
            # Erstelle nummerierte Liste
            numbered_sources = []
            for i, source_value in enumerate(valid_source_values, 1):
                numbered_sources.append(f"[{i}] {source_value}")
            data['Quellenangaben'] = '+++'.join(numbered_sources)
        else:
            data['Quellenangaben'] = 'Keine spezifischen Quellen dokumentiert'
        
        return data


def extract_structured_data(content: str, mine_name: str, country: Optional[str] = None) -> Dict[str, str]:
    """Wrapper-Funktion für Kompatibilität"""
    extractor = DataExtractor()
    return extractor.extract_structured_data(content, mine_name, country)


def extract_structured_data_with_sources(content: str, mine_name: str, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrahiere strukturierte Daten mit Quellenverfolgung
    
    Returns:
        Dict mit:
        - 'data': {field: value} - Bereinigte Werte
        - 'data_with_sources': {field: {'value': value, 'sources': [1,2,3]}}
        - 'source_index': {1: 'URL oder Dokumentname', 2: '...'}
    """
    # ÄNDERUNG 30.06.2025: Try-catch für Quellenextraktion (Regel 13)
    try:
        # Hole normale strukturierte Daten
        data = extract_structured_data(content, mine_name, country)
        
        # Erstelle Quellen-Index
        all_sources = extract_sources_from_content(content)
        source_index = {}
        
        # Sortiere Quellen nach Typ
        source_urls = [s for s in all_sources if s['type'] == 'url']
        source_docs = [s for s in all_sources if s['type'] == 'document']
        source_orgs = [s for s in all_sources if s['type'] == 'organization']
        
        # Erstelle Index
        idx = 1
        for source in source_urls + source_docs + source_orgs:
            source_index[idx] = source['value']
            idx += 1
        
        # Initialisiere data_with_sources
        data_with_sources = {}
        
        # Für jedes Feld: Finde zugehörige Quellennummern
        for field, value in data.items():
            needs_sources = (
                value and 
                value != '-' and
                field not in FIELDS_WITHOUT_SOURCES and
                value.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden']
            )
            
            source_numbers = []
            if needs_sources:
                source_numbers = _find_source_numbers_for_value(
                    field, value, content, all_sources
                )
            
            data_with_sources[field] = {
                'value': value,
                'sources': source_numbers
            }
        
        return {
            'data': data,
            'data_with_sources': data_with_sources,
            'source_index': source_index
        }
        
    except Exception as e:
        logger.error(f"[SOURCE EXTRACTION ERROR] {str(e)}")
        # Fallback
        return {
            'data': extract_structured_data(content, mine_name, country),
            'data_with_sources': {},
            'source_index': {}
        }


def _find_source_numbers_for_value(field: str, value: str, content: str, 
                                   all_sources: List[Dict]) -> List[int]:
    """Finde Quellennummern für einen bestimmten Wert"""
    
    source_numbers = []
    
    # Prüfe ob Content nummerierte Quellen hat
    has_numbered_sources = bool(re.search(r'\[\d+\]', content))
    
    if has_numbered_sources:
        # Suche explizite Quellennummern
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
            except:
                pass
    
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
        source_value = source['value'].lower()
        
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