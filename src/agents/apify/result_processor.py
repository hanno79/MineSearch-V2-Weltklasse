"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Apify Ergebnis-Verarbeitung und Datenextraktion
"""

import re
from typing import List, Dict, Any
from datetime import datetime

from ..base_agent import SearchResult, MineQuery
from src.core.logger import get_logger


class ApifyResultProcessor:
    """Verarbeitet und extrahiert Daten aus Apify-Ergebnissen"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger("apify.processor")
        
        # Pattern-Definitionen für Textextraktion
        self.text_patterns = {
            'betreiber': r'(?:operated by|operator|owner)[:\s]+([A-Za-z0-9\s&.,()-]+?)(?:\.|,|\n)',
            'sanierungskosten': r'(?:restoration|rehabilitation|closure)\s*(?:cost|bond)[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
            'rohstofftyp': r'(?:commodit\w+|mineral\w*|produces?)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,|\n)',
            'jahresproduktion': r'(?:annual production|produces?)[:\s]*([\d,\.]+)\s*(?:tonnes?|ounces?|oz)',
            'koordinaten': r'(?:coordinates?|location)[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)'
        }
        
        # Header-Mapping für Tabellenextraktion
        self.header_mapping = {
            'operator': 'betreiber',
            'owner': 'betreiber',
            'commodity': 'rohstofftyp',
            'commodities': 'rohstofftyp',
            'production': 'jahresproduktion',
            'annual production': 'jahresproduktion',
            'restoration': 'sanierungskosten',
            'rehabilitation': 'sanierungskosten',
            'closure cost': 'sanierungskosten',
            'employees': 'mitarbeiter',
            'workforce': 'mitarbeiter',
            'area': 'flaeche',
            'size': 'flaeche'
        }
        
        # GESTIM Feld-Mapping
        self.gestim_field_mapping = {
            'Titulaire': 'betreiber',
            'Coordonnées': 'koordinaten',
            'Superficie': 'flaeche',
            'Substances': 'rohstofftyp',
            'Statut': 'aktivitaetsstatus'
        }
    
    def is_relevant_url(self, url: str, query: MineQuery) -> bool:
        """Prüft ob URL relevant für Mining-Recherche ist"""
        # Bevorzuge offizielle Quellen
        preferred_domains = [
            'gov.ca', 'gc.ca', 'gouv.qc.ca',
            'mining.com', 'mining-technology.com',
            'nrcan.gc.ca', 'mern.gouv.qc.ca',
            'sedar.com'
        ]
        
        # Vermeide Social Media und unrelevante Seiten
        avoid_domains = [
            'facebook.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'wikipedia.org', 'reddit.com'
        ]
        
        url_lower = url.lower()
        
        # Prüfe auf vermeidbare Domains
        for domain in avoid_domains:
            if domain in url_lower:
                return False
        
        # Prüfe auf bevorzugte Domains
        for domain in preferred_domains:
            if domain in url_lower:
                return True
        
        # Prüfe auf Mining-relevante Keywords
        mining_keywords = ['mining', 'mine', 'mineral', 'resources', 'extraction']
        return any(keyword in url_lower for keyword in mining_keywords)
    
    def extract_from_scraped_data(self, data: Dict[str, Any], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert strukturierte Daten aus gescrapten Inhalten"""
        results = []
        
        text = data.get('text', '')
        tables = data.get('tables', [])
        
        # Text-basierte Extraktion
        text_results = self.extract_from_text(text, url, query)
        results.extend(text_results)
        
        # Tabellen-basierte Extraktion
        for table in tables:
            table_results = self.extract_from_table(table, url, query)
            results.extend(table_results)
        
        return results
    
    def extract_from_text(self, text: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Text"""
        results = []
        
        for field_name, pattern in self.text_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if field_name == 'koordinaten' and len(match.groups()) > 1:
                    value = f"{match.group(1)}, {match.group(2)}"
                
                result = SearchResult(
                    mine_name=query.mine_name,
                    field_name=field_name,
                    value=value,
                    source=f"Apify: {url.split('/')[2]}",
                    source_url=url,
                    source_date=datetime.now().year,
                    confidence_score=0.7,
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={}
                )
                results.append(result)
                self.logger.info(f"Gefunden via Text: {field_name} = {value}")
        
        return results
    
    def extract_from_table(self, table: List[List[str]], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Tabellen"""
        results = []
        
        if not table or len(table) < 2:
            return results
        
        # Versuche Header zu identifizieren
        headers = [h.lower() for h in table[0]]
        
        # Durchsuche Tabelle
        for row_idx in range(1, min(len(table), 10)):  # Max 10 Zeilen
            row = table[row_idx]
            
            for col_idx, header in enumerate(headers):
                if col_idx < len(row):
                    for header_key, field_name in self.header_mapping.items():
                        if header_key in header:
                            value = row[col_idx].strip()
                            if value and value.lower() not in ['n/a', 'na', '-', '']:
                                result = SearchResult(
                                    mine_name=query.mine_name,
                                    field_name=field_name,
                                    value=value,
                                    source=f"Apify Table: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.agent_name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                )
                                results.append(result)
                                self.logger.info(f"Gefunden via Tabelle: {field_name} = {value}")
                                break
        
        return results
    
    def parse_gestim_data(self, data: Dict[str, Any], query: MineQuery) -> List[SearchResult]:
        """Parst GESTIM-spezifische Daten"""
        results = []
        
        content = data.get('content', {})
        
        for gestim_field, our_field in self.gestim_field_mapping.items():
            if gestim_field in content:
                value = content[gestim_field]
                result = SearchResult(
                    mine_name=query.mine_name,
                    field_name=our_field,
                    value=value,
                    source="GESTIM Quebec",
                    source_url="https://gestim.mines.gouv.qc.ca",
                    source_date=datetime.now().year,
                    confidence_score=0.9,
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={}
                )
                results.append(result)
                self.logger.info(f"GESTIM Fund: {our_field} = {value}")
        
        return results
    
    def extract_urls_from_google_results(self, results: List[Dict[str, Any]], query: MineQuery) -> List[str]:
        """Extrahiert relevante URLs aus Google-Suchergebnissen"""
        urls = []
        
        for item in results:
            if 'organicResults' in item:
                for result in item['organicResults'][:10]:  # Mehr URLs prüfen
                    url = result.get('url')
                    if url and self.is_relevant_url(url, query):
                        urls.append(url)
        
        return list(set(urls))  # Deduplizieren