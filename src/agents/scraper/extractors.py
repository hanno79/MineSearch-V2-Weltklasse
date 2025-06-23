"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Extraktor-Module für Web Scraping
"""

import re
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
import logging


class DataExtractor:
    """Klasse für Datenextraktion aus HTML"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_text(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """Extrahiert Text basierend auf Label"""
        # Suche nach Label in verschiedenen HTML-Strukturen
        patterns = [
            soup.find('td', string=re.compile(label, re.I)),
            soup.find('th', string=re.compile(label, re.I)),
            soup.find('label', string=re.compile(label, re.I))
        ]
        
        for element in patterns:
            if element:
                # Finde zugehörigen Wert
                next_element = element.find_next_sibling()
                if next_element:
                    return next_element.get_text(strip=True)
                    
                # Oder im Parent
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    text = text.replace(label, '').strip()
                    if text:
                        return text
        
        return None
    
    def extract_coordinates(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Extrahiert Koordinaten aus HTML"""
        coords = {}
        
        # Suche nach verschiedenen Koordinaten-Formaten
        patterns = [
            r'latitude[:\s]*(-?\d+\.?\d*)',
            r'lat[:\s]*(-?\d+\.?\d*)',
            r'longitude[:\s]*(-?\d+\.?\d*)',
            r'lon[:\s]*(-?\d+\.?\d*)',
            r'(-?\d+\.?\d*)[°\s]*[NS].*?(-?\d+\.?\d*)[°\s]*[EW]'
        ]
        
        text = soup.get_text()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                if isinstance(matches[0], tuple):
                    coords['latitude'] = float(matches[0][0])
                    coords['longitude'] = float(matches[0][1])
                else:
                    if 'lat' in pattern:
                        coords['latitude'] = float(matches[0])
                    elif 'lon' in pattern:
                        coords['longitude'] = float(matches[0])
        
        return coords
    
    def extract_costs(self, text: str) -> Dict[str, Any]:
        """Extrahiert Kostenangaben aus Text"""
        costs = {}
        
        # Suche nach Währungsangaben
        currency_patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)?',
            r'([\d,]+(?:\.\d{2})?)\s*(?:CAD|USD|EUR)',
            r'restoration.*?costs?.*?([\d,]+(?:\.\d{2})?)',
            r'environmental.*?liability.*?([\d,]+(?:\.\d{2})?)'
        ]
        
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                # Konvertiere zu Zahl
                value = matches[0].replace(',', '')
                if 'million' in text.lower() or 'M' in text:
                    value = float(value) * 1000000
                else:
                    value = float(value)
                
                costs['value'] = value
                
                # Erkenne Währung
                if 'CAD' in text or '$' in text and 'canad' in text.lower():
                    costs['currency'] = 'CAD'
                elif 'USD' in text:
                    costs['currency'] = 'USD'
                elif 'EUR' in text:
                    costs['currency'] = 'EUR'
                else:
                    costs['currency'] = 'CAD'  # Default für Kanada
                
                # ÄNDERUNG 21.06.2025: Debug-Logging für extrahierte Kosten
                self.logger.info(f"DEBUG: Extrahierte Kosten aus Text: {value} {costs.get('currency', 'CAD')}")
                self.logger.info(f"DEBUG: Text-Snippet: {text[:200]}...")
                
                break
        
        return costs
    
    def extract_operator(self, text: str, mine_name: str) -> Optional[str]:
        """Extrahiert Betreiber-Informationen"""
        operator_patterns = [
            rf'{re.escape(mine_name)}.*?(?:operated by|owned by|operator:|owner:)\s*([A-Za-z0-9\s&.,()-]+)',
            rf'([A-Za-z0-9\s&.,()-]+?)\s+(?:operates|owns)\s+{re.escape(mine_name)}'
        ]
        
        for pattern in operator_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def validate_cost_context(self, text: str, cost_value: float) -> bool:
        """Validiert ob Kostenwert im richtigen Kontext steht"""
        # Plausibilitätsprüfung
        if cost_value < 1000:  # Weniger als 1000 (zu klein)
            self.logger.warning(f"Kostenwert zu klein: {cost_value}")
            return False
        
        if cost_value > 5000000000:  # Mehr als 5 Milliarden (unrealistisch)
            self.logger.warning(f"Kostenwert zu groß: {cost_value}")
            return False
        
        # Prüfe ob die Zahl im Kontext von Kosten steht
        cost_context = ['cost', 'remediation', 'closure', 'rehabilitation', 'liability', 
                       'bond', 'financial', 'sanierung', 'kosten', 'restauration']
        
        # Extrahiere Kontext um die Zahl (100 Zeichen vor und nach)
        number_pattern = rf"{int(cost_value):,}|{int(cost_value)}"
        match = re.search(number_pattern, text)
        if match:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context_text = text[start:end].lower()
            
            if not any(keyword in context_text for keyword in cost_context):
                self.logger.warning(f"Kostenwert ohne passenden Kontext: {cost_value}")
                return False
        
        return True
