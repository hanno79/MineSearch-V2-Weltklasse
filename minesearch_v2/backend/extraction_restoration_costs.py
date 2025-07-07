"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: Spezialisierte Extraktion für Restaurationskosten
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from extraction_patterns import get_restoration_cost_patterns

logger = logging.getLogger(__name__)


class RestorationCostExtractor:
    """Spezialisierte Klasse für die Extraktion von Restaurationskosten"""
    
    def __init__(self):
        self.patterns = get_restoration_cost_patterns()
        
        # Währungs-Mapping
        self.currency_map = {
            'cad': 'CAD',
            'cdn': 'CAD',
            'c$': 'CAD',
            'usd': 'USD',
            'us$': 'USD',
            '$': 'USD',  # Default
            'eur': 'EUR',
            '€': 'EUR',
            'aud': 'AUD',
            'a$': 'AUD'
        }
        
        # Einheiten-Multiplikatoren
        self.unit_multipliers = {
            'million': 1_000_000,
            'millions': 1_000_000,
            'millionen': 1_000_000,
            'mio': 1_000_000,
            'm': 1_000_000,
            'thousand': 1_000,
            'thousands': 1_000,
            'tausend': 1_000,
            'k': 1_000,
            'billion': 1_000_000_000,
            'billions': 1_000_000_000,
            'milliarden': 1_000_000_000,
            'b': 1_000_000_000
        }
    
    def extract_restoration_costs(self, text: str) -> Dict[str, any]:
        """
        Extrahiert Restaurationskosten aus Text
        
        Args:
            text: Der zu analysierende Text
            
        Returns:
            Dict mit extrahierten Informationen
        """
        if not text:
            return {}
        
        # Normalisiere Text
        text_normalized = self._normalize_text(text)
        
        # Suche nach Restaurationskosten
        findings = []
        
        for pattern in self.patterns:
            matches = re.finditer(pattern, text_normalized, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Extrahiere Kontext
                context_start = max(0, match.start() - 100)
                context_end = min(len(text_normalized), match.end() + 100)
                context = text_normalized[context_start:context_end]
                
                # Parse den gefundenen Wert
                parsed = self._parse_match(match, context)
                
                if parsed and parsed['amount'] >= 1000:  # Minimum $1,000
                    findings.append(parsed)
        
        # Dedupliziere und wähle besten Wert
        if findings:
            best_finding = self._select_best_finding(findings)
            return best_finding
        
        return {}
    
    def _normalize_text(self, text: str) -> str:
        """Normalisiert Text für bessere Pattern-Matches"""
        # Ersetze verschiedene Leerzeichen
        text = re.sub(r'\s+', ' ', text)
        
        # Normalisiere Währungssymbole
        text = re.sub(r'CAD\s*\$', 'CAD$', text)
        text = re.sub(r'USD\s*\$', 'USD$', text)
        
        # Normalisiere Zahlenformate
        text = re.sub(r'(\d)\s+(\d{3})', r'\1,\2', text)  # 45 000 -> 45,000
        
        return text
    
    def _parse_match(self, match: re.Match, context: str) -> Optional[Dict]:
        """Parse einen Regex-Match zu strukturierten Daten"""
        try:
            # Extrahiere Betrag
            amount_str = match.group(1)
            amount = self._parse_amount(amount_str)
            
            if amount is None:
                return None
            
            # Extrahiere Währung
            currency = self._extract_currency(match.group(0), context)
            
            # Extrahiere Einheit
            unit = self._extract_unit(match.group(0), context)
            
            # Berechne finalen Betrag
            final_amount = amount * unit
            
            # Extrahiere Jahr
            year = self._extract_year(context)
            
            # Bestimme Typ
            cost_type = self._determine_cost_type(context)
            
            return {
                'amount': final_amount,
                'currency': currency,
                'year': year,
                'type': cost_type,
                'raw_text': match.group(0).strip(),
                'confidence': self._calculate_confidence(match, context)
            }
            
        except Exception as e:
            logger.debug(f"Fehler beim Parsen von Match: {str(e)}")
            return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse Betrag aus String"""
        try:
            # Entferne Tausender-Trennzeichen
            amount_str = amount_str.replace(',', '')
            
            # Parse zu Float
            return float(amount_str)
            
        except ValueError:
            return None
    
    def _extract_currency(self, match_text: str, context: str) -> str:
        """Extrahiere Währung aus Match und Kontext"""
        text_to_search = (match_text + ' ' + context).lower()
        
        # Suche nach Währungen
        for indicator, currency in self.currency_map.items():
            if indicator in text_to_search:
                return currency
        
        # Default basierend auf Land (wenn verfügbar)
        if 'canada' in context.lower() or 'quebec' in context.lower():
            return 'CAD'
        elif 'united states' in context.lower() or 'usa' in context.lower():
            return 'USD'
        
        return 'USD'  # Default
    
    def _extract_unit(self, match_text: str, context: str) -> float:
        """Extrahiere Einheit (Million, Thousand, etc.)"""
        text_to_search = (match_text + ' ' + context).lower()
        
        for unit_name, multiplier in self.unit_multipliers.items():
            if unit_name in text_to_search:
                return multiplier
        
        # Wenn keine Einheit gefunden, prüfe Größenordnung
        # Wenn Zahl > 1000, nehme an es sind bereits volle Beträge
        # Wenn Zahl < 100, nehme an es sind Millionen
        try:
            amount = float(re.search(r'[\d,]+(?:\.\d+)?', match_text).group().replace(',', ''))
            if amount < 100:
                return 1_000_000  # Wahrscheinlich Millionen
            else:
                return 1  # Wahrscheinlich voller Betrag
        except:
            return 1
    
    def _extract_year(self, context: str) -> Optional[int]:
        """Extrahiere Jahr aus Kontext"""
        # Suche nach Jahren (1900-2099)
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        matches = re.findall(year_pattern, context)
        
        if matches:
            # Nimm das neueste Jahr
            years = [int(year) for year in matches]
            return max(years)
        
        return None
    
    def _determine_cost_type(self, context: str) -> str:
        """Bestimme Art der Kosten"""
        context_lower = context.lower()
        
        if 'aro' in context_lower or 'asset retirement' in context_lower:
            return 'ARO'
        elif 'closure' in context_lower:
            return 'closure_costs'
        elif 'environmental liabilit' in context_lower:
            return 'environmental_liability'
        elif 'rehabilitation' in context_lower or 'rehab' in context_lower:
            return 'rehabilitation'
        elif 'bond' in context_lower or 'guarantee' in context_lower:
            return 'financial_guarantee'
        elif 'provision' in context_lower:
            return 'provision'
        else:
            return 'restoration_costs'
    
    def _calculate_confidence(self, match: re.Match, context: str) -> float:
        """Berechne Konfidenz-Score für die Extraktion"""
        confidence = 0.5  # Basis
        
        # Bonus für klare Patterns
        if 'ARO' in match.group(0) or 'Asset Retirement Obligation' in match.group(0):
            confidence += 0.2
        
        # Bonus für Währungsangabe
        if any(curr in match.group(0) for curr in ['CAD', 'USD', 'EUR', '$']):
            confidence += 0.1
        
        # Bonus für Jahr
        if re.search(r'\b(19\d{2}|20\d{2})\b', context):
            confidence += 0.1
        
        # Bonus für Kontext-Keywords
        keywords = ['provision', 'liability', 'obligation', 'bond', 'guarantee']
        if any(kw in context.lower() for kw in keywords):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _select_best_finding(self, findings: List[Dict]) -> Dict:
        """Wähle das beste Ergebnis aus mehreren Findings"""
        if not findings:
            return {}
        
        # Sortiere nach Konfidenz und Betrag
        sorted_findings = sorted(
            findings,
            key=lambda x: (x['confidence'], x['amount']),
            reverse=True
        )
        
        best = sorted_findings[0]
        
        # Formatiere für Ausgabe
        formatted_amount = f"{best['currency']}${best['amount']:,.0f}"
        
        if best['amount'] >= 1_000_000:
            formatted_amount = f"{best['currency']}${best['amount']/1_000_000:.1f} million"
        elif best['amount'] >= 1_000:
            formatted_amount = f"{best['currency']}${best['amount']/1_000:.0f} thousand"
        
        result = {
            'restoration_costs': formatted_amount,
            'restoration_costs_raw': best['amount'],
            'restoration_costs_currency': best['currency'],
            'restoration_costs_type': best['type'],
            'restoration_costs_confidence': best['confidence']
        }
        
        if best['year']:
            result['restoration_costs_year'] = best['year']
            result['restoration_costs'] += f" ({best['year']})"
        
        return result