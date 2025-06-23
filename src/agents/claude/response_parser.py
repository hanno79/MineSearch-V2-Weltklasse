"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Response Parser für Claude Agent
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..base_agent import SearchResult, MineQuery


class ClaudeResponseParser:
    """Parst und verarbeitet Claude-Antworten"""
    
    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        self.agent_name = agent_name
        self.logger = logger or logging.getLogger(__name__)
        
        # Feld-Mappings
        self.field_mappings = {
            'operator': 'betreiber',
            'owner': 'betreiber',
            'coordinates': 'koordinaten',
            'gps': 'koordinaten',
            'location': 'koordinaten',
            'environmental costs': 'sanierungskosten',
            'closure costs': 'sanierungskosten',
            'remediation costs': 'sanierungskosten',
            'restoration costs': 'sanierungskosten',
            'bond amount': 'sanierungskosten',
            'status': 'aktivitaetsstatus',
            'operational status': 'aktivitaetsstatus',
            'production': 'produktionsdaten',
            'annual production': 'jahresproduktion',
            'commodity': 'rohstofftyp',
            'commodities': 'rohstofftyp',
            'area': 'flaeche',
            'employees': 'mitarbeiter',
            'depth': 'tiefe',
            'founded': 'gruendungsjahr',
            'closed': 'schliessungsjahr'
        }
    
    def parse_response(self, response: str, query: MineQuery, 
                      prompt_type: str) -> List[SearchResult]:
        """Parst Claude-Response und extrahiert strukturierte Daten"""
        results = []
        
        if not response:
            return results
        
        # ÄNDERUNG 21.06.2025: Verbesserte Extraktion
        lines = response.split('\n')
        current_field = None
        current_value = None
        current_source = None
        current_year = None
        current_confidence = 0.8
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Suche nach Feld-Mustern
            field_match = re.match(r'^([^:]+):\s*(.+)$', line)
            if field_match:
                field_name = field_match.group(1).lower().strip()
                value = field_match.group(2).strip()
                
                # Normalisiere Feldname
                normalized_field = self._normalize_field_name(field_name)
                
                if normalized_field:
                    # Speichere vorherigen Eintrag
                    if current_field and current_value:
                        results.append(self._create_result(
                            query, current_field, current_value,
                            current_source, current_year, current_confidence
                        ))
                    
                    current_field = normalized_field
                    current_value = value
                    current_source = None
                    current_year = None
                    
                elif 'source' in field_name:
                    current_source = value
                elif 'year' in field_name:
                    current_year = self._extract_year(value)
                elif 'confidence' in field_name:
                    current_confidence = self._parse_confidence(value)
        
        # Speichere letzten Eintrag
        if current_field and current_value:
            results.append(self._create_result(
                query, current_field, current_value,
                current_source, current_year, current_confidence
            ))
        
        # Falls keine strukturierten Daten, versuche Freitext-Extraktion
        if not results:
            results.extend(self._extract_from_freetext(response, query, prompt_type))
        
        self.logger.info(f"Claude Parser: {len(results)} Ergebnisse extrahiert")
        return results
    
    def _normalize_field_name(self, field_name: str) -> Optional[str]:
        """Normalisiert Feldnamen zu Standard-Feldnamen"""
        field_lower = field_name.lower()
        
        # Direkte Mappings
        for key, mapped in self.field_mappings.items():
            if key in field_lower:
                return mapped
        
        # Fuzzy Matching für deutsche Begriffe
        german_mappings = {
            'betreiber': ['betreiber', 'eigent', 'operator', 'owner'],
            'koordinaten': ['koordinat', 'gps', 'position', 'lage'],
            'sanierungskosten': ['sanier', 'kosten', 'bond', 'rückstellung'],
            'aktivitaetsstatus': ['status', 'betrieb', 'aktiv'],
            'produktionsdaten': ['produktion', 'förder', 'output'],
            'rohstofftyp': ['rohstoff', 'mineral', 'commodity'],
            'flaeche': ['fläche', 'area', 'größe', 'hektar']
        }
        
        for standard_field, keywords in german_mappings.items():
            if any(keyword in field_lower for keyword in keywords):
                return standard_field
        
        return None
    
    def _extract_from_freetext(self, text: str, query: MineQuery, 
                              prompt_type: str) -> List[SearchResult]:
        """Extrahiert Informationen aus Freitext"""
        results = []
        
        # Koordinaten-Extraktion
        coord_patterns = [
            r'([-]?\d{1,3}\.\d+)[,\s]+([-]?\d{1,3}\.\d+)',
            r'(\d{1,3}°\d+\'[\d.]+"?[NS])[,\s]+(\d{1,3}°\d+\'[\d.]+"?[EW])',
            r'lat(?:itude)?[:\s]+([-]?\d{1,3}\.\d+).*?lon(?:gitude)?[:\s]+([-]?\d{1,3}\.\d+)'
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    coord_str = f"{match[0]}, {match[1]}" if isinstance(match, tuple) else match
                    results.append(self._create_result(
                        query, 'koordinaten', coord_str,
                        'Claude-Extraktion', datetime.now().year, 0.85
                    ))
                break
        
        # Kosten-Extraktion
        cost_patterns = [
            r'(\$|CAD|USD|EUR)\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?)',
            r'([\d,]+(?:\.\d{2})?)\s*(\$|CAD|USD|EUR)(?:\s*(?:million|billion|M|B))?',
            r'(?:bond|closure|remediation|restoration).*?([\d,]+(?:\.\d{2})?)\s*(?:million|billion|M|B)?'
        ]
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Verarbeite Match basierend auf Muster
                    if isinstance(match, tuple):
                        if match[0] in ['$', 'CAD', 'USD', 'EUR']:
                            value = f"{match[1]} {match[0]}"
                        else:
                            value = f"{match[0]} {match[1] if len(match) > 1 else 'CAD'}"
                    else:
                        value = f"{match} CAD"
                    
                    # Prüfe ob im Kontext von Kosten
                    context = text[max(0, text.find(str(match[0]))-100):text.find(str(match[0]))+100]
                    if any(word in context.lower() for word in ['closure', 'bond', 'remediation', 'restoration', 'environmental']):
                        results.append(self._create_result(
                            query, 'sanierungskosten', value,
                            'Claude-Extraktion', datetime.now().year, 0.75
                        ))
        
        # Betreiber-Extraktion
        if query.mine_name in text:
            operator_patterns = [
                rf'{re.escape(query.mine_name)}.*?(?:operated by|owned by|belongs to)\s+([A-Z][\w\s&.,()-]+?)(?:\.|,|;|\n)',
                rf'([A-Z][\w\s&.,()-]+?)\s+(?:operates|owns|manages)\s+.*?{re.escape(query.mine_name)}'
            ]
            
            for pattern in operator_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        operator = match.strip()
                        if len(operator) > 3 and len(operator) < 100:
                            results.append(self._create_result(
                                query, 'betreiber', operator,
                                'Claude-Extraktion', datetime.now().year, 0.8
                            ))
        
        return results
    
    def _create_result(self, query: MineQuery, field_name: str, value: str,
                      source: Optional[str], year: Optional[int], 
                      confidence: float) -> SearchResult:
        """Erstellt SearchResult-Objekt"""
        return SearchResult(
            mine_name=query.mine_name,
            field_name=field_name,
            value=value,
            source=source or 'Claude AI Analysis',
            source_url='OpenRouter API',
            source_date=year or datetime.now().year,
            confidence_score=confidence,
            agent_name=self.agent_name,
            timestamp=datetime.now(),
            metadata={
                'model': 'claude-3-opus',
                'extraction_method': 'ai_analysis'
            }
        )
    
    def _extract_year(self, value: str) -> Optional[int]:
        """Extrahiert Jahr aus String"""
        year_match = re.search(r'(19\d{2}|20\d{2})', value)
        if year_match:
            return int(year_match.group(1))
        return None
    
    def _parse_confidence(self, value: str) -> float:
        """Parst Konfidenz-Level"""
        value_lower = value.lower()
        if 'high' in value_lower:
            return 0.9
        elif 'medium' in value_lower:
            return 0.7
        elif 'low' in value_lower:
            return 0.5
        else:
            # Versuche numerischen Wert
            try:
                conf = float(re.search(r'\d+\.?\d*', value).group())
                return min(1.0, conf / 100 if conf > 1 else conf)
            except:
                return 0.8
