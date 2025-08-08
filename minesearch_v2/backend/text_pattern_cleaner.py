"""
Author: rahn
Datum: 30.07.2025
Version: 1.0
Beschreibung: Text Pattern Cleaner für Mining-Datenextraktion
Basierend auf Text Pattern Research Report
"""

import re
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class TextPatternCleaner:
    """
    Bereinigt problematische Textmuster in extrahierten Mining-Daten
    
    Kategorien:
    1. LEER-Varianten → 'X'
    2. Lange Beschreibungen → Wert-Extraktion
    3. Wert + Erklärung → Wert-Extraktion  
    4. Anweisungen → 'X'
    """
    
    def __init__(self):
        self.leer_patterns = [
            r'\(leer\)',
            r'leer\s*-[^,]*',
            r'unbekannt.*(?:aufgrund|da).*',
            r'leave blank.*',
            r'possibly.*leave blank',
            r'keine.*(?:daten|angabe|informationen).*',
            r'not?\s*(?:found|available|specified).*',
            r'unknown.*(?:due to|because).*',
            r'keine spezifischen.*gefunden'
        ]
        
        self.instruction_patterns = [
            r'leave blank',  # Erweitert für alle "leave blank" Varianten
            r'lassen.*leer',
            r'fill only if',
            r'ausfüllen nur wenn',
            r'enter only if',
            r'nur eingeben wenn'
        ]
        
        self.commodities = {
            'gold': 'Gold',
            'kupfer': 'Kupfer', 
            'copper': 'Kupfer',
            'nickel': 'Nickel',
            'eisenerz': 'Eisenerz',
            'iron ore': 'Eisenerz',
            'kohle': 'Kohle',
            'coal': 'Kohle',
            'silber': 'Silber',
            'silver': 'Silber',
            'zink': 'Zink',
            'zinc': 'Zink',
            'blei': 'Blei',
            'lead': 'Blei',
            'uran': 'Uran',
            'uranium': 'Uran',
            'platin': 'Platin',
            'platinum': 'Platin',
            'niob': 'Niob',
            'niobium': 'Niob',
            'asbest': 'Asbest',
            'asbestos': 'Asbest',
            'chrysotil': 'Chrysotil',
            'chrysotile': 'Chrysotil'
        }


    def clean_field_value(self, value: str, field: str) -> str:
        """
        Master-Funktion zur Bereinigung problematischer Textmuster
        
        Args:
            value: Ursprünglicher Feldwert
            field: Feldname für kontextuelle Bereinigung
            
        Returns:
            Bereinigter Wert oder 'X' wenn nicht extrahierbar
        """
        if not value or not str(value).strip():
            return "X"
        
        cleaned = str(value).strip()
        
        # 1. LEER-Varianten normalisieren
        if self._is_leer_variant(cleaned):
            logger.debug(f"[PATTERN CLEANER] LEER-Variante erkannt in {field}: {cleaned}")
            return "X"
        
        # 2. Anweisungen entfernen - aber nur wenn sie primär Anweisungen sind
        # Wenn der Text weitere verwertbare Informationen enthält, extrahiere diese zuerst
        if self._is_primary_instruction(cleaned):
            logger.debug(f"[PATTERN CLEANER] Primäre Anweisung erkannt in {field}: {cleaned}")
            return "X"
        
        # 3. Spezifische Pattern-Erkennung für Eigentümer/Betreiber
        if field in ['Eigentümer', 'Betreiber'] and ('property of' in cleaned.lower() or 'owned by' in cleaned.lower() or 'operated by' in cleaned.lower()):
            extracted = self._extract_from_long_description(cleaned, field)
            if extracted != cleaned:
                logger.debug(f"[PATTERN CLEANER] Spezifisches Pattern extrahiert in {field}: {cleaned} → {extracted}")
                return extracted
        
        # 4. Lange Beschreibungen nach Feld verarbeiten
        if len(cleaned) > 60:  # Reduzierter Schwellenwert für bessere Erkennung
            extracted = self._extract_from_long_description(cleaned, field)
            if extracted != cleaned:
                logger.debug(f"[PATTERN CLEANER] Aus langer Beschreibung extrahiert in {field}: {cleaned[:50]}... → {extracted}")
                return extracted
        
        # 5. Wert + Erklärung Format
        if re.match(r'^\w+\.\s+.*', cleaned):
            extracted = self._extract_value_from_explanation(cleaned)
            logger.debug(f"[PATTERN CLEANER] Aus Wert+Erklärung extrahiert in {field}: {cleaned} → {extracted}")
            return extracted
        
        return cleaned


    def _is_leer_variant(self, text: str) -> bool:
        """Prüft ob Text eine LEER-Variante ist"""
        text_lower = text.lower()
        
        for pattern in self.leer_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False


    def _is_instruction(self, text: str) -> bool:
        """Prüft ob Text eine Anweisung ist"""
        text_lower = text.lower()
        
        for pattern in self.instruction_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False

    def _is_primary_instruction(self, text: str) -> bool:
        """Prüft ob Text PRIMÄR eine Anweisung ist (ohne andere verwertbare Infos)"""
        if not self._is_instruction(text):
            return False
        
        # Wenn Anweisung vorhanden ist, aber auch andere verwertbare Infos
        text_lower = text.lower()
        valuable_content = any(commodity in text_lower for commodity in self.commodities.keys())
        
        if valuable_content:
            return False  # Nicht primär Anweisung, hat verwertbaren Inhalt
        
        return True  # Primär Anweisung


    def _extract_from_long_description(self, text: str, field: str) -> str:
        """Extrahiert Werte aus langen Beschreibungen je nach Feld"""
        
        if field == "Rohstoffe":
            return self._extract_commodity_from_description(text)
        
        elif field == "Eigentümer":
            return self._extract_owner_from_description(text)
        
        elif field == "Betreiber":
            return self._extract_operator_from_description(text)
        
        elif field == "Aktivitätsstatus":
            return self._extract_status_from_description(text)
        
        elif field.endswith("jahr"):  # Kostenjahr, Dokumentenjahr
            return self._extract_year_from_description(text)
        
        # Fallback: Wenn zu lang und keine Extraktion möglich
        if len(text) > 200:
            return "X"
        
        return text


    def _extract_commodity_from_description(self, text: str) -> str:
        """Extrahiert Rohstoff aus langer Beschreibung"""
        text_lower = text.lower()
        
        # Pattern: "etwa X Unzen ROHSTOFF pro Jahr"
        production_match = re.search(r'(\d+[,.]?\d*)\s*(?:unzen|ounces)\s+(\w+)\s+pro\s+jahr', text_lower)
        if production_match:
            commodity = production_match.group(2)
            return self.commodities.get(commodity, commodity.title())
        
        # Pattern: "maybe it's a ROHSTOFF mine"
        maybe_match = re.search(r'maybe it\'s a (\w+) mine', text_lower)
        if maybe_match:
            commodity = maybe_match.group(1)
            if commodity in self.commodities:
                return self.commodities[commodity]
        
        # Pattern: Direkte Rohstoff-Erwähnung
        for commodity_key, commodity_value in self.commodities.items():
            if commodity_key in text_lower:
                return commodity_value
        
        # Pattern: "primary commodity is ROHSTOFF"
        primary_match = re.search(r'primary commodity is (\w+)', text_lower)
        if primary_match:
            commodity = primary_match.group(1)
            return self.commodities.get(commodity, commodity.title())
        
        return "X"


    def _extract_owner_from_description(self, text: str) -> str:
        """Extrahiert spezifischen Eigentümer oder gibt 'X' zurück"""
        
        # Generische Beschreibungen ohne spezifische Namen
        generic_terms = [
            'junior mining', 'subsidiaries', 'without specific', 'typical structures',
            'mining companies', 'larger firms', 'might have to', 'based on typical'
        ]
        
        if any(term in text.lower() for term in generic_terms):
            return "X"
        
        # Pattern: "owned by FIRMA", "property of FIRMA"
        owner_patterns = [
            r'property of\s+([A-Z][a-zA-Z\s&\-]+Corporation)\s+since',  # Spezifisch für "Corporation since"
            r'(?:owned by|property of|belongs to|eigentum von|gehört)\s+([A-Z][^.]+?)(?:\.|,|$)',
            r'([A-Z][a-zA-Z\s&\-]+(?:Inc|Corp|Ltd|Corporation|Company|GmbH|AG|Mining|Resources))\s*(?:since|from|\.|,|$)'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                owner = match.group(1).strip()
                # Bereinige typische Suffix-Probleme
                owner = re.sub(r'\s+(?:and|und|&).*$', '', owner)
                return owner
        
        return "X"


    def _extract_operator_from_description(self, text: str) -> str:
        """Extrahiert Betreiber aus Beschreibung"""
        
        # Pattern: "operated by FIRMA", "betrieben von FIRMA"
        operator_patterns = [
            r'(?:operated by|betrieben von|exploité par)\s+([A-Z][^.]+?)(?:\.|,|$)',
            r'(?:operator|betreiber|exploitant):\s*([A-Z][^.]+?)(?:\.|,|$)'
        ]
        
        for pattern in operator_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "X"


    def _extract_status_from_description(self, text: str) -> str:
        """Extrahiert Aktivitätsstatus aus Beschreibung"""
        text_lower = text.lower()
        
        # Standard-Status erkennen
        status_patterns = {
            'aktiv': ['aktiv', 'active', 'in betrieb', 'operating', 'production'],
            'geschlossen': ['geschlossen', 'closed', 'shut down', 'ceased'],
            'stillgelegt': ['stillgelegt', 'suspended', 'mothballed'],
            'geplant': ['geplant', 'planned', 'proposed', 'development'],
            'exploration': ['exploration', 'explorationsphase', 'prospect']
        }
        
        for status, patterns in status_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return status.title()
        
        return "X"


    def _extract_year_from_description(self, text: str) -> str:
        """Extrahiert Jahr aus Beschreibung"""
        
        # Pattern: 4-stellige Jahreszahl
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        if year_match:
            return year_match.group(1)
        
        return "X"


    def _extract_value_from_explanation(self, text: str) -> str:
        """Extrahiert Wert aus 'Wert. Erklärung...' Format"""
        
        # Pattern: "WERT. Erklärung..."
        match = re.match(r'^(\w+)\.\s+.*', text)
        if match:
            value = match.group(1)
            # Normalisiere bekannte Rohstoffe
            return self.commodities.get(value.lower(), value)
        
        return text


    def batch_clean_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Bereinigt ein komplettes Daten-Dictionary
        
        Args:
            data: Dictionary mit Feldname -> Wert
            
        Returns:
            Bereinigtes Dictionary
        """
        cleaned_data = {}
        
        for field, value in data.items():
            if field.startswith('_'):  # Skip metadata
                cleaned_data[field] = value
                continue
                
            cleaned_value = self.clean_field_value(value, field)
            cleaned_data[field] = cleaned_value
        
        return cleaned_data


    def get_cleaning_statistics(self, original_data: Dict[str, str], cleaned_data: Dict[str, str]) -> Dict[str, int]:
        """
        Erzeugt Statistiken über die Bereinigung
        
        Returns:
            Dictionary mit Bereinigungsstatistiken
        """
        stats = {
            'total_fields': len(original_data),
            'fields_changed': 0,
            'fields_set_to_x': 0,
            'leer_variants_normalized': 0,
            'long_descriptions_processed': 0,
            'instructions_removed': 0
        }
        
        for field in original_data:
            if field.startswith('_'):
                continue
                
            original = str(original_data.get(field, ''))
            cleaned = str(cleaned_data.get(field, ''))
            
            if original != cleaned:
                stats['fields_changed'] += 1
                
                if cleaned == 'X':
                    stats['fields_set_to_x'] += 1
                
                if self._is_leer_variant(original):
                    stats['leer_variants_normalized'] += 1
                
                if len(original) > 80:
                    stats['long_descriptions_processed'] += 1
                
                if self._is_instruction(original):
                    stats['instructions_removed'] += 1
        
        return stats


# Test-Funktion
def test_text_pattern_cleaner():
    """Test-Cases für die Bereinigungsfunktionen"""
    
    cleaner = TextPatternCleaner()
    
    test_cases = [
        # LEER-Varianten
        ("LEER - Minentyp nicht spezifiziert", "Minentyp", "X"),
        ("Unbekannt, da keine Daten", "Eigentümer", "X"),
        ("Leave blank if unknown", "Aktivitätsstatus", "X"),
        ("(leer)", "Betreiber", "X"),
        
        # Lange Beschreibungen - Rohstoffe
        ("derzeit etwa 270.000 Unzen Gold pro Jahr. Die Mine befindet sich in der Nähe von Eeyou Istchee James Bay in Nord-Quebec", "Rohstoffe", "Gold"),
        ("If unknown, leave blank. But maybe it's a nickel mine? Some Quebec mines are nickel.", "Rohstoffe", "X"),  # Anweisung dominant
        
        # Lange Beschreibungen - Eigentümer
        ("junior mining companies or subsidiaries of larger firms. Without specific data...", "Eigentümer", "X"),
        ("Property of Canadian Malartic Corporation since 2014", "Eigentümer", "Canadian Malartic Corporation"),
        
        # Wert + Erklärung
        ("Gold. Lapa is a gold mine, so primary commodity is gold", "Rohstoffe", "Gold"),
        ("Nickel. This is a nickel mining operation", "Rohstoffe", "Nickel"),
        
        # Normale Werte (sollten unverändert bleiben)
        ("Canadian Malartic Corporation", "Eigentümer", "Canadian Malartic Corporation"),
        ("Aktiv", "Aktivitätsstatus", "Aktiv"),
        ("Gold", "Rohstoffe", "Gold")
    ]
    
    print("Testing Text Pattern Cleaner...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for original, field, expected in test_cases:
        result = cleaner.clean_field_value(original, field)
        
        if result == expected:
            print(f"✅ PASS: {field}")
            passed += 1
        else:
            print(f"❌ FAIL: {field}")
            print(f"   Input: {original}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    test_text_pattern_cleaner()