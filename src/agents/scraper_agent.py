"""Web Scraper Agent Implementation"""
import aiohttp
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class ScraperAgent(BaseAgent):
    """Web Scraping Agent für Mining-Informationen"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.scraping_config = config['scraping_config']
        self._rate_limiter = RateLimiter(rate=60, per=60.0)  # 60 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="scraper")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
        # Erweiterte Mining-Informationsquellen
        self.mining_sources = self._get_mining_sources()
        
    async def initialize(self) -> bool:
        """Initialisiert den Scraper Agent"""
        try:
            # Erstelle Session mit User-Agent
            self._session = aiohttp.ClientSession(
                headers={'User-Agent': self.scraping_config.user_agent}
            )
            
            self.logger.info("Scraper Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Scraper benötigt keine Credentials"""
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifisches Web-Scraping durch"""
        results = []
        
        self.perf_logger.start_timer(f"scraper_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            
            # Suche auf verschiedenen Seiten
            search_tasks = []
            
            # Erweiterte Google-Suche mit mehreren Queries
            for idx, mining_query in enumerate(mining_queries[:15]):
                search_tasks.append(self._enhanced_search(query, mining_query, idx))
            
            # Direkte Suche auf Mining-spezifischen Seiten
            search_tasks.append(self._search_mining_sites(query))
            
            # Direkte Suche auf bekannten Mining-Seiten
            if query.country == "Canada":
                search_tasks.append(self._search_canadian_sources(query))
            
            # Government und Regulatory Websites
            search_tasks.append(self._search_government_sources(query))
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Scraper: Starte {len(search_tasks)} Mining-Suchen")
            
            # Führe alle Suchen parallel aus
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Verarbeite Ergebnisse
            for result in search_results:
                if isinstance(result, list):
                    results.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Suchfehler: {result}")
            
            self.perf_logger.end_timer(
                f"scraper_search_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Scraper-Suche: {e}")
            return results
    
    async def _enhanced_search(self, query: MineQuery, search_query: str, idx: int) -> List[SearchResult]:
        """Erweiterte Suche mit Mining-spezifischen Queries"""
        results = []
        
        try:
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Scraper: Mining-Suche {idx + 1} - {search_query[:50]}...")
            
            # Simuliere erweiterte Suche (in Produktion: Custom Search API oder direkte Scraping)
            self.logger.info(f"Mining-Suche: {search_query}")
            
            # Hier würde die echte Implementierung erfolgen
            # z.B. Google Custom Search API, Bing Search API, oder direktes Scraping
            
            await asyncio.sleep(self.scraping_config.delay_seconds)
            
        except Exception as e:
            self.logger.error(f"Erweiterte Suche fehlgeschlagen: {e}")
        
        return results
    
    async def _search_mining_sites(self, query: MineQuery) -> List[SearchResult]:
        """Durchsucht Mining-spezifische Websites"""
        results = []
        mining_domains = get_mining_domains()
        
        # Durchsuche Top Mining-Websites
        for domain in mining_domains[:10]:
            try:
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Scraper: Durchsuche {domain}")
                
                # Konstruiere Suchurl für die Domain
                if "mining.com" in domain:
                    search_url = f"https://{domain}/search/?q={quote_plus(query.mine_name)}"
                elif "mindat.org" in domain:
                    search_url = f"https://{domain}/search.php?search={quote_plus(query.mine_name)}"
                else:
                    # Generische Suche
                    search_url = f"https://{domain}/search?q={quote_plus(query.mine_name + ' mine')}"
                
                # Scrape die Seite
                page_results = await self._scrape_page(search_url, query)
                results.extend(page_results)
                
                await asyncio.sleep(self.scraping_config.delay_seconds)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Scraping von {domain}: {e}")
        
        return results
    
    async def _search_government_sources(self, query: MineQuery) -> List[SearchResult]:
        """Durchsucht Regierungs- und Regulatory-Websites"""
        results = []
        
        # Government-spezifische URLs
        gov_urls = {
            'Canada': [
                f"https://www.nrcan.gc.ca/search?q={quote_plus(query.mine_name)}",
                f"https://www.canada.ca/en/services/environment/pollution-waste-management/managing-reducing-waste/sites-contaminated-federal-activities.html"
            ],
            'Quebec': [
                f"https://mern.gouv.qc.ca/en/search/?q={quote_plus(query.mine_name)}",
                f"https://gestim.mines.gouv.qc.ca/"
            ],
            'Ontario': [
                f"https://www.ontario.ca/search/search-results?query={quote_plus(query.mine_name)}",
                f"https://www.mndm.gov.on.ca/en/mines-and-minerals"
            ]
        }
        
        # Suche nach Land/Region
        urls_to_search = gov_urls.get(query.country, [])
        if query.region in gov_urls:
            urls_to_search.extend(gov_urls[query.region])
        
        for url in urls_to_search:
            try:
                page_results = await self._scrape_page(url, query)
                results.extend(page_results)
                await asyncio.sleep(self.scraping_config.delay_seconds)
            except Exception as e:
                self.logger.error(f"Government source scraping error: {e}")
        
        return results
    
    async def _search_canadian_sources(self, query: MineQuery) -> List[SearchResult]:
        """Suche auf kanadischen Regierungsseiten"""
        results = []
        
        # Quebec Mining Registry
        if query.region.lower() == "quebec":
            results.extend(await self._search_quebec_registry(query))
        
        # Ontario Mining Lands
        elif query.region.lower() == "ontario":
            results.extend(await self._search_ontario_registry(query))
        
        return results
    
    async def _search_quebec_registry(self, query: MineQuery) -> List[SearchResult]:
        """Suche im Quebec Mining Registry"""
        results = []
        
        try:
            # GESTIM - Quebec's mining titles management system
            base_url = "https://gestim.mines.gouv.qc.ca"
            search_url = f"{base_url}/fiche_titre.asp?nom_mine={quote_plus(query.mine_name)}"
            
            async with self._session.get(
                search_url,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Parse Quebec-spezifische Felder
                    operator = self._extract_text(soup, 'Titulaire')
                    if operator:
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='betreiber',
                            value=operator,
                            source='GESTIM Quebec',
                            source_url=search_url,
                            source_date=datetime.now().year,
                            confidence_score=0.95,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'registry': 'quebec'}
                        ))
                    
                    # Weitere Felder extrahieren...
                    
        except Exception as e:
            self.logger.error(f"Quebec Registry Fehler: {e}")
            
        return results
    
    async def _search_ontario_registry(self, query: MineQuery) -> List[SearchResult]:
        """Suche im Ontario Mining Registry"""
        results = []
        
        try:
            # CLAIMaps - Ontario's mining claims system
            base_url = "https://www.ontario.ca/page/mining-claims"
            
            # Implementierung für Ontario...
            
        except Exception as e:
            self.logger.error(f"Ontario Registry Fehler: {e}")
            
        return results
    
    def _extract_text(self, soup: BeautifulSoup, label: str) -> str:
        """Extrahiert Text basierend auf Label"""
        # Suche nach Label in verschiedenen HTML-Strukturen
        patterns = [
            soup.find('td', string=re.compile(label, re.I)),
            soup.find('th', string=re.compile(label, re.I)),
            soup.find('label', string=re.compile(label, re.I))
        ]
        
        for element in patterns:
            if element:
                # Finde zugehörigen Wert
                next_element = element.find_next_sibling()
                if next_element:
                    return next_element.get_text(strip=True)
                    
                # Oder im Parent
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    text = text.replace(label, '').strip()
                    if text:
                        return text
        
        return None
    
    async def _extract_coordinates(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Extrahiert Koordinaten aus HTML"""
        coords = {}
        
        # Suche nach verschiedenen Koordinaten-Formaten
        patterns = [
            r'latitude[:\s]*(-?\d+\.?\d*)',
            r'lat[:\s]*(-?\d+\.?\d*)',
            r'longitude[:\s]*(-?\d+\.?\d*)',
            r'lon[:\s]*(-?\d+\.?\d*)',
            r'(-?\d+\.?\d*)[°\s]*[NS].*?(-?\d+\.?\d*)[°\s]*[EW]'
        ]
        
        text = soup.get_text()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                if isinstance(matches[0], tuple):
                    coords['latitude'] = float(matches[0][0])
                    coords['longitude'] = float(matches[0][1])
                else:
                    if 'lat' in pattern:
                        coords['latitude'] = float(matches[0])
                    elif 'lon' in pattern:
                        coords['longitude'] = float(matches[0])
        
        return coords
    
    async def _extract_costs(self, text: str) -> Dict[str, Any]:
        """Extrahiert Kostenangaben aus Text"""
        costs = {}
        
        # Suche nach Währungsangaben
        currency_patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)?',
            r'([\d,]+(?:\.\d{2})?)\s*(?:CAD|USD|EUR)',
            r'restoration.*?costs?.*?([\d,]+(?:\.\d{2})?)',
            r'environmental.*?liability.*?([\d,]+(?:\.\d{2})?)'
        ]
        
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                # Konvertiere zu Zahl
                value = matches[0].replace(',', '')
                if 'million' in text.lower() or 'M' in text:
                    value = float(value) * 1000000
                else:
                    value = float(value)
                
                costs['value'] = value
                
                # Erkenne Währung
                if 'CAD' in text or '$' in text and 'canad' in text.lower():
                    costs['currency'] = 'CAD'
                elif 'USD' in text:
                    costs['currency'] = 'USD'
                elif 'EUR' in text:
                    costs['currency'] = 'EUR'
                else:
                    costs['currency'] = 'CAD'  # Default für Kanada
                
                break
        
        return costs
    
    def _get_mining_sources(self) -> Dict[str, List[str]]:
        """Erweiterte Liste von Mining-Informationsquellen"""
        mining_domains = get_mining_domains()
        
        return {
            'government': [
                'https://www.nrcan.gc.ca/mining-materials',
                'https://mern.gouv.qc.ca',
                'https://www.ontario.ca/page/mines-and-minerals',
                'https://www.gov.bc.ca/gov/content/industry/mineral-exploration-mining',
                'https://www.alberta.ca/energy-minerals.aspx',
                'https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/mineral-exploration-and-mining',
                'https://www.gov.mb.ca/iem/mines/index.html'
            ],
            'industry': [
                f'https://{domain}' for domain in mining_domains[:15]
            ],
            'environmental': [
                'https://miningwatch.ca',
                'https://www.environmentaldefence.ca',
                'https://www.ecojustice.ca',
                'https://www.pembina.org'
            ],
            'financial': [
                'https://www.sedar.com',
                'https://www.sec.gov/edgar',
                'https://www.tsx.com',
                'https://ca.finance.yahoo.com'
            ],
            'technical': [
                'https://www.geologyontario.mndm.gov.on.ca',
                'https://sigeom.mines.gouv.qc.ca',
                'https://www.usgs.gov',
                'https://www.ga.gov.au'
            ]
        }
    
    async def _scrape_page(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Scraped eine einzelne Seite nach Mining-Informationen"""
        results = []
        
        try:
            async with self._session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extrahiere verschiedene Informationen
                    text = soup.get_text()
                    
                    # Betreiber/Eigentümer
                    operator_patterns = [
                        rf'{re.escape(query.mine_name)}.*?(?:operated by|owned by|operator:|owner:)\s*([A-Za-z0-9\s&.,()-]+)',
                        rf'([A-Za-z0-9\s&.,()-]+?)\s+(?:operates|owns)\s+{re.escape(query.mine_name)}'
                    ]
                    
                    for pattern in operator_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            results.append(SearchResult(
                                mine_name=query.mine_name,
                                field_name='betreiber',
                                value=match.group(1).strip(),
                                source=f'Web Scraping: {url}',
                                source_url=url,
                                source_date=datetime.now().year,
                                confidence_score=0.8,
                                agent_name=self.name,
                                timestamp=datetime.now(),
                                metadata={'scraping_method': 'regex'}
                            ))
                            break
                    
                    # Koordinaten
                    coords = await self._extract_coordinates(soup)
                    if coords:
                        coord_str = f"{coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}"
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='koordinaten',
                            value=coord_str,
                            source=f'Web Scraping: {url}',
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=0.85,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'format': 'lat,lon'}
                        ))
                    
                    # Sanierungskosten
                    costs = await self._extract_costs(text)
                    if costs:
                        value = f"{costs['value']:,.0f} {costs.get('currency', 'CAD')}"
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='sanierungskosten',
                            value=value,
                            source=f'Web Scraping: {url}',
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=0.75,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'currency': costs.get('currency', 'CAD')}
                        ))
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Scraping von {url}: {e}")
        
        return results