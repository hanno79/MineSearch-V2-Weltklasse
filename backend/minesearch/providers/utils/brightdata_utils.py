"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Utility-Funktionen für Brightdata Provider
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BrightdataExtractor:
    """Extractor für strukturierte Daten aus Brightdata-Ergebnissen"""
    
    @staticmethod
    def extract_mining_data(content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert Mining-spezifische Daten aus dem Content"""
        
        mine_name = options.get('mine_name', '')
        
        extracted_data = {
            'Name': mine_name,
            'Country': options.get('country', ''),
            'Region': options.get('region', '-'),
            'Eigentümer': '-',
            'Betreiber': '-',
            'x-Koordinate': '-',
            'y-Koordinate': '-',
            'Aktivitätsstatus': '-',
            'Restaurationskosten': '-',
            'Jahr der Aufnahme der Kosten': '-',
            'Jahr der Erstellung des Dokumentes': '-',
            'Rohstoffabbau': options.get('commodity', '-'),
            'Minentyp': '-',
            'Produktionsstart': '-',
            'Produktionsende': '-',
            'Fördermenge/Jahr': '-',
            'Fläche der Mine in qkm': '-',
            'Quellenangaben': '-'
        }
        
        content_lower = content.lower()
        
        # Koordinaten-Extraktion
        coord_patterns = [
            r'latitude[:\s]+(-?\d+\.?\d*)',
            r'longitude[:\s]+(-?\d+\.?\d*)',
            r'coordinates[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            r'lat[:\s]+(-?\d+\.?\d*)',
            r'lon[:\s]+(-?\d+\.?\d*)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, content_lower)
            if match:
                if 'lat' in pattern:
                    extracted_data['y-Koordinate'] = match.group(1)
                elif 'lon' in pattern:
                    extracted_data['x-Koordinate'] = match.group(1)
                elif len(match.groups()) == 2:
                    extracted_data['y-Koordinate'] = match.group(1)
                    extracted_data['x-Koordinate'] = match.group(2)
        
        # Eigentümer/Betreiber
        owner_patterns = [
            r'owner[:\s]+([^,\n]+)',
            r'owned by[:\s]+([^,\n]+)',
            r'operator[:\s]+([^,\n]+)',
            r'operated by[:\s]+([^,\n]+)'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, content_lower)
            if match:
                company = match.group(1).strip().title()
                if 'owner' in pattern:
                    extracted_data['Eigentümer'] = company
                else:
                    extracted_data['Betreiber'] = company
        
        # Restaurationskosten
        cost_patterns = [
            r'closure cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b)?',
            r'restoration cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b)?',
            r'aro[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b)?',
            r'environmental liability[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b)?'
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, content_lower)
            if match:
                value = match.group(1).replace(',', '')
                unit = match.group(2) if len(match.groups()) > 1 else ''
                if unit and unit[0] in ['m', 'M']:
                    extracted_data['Restaurationskosten'] = f"${value} million"
                elif unit and unit[0] in ['b', 'B']:
                    extracted_data['Restaurationskosten'] = f"${value} billion"
                else:
                    extracted_data['Restaurationskosten'] = f"${value}"
                break
        
        # Status
        status_patterns = [
            r'status[:\s]+(\w+)',
            r'(operating|closed|suspended|care and maintenance|abandoned)',
            r'mine status[:\s]+([^,\n]+)'
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, content_lower)
            if match:
                extracted_data['Aktivitätsstatus'] = match.group(1).strip().title()
                break
        
        # Minentyp
        mine_type_patterns = [
            r'mine type[:\s]+([^,\n]+)',
            r'(open[\s-]?pit|underground|surface|subsurface)\s+mine',
            r'mining method[:\s]+([^,\n]+)'
        ]
        
        for pattern in mine_type_patterns:
            match = re.search(pattern, content_lower)
            if match:
                mine_type = match.group(1) if len(match.groups()) > 0 else match.group(0)
                extracted_data['Minentyp'] = mine_type.strip().title()
                break
        
        # Produktionsdaten
        prod_patterns = [
            r'production[:\s]+([0-9,\.]+)\s*(tonnes?|tons?|mt|million tonnes?)',
            r'annual production[:\s]+([0-9,\.]+)\s*(tonnes?|tons?|mt)'
        ]
        
        for pattern in prod_patterns:
            match = re.search(pattern, content_lower)
            if match:
                extracted_data['Fördermenge/Jahr'] = f"{match.group(1)} {match.group(2)}"
                break
        
        # Jahr der Kostenaufnahme
        year_pattern = r'(19|20)\d{2}'
        if extracted_data['Restaurationskosten'] != '-':
            # Suche nach Jahr in der Nähe der Kosten
            cost_section = content_lower[max(0, content_lower.find('cost')-100):content_lower.find('cost')+100]
            year_match = re.findall(year_pattern, cost_section)
            if year_match:
                extracted_data['Jahr der Aufnahme der Kosten'] = year_match[-1]
        
        return extracted_data


class BrightdataDataProcessor:
    """Prozessor für Brightdata-Scraped-Daten"""
    
    @staticmethod
    def process_search_results(results: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet Brightdata-Suchergebnisse zu strukturierten Daten"""
        
        # Initialisiere Basis-Struktur
        mine_name = options.get('mine_name', '')
        structured_data = {
            'Name': mine_name,
            'Country': options.get('country', ''),
            'Region': options.get('region', '-'),
            'Eigentümer': '-',
            'Betreiber': '-',
            'x-Koordinate': '-',
            'y-Koordinate': '-',
            'Aktivitätsstatus': '-',
            'Restaurationskosten': '-',
            'Jahr der Aufnahme der Kosten': '-',
            'Jahr der Erstellung des Dokumentes': '-',
            'Rohstoffabbau': options.get('commodity', '-'),
            'Minentyp': '-',
            'Produktionsstart': '-',
            'Produktionsende': '-',
            'Fördermenge/Jahr': '-',
            'Fläche der Mine in qkm': '-',
            'Quellenangaben': '-'
        }
        
        # Aggregiere Daten aus allen Ergebnissen
        for result in results:
            # Überschreibe nur wenn bessere Daten gefunden wurden
            for key, value in result.items():
                if key in structured_data and value != '-' and structured_data[key] == '-':
                    structured_data[key] = value
        
        # Sammle Quellen
        sources = []
        for idx, result in enumerate(results):
            if result.get('url'):
                sources.append(result['url'])
        
        if sources:
            structured_data['Quellenangaben'] = '; '.join(sources[:3])  # Max 3 Quellen
        
        return structured_data
    
    @staticmethod
    def build_search_urls(mine_name: str, country: str = None, commodity: str = None) -> List[str]:
        """Erstellt optimierte Such-URLs für Brightdata"""
        
        urls = []
        
        # Länderspezifische Mining-Portale
        if country:
            if country.lower() in ['kanada', 'canada']:
                urls.extend([
                    f"https://www.nrcan.gc.ca/search?search_api_views_fulltext={mine_name}",
                    f"https://www.mining.ca/search?query={mine_name}"
                ])
            elif country.lower() in ['australien', 'australia']:
                urls.extend([
                    f"https://www.ga.gov.au/search?query={mine_name}",
                    f"https://www.industry.gov.au/search?keys={mine_name}+mine"
                ])
        
        # Technische Report-Datenbanken
        urls.extend([
            f"https://www.sedar.com/search/search_form_pc_en.htm?searchText={mine_name}",
            f"https://www.sec.gov/edgar/search/?q={mine_name}+mine"
        ])
        
        # Mining-News und Datenbanken
        urls.extend([
            f"https://www.mining.com/?s={mine_name}",
            f"https://www.northernminer.com/?s={mine_name}",
            f"https://www.miningweekly.com/search?q={mine_name}"
        ])
        
        return urls
    
    @staticmethod
    def parse_table_data(html_content: str) -> List[Dict[str, Any]]:
        """Extrahiert Tabellendaten aus HTML"""
        tables = []
        
        # Einfache Tabellen-Extraktion
        table_pattern = r'<table[^>]*>(.*?)</table>'
        table_matches = re.findall(table_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for table_html in table_matches:
            # Extrahiere Zeilen
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, table_html, re.IGNORECASE | re.DOTALL)
            
            if rows:
                table_data = []
                for row in rows:
                    # Extrahiere Zellen
                    cell_pattern = r'<t[dh][^>]*>(.*?)</t[dh]>'
                    cells = re.findall(cell_pattern, row, re.IGNORECASE | re.DOTALL)
                    
                    # Bereinige HTML-Tags
                    clean_cells = []
                    for cell in cells:
                        clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                        clean_cells.append(clean_text)
                    
                    if clean_cells:
                        table_data.append(clean_cells)
                
                if table_data:
                    tables.append({
                        'type': 'html_table',
                        'data': table_data
                    })
        
        return tables