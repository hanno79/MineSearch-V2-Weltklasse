"""
Author: rahn
Datum: 26.08.2025
Version: 1.0
Beschreibung: Intelligente Werte-Normalisierung für semantisch identische Begriffe
ZWECK: Kanada=Canada, Untertage=Underground, Quebec=Québec etc. als identisch erkennen
"""

import re
import logging
from typing import Dict, List, Optional, Set
from unicodedata import normalize

logger = logging.getLogger(__name__)

class ValueNormalizer:
    """
    Intelligente Normalisierung semantisch identischer Werte aus verschiedenen Sprachen/Schreibweisen
    """
    
    def __init__(self):
        # Country normalization mappings
        self.country_mappings = {
            'kanada': 'Kanada',
            'canada': 'Kanada', 
            'can': 'Kanada',
            'canadá': 'Kanada',
            'australien': 'Australien',
            'australia': 'Australien',
            'aus': 'Australien',
            'vereinigte staaten': 'USA',
            'united states': 'USA',
            'usa': 'USA',
            'united states of america': 'USA',
            'us': 'USA',
            'deutschland': 'Deutschland',
            'germany': 'Deutschland',
            'ger': 'Deutschland',
            'chile': 'Chile',
            'südafrika': 'Südafrika',
            'south africa': 'Südafrika',
            'rsa': 'Südafrika'
        }
        
        # Region normalization (Quebec focus for Canadian mines)
        self.region_mappings = {
            'quebec': 'Quebec',
            'québec': 'Quebec',
            'qc': 'Quebec',
            'nord-du-québec': 'Quebec',
            'james bay': 'Quebec',
            'james bay territory': 'Quebec',
            'james bay region': 'Quebec',
            'james bay gebiet': 'Quebec',
            'eeyou istchee': 'Quebec',
            'eeyou istchee james bay': 'Quebec',
            'eeyou istchee/james bay': 'Quebec',
            'nord-québec': 'Quebec',
            'northern quebec': 'Quebec',
            'nördliches quebec': 'Quebec',
            'james bay, quebec': 'Quebec',
            'québec, james bay region': 'Quebec',
            'québec (nord-du-québec, james bay region)': 'Quebec',
            'québec, nord-du-québec': 'Quebec',
            'eeyou istchee/james bay, nördliches quebec': 'Quebec',
            'eeyou istchee/james bay, nord-quebec': 'Quebec',
            'ontario': 'Ontario',
            'on': 'Ontario',
            'british columbia': 'British Columbia',
            'bc': 'British Columbia',
            'alberta': 'Alberta',
            'ab': 'Alberta'
        }
        
        # Mine type normalization (multilingual) - DEUTSCHE AUSGABE
        self.mine_type_mappings = {
            'untertage': 'Untertage',
            'underground': 'Untertage', 
            'souterrain': 'Untertage',
            'untertagebau': 'Untertage',
            'untertagebergbau': 'Untertage',
            'unterirdisch': 'Untertage',
            'subterranean': 'Untertage',
            'open-pit': 'Tagebau',
            'openpit': 'Tagebau',
            'open pit': 'Tagebau',
            'tagebau': 'Tagebau',
            'à ciel ouvert': 'Tagebau',
            'surface': 'Tagebau',
            'oberflächenabbau': 'Tagebau'
        }
        
        # Commodity normalization (multilingual) - DEUTSCHE AUSGABE
        self.commodity_mappings = {
            'gold': 'Gold',
            'or': 'Gold',
            'oro': 'Gold',
            'emas': 'Gold',
            'copper': 'Kupfer',
            'cuivre': 'Kupfer',
            'cobre': 'Kupfer',
            'tembaga': 'Kupfer',
            'kupfer': 'Kupfer',
            'silver': 'Silber',
            'argent': 'Silber',
            'plata': 'Silber',
            'perak': 'Silber',
            'silber': 'Silber',
            'iron ore': 'Eisenerz',
            'minerai de fer': 'Eisenerz',
            'mineral de hierro': 'Eisenerz',
            'eisenerz': 'Eisenerz',
            'coal': 'Kohle',
            'charbon': 'Kohle',
            'carbón': 'Kohle',
            'kohle': 'Kohle'
        }
        
        # Status normalization - DEUTSCHE AUSGABE
        self.status_mappings = {
            'aktiv': 'Aktiv',
            'active': 'Aktiv',
            'actif': 'Aktiv',
            'activo': 'Aktiv',
            'operating': 'Aktiv',
            'in operation': 'Aktiv',
            'operational': 'Aktiv',
            'geschlossen': 'Geschlossen',
            'closed': 'Geschlossen',
            'fermé': 'Geschlossen',
            'cerrado': 'Geschlossen',
            'stillgelegt': 'Geschlossen',
            'shutdown': 'Geschlossen',
            'geplant': 'Geplant',
            'planned': 'Geplant',
            'planifié': 'Geplant',
            'planeado': 'Geplant',
            'entwicklung': 'Entwicklung',
            'development': 'Entwicklung',
            'développement': 'Entwicklung',
            'desarrollo': 'Entwicklung'
        }
        
        # Company name normalization patterns
        self.company_patterns = [
            # Remove legal suffixes
            (r'\s+(inc\.?|corporation|corp\.?|ltd\.?|limited|llc|sa|gmbh|ag)$', ''),
            # Normalize common company name variations
            (r'^newmont\s+.*', 'Newmont Corporation'),
            (r'^goldcorp\s*.*', 'Goldcorp'),
            (r'^barrick\s+.*', 'Barrick Gold'),
            (r'^anglogold\s+.*', 'AngloGold Ashanti')
        ]
    
    def normalize_value(self, value: str, field_name: str) -> str:
        """
        Hauptfunktion: Normalisiert einen Wert basierend auf Feldtyp
        
        Args:
            value: Zu normalisierender Wert
            field_name: Name des Feldes zur Bestimmung der Normalisierungsregel
            
        Returns:
            Normalisierter Wert
        """
        if not value or not isinstance(value, str):
            return str(value) if value else ""
        
        # Basis-Normalisierung: Whitespace, Akzente, Case
        normalized = self._basic_normalize(value)
        
        # Feld-spezifische Normalisierung
        field_lower = field_name.lower()
        
        if 'country' in field_lower or 'land' in field_lower:
            return self._normalize_country(normalized)
        elif 'region' in field_lower:
            return self._normalize_region(normalized)
        elif 'minentyp' in field_lower or 'mine type' in field_lower:
            return self._normalize_mine_type(normalized)
        elif 'rohstoff' in field_lower or 'commodity' in field_lower:
            return self._normalize_commodity(normalized)
        elif 'status' in field_lower or 'aktivität' in field_lower:
            return self._normalize_status(normalized)
        elif 'eigentümer' in field_lower or 'betreiber' in field_lower or 'owner' in field_lower or 'operator' in field_lower:
            return self._normalize_company(normalized)
        elif 'koordinate' in field_lower or 'coordinate' in field_lower:
            return self._normalize_coordinate(normalized)
        elif 'menge' in field_lower or 'production' in field_lower or 'förder' in field_lower:
            return self._normalize_production_amount(normalized)
        else:
            return normalized
    
    def _basic_normalize(self, value: str) -> str:
        """Basis-Normalisierung: Whitespace, Unicode, Quellenreferenzen - BEHÄLT Original-Case"""
        # Unicode-Normalisierung für Akzente
        normalized = normalize('NFD', value).encode('ascii', 'ignore').decode('ascii')
        
        # CRITICAL FIX 26.08.2025: Entferne Quellenreferenzen für Vergleiche
        # "geschlossen [1,2,3]" wird zu "geschlossen"
        normalized = re.sub(r'\s*\[\d+(?:,\d+)*\]', '', normalized)
        
        # Whitespace normalisieren
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        # WICHTIG: Case NICHT normalisieren - das machen die spezifischen Normalisierer
        return normalized
    
    def _normalize_country(self, value: str) -> str:
        """Normalisiert Ländernamen"""
        value_key = value.lower().strip()
        
        # Direkte Mapping-Suche
        if value_key in self.country_mappings:
            result = self.country_mappings[value_key]
            logger.debug(f"[NORMALIZE] Country '{value}' → '{result}'")
            return result
        
        # Partial matches für zusammengesetzte Namen
        for key, normalized in self.country_mappings.items():
            if key in value_key or value_key in key:
                logger.debug(f"[NORMALIZE] Country partial match '{value}' → '{normalized}'")
                return normalized
        
        # Fallback: Erste Buchstabe groß
        return value.title()
    
    def _normalize_region(self, value: str) -> str:
        """Normalisiert Regionsnamen (speziell für Quebec)"""
        value_key = value.lower().strip()
        
        # ERWEITERTE Quebec-spezifische Normalisierung 27.08.2025
        quebec_indicators = ['quebec', 'québec', 'james bay', 'eeyou', 'nord-du-québec', 'nord-québec', 'nördliches quebec']
        if any(indicator in value_key for indicator in quebec_indicators):
            logger.debug(f"[NORMALIZE] Region '{value}' → 'Quebec' (Quebec-Indikator erkannt)")
            return 'Quebec'
        
        # Direkte Mappings
        if value_key in self.region_mappings:
            result = self.region_mappings[value_key]
            logger.debug(f"[NORMALIZE] Region '{value}' → '{result}'")
            return result
        
        # Fallback: Title Case
        return value.title()
    
    def _normalize_mine_type(self, value: str) -> str:
        """Normalisiert Minentypen (mehrsprachig)"""
        value_key = value.lower().strip()
        
        # Entferne Sonderzeichen und Klammern
        cleaned = re.sub(r'["\(\)]', '', value_key)
        
        # Direkte Mappings
        if cleaned in self.mine_type_mappings:
            result = self.mine_type_mappings[cleaned]
            logger.debug(f"[NORMALIZE] Mine Type '{value}' → '{result}'")
            return result
        
        # Pattern-basierte Erkennung - DEUTSCHE AUSGABE
        if any(term in cleaned for term in ['untertage', 'underground', 'souterrain']):
            logger.debug(f"[NORMALIZE] Mine Type '{value}' → 'Untertage' (Pattern-Erkennung)")
            return 'Untertage'
        elif any(term in cleaned for term in ['open', 'tagebau', 'ciel ouvert', 'surface']):
            logger.debug(f"[NORMALIZE] Mine Type '{value}' → 'Tagebau' (Pattern-Erkennung)")
            return 'Tagebau'
        
        return value.title()
    
    def _normalize_commodity(self, value: str) -> str:
        """Normalisiert Rohstoffe (mehrsprachig) - CASE INSENSITIVE FIX"""
        # WICHTIG: Behalte den Original-Wert für bessere Logging
        original_value = value
        value_key = value.lower().strip()
        
        # Entferne zusätzliche Informationen in Klammern
        cleaned = re.sub(r'\s*\([^)]*\)', '', value_key)
        cleaned = re.sub(r',.*', '', cleaned)  # Entferne alles nach Komma
        cleaned = cleaned.strip()
        
        # Direkte Mappings (Case-insensitive durch value_key.lower())
        if cleaned in self.commodity_mappings:
            result = self.commodity_mappings[cleaned]
            logger.debug(f"[NORMALIZE] Commodity '{original_value}' → '{result}' (Direct mapping)")
            return result
        
        # ERWEITERTE Pattern-basierte Erkennung für Gold/gold Problem
        gold_patterns = ['gold', 'or', 'oro', 'emas']
        if any(pattern in cleaned for pattern in gold_patterns):
            logger.debug(f"[NORMALIZE] Commodity '{original_value}' → 'Gold' (Pattern-Erkennung: {cleaned})")
            return 'Gold'
            
        copper_patterns = ['copper', 'cuivre', 'cobre', 'kupfer']  
        if any(pattern in cleaned for pattern in copper_patterns):
            logger.debug(f"[NORMALIZE] Commodity '{original_value}' → 'Kupfer' (Pattern-Erkennung: {cleaned})")
            return 'Kupfer'
            
        silver_patterns = ['silver', 'argent', 'plata', 'silber', 'perak']
        if any(pattern in cleaned for pattern in silver_patterns):
            logger.debug(f"[NORMALIZE] Commodity '{original_value}' → 'Silber' (Pattern-Erkennung: {cleaned})")
            return 'Silber'
        
        # Fallback: Title Case für unbekannte Rohstoffe
        result = original_value.title() if original_value else ''
        logger.debug(f"[NORMALIZE] Commodity '{original_value}' → '{result}' (Fallback - unbekannter Rohstoff)")
        return result
    
    def _normalize_status(self, value: str) -> str:
        """Normalisiert Aktivitätsstatus"""
        value_key = value.lower().strip()
        
        if value_key in self.status_mappings:
            result = self.status_mappings[value_key]
            logger.debug(f"[NORMALIZE] Status '{value}' → '{result}'")
            return result
        
        return value.title()
    
    def _normalize_company(self, value: str) -> str:
        """Normalisiert Firmennamen"""
        normalized = value.strip()
        
        # Anwende Company-Pattern
        for pattern, replacement in self.company_patterns:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        if normalized != value:
            logger.debug(f"[NORMALIZE] Company '{value}' → '{normalized}'")
        
        return normalized
    
    def _normalize_coordinate(self, value: str) -> str:
        """Normalisiert GPS-Koordinaten auf einheitliches Format"""
        # Extrahiere Zahl und formatiere einheitlich
        coord_match = re.search(r'(-?\d+\.?\d*)', str(value))
        if coord_match:
            coord_num = float(coord_match.group(1))
            # Formatiere auf 6 Nachkommastellen
            normalized = f"{coord_num:.6f}"
            if normalized != str(value):
                logger.debug(f"[NORMALIZE] Coordinate '{value}' → '{normalized}'")
            return normalized
        return str(value)
    
    def _normalize_production_amount(self, value: str) -> str:
        """Normalisiert Produktionsmengen (einheitliche Formatierung)"""
        # Normalisiere Tausendertrennzeichen
        normalized = value.replace(',', '.')
        
        # Normalisiere Leerzeichen um Zahlen
        normalized = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', normalized)
        normalized = re.sub(r'(\d+)\s+', r'\1 ', normalized)
        
        if normalized != value:
            logger.debug(f"[NORMALIZE] Production '{value}' → '{normalized}'")
        
        return normalized

# Globale Instanz
value_normalizer = ValueNormalizer()

def normalize_field_value(value: str, field_name: str) -> str:
    """
    Globale Funktion zur Werte-Normalisierung
    
    Args:
        value: Zu normalisierender Wert
        field_name: Feldname für kontextspezifische Normalisierung
        
    Returns:
        Normalisierter Wert
    """
    return value_normalizer.normalize_value(value, field_name)