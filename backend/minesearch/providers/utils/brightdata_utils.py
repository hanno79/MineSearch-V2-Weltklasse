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
        
        # REGEL 10 COMPLIANCE 30.08.2025: Keine Fallback-Werte - nur None oder echte Daten
        extracted_data = {
            'Name': mine_name,
            'Country': options.get('country', ''),
            'Region': options.get('region', None),
            'Eigentümer': None,
            'Betreiber': None,
            'x-Koordinate': None,
            'y-Koordinate': None,
            'Aktivitätsstatus': None,
            'Restaurationskosten': None,
            'Jahr der Aufnahme der Kosten': None,
            'Jahr der Erstellung des Dokumentes': None,
            'Rohstoffabbau': options.get('commodity', None),
            'Minentyp': None,
            'Produktionsstart': None,
            'Produktionsende': None,
            'Fördermenge/Jahr': None,
            'Fläche der Mine in qkm': None,
            'Quellenangaben': None
        }
        
        content_lower = content.lower()
        
        # FLEXIBLERE Koordinaten-Extraktion 30.08.2025
        coord_patterns = [
            # Standard Latitude/Longitude Pattern
            r'latitude[:\s]+(-?\d+\.?\d*)',
            r'longitude[:\s]+(-?\d+\.?\d*)',
            r'coordinates[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            r'lat[:\s]+(-?\d+\.?\d*)',
            r'lon[:\s]+(-?\d+\.?\d*)',
            # Deutsche Begriffe
            r'breitengrad[:\s]+(-?\d+\.?\d*)',
            r'längengrad[:\s]+(-?\d+\.?\d*)',
            r'koordinaten[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            # Verschiedene Formate
            r'(-?\d+\.?\d*)[°\s]*[n,s][,\s]*(-?\d+\.?\d*)[°\s]*[e,w]',
            r'GPS[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            r'location[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            r'position[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
            # Dezimalgrad-Muster
            r'(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)',
            # In Tabellen
            r'<td[^>]*>.*?(-?\d+\.?\d+).*?</td>.*?<td[^>]*>.*?(-?\d+\.?\d+).*?</td>'
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
        
        # FLEXIBLERE Eigentümer/Betreiber Pattern 30.08.2025
        owner_patterns = [
            # Standard English
            r'owner[:\s]+([^,\n\.<>]{3,100})',
            r'owned by[:\s]+([^,\n\.<>]{3,100})',
            r'operator[:\s]+([^,\n\.<>]{3,100})',
            r'operated by[:\s]+([^,\n\.<>]{3,100})',
            # Deutsche Begriffe
            r'eigentümer[:\s]+([^,\n\.<>]{3,100})',
            r'betreiber[:\s]+([^,\n\.<>]{3,100})',
            r'betrieben von[:\s]+([^,\n\.<>]{3,100})',
            r'im besitz von[:\s]+([^,\n\.<>]{3,100})',
            # Company mentions
            r'([A-Z][a-z]+\s+(?:Corp|Corporation|Company|Ltd|Limited|Inc|Incorporated|AG|GmbH|SA|Holdings|Mining|Mines|Resources))',
            r'([A-Z][a-zA-Z\s&]+(?:Corp|Corporation|Company|Ltd|Limited|Inc|Incorporated|AG|GmbH|SA|Holdings|Mining|Mines|Resources))',
            # In Tabellen
            r'<td[^>]*>.*?owner.*?</td>.*?<td[^>]*>([^<]{3,50})</td>',
            r'<td[^>]*>.*?operator.*?</td>.*?<td[^>]*>([^<]{3,50})</td>',
            # Verschiedene Formate
            r'company[:\s]+([^,\n\.<>]{3,100})',
            r'mining company[:\s]+([^,\n\.<>]{3,100})',
            r'parent company[:\s]+([^,\n\.<>]{3,100})'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, content_lower)
            if match:
                company = match.group(1).strip().title()
                if 'owner' in pattern:
                    extracted_data['Eigentümer'] = company
                else:
                    extracted_data['Betreiber'] = company
        
        # FLEXIBLERE Restaurationskosten Pattern 30.08.2025
        cost_patterns = [
            # Standard English
            r'closure cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            r'restoration cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            r'aro[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            r'environmental liability[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            r'reclamation cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            r'rehabilitation cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion|m|b|mio|mrd)?',
            # Deutsche Begriffe
            r'schließungskosten[:\s]+([0-9,\.]+)\s*(millionen?|milliarden?|mio|mrd|euro|€|\$|dollar|usd)?',
            r'restaurationskosten[:\s]+([0-9,\.]+)\s*(millionen?|milliarden?|mio|mrd|euro|€|\$|dollar|usd)?',
            r'wiederherstellungskosten[:\s]+([0-9,\.]+)\s*(millionen?|milliarden?|mio|mrd|euro|€|\$|dollar|usd)?',
            r'rückbaukosten[:\s]+([0-9,\.]+)\s*(millionen?|milliarden?|mio|mrd|euro|€|\$|dollar|usd)?',
            # Verschiedene Währungen und Formate
            r'([0-9,\.]+)\s*(million|billion|mio|mrd)?\s*(euro|€|\$|dollar|usd|cad|eur).*?(?:closure|restoration|aro|reclamation)',
            r'([0-9,\.]+)\s*(€|\$)\s*(million|billion|mio|mrd)?.*?(?:closure|restoration|cost)',
            # In Tabellen
            r'<td[^>]*>.*?cost.*?</td>.*?<td[^>]*>([^<]{1,30})</td>',
            r'<td[^>]*>.*?aro.*?</td>.*?<td[^>]*>([^<]{1,30})</td>'
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
        
        # REGEL 10 COMPLIANCE 30.08.2025: Basis-Struktur ohne Fallback-Werte
        mine_name = options.get('mine_name', '')
        structured_data = {
            'Name': mine_name,
            'Country': options.get('country', ''),
            'Region': options.get('region', None),
            'Eigentümer': None,
            'Betreiber': None,
            'x-Koordinate': None,
            'y-Koordinate': None,
            'Aktivitätsstatus': None,
            'Restaurationskosten': None,
            'Jahr der Aufnahme der Kosten': None,
            'Jahr der Erstellung des Dokumentes': None,
            'Rohstoffabbau': options.get('commodity', None),
            'Minentyp': None,
            'Produktionsstart': None,
            'Produktionsende': None,
            'Fördermenge/Jahr': None,
            'Fläche der Mine in qkm': None,
            'Quellenangaben': None
        }
        
        # REGEL 10 COMPLIANCE 30.08.2025: Aggregiere Daten nur mit echten Werten
        for result in results:
            # Überschreibe nur wenn echte Daten gefunden wurden
            for key, value in result.items():
                if key in structured_data and value is not None and value != '' and structured_data[key] is None:
                    # Zusätzliche Validierung: Keine versteckten Fallback-Werte
                    if str(value).strip() not in ['-', 'N/A', 'Unknown', 'None', 'null']:
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
        """VERBESSERTE Mining-spezifische URLs 30.08.2025"""
        
        urls = []
        from urllib.parse import quote
        encoded_mine = quote(mine_name.replace(' ', '+'))
        
        # 1. GOVERNMENT MINING DATABASES - Höchste Priorität für offizielle Daten
        if country:
            if country.lower() in ['kanada', 'canada']:
                urls.extend([
                    f"https://www.nrcan.gc.ca/mining-materials/mining/mining-data-statistics/8772",
                    f"https://www.mindat.org/loc-5926.html",  # Canadian mines database
                    f"https://geoscan.nrcan.gc.ca/geoscan_lite.php?search={encoded_mine}",
                    f"https://mern.gouv.qc.ca/mines/industrie/sites-miniers/",
                    f"https://www.snclavalin.com/en/beyond-engineering/mining-metals"
                ])
            elif country.lower() in ['australien', 'australia']:
                urls.extend([
                    f"https://data.gov.au/dataset?q={encoded_mine}+mine",
                    f"https://www.ga.gov.au/data-pubs/datastandards",
                    f"https://minedex.dmirs.wa.gov.au/",
                    f"https://www.business.qld.gov.au/industries/mining-energy-water/mining"
                ])
            elif country.lower() in ['usa', 'united states']:
                urls.extend([
                    f"https://mrdata.usgs.gov/mrds/",
                    f"https://www.usgs.gov/centers/nmic/mineral-resources-data-system",
                    f"https://edx.netl.doe.gov/dataset?q={encoded_mine}"
                ])
        
        # 2. MINING INTELLIGENCE PLATFORMS - Spezialisierte Datenbanken
        urls.extend([
            f"https://www.mineralinfo.fr/mines-monde",
            f"https://www.mindat.org/search.php?search={encoded_mine}",
            f"https://www.mining-atlas.com/",
            f"https://www.infomine.com/search/?q={encoded_mine}",
            f"https://www.miningglobal.com/search?q={encoded_mine}",
            f"https://www.globaldata.com/store/search/?q={encoded_mine}+mine"
        ])
        
        # 3. TECHNICAL REPORTS & FINANCIAL FILINGS
        urls.extend([
            f"https://www.sedarplus.ca/search?q={encoded_mine}",
            f"https://www.sec.gov/edgar/searchedgar/companysearch.html",
            f"https://disclosure.spsx.com.au/gns/search.jsp",  # ASX filings
            f"https://webfiles.thecse.com/"  # CSE filings
        ])
        
        # 4. ENVIRONMENTAL & CLOSURE DATA SOURCES
        urls.extend([
            f"https://www.epa.gov/superfund-redevelopment/mine-scarred-lands",
            f"https://www.environmentaldefence.ca/mining/",
            f"https://www.pollutionwaste.canada.ca/national-releases-inventory/",
            f"https://projects.eia.gov/powerplant-cleanup-costs/",  # Closure cost references
            f"https://www.canada.ca/en/environment-climate-change/services/environmental-indicators.html"
        ])
        
        # 5. MINING INDUSTRY DATABASES & NEWS ARCHIVES
        urls.extend([
            f"https://www.mining.com/tag/{encoded_mine.replace('+', '-')}/",
            f"https://www.northernminer.com/?s={mine_name}",
            f"https://www.miningweekly.com/search?searchword={encoded_mine}",
            f"https://www.resourceworld.com/?s={mine_name}",
            f"https://www.miningmagazine.com/search/?q={mine_name}",
            f"https://www.mining-journal.com/search/?q={mine_name}"
        ])
        
        # 6. COMMODITY-SPECIFIC SOURCES
        if commodity:
            commodity_encoded = quote(commodity.replace(' ', '+'))
            urls.extend([
                f"https://www.kitco.com/news/search/?q={encoded_mine}+{commodity_encoded}",
                f"https://www.metalbulletin.com/search?q={mine_name}+{commodity}",
                f"https://www.platts.com/search?query={mine_name}+{commodity}",
                f"https://www.fastmarkets.com/search?q={mine_name}+{commodity}"
            ])
        
        logger.info(f"[BrightData-URLs] Generated {len(urls)} mining-specific URLs for {mine_name}")
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