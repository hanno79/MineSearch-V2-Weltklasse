"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Apify Web Scraping Agent Implementation
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
from .enhanced_search import get_mining_search_queries, get_mining_domains


class ApifyAgent(BaseAgent):
    """Apify Agent für strukturiertes Web Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].apify_key
        self.base_url = "https://api.apify.com/v2"
        self._rate_limiter = RateLimiter(rate=30, per=60.0)  # 30 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="apify")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
        # Apify Actor IDs für verschiedene Scraping-Aufgaben
        self.actors = {
            'google_search': 'apify/google-search-scraper',
            'web_scraper': 'apify/web-scraper',
            'cheerio_scraper': 'apify/cheerio-scraper',
            'website_content': 'apify/website-content-crawler'
        }
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Apify Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Apify API-Key konfiguriert")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Test API-Zugriff
            async with self._session.get(
                f"{self.base_url}/acts",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifisches Web Scraping mit Apify durch"""
        results = []
        
        self.perf_logger.start_timer(f"apify_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Apify: Starte erweiterte Mining-Suche")
            
            # 1. Erweiterte Google-Suche mit Mining-Queries
            urls = await self._enhanced_google_search(query, mining_queries[:15])
            
            # 2. Scrape Mining-spezifische Websites
            if urls:
                scraped_data = await self._scrape_mining_sites(urls, query)
                results.extend(scraped_data)
            
            # 3. Spezielle Regierungsseiten-Scraping für Kanada
            if query.country.lower() == 'canada':
                gov_results = await self._scrape_government_sites(query)
                results.extend(gov_results)
            
            self.perf_logger.end_timer(
                f"apify_search_{query.mine_name}",
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
    
    async def _enhanced_google_search(self, query: MineQuery, mining_queries: List[str]) -> List[str]:
        """Sucht relevante URLs via Google"""
        urls = []
        
        # Verwende die erweiterten Mining-Queries
        completed = 0
        
        for search_query in mining_queries:
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Apify: Google-Suche {completed + 1}/{len(mining_queries)}")
            
            completed += 1
            try:
                actor_input = {
                    "queries": [search_query],
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": 20,  # Mehr Ergebnisse für Mining-Suche
                    "languageCode": "en",
                    "includeUnfilteredResults": False
                }
                
                # Starte Actor Run
                run_id = await self._start_actor_run(
                    self.actors['google_search'],
                    actor_input
                )
                
                if run_id:
                    # Warte auf Ergebnisse
                    results = await self._get_actor_results(run_id)
                    if results:
                        for item in results:
                            if 'organicResults' in item:
                                for result in item['organicResults'][:10]:  # Mehr URLs prüfen
                                    url = result.get('url')
                                    if url and self._is_relevant_url(url, query):
                                        urls.append(url)
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Google-Suche Fehler: {e}")
        
        return list(set(urls))  # Deduplizieren
    
    async def _scrape_mining_sites(self, urls: List[str], query: MineQuery) -> List[SearchResult]:
        """Scraped Websites für Mining-Informationen"""
        results = []
        
        for url in urls[:10]:  # Max 10 URLs
            try:
                actor_input = {
                    "startUrls": [{"url": url}],
                    "maxPagesPerCrawl": 1,
                    "useChrome": False,
                    "waitForLoadEvent": True,
                    "pageFunction": """
                    async function pageFunction(context) {
                        const $ = context.jQuery;
                        const data = {
                            title: $('title').text(),
                            text: $('body').text().substring(0, 5000),
                            tables: []
                        };
                        
                        // Extrahiere Tabellen
                        $('table').each((i, table) => {
                            if (i < 3) {  // Max 3 Tabellen
                                const tableData = [];
                                $(table).find('tr').each((j, row) => {
                                    const rowData = [];
                                    $(row).find('td, th').each((k, cell) => {
                                        rowData.push($(cell).text().trim());
                                    });
                                    tableData.push(rowData);
                                });
                                data.tables.push(tableData);
                            }
                        });
                        
                        return data;
                    }
                    """
                }
                
                # Starte Scraping
                run_id = await self._start_actor_run(
                    self.actors['cheerio_scraper'],
                    actor_input
                )
                
                if run_id:
                    # Hole Ergebnisse
                    scraped_data = await self._get_actor_results(run_id)
                    if scraped_data:
                        for item in scraped_data:
                            # Extrahiere Daten
                            extracted = self._extract_from_scraped_data(
                                item,
                                url,
                                query
                            )
                            results.extend(extracted)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Website Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _scrape_government_sites(self, query: MineQuery) -> List[SearchResult]:
        """Spezielles Scraping für Regierungsseiten"""
        results = []
        
        # Quebec GESTIM
        if query.region.lower() in ['quebec', 'québec']:
            gestim_url = f"https://gestim.mines.gouv.qc.ca/MRN_GestimP_Presentation/ODM02301_menu_base.aspx"
            
            try:
                actor_input = {
                    "startUrls": [{"url": gestim_url}],
                    "pseudoUrls": [{"purl": "https://gestim.mines.gouv.qc.ca/[.*]"}],
                    "maxPagesPerCrawl": 5,
                    "pageFunction": f"""
                    async function pageFunction(context) {{
                        const $ = context.jQuery;
                        const mineName = "{query.mine_name}";
                        
                        // Suche nach Minennamen
                        const found = $('body').text().toLowerCase().includes(mineName.toLowerCase());
                        if (!found) return null;
                        
                        // Extrahiere relevante Daten
                        const data = {{
                            mineName: mineName,
                            pageTitle: $('title').text(),
                            content: {{}}
                        }};
                        
                        // Suche nach Tabellen mit Mining-Daten
                        $('table').each((i, table) => {{
                            const headers = [];
                            const values = [];
                            
                            $(table).find('th').each((j, th) => {{
                                headers.push($(th).text().trim());
                            }});
                            
                            $(table).find('tr').first().find('td').each((j, td) => {{
                                values.push($(td).text().trim());
                            }});
                            
                            headers.forEach((header, idx) => {{
                                if (values[idx]) {{
                                    data.content[header] = values[idx];
                                }}
                            }});
                        }});
                        
                        return data;
                    }}
                    """
                }
                
                run_id = await self._start_actor_run(
                    self.actors['web_scraper'],
                    actor_input
                )
                
                if run_id:
                    scraped_data = await self._get_actor_results(run_id)
                    if scraped_data:
                        for item in scraped_data:
                            if item and 'content' in item:
                                # Parse GESTIM-spezifische Felder
                                extracted = self._parse_gestim_data(item, query)
                                results.extend(extracted)
                
            except Exception as e:
                self.logger.error(f"GESTIM Scraping Fehler: {e}")
        
        return results
    
    async def _start_actor_run(self, actor_id: str, input_data: Dict[str, Any]) -> Optional[str]:
        """Startet einen Apify Actor Run"""
        await self._rate_limiter.acquire()
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with self._session.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                headers=headers,
                json=input_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return data.get('data', {}).get('id')
                else:
                    error_text = await response.text()
                    self.logger.error(f"Actor Start Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Actor Start Fehler: {e}")
            return None
    
    async def _get_actor_results(self, run_id: str, max_wait: int = 60) -> Optional[List[Dict[str, Any]]]:
        """Wartet auf Actor-Ergebnisse"""
        # Warte auf Completion
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            try:
                # Check Run Status
                async with self._session.get(
                    f"{self.base_url}/actor-runs/{run_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('data', {}).get('status')
                        
                        if status == 'SUCCEEDED':
                            # Hole Ergebnisse
                            dataset_id = data.get('data', {}).get('defaultDatasetId')
                            if dataset_id:
                                return await self._get_dataset_items(dataset_id)
                        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                            self.logger.error(f"Actor Run fehlgeschlagen: {status}")
                            return None
                            
            except Exception as e:
                self.logger.error(f"Status Check Fehler: {e}")
                
        return None
    
    async def _get_dataset_items(self, dataset_id: str) -> Optional[List[Dict[str, Any]]]:
        """Holt Items aus Apify Dataset"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with self._session.get(
                f"{self.base_url}/datasets/{dataset_id}/items",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Dataset Abruf Fehler: {e}")
            return None
    
    def _is_relevant_url(self, url: str, query: MineQuery) -> bool:
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
    
    def _extract_from_scraped_data(self, data: Dict[str, Any], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert strukturierte Daten aus gescrapten Inhalten"""
        results = []
        
        text = data.get('text', '')
        tables = data.get('tables', [])
        
        # Text-basierte Extraktion
        text_results = self._extract_from_text(text, url, query)
        results.extend(text_results)
        
        # Tabellen-basierte Extraktion
        for table in tables:
            table_results = self._extract_from_table(table, url, query)
            results.extend(table_results)
        
        return results
    
    def _extract_from_text(self, text: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Text"""
        results = []
        
        patterns = {
            'betreiber': r'(?:operated by|operator|owner)[:\s]+([A-Za-z0-9\s&.,()-]+?)(?:\.|,|\n)',
            'sanierungskosten': r'(?:restoration|rehabilitation|closure)\s*(?:cost|bond)[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
            'rohstofftyp': r'(?:commodit\w+|mineral\w*|produces?)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,|\n)',
            'jahresproduktion': r'(?:annual production|produces?)[:\s]*([\d,\.]+)\s*(?:tonnes?|ounces?|oz)',
            'koordinaten': r'(?:coordinates?|location)[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)'
        }
        
        for field_name, pattern in patterns.items():
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
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={}
                )
                results.append(result)
                self.logger.info(f"Gefunden via Text: {field_name} = {value}")
        
        return results
    
    def _extract_from_table(self, table: List[List[str]], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Tabellen"""
        results = []
        
        if not table or len(table) < 2:
            return results
        
        # Versuche Header zu identifizieren
        headers = [h.lower() for h in table[0]]
        
        # Mapping von Headers zu Feldern
        header_mapping = {
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
        
        # Durchsuche Tabelle
        for row_idx in range(1, min(len(table), 10)):  # Max 10 Zeilen
            row = table[row_idx]
            
            for col_idx, header in enumerate(headers):
                if col_idx < len(row):
                    for header_key, field_name in header_mapping.items():
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
                                    agent_name=self.name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                )
                                results.append(result)
                                self.logger.info(f"Gefunden via Tabelle: {field_name} = {value}")
                                break
        
        return results
    
    def _parse_gestim_data(self, data: Dict[str, Any], query: MineQuery) -> List[SearchResult]:
        """Parst GESTIM-spezifische Daten"""
        results = []
        
        content = data.get('content', {})
        
        # GESTIM Feld-Mapping
        field_mapping = {
            'Titulaire': 'betreiber',
            'Coordonnées': 'koordinaten',
            'Superficie': 'flaeche',
            'Substances': 'rohstofftyp',
            'Statut': 'aktivitaetsstatus'
        }
        
        for gestim_field, our_field in field_mapping.items():
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
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={}
                )
                results.append(result)
                self.logger.info(f"GESTIM Fund: {our_field} = {value}")
        
        return results
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Apify Agent beendet")