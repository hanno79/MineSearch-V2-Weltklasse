"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Such-Utilities für Brightdata Provider
"""

import re
import json
from typing import Dict, Any, List, Optional
from urllib.parse import unquote


class BrightdataSearchUtils:
    """Utility-Funktionen für Brightdata-Suchen"""
    
    @staticmethod
    def format_scraped_content(scraped_data: List[Dict]) -> str:
        """Formatiere gescrapte Daten als lesbaren Content"""
        
        content = "BRIGHTDATA SCRAPING ERGEBNISSE\n" + "="*50 + "\n\n"
        
        for i, data in enumerate(scraped_data, 1):
            content += f"Quelle {i}:\n"
            content += f"Titel: {data.get('title', 'N/A')}\n"
            
            if data.get('latitude') or data.get('longitude'):
                content += f"Koordinaten: {data.get('latitude', '?')}, {data.get('longitude', '?')}\n"
            
            if data.get('owner_operator'):
                content += f"Eigentümer/Betreiber: {data['owner_operator']}\n"
            
            if data.get('restoration_costs'):
                content += f"Restaurationskosten: {data['restoration_costs']}\n"
            
            content += "\n"
        
        return content
    
    @staticmethod
    def extract_advanced_data(html: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Erweiterte Datenextraktion für Browser API"""
        data = {}
        
        # Suche nach strukturierten Daten (JSON-LD)
        json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
        matches = re.findall(json_ld_pattern, html, re.DOTALL)
        for match in matches:
            try:
                json_data = json.loads(match)
                if isinstance(json_data, dict):
                    # Extrahiere relevante Felder
                    if 'name' in json_data:
                        data['structured_name'] = json_data['name']
                    if 'geo' in json_data:
                        geo = json_data['geo']
                        if 'latitude' in geo:
                            data['latitude'] = str(geo['latitude'])
                        if 'longitude' in geo:
                            data['longitude'] = str(geo['longitude'])
            except json.JSONDecodeError:
                pass
        
        # Suche nach Tabellen mit Finanzdaten
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            if any(term in table.lower() for term in ['closure', 'restoration', 'aro', 'liability']):
                # Extrahiere Werte aus der Tabelle
                value_pattern = r'\$([0-9,\.]+)\s*(million|billion|m|b)?'
                value_match = re.search(value_pattern, table, re.IGNORECASE)
                if value_match:
                    data['table_cost'] = value_match.group(0)
        
        return data
    
    @staticmethod
    def build_search_queries(mine_name: str, country: str, commodity: str) -> List[str]:
        """Erstellt optimierte Suchqueries für Mining-Daten"""
        queries = [
            f"{mine_name} mine {country} coordinates GPS",
            f"{mine_name} {country} owner operator {commodity}",
            f"{mine_name} closure costs restoration ARO liability",
            f"{mine_name} technical report NI 43-101 PDF",
            f"{mine_name} {country} production annual tonnage"
        ]
        
        # Füge länderspezifische Queries hinzu
        if country.lower() in ['kanada', 'canada']:
            queries.append(f"{mine_name} MERN Quebec mining registry")
            queries.append(f"{mine_name} SEDAR filings annual report")
        elif country.lower() in ['australien', 'australia']:
            queries.append(f"{mine_name} DMIRS MineDex Western Australia")
            queries.append(f"{mine_name} ASX announcements reserves")
        
        return queries
    
    @staticmethod
    def extract_search_results(html: str) -> List[Dict[str, Any]]:
        """Extrahiert Suchergebnisse aus Google SERP HTML"""
        results = []
        
        # Einfache Extraktion von URLs und Titeln
        # Google Suchergebnisse haben verschiedene Strukturen
        result_pattern = r'<a href="([^"]+)"[^>]*><h3[^>]*>([^<]+)</h3>'
        matches = re.findall(result_pattern, html)
        
        for url, title in matches:
            if url.startswith('/url?q='):
                # Extrahiere die echte URL
                url = url.replace('/url?q=', '').split('&')[0]
                url = unquote(url)
            
            if url.startswith('http'):
                results.append({
                    'url': url,
                    'title': title.strip()
                })
        
        # Alternative Pattern für neuere Google-Strukturen
        if not results:
            alt_pattern = r'<div class="[^"]*"><a href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(alt_pattern, html)
            for url, title in matches:
                if url.startswith('http'):
                    results.append({
                        'url': url,
                        'title': title.strip()
                    })
        
        return results
    
    @staticmethod
    def build_mining_query(mine_name: str, country: str = None, commodity: str = None) -> str:
        """Erstellt optimierte Mining-Suchquery"""
        query_parts = [mine_name, "mine"]
        
        if country:
            query_parts.append(country)
        
        if commodity:
            query_parts.append(commodity)
        
        # Füge spezifische Keywords hinzu
        query_parts.extend(["closure costs", "restoration", "coordinates", "owner"])
        
        return " ".join(query_parts)