"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Firecrawl Web Scraping Agent Implementation
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger


class FirecrawlAgent(BaseAgent):
    """Firecrawl Agent für intelligentes Web Crawling und Datenextraktion"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].firecrawl_key
        self.base_url = "https://api.firecrawl.dev/v0"
        self._rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="firecrawl")
        self.perf_logger = PerformanceLogger(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Firecrawl Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Firecrawl API-Key konfiguriert")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test mit kleinem Scraping
            payload = {
                "url": "https://example.com",
                "formats": ["markdown"]
            }
            
            async with self._session.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status in [200, 201]
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt intelligentes Web Crawling für Mine durch"""
        results = []
        
        self.perf_logger.start_timer(f"firecrawl_search_{query.mine_name}")
        
        try:
            # 1. Erstelle Seed-URLs für Crawling
            seed_urls = self._create_seed_urls(query)
            
            # 2. Starte Crawl für Mining-Websites
            for seed_url in seed_urls:
                crawl_results = await self._crawl_website(seed_url, query)
                results.extend(crawl_results)
            
            # 3. Führe gezielte Scrapes auf bekannten Seiten durch
            targeted_results = await self._targeted_scraping(query)
            results.extend(targeted_results)
            
            self.perf_logger.end_timer(
                f"firecrawl_search_{query.mine_name}",
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
    
    def _create_seed_urls(self, query: MineQuery) -> List[str]:
        """Erstellt Seed-URLs für Crawling"""
        urls = []
        
        # Regierungsseiten basierend auf Region
        if query.country.lower() == 'canada':
            if query.region.lower() in ['quebec', 'québec']:
                urls.extend([
                    "https://mern.gouv.qc.ca/mines/",
                    "https://sigeom.mines.gouv.qc.ca/",
                    "https://gestim.mines.gouv.qc.ca/"
                ])
            elif query.region.lower() == 'ontario':
                urls.extend([
                    "https://www.ontario.ca/page/mining-and-minerals",
                    "https://www.geologyontario.mines.gov.on.ca/"
                ])
            
            # Pan-kanadische Seiten
            urls.extend([
                "https://www.nrcan.gc.ca/mining-materials/mining",
                "https://mining.ca/"
            ])
        
        # Allgemeine Mining-Portale
        urls.extend([
            "https://www.mining.com/",
            "https://www.mining-technology.com/",
            "https://www.miningnewsnorth.com/"
        ])
        
        return urls
    
    async def _crawl_website(self, seed_url: str, query: MineQuery) -> List[SearchResult]:
        """Crawlt eine Website nach Mining-Informationen"""
        results = []
        
        try:
            # Starte Crawl mit Firecrawl
            crawl_id = await self._start_crawl(seed_url, query)
            
            if crawl_id:
                # Warte auf Crawl-Completion
                crawl_data = await self._wait_for_crawl(crawl_id)
                
                if crawl_data:
                    # Extrahiere Daten aus gecrawlten Seiten
                    for page in crawl_data.get('data', [])[:20]:  # Max 20 Seiten
                        page_url = page.get('url', '')
                        content = page.get('markdown', '') or page.get('content', '')
                        
                        if query.mine_name.lower() in content.lower():
                            extracted = self._extract_from_content(
                                content,
                                page_url,
                                query
                            )
                            results.extend(extracted)
                            
                            # Falls relevante Seite gefunden, führe Deep Scrape durch
                            if extracted:
                                deep_results = await self._deep_scrape(page_url, query)
                                results.extend(deep_results)
        
        except Exception as e:
            self.logger.error(f"Crawl-Fehler für {seed_url}: {e}")
        
        return results
    
    async def _start_crawl(self, url: str, query: MineQuery) -> Optional[str]:
        """Startet einen Firecrawl Crawl-Job"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Crawl-Konfiguration
        payload = {
            "url": url,
            "crawlerOptions": {
                "includes": [
                    f"*{query.mine_name.lower().replace(' ', '*')}*",
                    "*mining*", "*mine*", "*mineral*"
                ],
                "excludes": [
                    "*/privacy*", "*/terms*", "*/login*"
                ],
                "generateImgAltText": False,
                "returnOnlyUrls": False,
                "maxDepth": 2,
                "limit": 50
            },
            "pageOptions": {
                "onlyMainContent": True,
                "includeHtml": False
            }
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/crawl",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return data.get('jobId')
                else:
                    error_text = await response.text()
                    self.logger.error(f"Crawl Start Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Crawl Start Exception: {e}")
            return None
    
    async def _wait_for_crawl(self, job_id: str, max_wait: int = 120) -> Optional[Dict[str, Any]]:
        """Wartet auf Crawl-Completion"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            try:
                async with self._session.get(
                    f"{self.base_url}/crawl/status/{job_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status')
                        
                        if status == 'completed':
                            return data
                        elif status in ['failed', 'cancelled']:
                            self.logger.error(f"Crawl fehlgeschlagen: {status}")
                            return None
                            
            except Exception as e:
                self.logger.error(f"Crawl Status Check Fehler: {e}")
        
        return None
    
    async def _deep_scrape(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Führt Deep Scrape auf spezifischer Seite durch"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "formats": ["markdown", "links", "screenshot"],
            "onlyMainContent": True,
            "waitFor": 2000,  # Warte auf dynamischen Content
            "screenshot": {
                "fullPage": False
            }
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extrahiere aus Markdown
                    markdown = data.get('data', {}).get('markdown', '')
                    extracted = self._extract_from_content(markdown, url, query)
                    
                    # Zusätzliche Extraktion aus Links
                    links = data.get('data', {}).get('links', [])
                    for link in links:
                        if any(keyword in link.get('text', '').lower() 
                              for keyword in ['operator', 'owner', 'contact', 'environmental']):
                            # Potentiell relevanter Link
                            self.logger.info(f"Relevanter Link gefunden: {link.get('href')}")
                    
                    return extracted
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"Deep Scrape Fehler: {e}")
            return []
    
    async def _targeted_scraping(self, query: MineQuery) -> List[SearchResult]:
        """Führt gezieltes Scraping auf bekannten URLs durch"""
        results = []
        
        # Erstelle gezielte URLs basierend auf Minenname
        target_urls = []
        
        # Kanadische Regierungsdatenbanken
        if query.country.lower() == 'canada':
            target_urls.extend([
                f"https://www.nrcan.gc.ca/mining-materials/mining/canadian-minerals-yearbook/search?text={query.mine_name}",
                f"https://www.sedar.com/search/search_form_pc_en.htm?searchType=Company&searchText={query.mine_name}"
            ])
            
            if query.region.lower() in ['quebec', 'québec']:
                target_urls.append(
                    f"https://sigeom.mines.gouv.qc.ca/signet/classes/I1108_rechercheEntite?C_ETIQ_NOM_MINE={query.mine_name}"
                )
        
        # Scrape jede URL
        for url in target_urls:
            try:
                results_from_url = await self._scrape_single_url(url, query)
                results.extend(results_from_url)
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Targeted Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _scrape_single_url(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Scraped eine einzelne URL"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "formats": ["markdown", "html"],
            "onlyMainContent": True,
            "includeHtml": True
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('data', {}).get('markdown', '')
                    html = data.get('data', {}).get('html', '')
                    
                    # Kombiniere Extraktion aus Markdown und HTML
                    results = self._extract_from_content(content, url, query)
                    
                    # Zusätzliche HTML-spezifische Extraktion
                    if html:
                        html_results = self._extract_from_html_structure(html, url, query)
                        results.extend(html_results)
                    
                    return results
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"Single URL Scrape Fehler: {e}")
            return []
    
    def _extract_from_content(self, content: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert strukturierte Daten aus Content"""
        results = []
        
        # Definiere erweiterte Extraktionsmuster
        patterns = {
            'betreiber': [
                rf'(?:{re.escape(query.mine_name)}.*?)?(?:operated by|operator|owned by|owner|propriétaire)[:\s]+([A-Za-z0-9\s&.,()À-ÿ-]+?)(?:\.|,|\n|;)',
                rf'([A-Z][A-Za-z0-9\s&.,()À-ÿ-]+?)\s+(?:operates?|owns?|exploite)\s+(?:the\s+|la\s+)?{re.escape(query.mine_name)}'
            ],
            'koordinaten': [
                r'coordinates?[:\s]*([-\d\.]+)[°\s,]+([-\d\.]+)',
                r'latitude[:\s]*([-\d\.]+).*?longitude[:\s]*([-\d\.]+)',
                r'UTM[:\s]+(\d+[NS])\s+(\d+[EW])',
                r'(\d{1,2}°\d{1,2}\'[\d\.]*\"?[NS])[,\s]+(\d{1,3}°\d{1,2}\'[\d\.]*\"?[EW])'
            ],
            'sanierungskosten': [
                r'(?:restoration|rehabilitation|closure|reclamation|restauration)\s*(?:cost|bond|security|coût|garantie)[:\s]*\$?([\d\s,\.]+)\s*(?:million|M|CAD|USD)?',
                r'(?:environmental|environnemental)\s+(?:bond|liability|assurance|garantie)[:\s]*\$?([\d\s,\.]+)\s*(?:million|M)?',
                r'garantie\s+financière[:\s]*\$?([\d\s,\.]+)\s*(?:million|M)?'
            ],
            'aktivitaetsstatus': [
                rf'{re.escape(query.mine_name)}.*?(?:is\s+)?(?:currently\s+)?(\w+ing|\w+ed|active|inactive|fermée?)',
                r'(?:mine\s+)?status[:\s]+(\w+)',
                r'statut[:\s]+(\w+)',
                r'état[:\s]+(\w+)'
            ],
            'rohstofftyp': [
                r'(?:produces?|producing|commodit\w+|mineral\w*|produit|substance)[:\s]+([A-Za-z0-9\s,&À-ÿ-]+?)(?:\.|,|\n|;)',
                r'(?:primary|main|principal)\s+(?:commodity|mineral|substance)[:\s]+([A-Za-z0-9\s,&À-ÿ-]+?)(?:\.|,|\n)'
            ],
            'jahresproduktion': [
                r'(?:annual\s+)?production[:\s]*([\d\s,\.]+)\s*(?:tonnes?|tons?|ounces?|oz|kg)',
                r'(?:produces?|produit)\s+([\d\s,\.]+)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per\s+year|annually|par\s+an|/year|/an)'
            ],
            'flaeche': [
                r'(?:property|mine|site|propriété)\s*(?:area|size|superficie)[:\s]*([\d\s,\.]+)\s*(?:km²|km2|hectares?|ha|acres?)',
                r'(?:covers?|couvre)\s+([\d\s,\.]+)\s*(?:km²|km2|hectares?|ha)'
            ],
            'mitarbeiter': [
                r'(?:employs?|employees?|workforce|employés?|travailleurs)[:\s]*([\d\s,]+)\s*(?:people|persons?|workers?|personnes?)?',
                r'([\d\s,]+)\s*(?:employees?|workers?|employés?)'
            ]
        }
        
        # Suche nach Mustern
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    match = matches[0]
                    if isinstance(match, tuple):
                        value = ", ".join(str(m).strip() for m in match if m)
                    else:
                        value = str(match).strip()
                    
                    # Bereinige Wert
                    value = self._clean_value(value, field_name)
                    
                    if value:
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=value,
                            source=f"Firecrawl: {url.split('/')[2]}",
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=0.9 if len(matches) == 1 else 0.7,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={}
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {field_name} = {value}")
                        break
        
        return results
    
    def _extract_from_html_structure(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus HTML-Struktur mit BeautifulSoup"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Suche nach strukturierten Daten (Schema.org)
            schema_scripts = soup.find_all('script', type='application/ld+json')
            for script in schema_scripts:
                try:
                    schema_data = json.loads(script.string)
                    if '@type' in schema_data and 'Mine' in schema_data.get('@type', ''):
                        # Extrahiere Schema.org Daten
                        if 'operator' in schema_data:
                            results.append(SearchResult(
                                mine_name=query.mine_name,
                                field_name='betreiber',
                                value=schema_data['operator'].get('name', schema_data['operator']),
                                source=f"Firecrawl Schema: {url.split('/')[2]}",
                                source_url=url,
                                source_date=datetime.now().year,
                                confidence_score=0.9,
                                agent_name=self.name,
                                timestamp=datetime.now(),
                                metadata={}
                            ))
                except:
                    pass
            
            # Suche nach Mikroformaten
            microformats = soup.find_all(attrs={'itemtype': re.compile('Mine|Organization|Place')})
            for mf in microformats:
                props = mf.find_all(attrs={'itemprop': True})
                for prop in props:
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text().strip()
                    
                    if prop_name in ['operator', 'owner'] and prop_value:
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='betreiber',
                            value=prop_value,
                            source=f"Firecrawl Microformat: {url.split('/')[2]}",
                            source_url=url,
                            source_date=datetime.now().year,
                            confidence_score=0.9,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={}
                        ))
                        
        except Exception as e:
            self.logger.error(f"HTML Struktur Parsing Fehler: {e}")
        
        return results
    
    def _clean_value(self, value: str, field_name: str) -> str:
        """Bereinigt extrahierte Werte"""
        # Entferne übermäßige Whitespaces
        value = re.sub(r'\s+', ' ', value).strip()
        
        if field_name == 'sanierungskosten':
            # Normalisiere Zahlen
            value = value.replace(' ', '')
            if 'million' in value.lower() or 'M' in value:
                try:
                    num_match = re.search(r'([\d,\.]+)', value)
                    if num_match:
                        num = float(num_match.group(1).replace(',', ''))
                        value = f"{int(num * 1000000):,} CAD"
                except:
                    pass
        
        elif field_name == 'koordinaten':
            # Konvertiere verschiedene Koordinatenformate
            if '°' in value:
                # DMS zu Dezimal
                try:
                    parts = re.findall(r'(\d+)°(\d+)\'([\d\.]+)"?([NSEW])', value)
                    if len(parts) == 2:
                        lat_d, lat_m, lat_s, lat_dir = parts[0]
                        lon_d, lon_m, lon_s, lon_dir = parts[1]
                        
                        lat = float(lat_d) + float(lat_m)/60 + float(lat_s)/3600
                        if lat_dir in ['S', 'W']:
                            lat = -lat
                            
                        lon = float(lon_d) + float(lon_m)/60 + float(lon_s)/3600
                        if lon_dir in ['W']:
                            lon = -lon
                            
                        value = f"{lat:.6f}, {lon:.6f}"
                except:
                    pass
        
        elif field_name == 'aktivitaetsstatus':
            # Normalisiere Status
            status_mapping = {
                'operating': 'aktiv',
                'active': 'aktiv',
                'fermée': 'geschlossen',
                'fermé': 'geschlossen',
                'closed': 'geschlossen',
                'suspended': 'pausiert',
                'inactive': 'inaktiv'
            }
            for key, mapped in status_mapping.items():
                if key in value.lower():
                    value = mapped
                    break
        
        return value
    
    def _generate_crawl_includes(self, query: MineQuery, mining_queries: List[str]) -> List[str]:
        """Generiert erweiterte Include-Patterns für Crawling"""
        includes = [
            f"*{query.mine_name.lower().replace(' ', '*')}*",
            "*mining*", "*mine*", "*mineral*", "*resources*",
            "*operator*", "*owner*", "*production*", "*reserves*",
            "*environmental*", "*restoration*", "*closure*",
            "*coordinates*", "*location*", "*GPS*",
            "*NI-43-101*", "*technical-report*", "*feasibility*"
        ]
        
        # Füge Keywords aus Mining-Queries hinzu
        for query_str in mining_queries:
            keywords = query_str.lower().split()
            for keyword in keywords:
                if len(keyword) > 3 and keyword not in ['mine', 'mining']:
                    includes.append(f"*{keyword}*")
        
        # Deduplizieren
        return list(set(includes))[:20]  # Max 20 Includes
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Firecrawl Agent beendet")