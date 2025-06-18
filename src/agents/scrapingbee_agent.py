"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: ScrapingBee Web Scraping Agent Implementation
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger


class ScrapingBeeAgent(BaseAgent):
    """ScrapingBee Agent für JavaScript-rendering und komplexes Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].scrapingbee_key
        self.base_url = "https://app.scrapingbee.com/api/v1"
        self._rate_limiter = RateLimiter(rate=50, per=60.0)  # 50 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="scrapingbee")
        self.perf_logger = PerformanceLogger(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("ScrapingBee Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein ScrapingBee API-Key konfiguriert")
            return False
            
        try:
            # Test-Scraping
            params = {
                'api_key': self.api_key,
                'url': 'https://httpbin.org/anything'
            }
            
            async with self._session.get(
                self.base_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Web Scraping mit ScrapingBee durch"""
        results = []
        
        self.perf_logger.start_timer(f"scrapingbee_search_{query.mine_name}")
        
        try:
            # Erstelle Ziel-URLs basierend auf Region
            target_urls = self._get_target_urls(query)
            
            # Scrape jede URL
            for url_info in target_urls:
                url = url_info['url']
                scrape_config = url_info.get('config', {})
                
                self.logger.info(f"ScrapingBee scraping: {url}")
                
                html_content = await self._scrape_url(url, scrape_config)
                if html_content:
                    # Parse HTML und extrahiere Daten
                    extracted = self._extract_mining_data(html_content, url, query)
                    results.extend(extracted)
                
                await asyncio.sleep(1)  # Rate limiting
            
            # Google Search für zusätzliche Informationen
            google_results = await self._google_search_scrape(query)
            results.extend(google_results)
            
            self.perf_logger.end_timer(
                f"scrapingbee_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    def _get_target_urls(self, query: MineQuery) -> List[Dict[str, Any]]:
        """Erstellt Liste von Ziel-URLs basierend auf Region"""
        urls = []
        
        if query.country.lower() == 'canada':
            # Kanadische Regierungsseiten
            if query.region.lower() in ['quebec', 'québec']:
                urls.extend([
                    {
                        'url': f"https://mern.gouv.qc.ca/mines/titres-miniers/recherche/?nom={quote(query.mine_name)}",
                        'config': {'render_js': True, 'wait': 3000}
                    },
                    {
                        'url': f"https://sigeom.mines.gouv.qc.ca/signet/classes/I1108_indexAccueil?l=F&mine={quote(query.mine_name)}",
                        'config': {'render_js': True}
                    }
                ])
            elif query.region.lower() == 'ontario':
                urls.extend([
                    {
                        'url': f"https://www.geologyontario.mines.gov.on.ca/minesite/?search={quote(query.mine_name)}",
                        'config': {'render_js': True}
                    }
                ])
            
            # Pan-kanadische Quellen
            urls.extend([
                {
                    'url': f"https://www.nrcan.gc.ca/mining-materials/mining/canadian-minerals-yearbook/search?name={quote(query.mine_name)}",
                    'config': {'render_js': False}
                },
                {
                    'url': f"https://mining.ca/our-members/?search={quote(query.mine_name)}",
                    'config': {'render_js': True}
                }
            ])
        
        # Allgemeine Mining-Portale
        urls.extend([
            {
                'url': f"https://www.mining.com/?s={quote(query.mine_name)}",
                'config': {'render_js': False}
            },
            {
                'url': f"https://www.infomine.com/search/mines.aspx?q={quote(query.mine_name)}",
                'config': {'render_js': True, 'wait': 2000}
            }
        ])
        
        return urls
    
    async def _scrape_url(self, url: str, config: Dict[str, Any]) -> Optional[str]:
        """Scraped eine URL mit ScrapingBee"""
        await self._rate_limiter.acquire()
        
        params = {
            'api_key': self.api_key,
            'url': url,
            'render_js': str(config.get('render_js', True)).lower(),
            'premium_proxy': 'true',  # Für bessere Erfolgsrate
            'country_code': 'ca'  # Kanadische IP für lokale Seiten
        }
        
        # Zusätzliche Parameter
        if config.get('wait'):
            params['wait'] = config['wait']
        
        if config.get('javascript_snippet'):
            params['js_scenario'] = config['javascript_snippet']
        
        try:
            async with self._session.get(
                self.base_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    error_text = await response.text()
                    self.logger.error(f"ScrapingBee Fehler {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout beim Scraping von {url}")
            return None
        except Exception as e:
            self.logger.error(f"Scraping Fehler für {url}: {e}")
            return None
    
    async def _google_search_scrape(self, query: MineQuery) -> List[SearchResult]:
        """Führt Google-Suche mit ScrapingBee durch"""
        results = []
        
        search_queries = [
            f'"{query.mine_name}" mine {query.region} operator company contact',
            f'"{query.mine_name}" environmental restoration costs bonds {query.country}',
            f'"{query.mine_name}" coordinates latitude longitude location'
        ]
        
        for search_query in search_queries:
            google_url = f"https://www.google.com/search?{urlencode({'q': search_query})}"
            
            config = {
                'render_js': False,  # Google funktioniert ohne JS
                'block_ads': True,
                'stealth_proxy': True
            }
            
            html_content = await self._scrape_url(google_url, config)
            if html_content:
                # Parse Google-Ergebnisse
                soup = BeautifulSoup(html_content, 'html.parser')
                
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
                        url = link.get('href', '') if link else ''
                        
                        extracted = self._extract_from_text(text, url, query)
                        results.extend(extracted)
            
            await asyncio.sleep(2)  # Respektiere Google
        
        return results
    
    def _extract_mining_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
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
                                agent_name=self.name,
                                timestamp=datetime.now(),
                                metadata={}
                            )
                            results.append(result)
        
        return results
    
    def _extract_from_text(self, text: str, source: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Text mit Regex"""
        results = []
        
        # Definiere Extraktionsmuster
        patterns = {
            'betreiber': [
                rf'{re.escape(query.mine_name)}.*?(?:operated by|operator|owned by|owner)[:\s]+([A-Za-z0-9\s&.,()-]+?)(?:\.|,|\n|;)',
                rf'([A-Z][A-Za-z0-9\s&.,()-]+?)\s+(?:operates?|owns?)\s+(?:the\s+)?{re.escape(query.mine_name)}'
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
                rf'{re.escape(query.mine_name)}.*?(?:is\s+)?(?:currently\s+)?(\w+ing|\w+ed)(?:\s+mine)?',
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
        
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
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
                        agent_name=self.name,
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
        
        # Header-zu-Feld Mapping
        header_mapping = {
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
                    for header_key, field_name in header_mapping.items():
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
                                    agent_name=self.name,
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
                            agent_name=self.name,
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
    
    async def _get_enhanced_mining_urls(self, query: MineQuery, mining_domains: List[str]) -> List[Dict[str, Any]]:
        """Erstellt URLs für Mining-spezifische Websites"""
        urls = []
        
        for domain in mining_domains:
            # Erstelle Such-URLs für verschiedene Mining-Websites
            if "sedar.com" in domain:
                urls.append({
                    'url': f"https://www.sedar.com/search/search_form_pc_en.htm?searchType=Company&searchText={quote(query.mine_name)}",
                    'config': {'render_js': True, 'wait': 3000}
                })
            elif "sec.gov" in domain:
                urls.append({
                    'url': f"https://www.sec.gov/edgar/search/#/q={quote(query.mine_name)}%20AND%20mining",
                    'config': {'render_js': True, 'wait': 2000}
                })
            elif "tsx.com" in domain:
                urls.append({
                    'url': f"https://www.tsx.com/listings/listing-with-us/listed-company-directory?name={quote(query.mine_name)}",
                    'config': {'render_js': True, 'wait': 2000}
                })
            elif "asx.com.au" in domain:
                urls.append({
                    'url': f"https://www2.asx.com.au/markets/company/{query.mine_name.upper()[:3]}",
                    'config': {'render_js': True}
                })
            elif "mining.com" not in domain:  # Bereits in _get_target_urls
                # Generische Suche für andere Mining-Websites
                urls.append({
                    'url': f"https://{domain}/search?q={quote(query.mine_name)}",
                    'config': {'render_js': True}
                })
        
        return urls
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("ScrapingBee Agent beendet")