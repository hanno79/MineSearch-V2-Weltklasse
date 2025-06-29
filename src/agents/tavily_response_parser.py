"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Response Parser für Tavily Agent - extrahiert aus tavily_agent.py
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from src.agents.base_agent import MineQuery, SearchResult
from src.core.logger import get_logger
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list


class TavilyResponseParser:
    """Parst Tavily API Responses und extrahiert strukturierte Daten"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"tavily_parser.{agent_name}")
        
    def parse_response(self, response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Tavily-Response und extrahiert strukturierte Daten"""
        results = []
        
        # ÄNDERUNG 27.06.2025: Extrahiert aus tavily_agent.py
        # 1. Versuche strukturierte Antwort zu parsen (answer field)
        answer = safe_get(response, 'answer', '')
        if answer:
            answer_results = self._extract_from_answer(answer, query)
            results.extend(answer_results)
        
        # 2. Parse einzelne Suchergebnisse
        search_results = ensure_list(safe_get(response, 'results', []))
        
        for idx, result in enumerate(search_results[:10]):  # Max 10 Ergebnisse
            if not isinstance(result, dict):
                continue
                
            url = safe_get(result, 'url', '')
            content = safe_get(result, 'content', '')
            
            if content:
                content_results = self._extract_from_content(content, url, query)
                results.extend(content_results)
        
        # Deduplizierung
        seen = set()
        unique_results = []
        for result in results:
            key = f"{result.field_name}:{result.value}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def _extract_from_answer(self, answer: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Informationen aus dem strukturierten Answer-Feld"""
        results = []
        
        # Patterns für verschiedene Datentypen
        patterns = {
            'betreiber': [
                r'operated by\s+([A-Za-z0-9\s\-\.&,]+?)(?:\s*\(|,|\.|$)',
                r'operator[:\s]+([A-Za-z0-9\s\-\.&,]+?)(?:\s*\(|,|\.|$)',
                r'owned by\s+([A-Za-z0-9\s\-\.&,]+?)(?:\s*\(|,|\.|$)',
                r'([A-Za-z0-9\s\-\.&,]+?)\s+operates\s+the\s+mine'
            ],
            'koordinaten': [
                r'coordinates[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'latitude[:\s]*([-\d\.]+).*longitude[:\s]*([-\d\.]+)',
                r'([-\d\.]+)°[NS][,\s]+([-\d\.]+)°[EW]'
            ],
            'aktivitaetsstatus': [
                r'status[:\s]+(active|closed|suspended|care and maintenance|exploration)',
                r'currently\s+(active|closed|suspended|operating|non-operating)',
                r'mine is\s+(active|closed|suspended|operational)',
                r'(active|closed|suspended)\s+mine'
            ]
        }
        
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.finditer(pattern, answer, re.IGNORECASE)
                for match in matches:
                    value = match.group(1)
                    if len(match.groups()) > 1:  # Für Koordinaten
                        value = f"{match.group(1)}, {match.group(2)}"
                    
                    # Bereinige Wert
                    value = value.strip()
                    if value and len(value) > 2:
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=value,
                            source="Tavily AI Answer",
                            source_url="",
                            source_date=datetime.now().year,
                            confidence_score=0.85,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={'search_type': 'answer_extraction'}
                        )
                        results.append(result)
                        break  # Nur ersten Match pro Feld
        
        return results
    
    def _extract_from_content(self, content: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Informationen aus Suchergebnis-Content"""
        results = []
        
        # Domain für Quellen-Info
        domain = urlparse(url).netloc if url else "Unknown"
        
        # Erweiterte Patterns für Content-Extraktion
        patterns = {
            'betreiber': [
                r'(?:owned|operated|managed)\s+by\s+([A-Z][A-Za-z0-9\s\-\.&,]+?)(?:\s*\(|,|\.|;|$)',
                r'([A-Z][A-Za-z0-9\s\-\.&,]+?)\s+(?:owns|operates|manages)\s+(?:the\s+)?(?:' + re.escape(query.mine_name) + ')',
                r'operator[:\s]+([A-Z][A-Za-z0-9\s\-\.&,]+?)(?:\s*\(|,|\.|;|$)'
            ],
            'koordinaten': [
                r'coordinates?[:\s]*([-\d\.]+°?[NS]?)[,\s]+([-\d\.]+°?[EW]?)',
                r'lat(?:itude)?[:\s]*([-\d\.]+).*?lon(?:gitude)?[:\s]*([-\d\.]+)',
                r'location[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)'
            ],
            'aktivitaetsstatus': [
                r'(?:mine\s+)?status[:\s]+(active|closed|suspended|care\s+and\s+maintenance|exploration|development)',
                r'(?:currently\s+|is\s+)?(active|closed|suspended|operating|non-operating|producing)',
                r'(ceased|suspended|resumed|started)\s+(?:operations|production|mining)'
            ],
            'sanierungskosten': [
                r'closure\s+(?:cost|bond)[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                r'rehabilitation\s+(?:cost|bond)[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                r'environmental\s+bond[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?'
            ],
            'rohstofftyp': [
                r'produc(?:es|ing|tion)\s+(?:of\s+)?(gold|silver|copper|zinc|lead|iron|nickel|uranium|diamonds?)',
                r'(gold|silver|copper|zinc|lead|iron|nickel|uranium|diamonds?)\s+(?:mine|project|deposit)',
                r'mining\s+(?:for\s+)?(gold|silver|copper|zinc|lead|iron|nickel|uranium|diamonds?)'
            ]
        }
        
        # Prüfe ob Content relevant für die Mine ist
        mine_mentioned = any(term.lower() in content.lower() for term in [query.mine_name, query.mine_name.replace(' ', '')])
        
        if not mine_mentioned and len(content) < 100:
            return results
        
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value = match.group(1)
                    if len(match.groups()) > 1:  # Für Koordinaten
                        value = f"{match.group(1)}, {match.group(2)}"
                    
                    # Bereinige und validiere Wert
                    value = self._clean_extracted_value(value, field_name)
                    
                    if value and self._validate_extraction(value, field_name):
                        # Confidence basierend auf Quelle
                        confidence = 0.7
                        if mine_mentioned:
                            confidence += 0.1
                        if any(gov in domain for gov in ['gov', 'gouv', 'gc.ca']):
                            confidence += 0.1
                        
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=value,
                            source=domain,
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=confidence,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={
                                'search_type': 'content_extraction',
                                'url': url
                            }
                        )
                        results.append(result)
                        break  # Nur ersten validen Match pro Feld
        
        return results
    
    def _clean_extracted_value(self, value: str, field_name: str) -> str:
        """Bereinigt extrahierte Werte"""
        if not value:
            return ""
        
        # Entferne überschüssige Whitespaces
        value = ' '.join(value.split())
        
        # Feld-spezifische Bereinigung
        if field_name == 'betreiber':
            # Entferne trailing Punkte, Kommata
            value = value.rstrip('.,;')
            # Entferne "Ltd", "Inc" etc. wenn am Ende in Klammern
            value = re.sub(r'\s*\((?:Ltd|Inc|Corp|Limited|Corporation)\)$', '', value)
        
        elif field_name == 'koordinaten':
            # Normalisiere Koordinatenformat
            value = re.sub(r'°', '', value)
            value = re.sub(r'[NS]', '', value)
            value = re.sub(r'[EW]', '', value)
            value = value.strip()
        
        elif field_name == 'aktivitaetsstatus':
            # Normalisiere Status
            value = value.lower()
            if 'care' in value and 'maintenance' in value:
                value = 'care and maintenance'
        
        elif field_name == 'sanierungskosten':
            # Normalisiere Zahlenformat
            value = value.replace(',', '')
            if 'million' in value.lower() or 'M' in value:
                value = value.replace('million', 'M').replace('Million', 'M')
        
        return value.strip()
    
    def _validate_extraction(self, value: str, field_name: str) -> bool:
        """Validiert extrahierte Werte"""
        if not value or len(value) < 2:
            return False
        
        # Feld-spezifische Validierung
        if field_name == 'betreiber':
            # Muss mit Großbuchstaben beginnen
            if not re.match(r'^[A-Z]', value):
                return False
            # Mindestlänge
            if len(value) < 3:
                return False
            # Keine reinen Zahlen
            if value.isdigit():
                return False
        
        elif field_name == 'koordinaten':
            # Muss Zahlen enthalten
            if not re.search(r'\d', value):
                return False
            # Muss Komma oder Leerzeichen als Trenner haben
            if ',' not in value and ' ' not in value:
                return False
        
        elif field_name == 'aktivitaetsstatus':
            # Muss bekannter Status sein
            valid_statuses = ['active', 'closed', 'suspended', 'operating', 
                            'non-operating', 'care and maintenance', 'exploration',
                            'development', 'producing']
            if value.lower() not in valid_statuses:
                return False
        
        elif field_name == 'sanierungskosten':
            # Muss Zahlen enthalten
            if not re.search(r'\d', value):
                return False
        
        return True