"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Flexible Extraction Patterns für Mining-Daten - Anpassbar für alle Länder/Sprachen
"""

from typing import List, Dict, Pattern, Optional, Tuple, Any
import re
from dataclasses import dataclass
from enum import Enum

class FieldType(Enum):
    """Typen von Mining-Datenfeldern"""
    OPERATOR = "operator"
    COORDINATES = "coordinates"
    COMMODITY = "commodity"
    STATUS = "status"
    COSTS = "costs"
    PRODUCTION = "production"
    DATES = "dates"
    AREA = "area"
    EMPLOYEES = "employees"
    CONTACT = "contact"
    ENVIRONMENTAL = "environmental"
    PERMITS = "permits"

@dataclass
class ExtractionPattern:
    """Ein Muster zur Datenextraktion"""
    field_type: FieldType
    pattern: Pattern
    language: str
    confidence: float
    extraction_method: str
    post_processor: Optional[callable] = None

class ExtractionPatterns:
    """
    Verwaltung von Extraktionsmustern für Mining-Daten
    
    - Flexibel: Unterstützt alle Sprachen
    - Erweiterbar: Neue Muster können dynamisch hinzugefügt werden
    - Intelligent: Lernt aus erfolgreichen Extraktionen
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.custom_patterns = {}
        self.success_history = {}
        
    def _initialize_patterns(self) -> Dict[FieldType, List[ExtractionPattern]]:
        """Initialisiert Basis-Extraktionsmuster"""
        patterns = {field_type: [] for field_type in FieldType}
        
        # KOORDINATEN - Verschiedene Formate
        patterns[FieldType.COORDINATES].extend([
            # Dezimalgrad
            ExtractionPattern(
                field_type=FieldType.COORDINATES,
                pattern=re.compile(r'(?:lat(?:itude)?[:\s]*)?(-?\d{1,2}\.?\d*)[°\s,]+(?:lon(?:gitude)?[:\s]*)?(-?\d{1,3}\.?\d*)', re.IGNORECASE),
                language="universal",
                confidence=0.9,
                extraction_method="decimal_degrees",
                post_processor=self._normalize_decimal_coordinates
            ),
            # DMS (Degrees Minutes Seconds)
            ExtractionPattern(
                field_type=FieldType.COORDINATES,
                pattern=re.compile(r'(\d{1,2})[°\s](\d{1,2})[′\'\s](\d{1,2}(?:\.\d+)?)[″"\s]*([NS])[,\s]+(\d{1,3})[°\s](\d{1,2})[′\'\s](\d{1,2}(?:\.\d+)?)[″"\s]*([EW])', re.IGNORECASE),
                language="universal",
                confidence=0.95,
                extraction_method="dms",
                post_processor=self._convert_dms_to_decimal
            ),
            # UTM
            ExtractionPattern(
                field_type=FieldType.COORDINATES,
                pattern=re.compile(r'(?:UTM|utm)[:\s]*(?:Zone\s*)?(\d{1,2})\s*([NS])[,\s]+(\d{6,7})[,\s]+(\d{6,7})', re.IGNORECASE),
                language="universal",
                confidence=0.85,
                extraction_method="utm",
                post_processor=None  # UTM conversion würde implementiert
            )
        ])
        
        # BETREIBER/OPERATOR - Mehrsprachig
        patterns[FieldType.OPERATOR].extend([
            # Englisch
            ExtractionPattern(
                field_type=FieldType.OPERATOR,
                pattern=re.compile(r'(?:operator|owner|operated by|owned by)[:\s]+([A-Z][A-Za-z\s&\-\.]+(?:Ltd|Inc|Corp|Company|Mining|Mines)?)', re.IGNORECASE),
                language="en",
                confidence=0.9,
                extraction_method="labeled",
                post_processor=self._clean_company_name
            ),
            # Spanisch
            ExtractionPattern(
                field_type=FieldType.OPERATOR,
                pattern=re.compile(r'(?:operador|propietario|operado por)[:\s]+([A-Z][A-Za-z\s&\-\.]+(?:S\.A\.|S\.L\.|Minera|Minas)?)', re.IGNORECASE),
                language="es",
                confidence=0.9,
                extraction_method="labeled",
                post_processor=self._clean_company_name
            ),
            # Französisch
            ExtractionPattern(
                field_type=FieldType.OPERATOR,
                pattern=re.compile(r'(?:opérateur|propriétaire|exploité par)[:\s]+([A-Z][A-Za-z\s&\-\.]+(?:S\.A\.|SARL|Mines|Minière)?)', re.IGNORECASE),
                language="fr",
                confidence=0.9,
                extraction_method="labeled",
                post_processor=self._clean_company_name
            ),
            # Portugiesisch
            ExtractionPattern(
                field_type=FieldType.OPERATOR,
                pattern=re.compile(r'(?:operador|proprietário|operado por)[:\s]+([A-Z][A-Za-z\s&\-\.]+(?:S\.A\.|Ltda|Mineração|Minas)?)', re.IGNORECASE),
                language="pt",
                confidence=0.9,
                extraction_method="labeled",
                post_processor=self._clean_company_name
            )
        ])
        
        # ROHSTOFFTYP/COMMODITY
        patterns[FieldType.COMMODITY].extend([
            # Generisches Muster
            ExtractionPattern(
                field_type=FieldType.COMMODITY,
                pattern=re.compile(r'(?:commodity|commodities|mineral|minerals|resource)[:\s]+([A-Za-z,\s\-/]+)(?:\.|,|;|$)', re.IGNORECASE),
                language="en",
                confidence=0.85,
                extraction_method="labeled",
                post_processor=self._parse_commodity_list
            ),
            # Spezifische Mineralien
            ExtractionPattern(
                field_type=FieldType.COMMODITY,
                pattern=re.compile(r'\b(gold|silver|copper|iron|zinc|lead|nickel|cobalt|lithium|uranium|coal|diamond|platinum|palladium|molybdenum|tungsten|tin|bauxite|phosphate)\b', re.IGNORECASE),
                language="en",
                confidence=0.7,
                extraction_method="keyword",
                post_processor=self._standardize_commodity
            )
        ])
        
        # PRODUKTIONSDATEN
        patterns[FieldType.PRODUCTION].extend([
            # Jährliche Produktion
            ExtractionPattern(
                field_type=FieldType.PRODUCTION,
                pattern=re.compile(r'(?:annual production|yearly production|produces)[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(tonnes?|tons?|mt|kt|oz|ounces|pounds?|lbs?)', re.IGNORECASE),
                language="en",
                confidence=0.9,
                extraction_method="quantity",
                post_processor=self._normalize_production_units
            ),
            # Produktionskapazität
            ExtractionPattern(
                field_type=FieldType.PRODUCTION,
                pattern=re.compile(r'(?:capacity|throughput)[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(tonnes?|tons?|mt|kt)\s*(?:per|/)\s*(day|month|year|annum)', re.IGNORECASE),
                language="en",
                confidence=0.85,
                extraction_method="capacity",
                post_processor=self._normalize_capacity
            )
        ])
        
        # STATUS
        patterns[FieldType.STATUS].extend([
            # Englisch
            ExtractionPattern(
                field_type=FieldType.STATUS,
                pattern=re.compile(r'(?:status|mine status|operational status)[:\s]*(operational|operating|active|closed|suspended|care and maintenance|exploration|development|construction)', re.IGNORECASE),
                language="en",
                confidence=0.9,
                extraction_method="labeled",
                post_processor=self._standardize_status
            ),
            # Mehrsprachige Status-Keywords
            ExtractionPattern(
                field_type=FieldType.STATUS,
                pattern=re.compile(r'\b(activ[eo]|operacional|fermé|cerrado|suspendu|suspendido|en construcción|under construction|producing|non-producing)\b', re.IGNORECASE),
                language="multi",
                confidence=0.75,
                extraction_method="keyword",
                post_processor=self._translate_status
            )
        ])
        
        # SANIERUNGSKOSTEN
        patterns[FieldType.COSTS].extend([
            # Währungsbeträge
            ExtractionPattern(
                field_type=FieldType.COSTS,
                pattern=re.compile(r'(?:closure cost|remediation cost|restoration cost|rehabilitation cost|bond)[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|M|B)?\s*(USD|CAD|AUD|EUR)?', re.IGNORECASE),
                language="en",
                confidence=0.9,
                extraction_method="currency",
                post_processor=self._normalize_currency
            )
        ])
        
        return patterns
    
    def extract_field(self, text: str, field_type: FieldType, 
                     language: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Extrahiert Feldwerte aus Text
        
        Returns:
            Liste von (Wert, Konfidenz) Tupeln
        """
        results = []
        
        # Hole passende Muster
        patterns = self.patterns.get(field_type, [])
        
        # Filtere nach Sprache wenn angegeben
        if language:
            patterns = [p for p in patterns if p.language in [language, "universal", "multi"]]
        
        # Wende alle Muster an
        for pattern in patterns:
            matches = pattern.pattern.finditer(text)
            
            for match in matches:
                # Extrahiere Wert
                if pattern.extraction_method == "labeled":
                    value = match.group(1)
                elif pattern.extraction_method == "keyword":
                    value = match.group(0)
                elif pattern.extraction_method in ["quantity", "capacity", "currency"]:
                    value = match.group(0)
                elif pattern.extraction_method == "decimal_degrees":
                    value = f"{match.group(1)}, {match.group(2)}"
                elif pattern.extraction_method == "dms":
                    value = match.group(0)
                elif pattern.extraction_method == "utm":
                    value = match.group(0)
                else:
                    value = match.group(0)
                
                # Wende Post-Processor an wenn vorhanden
                if pattern.post_processor:
                    value = pattern.post_processor(value, match)
                
                # Berechne Kontext-basierte Konfidenz
                context_confidence = self._calculate_context_confidence(
                    text, match.start(), match.end(), field_type
                )
                
                final_confidence = pattern.confidence * context_confidence
                
                results.append((value, final_confidence))
        
        # Dedupliziere und sortiere nach Konfidenz
        unique_results = {}
        for value, conf in results:
            if value not in unique_results or conf > unique_results[value]:
                unique_results[value] = conf
        
        return sorted(unique_results.items(), key=lambda x: x[1], reverse=True)
    
    def _calculate_context_confidence(self, text: str, start: int, end: int, 
                                    field_type: FieldType) -> float:
        """Berechnet Konfidenz basierend auf Kontext"""
        # Extrahiere umgebenden Text
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)
        context = text[context_start:context_end].lower()
        
        # Positive Indikatoren
        positive_indicators = {
            FieldType.OPERATOR: ["operated", "owner", "company", "mining"],
            FieldType.COORDINATES: ["location", "situated", "located", "position"],
            FieldType.COMMODITY: ["produces", "mineral", "ore", "resource"],
            FieldType.STATUS: ["currently", "status", "operational", "mine is"],
            FieldType.PRODUCTION: ["annual", "yearly", "produces", "capacity"],
            FieldType.COSTS: ["bond", "financial", "liability", "closure"]
        }
        
        indicators = positive_indicators.get(field_type, [])
        indicator_count = sum(1 for ind in indicators if ind in context)
        
        # Basis-Konfidenz
        confidence = 0.7
        
        # Erhöhe für jeden gefundenen Indikator
        confidence += indicator_count * 0.1
        
        return min(confidence, 1.0)
    
    # Post-Processor Funktionen
    def _normalize_decimal_coordinates(self, value: str, match: re.Match) -> str:
        """Normalisiert Dezimalkoordinaten"""
        lat = float(match.group(1))
        lon = float(match.group(2))
        return f"{lat:.6f}, {lon:.6f}"
    
    def _convert_dms_to_decimal(self, value: str, match: re.Match) -> str:
        """Konvertiert DMS zu Dezimalgrad"""
        # Latitude
        lat_deg = float(match.group(1))
        lat_min = float(match.group(2))
        lat_sec = float(match.group(3))
        lat_dir = match.group(4)
        
        lat_decimal = lat_deg + lat_min/60 + lat_sec/3600
        if lat_dir.upper() == 'S':
            lat_decimal = -lat_decimal
        
        # Longitude
        lon_deg = float(match.group(5))
        lon_min = float(match.group(6))
        lon_sec = float(match.group(7))
        lon_dir = match.group(8)
        
        lon_decimal = lon_deg + lon_min/60 + lon_sec/3600
        if lon_dir.upper() == 'W':
            lon_decimal = -lon_decimal
        
        return f"{lat_decimal:.6f}, {lon_decimal:.6f}"
    
    def _clean_company_name(self, value: str, match: re.Match) -> str:
        """Bereinigt Firmennamen"""
        # Entferne überflüssige Leerzeichen
        cleaned = ' '.join(value.split())
        # Entferne trailing Punkte
        cleaned = cleaned.rstrip('.')
        return cleaned
    
    def _parse_commodity_list(self, value: str, match: re.Match) -> str:
        """Parst Rohstoffliste"""
        # Teile bei Kommas oder 'and'
        commodities = re.split(r',|and', value)
        # Bereinige und filtere
        cleaned = [c.strip() for c in commodities if c.strip()]
        return ', '.join(cleaned)
    
    def _standardize_commodity(self, value: str, match: re.Match) -> str:
        """Standardisiert Rohstoffnamen"""
        commodity_map = {
            'gold': 'Gold',
            'silver': 'Silver',
            'copper': 'Copper',
            'iron': 'Iron Ore',
            'zinc': 'Zinc',
            'lead': 'Lead',
            'nickel': 'Nickel',
            'cobalt': 'Cobalt',
            'lithium': 'Lithium',
            'uranium': 'Uranium',
            'coal': 'Coal',
            'diamond': 'Diamond',
            'platinum': 'Platinum',
            'palladium': 'Palladium'
        }
        return commodity_map.get(value.lower(), value.title())
    
    def _normalize_production_units(self, value: str, match: re.Match) -> str:
        """Normalisiert Produktionseinheiten"""
        quantity = match.group(1).replace(',', '')
        unit = match.group(2).lower()
        
        # Konvertiere zu Standardeinheit (Tonnen)
        conversions = {
            'oz': 0.0000283495,  # Unzen zu Tonnen
            'ounces': 0.0000283495,
            'lbs': 0.000453592,  # Pfund zu Tonnen
            'pounds': 0.000453592,
            'kt': 1000,  # Kilotonnen zu Tonnen
            'mt': 1000000  # Megatonnen zu Tonnen
        }
        
        if unit in conversions:
            quantity = float(quantity) * conversions[unit]
            return f"{quantity:,.0f} tonnes/year"
        else:
            return f"{quantity} {unit}/year"
    
    def _normalize_capacity(self, value: str, match: re.Match) -> str:
        """Normalisiert Kapazitätsangaben"""
        quantity = match.group(1).replace(',', '')
        unit = match.group(2).lower()
        period = match.group(3).lower()
        
        # Konvertiere zu Jahreskapazität
        period_conversions = {
            'day': 365,
            'month': 12,
            'year': 1,
            'annum': 1
        }
        
        multiplier = period_conversions.get(period, 1)
        annual_capacity = float(quantity) * multiplier
        
        return f"{annual_capacity:,.0f} {unit}/year"
    
    def _standardize_status(self, value: str, match: re.Match) -> str:
        """Standardisiert Status-Angaben"""
        status_map = {
            'operational': 'Operational',
            'operating': 'Operational',
            'active': 'Active',
            'closed': 'Closed',
            'suspended': 'Suspended',
            'care and maintenance': 'Care & Maintenance',
            'exploration': 'Exploration',
            'development': 'Development',
            'construction': 'Under Construction'
        }
        return status_map.get(value.lower(), value.title())
    
    def _translate_status(self, value: str, match: re.Match) -> str:
        """Übersetzt Status aus verschiedenen Sprachen"""
        translations = {
            'activo': 'Active',
            'active': 'Active',
            'operacional': 'Operational',
            'fermé': 'Closed',
            'cerrado': 'Closed',
            'suspendu': 'Suspended',
            'suspendido': 'Suspended',
            'en construcción': 'Under Construction',
            'under construction': 'Under Construction',
            'producing': 'Operational',
            'non-producing': 'Not Operational'
        }
        return translations.get(value.lower(), value)
    
    def _normalize_currency(self, value: str, match: re.Match) -> str:
        """Normalisiert Währungsbeträge"""
        amount = match.group(1).replace(',', '')
        multiplier = match.group(2)
        currency = match.group(3) or 'USD'
        
        # Konvertiere zu voller Zahl
        if multiplier:
            if multiplier.lower() in ['million', 'm']:
                amount = float(amount) * 1000000
            elif multiplier.lower() in ['billion', 'b']:
                amount = float(amount) * 1000000000
        
        return f"{amount:,.2f} {currency}"
    
    def add_custom_pattern(self, field_type: FieldType, pattern: str, 
                          language: str, confidence: float = 0.8):
        """Fügt benutzerdefiniertes Muster hinzu"""
        if field_type not in self.custom_patterns:
            self.custom_patterns[field_type] = []
        
        custom = ExtractionPattern(
            field_type=field_type,
            pattern=re.compile(pattern, re.IGNORECASE),
            language=language,
            confidence=confidence,
            extraction_method="custom"
        )
        
        self.custom_patterns[field_type].append(custom)
        
        # Füge auch zu Hauptmustern hinzu
        self.patterns[field_type].append(custom)
    
    def learn_from_success(self, field_type: FieldType, pattern: str, value: str):
        """Lernt aus erfolgreichen Extraktionen"""
        if field_type not in self.success_history:
            self.success_history[field_type] = []
        
        self.success_history[field_type].append({
            'pattern': pattern,
            'value': value,
            'count': 1
        })
        
        # Nach genügend Erfolgen, erstelle neues Muster
        # (Implementierung würde ML verwenden)