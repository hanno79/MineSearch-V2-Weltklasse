"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Data Extractors für Firecrawl Agent
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from ..base_agent import SearchResult, MineQuery


class FirecrawlDataExtractor:
    """Extrahiert Mining-Daten aus gecrawlten Inhalten"""
    
    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        self.agent_name = agent_name
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_from_content(self, content: str, source_url: str, 
                           query: MineQuery) -> List[SearchResult]:
        """Extrahiert Informationen aus Markdown-Content"""
        results = []
        
        if not content:
            return results
        
        # Verschiedene Extraktionsmethoden
        results.extend(self._extract_coordinates(content, source_url, query))
        results.extend(self._extract_operator(content, source_url, query))
        results.extend(self._extract_costs(content, source_url, query))
        results.extend(self._extract_status(content, source_url, query))
        results.extend(self._extract_production(content, source_url, query))
        results.extend(self._extract_commodity(content, source_url, query))
        
        return results
    
    def _extract_coordinates(self, content: str, source_url: str, 
                           query: MineQuery) -> List[SearchResult]:
        """Extrahiert GPS-Koordinaten"""
        results = []
        
        # Verschiedene Koordinaten-Formate
        patterns = [
            r'([-]?\d{1,3}\.\d+)[,\s]+([-]?\d{1,3}\.\d+)',  # Dezimal
            r'(\d{1,3}°\d+\'[\d.]+"?[NS])[,\s]+(\d{1,3}°\d+\'[\d.]+"?[EW])',  # DMS
            r'(?:lat|latitude)[:\s]*([-]?\d{1,3}\.\d+).*?(?:lon|longitude)[:\s]*([-]?\d{1,3}\.\d+)',
            r'(?:coordinates|koordinaten)[:\s]*([-]?\d{1,3}\.\d+)[,\s]+([-]?\d{1,3}\.\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        lat = match[0]
                        lon = match[1]
                        
                        # Validiere Koordinaten
                        try:
                            lat_val = float(re.sub(r'[^\d.-]', '', str(lat)))
                            lon_val = float(re.sub(r'[^\d.-]', '', str(lon)))
                            
                            if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                                results.append(SearchResult(
                                    mine_name=query.mine_name,
                                    field_name='koordinaten',
                                    value=f"{lat}, {lon}",
                                    source='Firecrawl Web Crawling',
                                    source_url=source_url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.agent_name,
                                    timestamp=datetime.now(),
                                    metadata={'format': 'GPS'}
                                ))
                                break
                        except ValueError:
                            continue
                
                if results:
                    break
        
        return results
    
    def _extract_operator(self, content: str, source_url: str, 
                         query: MineQuery) -> List[SearchResult]:
        """Extrahiert Betreiber/Eigentümer"""
        results = []
        
        # Suche nach Betreiber-Mustern
        patterns = [
            rf'{re.escape(query.mine_name)}.*?(?:operated by|owned by|betrieben von|gehört)\s+([A-Z][\w\s&.,()-]+?)(?:\.|,|;|\n|$)',
            rf'([A-Z][\w\s&.,()-]+?)\s+(?:operates|owns|betreibt|besitzt)\s+.*?{re.escape(query.mine_name)}',
            rf'(?:operator|owner|betreiber|eigentümer)[:\s]+([A-Z][\w\s&.,()-]+?)(?:\.|,|;|\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    operator = match.strip()
                    # Validiere Länge und Inhalt
                    if 3 < len(operator) < 100 and not any(word in operator.lower() for word in ['click', 'here', 'more', 'info']):
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='betreiber',
                            value=operator,
                            source='Firecrawl Web Crawling',
                            source_url=source_url,
                            source_date=datetime.now().year,
                            confidence_score=0.85,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={'extraction_method': 'pattern_matching'}
                        ))
                        break
                
                if results:
                    break
        
        return results
    
    def _extract_costs(self, content: str, source_url: str, 
                      query: MineQuery) -> List[SearchResult]:
        """Extrahiert Sanierungskosten"""
        results = []
        
        # Suche nach Kosten-Mustern
        cost_patterns = [
            r'(?:closure|remediation|sanierung|restoration).*?(?:cost|bond|kosten|rückstellung).*?(\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?)',
            r'(?:environmental|umwelt).*?(?:liability|bond|verpflichtung).*?(\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?)',
            r'(?:bond|financial assurance|sicherheit).*?(\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?)',
            r'(\$|CAD|USD|EUR)\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?).*?(?:closure|remediation|restoration)'
        ]
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    currency = match[0] if match[0] else 'CAD'
                    amount_str = match[1]
                    
                    # Parse Betrag
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if 'million' in amount_str.lower() or 'M' in amount_str:
                            amount *= 1_000_000
                        elif 'billion' in amount_str.lower() or 'B' in amount_str:
                            amount *= 1_000_000_000
                        
                        # Plausibilitätsprüfung
                        if 10_000 < amount < 10_000_000_000:
                            results.append(SearchResult(
                                mine_name=query.mine_name,
                                field_name='sanierungskosten',
                                value=f"{amount:,.0f} {currency}",
                                source='Firecrawl Web Crawling',
                                source_url=source_url,
                                source_date=datetime.now().year,
                                confidence_score=0.8,
                                agent_name=self.agent_name,
                                timestamp=datetime.now(),
                                metadata={'currency': currency, 'amount': amount}
                            ))
                            break
                    except ValueError:
                        continue
                
                if results:
                    break
        
        return results
    
    def _extract_status(self, content: str, source_url: str, 
                       query: MineQuery) -> List[SearchResult]:
        """Extrahiert Aktivitätsstatus"""
        results = []
        
        # Status-Keywords
        status_keywords = {
            'operating': 'aktiv',
            'active': 'aktiv',
            'producing': 'aktiv',
            'closed': 'geschlossen',
            'suspended': 'pausiert',
            'care and maintenance': 'wartung',
            'abandoned': 'aufgegeben',
            'inactive': 'inaktiv'
        }
        
        # Suche nach Status-Mustern
        patterns = [
            rf'{re.escape(query.mine_name)}.*?(?:is|remains|currently|status)\s+(\w+)',
            rf'(?:mine|operation|projekt)\s+(?:status|zustand)[:\s]+(\w+)',
            rf'(?:currently|derzeit|aktuell)\s+(operating|closed|suspended|active|inactive)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    status_word = match.lower()
                    # Prüfe gegen bekannte Status
                    for keyword, normalized in status_keywords.items():
                        if keyword in status_word:
                            results.append(SearchResult(
                                mine_name=query.mine_name,
                                field_name='aktivitaetsstatus',
                                value=normalized,
                                source='Firecrawl Web Crawling',
                                source_url=source_url,
                                source_date=datetime.now().year,
                                confidence_score=0.85,
                                agent_name=self.agent_name,
                                timestamp=datetime.now(),
                                metadata={'original_status': status_word}
                            ))
                            return results
        
        return results
    
    def _extract_production(self, content: str, source_url: str, 
                           query: MineQuery) -> List[SearchResult]:
        """Extrahiert Produktionsdaten"""
        results = []
        
        # Produktions-Muster
        patterns = [
            r'(?:annual production|jahresproduktion|yearly output).*?([\d,]+(?:\.\d+)?)\s*(tonnes?|tons?|ounces?|oz|kg)',
            r'([\d,]+(?:\.\d+)?)\s*(tonnes?|tons?|ounces?|oz|kg)\s*(?:per year|annually|jährlich)',
            r'(?:produces?|produziert|output).*?([\d,]+(?:\.\d+)?)\s*(tonnes?|tons?|ounces?|oz|kg)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    amount = match[0]
                    unit = match[1]
                    
                    results.append(SearchResult(
                        mine_name=query.mine_name,
                        field_name='jahresproduktion',
                        value=f"{amount} {unit}",
                        source='Firecrawl Web Crawling',
                        source_url=source_url,
                        source_date=datetime.now().year,
                        confidence_score=0.8,
                        agent_name=self.agent_name,
                        timestamp=datetime.now(),
                        metadata={'unit': unit}
                    ))
                    break
                
                if results:
                    break
        
        return results
    
    def _extract_commodity(self, content: str, source_url: str, 
                          query: MineQuery) -> List[SearchResult]:
        """Extrahiert Rohstofftyp"""
        results = []
        
        # Rohstoff-Keywords
        commodities = [
            'gold', 'silver', 'copper', 'zinc', 'lead', 'nickel',
            'iron', 'coal', 'uranium', 'lithium', 'cobalt',
            'platinum', 'palladium', 'diamond', 'graphite'
        ]
        
        # Suche nach Rohstoff-Mustern
        patterns = [
            rf'{re.escape(query.mine_name)}.*?(?:produces?|mines?|extracts?)\s+([\w\s,]+)',
            rf'(?:commodity|commodities|rohstoff|mineral)[:\s]+([\w\s,]+)',
            rf'(?:primary|haupt|main)\s+(?:commodity|rohstoff|mineral)[:\s]+([\w\s,]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Prüfe auf bekannte Rohstoffe
                    found_commodities = []
                    match_lower = match.lower()
                    for commodity in commodities:
                        if commodity in match_lower:
                            found_commodities.append(commodity.capitalize())
                    
                    if found_commodities:
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='rohstofftyp',
                            value=', '.join(found_commodities),
                            source='Firecrawl Web Crawling',
                            source_url=source_url,
                            source_date=datetime.now().year,
                            confidence_score=0.85,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={'commodities': found_commodities}
                        ))
                        break
                
                if results:
                    break
        
        return results
