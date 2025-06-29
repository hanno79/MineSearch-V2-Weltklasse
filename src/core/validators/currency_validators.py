"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Währungs-Validierung und -Normalisierung
"""

import re
from typing import Any, Dict, Optional, Tuple
from .base import BaseValidator
from ..logger import get_logger

logger = get_logger(__name__)


class CurrencyValidator(BaseValidator):
    """Validierung für Währungsbeträge"""
    
    # Währungscodes
    VALID_CURRENCIES = ['CAD', 'USD', 'EUR', 'GBP', 'AUD', 'CHF', 'JPY', 'CNY']
    
    # Einfache Wechselkurse (sollten eigentlich dynamisch sein)
    EXCHANGE_RATES = {
        'USD': {'CAD': 1.35, 'EUR': 0.92},
        'CAD': {'USD': 0.74, 'EUR': 0.68},
        'EUR': {'USD': 1.09, 'CAD': 1.47}
    }
    
    def validate_currency_amount(self, amount: Any, field_name: str) -> None:
        """Validiert Währungsbeträge"""
        if amount is None or amount == "nichts gefunden":
            return
        
        # String zu Zahl konvertieren
        if isinstance(amount, str):
            # Entferne Währungssymbole und Formatierung
            cleaned = re.sub(r'[^\d,.-]', '', amount)
            cleaned = cleaned.replace(',', '.')
            
            try:
                numeric_amount = float(cleaned)
            except ValueError:
                self.errors.append(f"{field_name}: Ungültiger Betrag '{amount}'")
                return
                
            # Prüfe auf Währungscode
            currency_match = re.search(r'\b(' + '|'.join(self.VALID_CURRENCIES) + r')\b', amount, re.IGNORECASE)
            if not currency_match:
                self.warnings.append(f"{field_name}: Keine Währung angegeben")
        
        elif isinstance(amount, (int, float)):
            numeric_amount = float(amount)
        else:
            self.errors.append(f"{field_name}: Muss Zahl oder Text sein")
            return
        
        # Validiere Betragshöhe
        if numeric_amount < 0:
            self.errors.append(f"{field_name}: Betrag darf nicht negativ sein")
        
        if numeric_amount > 10_000_000_000:  # 10 Milliarden
            self.warnings.append(f"{field_name}: Ungewöhnlich hoher Betrag ({numeric_amount:,.0f})")
    
    def normalize_currency_amount(self, amount: Any, target_currency: str = 'CAD') -> Optional[Dict[str, Any]]:
        """Normalisiert Währungsbeträge zu Zielwährung"""
        if amount is None or amount == "nichts gefunden":
            return None
        
        # Parse Betrag
        if isinstance(amount, str):
            # Extrahiere Zahl und Währung
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:million|M)?\s*([A-Z]{3})?', amount, re.IGNORECASE)
            if not amount_match:
                return None
                
            value = float(amount_match.group(1).replace(',', ''))
            
            # Prüfe auf Millionen/Milliarden
            if 'million' in amount.lower() or ' M' in amount:
                value *= 1_000_000
            elif 'billion' in amount.lower() or ' B' in amount:
                value *= 1_000_000_000
                
            currency = amount_match.group(2) or 'CAD'  # Default CAD
            
        elif isinstance(amount, (int, float)):
            value = float(amount)
            currency = 'CAD'  # Default
        else:
            return None
            
        # Konvertiere zur Zielwährung
        if currency != target_currency and currency in self.EXCHANGE_RATES:
            if target_currency in self.EXCHANGE_RATES[currency]:
                value *= self.EXCHANGE_RATES[currency][target_currency]
                
        return {
            'value': value,
            'currency': target_currency,
            'original_currency': currency,
            'formatted': f"${value:,.2f} {target_currency}"
        }
    
    def clean_numeric_value(self, value: Any) -> Optional[float]:
        """Bereinigt und konvertiert numerische Werte"""
        if value is None or value == "nichts gefunden":
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Entferne Währungssymbole, Leerzeichen, etc.
            cleaned = re.sub(r'[^\d,.-]', '', value)
            
            # Ersetze Komma durch Punkt
            cleaned = cleaned.replace(',', '.')
            
            try:
                return float(cleaned)
            except ValueError:
                logger.warning(f"Konnte Wert nicht zu Zahl konvertieren: '{value}'")
                return None
        
        return None
    
    def extract_currency(self, amount_str: str) -> Tuple[Optional[float], Optional[str]]:
        """Extrahiert Betrag und Währung aus String"""
        if not isinstance(amount_str, str):
            return None, None
        
        # Suche nach Währung
        currency = None
        for curr in self.VALID_CURRENCIES:
            if curr in amount_str.upper():
                currency = curr
                break
        
        # Extrahiere numerischen Wert
        amount = self.clean_numeric_value(amount_str)
        
        return amount, currency
    
    def format_currency(self, amount: float, currency: str = 'CAD') -> str:
        """Formatiert Betrag mit Währung"""
        if currency not in self.VALID_CURRENCIES:
            currency = 'CAD'
        
        return f"${amount:,.2f} {currency}"