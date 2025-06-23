"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Result Parser für Exa Search
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..base_agent import MineQuery, SearchResult
from src.core.logger import get_logger

class ExaResultParser:
    """Parst und extrahiert Daten aus Exa Search Results"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Initialisiert Regex-Patterns für Datenextraktion"""
        return {
            'betreiber': [
                re.compile(r'operated\s+by\s+([A-Za-z0-9\s\.\&\-,]+?)(?:\s*[,\.]|\s*\n)', re.IGNORECASE),
                re.compile(r'operator:\s*([A-Za-z0-9\s\.\&\-,]+?)(?:\s*[,\.]|\s*\n)', re.IGNORECASE),
                re.compile(r'([A-Za-z0-9\s\.\&\-]+?)\s+(?:operates|owns)\s+the\s+mine', re.IGNORECASE)
            ],
            'koordinaten': [
                re.compile(r'coordinates?:\s*([-\d\.]+)[,\s]+([-\d\.]+)', re.IGNORECASE),
                re.compile(r'located\s+at\s+([-\d\.]+)[,\s]+([-\d\.]+)', re.IGNORECASE),
                re.compile(r'GPS:\s*([-\d\.]+)[,\s]+([-\d\.]+)', re.IGNORECASE)
            ],
            'aktivitaetsstatus': [
                re.compile(r'status:\s*(\w+)', re.IGNORECASE),
                re.compile(r'currently\s+(\w+)', re.IGNORECASE),
                re.compile(r'mine\s+is\s+(\w+)', re.IGNORECASE)
            ],
            'jahresproduktion': [
                re.compile(r'annual\s+production:?\s*([0-9,\.]+\s*(?:tonnes?|tons?|mt|kt)?)', re.IGNORECASE),
                re.compile(r'produces?\s+([0-9,\.]+\s*(?:tonnes?|tons?|mt|kt)?\s*(?:per\s+year|annually)?)', re.IGNORECASE)
            ],
            'sanierungskosten': [
                re.compile(r'closure\s+cost:?\s*\$?([0-9,\.]+\s*(?:million|M)?)', re.IGNORECASE),
                re.compile(r'rehabilitation\s+cost:?\s*\$?([0-9,\.]+\s*(?:million|M)?)', re.IGNORECASE),
                re.compile(r'environmental\s+bond:?\s*\$?([0-9,\.]+\s*(?:million|M)?)', re.IGNORECASE)
            ],
            'rohstofftyp': [
                re.compile(r'commodit(?:y|ies):\s*([^\n,]+(?:,\s*[^\n,]+)*)', re.IGNORECASE),
                re.compile(r'produces?\s+([^\n,]+(?:,\s*[^\n,]+)*)', re.IGNORECASE),
                re.compile(r'mining\s+([^\n,]+(?:,\s*[^\n,]+)*)', re.IGNORECASE)
            ]
        }
    
    def parse_results(self, exa_response: Dict[str, Any], query: MineQuery, 
                     query_type: str) -> List[SearchResult]:
        """Parst Exa Response und extrahiert SearchResults"""
        results = []
        
        if not exa_response or 'results' not in exa_response:
            return results
        
        for result in exa_response['results']:
            # Extrahiere relevante Daten aus jedem Ergebnis
            extracted_data = self._extract_data_from_result(result, query)
            
            for field_name, value in extracted_data.items():
                if value:
                    search_result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field_name,
                        value=value,
                        source=result.get('title', 'Exa Search'),
                        source_url=result.get('url', ''),
                        source_date=self._extract_date(result),
                        confidence_score=self._calculate_confidence(result, field_name),
                        agent_name="exa",
                        timestamp=datetime.now(),
                        metadata={
                            'query_type': query_type,
                            'score': result.get('score', 0),
                            'snippet': result.get('snippet', '')
                        }
                    )
                    results.append(search_result)
        
        return results
    
    def _extract_data_from_result(self, result: Dict[str, Any], 
                                 query: MineQuery) -> Dict[str, str]:
        """Extrahiert Daten aus einem einzelnen Suchergebnis"""
        extracted = {}
        
        # Kombiniere Title, Snippet und Text für Suche
        searchable_text = self._get_searchable_text(result)
        
        # Durchsuche mit allen Patterns
        for field_name, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(searchable_text)
                if match:
                    if field_name == 'koordinaten' and len(match.groups()) >= 2:
                        value = f"{match.group(1)}, {match.group(2)}"
                    else:
                        value = match.group(1).strip()
                    
                    extracted[field_name] = value
                    break  # Nur erstes Match pro Feld
        
        return extracted
    
    def _get_searchable_text(self, result: Dict[str, Any]) -> str:
        """Kombiniert alle durchsuchbaren Textfelder"""
        text_parts = []
        
        if 'title' in result:
            text_parts.append(result['title'])
        
        if 'snippet' in result:
            text_parts.append(result['snippet'])
        
        if 'text' in result:
            # Begrenzen auf ersten Teil des Texts
            text_parts.append(result['text'][:2000])
        
        if 'highlights' in result:
            text_parts.extend(result['highlights'])
        
        return '\n'.join(text_parts)
    
    def _extract_date(self, result: Dict[str, Any]) -> int:
        """Extrahiert Datum aus Ergebnis"""
        # Exa gibt oft publishedDate
        if 'publishedDate' in result:
            try:
                date_str = result['publishedDate']
                year_match = re.search(r'20\d{2}', date_str)
                if year_match:
                    return int(year_match.group())
            except:
                pass
        
        # Fallback auf aktuelles Jahr
        return datetime.now().year
    
    def _calculate_confidence(self, result: Dict[str, Any], field_name: str) -> float:
        """Berechnet Konfidenz-Score basierend auf verschiedenen Faktoren"""
        confidence = 0.5  # Basis-Konfidenz
        
        # Erhöhe für hohen Exa-Score
        if 'score' in result:
            confidence += min(result['score'] * 0.3, 0.3)
        
        # Erhöhe für offizielle Domains
        url = result.get('url', '')
        if any(domain in url for domain in ['.gov', '.org', '.edu']):
            confidence += 0.2
        
        # Erhöhe für Mining-spezifische Domains
        mining_domains = ['mining', 'mineral', 'geology', 'resources']
        if any(domain in url.lower() for domain in mining_domains):
            confidence += 0.1
        
        # Begrenze auf Maximum von 1.0
        return min(confidence, 1.0)