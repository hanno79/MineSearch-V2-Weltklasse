"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: ScrapingBee Data Parser Modul
"""

import re
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from ..base_agent import MineQuery, SearchResult


class ScrapingBeeDataParser:
    """Handles Daten-Extraktion aus gescrapten HTML-Inhalten"""
    
    def __init__(self, logger):
        self.logger = logger
        
        # Definiere Extraktionsmuster
        self.patterns = {
            'betreiber': [
                r'{mine_name}.*?(?:operated by|operator|owned by|owner)[:\s]+([A-Za-z0-9\s&.,()-]+?)(?:\.|,|\n|;)',
                r'([A-Z][A-Za-z0-9\s&.,()-]+?)\s+(?:operates?|owns?)\s+(?:the\s+)?{mine_name}'
            ],
            'koordinaten': [
                r'coordinates?[:\s]*([-\d\.]+)[°\s,]+([-\d\.]+)',
                r'latitude[:\s]*([-\d\.]+).*?longitude[:\s]*([-\d\.]+)',
                r'(\d{1,2}°\d{1,2}\'[\d\.]+\"[NS])[,\s]+(\d{1,3}°\d{1,2}\'[\d\.]+\"[EW])'
            ],
            'sanierungskosten': [
                r'(?:restoration|rehabilitation|closure|reclamation)\s*(?:cost|bond|security)[:\s]*\$?([\d,\.]+)\s*(?:million|M|CAD|USD)?',
                r'environmental\s+(?:bond|liability|assurance)[:\s]*\$?([\d,\.]+)\s*(?:million|M)?'
            ],
            'aktivitaetsstatus': [
                r'{mine_name}.*?(?:is\s+)?(?:currently\s+)?(\w+ing|\w+ed)(?:\s+mine)?',
                r'(?:mine\s+)?status[:\s]+(\w+)',
                r'operations?\s+(?:are\s+)?(\w+)'
            ],
            'rohstofftyp': [
                r'(?:produces?|producing|commodit\w+|mineral\w*)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,|\n|;)',
                r'(?:primary|main)\s+(?:commodity|mineral)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,|\n)'
            ],
            'jahresproduktion': [
                r'(?:annual\s+)?production[:\s]*([\d,\.]+)\s*(?:tonnes?|tons?|ounces?|oz|kg)',
                r'produces?\s+([\d,\.]+)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per\s+year|annually|/year)'
            ],
            'flaeche': [
                r'(?:property|mine|site)\s*(?:area|size)[:\s]*([\d,\.]+)\s*(?:km²|km2|hectares?|ha|acres?)',
                r'covers?\s+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)'
            ]
        }
        
        # Header-zu-Feld Mapping für Tabellen
        self.header_mapping = {
            'operator': 'betreiber',
            'owner': 'betreiber',
            'company': 'betreiber',
            'commodity': 'rohstofftyp',
            'commodities': 'rohstofftyp',
            'mineral': 'rohstofftyp',
            'production': 'jahresproduktion',
            'annual production': 'jahresproduktion',
            'coordinates': 'koordinaten',
            'location': 'koordinaten',
            'status': 'aktivitaetsstatus',
            'area': 'flaeche',
            'size': 'flaeche',
            'employees': 'mitarbeiter',
            'restoration': 'sanierungskosten',
            'closure cost': 'sanierungskosten'
        }
    
    def extract_mining_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Mining-Daten aus HTML"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Entferne Script und Style Tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Hole Text
        text = soup.get_text()
        
        # Text-basierte Extraktion
        text_results = self._extract_from_text(text, url, query)
        results.extend(text_results)
        
        # Strukturierte Daten-Extraktion
        # Suche nach Tabellen
        tables = soup.find_all('table')
        for table in tables[:3]:  # Max 3 Tabellen
            table_results = self._extract_from_html_table(table, url, query)
            results.extend(table_results)
        
        # Suche nach Definition Lists (oft für strukturierte Daten verwendet)
        dl_elements = soup.find_all('dl')
        for dl in dl_elements[:2]:
            dl_results = self._extract_from_definition_list(dl, url, query)
            results.extend(dl_results)
        
        # Suche nach spezifischen Daten-Attributen
        data_elements = soup.find_all(attrs={"data-mine": True})
        for elem in data_elements:
            if query.mine_name.lower() in elem.get('data-mine', '').lower():
                # Extrahiere alle data-* Attribute
                for attr, value in elem.attrs.items():
                    if attr.startswith('data-') and attr != 'data-mine':
                        field_name = attr.replace('data-', '').replace('-', '_')
                        if field_name in ['operator', 'coordinates', 'status', 'commodity']:
                            result = SearchResult(
                                mine_name=query.mine_name,
                                field_name=self._map_field_name(field_name),
                                value=value,
                                source=f"ScrapingBee: {url.split('/')[2]}",
                                source_url=url,
                                source_date=datetime.now().year,
                                confidence_score=0.9,
                                agent_name='scrapingbee',
                                timestamp=datetime.now(),
                                metadata={}
                            )
                            results.append(result)
        
        return results
    
    def parse_google_results(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Parst Google-Suchergebnisse"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extrahiere Featured Snippets
        featured = soup.find('div', class_='xpdopen')
        if featured:
            text = featured.get_text()
            extracted = self._extract_from_text(text, "Google Featured Snippet", query)
            results.extend(extracted)
        
        # Extrahiere aus normalen Suchergebnissen
        search_results = soup.find_all('div', class_='g')[:5]
        for result in search_results:
            snippet = result.find('span', class_='st')
            if snippet:
                text = snippet.get_text()
                link = result.find('a')
                source_url = link.get('href', '') if link else ''
                
                extracted = self._extract_from_text(text, source_url, query)
                results.extend(extracted)
        
        return results
    
    def _extract_from_text(self, text: str, source: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Text mit Regex"""
        results = []
        
        for field_name, field_patterns in self.patterns.items():
            for pattern in field_patterns:
                # Ersetze {mine_name} Platzhalter
                pattern = pattern.replace('{mine_name}', re.escape(query.mine_name))
                
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Nimm das erste Match
                    match = matches[0]
                    if isinstance(match, tuple):
                        value = ", ".join(str(m) for m in match)
                    else:
                        value = str(match)
                    
                    # Bereinige und formatiere Wert
                    value = self._clean_value(value, field_name)
                    
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field_name,
                        value=value,
                        source=f"ScrapingBee: {source.split('/')[2] if source.startswith('http') else source}",
                        source_url=source if source.startswith('http') else '',
                        source_date=datetime.now().year,
                        confidence_score=0.7,
                        agent_name='scrapingbee',
                        timestamp=datetime.now(),
                        metadata={}
                    )
                    results.append(result)
                    self.logger.info(f"Text-Extraktion: {field_name} = {value}")
                    break
        
        return results
    
    def _extract_from_html_table(self, table, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus HTML-Tabelle"""
        results = []
        
        # Extrahiere Headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text().strip().lower())
        
        # Durchsuche Zeilen
        rows = table.find_all('tr')[1:]  # Skip Header
        for row in rows[:10]:  # Max 10 Zeilen
            cells = row.find_all(['td', 'th'])
            
            # Prüfe ob Minenname in Zeile vorkommt
            row_text = row.get_text().lower()
            if query.mine_name.lower() not in row_text:
                continue
            
            # Extrahiere Daten basierend auf Headers
            for i, header in enumerate(headers):
                if i < len(cells):
                    for header_key, field_name in self.header_mapping.items():
                        if header_key in header:
                            value = cells[i].get_text().strip()
                            if value and value.lower() not in ['n/a', 'na', '-', '']:
                                result = SearchResult(
                                    mine_name=query.mine_name,
                                    field_name=field_name,
                                    value=value,
                                    source=f"ScrapingBee Table: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name='scrapingbee',
                                    timestamp=datetime.now(),
                                    metadata={}
                                )
                                results.append(result)
                                self.logger.info(f"Tabellen-Fund: {field_name} = {value}")
        
        return results
    
    def _extract_from_definition_list(self, dl, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Definition Lists (dl/dt/dd)"""
        results = []
        
        # Mapping von dt-Text zu Feldern
        dt_mapping = {
            'operator': 'betreiber',
            'owner': 'betreiber',
            'location': 'koordinaten',
            'coordinates': 'koordinaten',
            'commodity': 'rohstofftyp',
            'status': 'aktivitaetsstatus',
            'area': 'flaeche',
            'production': 'jahresproduktion'
        }
        
        dt_elements = dl.find_all('dt')
        dd_elements = dl.find_all('dd')
        
        for i, dt in enumerate(dt_elements):
            if i < len(dd_elements):
                term = dt.get_text().strip().lower()
                definition = dd_elements[i].get_text().strip()
                
                for key, field_name in dt_mapping.items():
                    if key in term:
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=definition,
                            source=f"ScrapingBee DL: {url.split('/')[2]}",
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=0.9,
                            agent_name='scrapingbee',
                            timestamp=datetime.now(),
                            metadata={}
                        )
                        results.append(result)
                        self.logger.info(f"DL-Fund: {field_name} = {definition}")
                        break
        
        return results
    
    def _clean_value(self, value: str, field_name: str) -> str:
        """Bereinigt und formatiert extrahierte Werte"""
        value = value.strip()
        
        if field_name == 'sanierungskosten':
            # Konvertiere Millionen zu vollen Zahlen
            if 'million' in value.lower() or 'M' in value:
                try:
                    num_match = re.search(r'([\d,\.]+)', value)
                    if num_match:
                        num = float(num_match.group(1).replace(',', ''))
                        value = f"{int(num * 1000000):,} CAD"
                except:
                    pass
        
        elif field_name == 'koordinaten':
            # Standardisiere Koordinatenformat
            value = re.sub(r'\s+', ' ', value)
            value = value.replace('°', '').replace("'", '').replace('"', '')
        
        elif field_name == 'aktivitaetsstatus':
            # Normalisiere Status
            status_mapping = {
                'operating': 'aktiv',
                'operational': 'aktiv',
                'active': 'aktiv',
                'closed': 'geschlossen',
                'suspended': 'pausiert',
                'inactive': 'inaktiv'
            }
            value_lower = value.lower()
            for eng, ger in status_mapping.items():
                if eng in value_lower:
                    value = ger
                    break
        
        return value
    
    def _map_field_name(self, field_name: str) -> str:
        """Mappt englische Feldnamen zu deutschen"""
        mapping = {
            'operator': 'betreiber',
            'coordinates': 'koordinaten',
            'status': 'aktivitaetsstatus',
            'commodity': 'rohstofftyp',
            'production': 'jahresproduktion',
            'area': 'flaeche',
            'employees': 'mitarbeiter',
            'restoration': 'sanierungskosten'
        }
        return mapping.get(field_name, field_name)