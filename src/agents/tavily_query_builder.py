"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Query Builder für Tavily Agent - extrahiert aus tavily_agent.py
"""

import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
from src.agents.base_agent import MineQuery
from src.agents.enhanced_search import get_mining_search_queries, get_mining_domains
from src.agents.search_strategies import SearchStrategies
from src.core.logger import get_logger


class TavilyQueryBuilder:
    """Baut optimierte Suchanfragen für Tavily API"""
    
    def __init__(self):
        self.logger = get_logger("tavily_query_builder")
        self.search_builder = SearchStrategies()
        
    def optimize_query_length(self, query: str, max_length: int = 395) -> str:
        """
        Optimiert die Query-Länge für Tavily API (max 400 chars)
        ÄNDERUNG 25.06.2025: Verbesserte Query-Optimierung mit mehreren Strategien
        """
        if len(query) <= max_length:
            return query
            
        # 1. Entferne Redundanzen
        query = self._remove_redundancies(query)
        
        if len(query) <= max_length:
            return query
            
        # 2. Extrahiere wichtigste Komponenten
        components = self._extract_query_components(query)
        
        # 3. Baue Query neu auf mit Prioritäten
        optimized = self._rebuild_query(components, max_length)
        
        self.logger.debug(f"Query optimiert von {len(query)} auf {len(optimized)} Zeichen")
        return optimized
    
    def clean_query(self, query: str) -> str:
        """Bereinigt Query von problematischen Zeichen"""
        # Entferne mehrfache Leerzeichen
        query = re.sub(r'\s+', ' ', query)
        # Entferne problematische Zeichen
        query = re.sub(r'[<>{}|\[\]\\]', '', query)
        return query.strip()
    
    def _remove_redundancies(self, query: str) -> str:
        """Entfernt redundante Begriffe und Phrasen"""
        # Entferne wiederholte Wörter
        words = query.split()
        seen = set()
        unique_words = []
        
        for word in words:
            # Behalte Stoppwörter und kurze Wörter
            if len(word) <= 3 or word.lower() not in seen:
                unique_words.append(word)
                if len(word) > 3:
                    seen.add(word.lower())
        
        # Entferne redundante Phrasen
        query = ' '.join(unique_words)
        
        # Entferne wiederholte Phrasen wie "mining mine", "gold gold"
        query = re.sub(r'\b(\w+)\s+\1\b', r'\1', query, flags=re.IGNORECASE)
        
        return query
    
    def _extract_query_components(self, query: str) -> dict:
        """Extrahiert wichtige Komponenten aus der Query"""
        components = {
            'mine_name': None,
            'location': [],
            'keywords': [],
            'operators': [],
            'modifiers': []
        }
        
        # Extrahiere Mine-Namen (in Anführungszeichen)
        quoted = re.findall(r'"([^"]+)"', query)
        if quoted:
            components['mine_name'] = quoted[0]
            query = query.replace(f'"{quoted[0]}"', '')
        
        # Extrahiere Orte (Länder, Provinzen)
        locations = ['Canada', 'Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                    'Saskatchewan', 'Manitoba', 'Yukon', 'Alaska', 'USA']
        for loc in locations:
            if loc in query:
                components['location'].append(loc)
                query = query.replace(loc, '')
        
        # Extrahiere Operatoren
        operators = ['AND', 'OR', 'NOT']
        for op in operators:
            if f' {op} ' in query:
                components['operators'].append(op)
                query = query.replace(f' {op} ', ' ')
        
        # Extrahiere wichtige Keywords
        keywords = ['mine', 'mining', 'operator', 'owner', 'coordinates', 'GPS', 
                   'production', 'gold', 'copper', 'iron', 'status', 'active', 
                   'closed', 'environmental', 'closure', 'rehabilitation']
        
        for kw in keywords:
            if kw.lower() in query.lower():
                components['keywords'].append(kw)
        
        # Rest sind Modifikatoren
        remaining = query.strip().split()
        components['modifiers'] = [w for w in remaining if len(w) > 2]
        
        return components
    
    def _rebuild_query(self, components: dict, max_length: int) -> str:
        """Baut Query mit Prioritäten neu auf"""
        query_parts = []
        current_length = 0
        
        # 1. Priorität: Mine Name
        if components['mine_name']:
            mine_part = f'"{components["mine_name"]}"'
            if current_length + len(mine_part) + 1 <= max_length:
                query_parts.append(mine_part)
                current_length += len(mine_part) + 1
        
        # 2. Priorität: Wichtigste Keywords (erste 3-4)
        for kw in components['keywords'][:4]:
            if current_length + len(kw) + 1 <= max_length:
                query_parts.append(kw)
                current_length += len(kw) + 1
        
        # 3. Priorität: Orte
        for loc in components['location'][:2]:
            if current_length + len(loc) + 1 <= max_length:
                query_parts.append(loc)
                current_length += len(loc) + 1
        
        # 4. Priorität: Operatoren mit Keywords
        if components['operators'] and len(query_parts) > 1:
            # Füge AND zwischen wichtigen Begriffen ein
            temp_parts = []
            for i, part in enumerate(query_parts):
                temp_parts.append(part)
                if i < len(query_parts) - 1 and current_length + 5 <= max_length:
                    temp_parts.append('AND')
                    current_length += 4
            query_parts = temp_parts
        
        return ' '.join(query_parts)
    
    def create_query_hash(self, query: str) -> str:
        """Erstellt einen Hash für Cache-Zwecke"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def create_search_queries(self, query: MineQuery) -> Dict[str, str]:
        """Erstellt optimierte Suchanfragen für verschiedene Suchstrategien"""
        queries = {}
        
        # ÄNDERUNG 27.06.2025: Extrahiert aus tavily_agent.py
        # Basis-Informationen
        mine_terms = [query.mine_name]
        if ' ' not in query.mine_name:
            mine_terms.extend([
                f"{query.mine_name} Mine",
                f"{query.mine_name} Project"
            ])
        
        # 1. Direkte Betreiber-Suche
        operator_query = self.search_builder.create_operator_query(
            mine_terms, query.region, query.country
        )
        queries['operator'] = self.optimize_query_length(operator_query)
        
        # 2. Koordinaten-Suche
        coords_query = self.search_builder.create_coordinates_query(
            mine_terms, query.region, query.country
        )
        queries['coordinates'] = self.optimize_query_length(coords_query)
        
        # 3. Status-Suche
        status_query = self.search_builder.create_status_query(
            mine_terms, query.region, query.country
        )
        queries['status'] = self.optimize_query_length(status_query)
        
        # 4. Produktions-Suche
        production_query = self.search_builder.create_production_query(
            mine_terms, query.region, query.country
        )
        queries['production'] = self.optimize_query_length(production_query)
        
        # 5. Umwelt/Kosten-Suche
        environmental_query = self.search_builder.create_environmental_query(
            mine_terms, query.region, query.country
        )
        queries['environmental'] = self.optimize_query_length(environmental_query)
        
        # 6. Regierungsdatenbank-Suche (für Kanada)
        if query.country.lower() == 'canada':
            gov_query = self._create_government_query(query)
            queries['government'] = self.optimize_query_length(gov_query)
        
        # 7. Nachrichten-Suche
        news_query = f'"{query.mine_name}" {query.region} latest news updates 2024 2025'
        queries['news'] = self.optimize_query_length(news_query)
        
        return queries
    
    def _create_government_query(self, query: MineQuery) -> str:
        """Erstellt spezielle Suchanfrage für Regierungsdatenbanken"""
        if query.region.lower() == 'quebec':
            return f'"{query.mine_name}" GESTIM Quebec MERN mining claims registry'
        elif query.region.lower() == 'ontario':
            return f'"{query.mine_name}" Ontario mining lands administration MLAS'
        else:
            return f'"{query.mine_name}" {query.region} mining registry government database'