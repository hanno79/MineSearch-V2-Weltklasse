"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Refactored Bright Data Agent mit Base-Modulen
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .base import BaseHTTPClient, ResultProcessor, QueryBuilder, CacheManager
from .brightdata_scraper import BrightDataScraper
from .brightdata_parser import BrightDataParser
from src.core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class BrightDataAgent(BaseAgent):
    """Refactored Bright Data Agent mit Base-Modulen"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].brightdata_key
        self.base_url = "https://api.brightdata.com"
        self.logger = get_logger(f"agent.{name}", agent_type="brightdata")
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Base-Module initialisieren
        self.http_client = BaseHTTPClient(
            timeout=120,
            max_retries=3,
            rate_limit=0.6,  # 100 pro Minute = 0.6s zwischen Requests
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        self.result_processor = BrightDataResultProcessor("BrightData")
        self.query_builder = QueryBuilder()
        self.cache_manager = CacheManager(
            cache_dir="cache/brightdata",
            default_ttl=3600
        )
        
        # Spezialisierte Module
        self.scraper = BrightDataScraper(self.http_client, self.logger)
        self.parser = BrightDataParser(self.logger)
        
        # Proxy-Konfiguration
        self.proxy_config = {
            'datacenter': True,
            'residential': False,
            'mobile': False
        }
    
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            await self.http_client.start()
            
            if not await self.validate_credentials():
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Bright Data Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Bright Data API-Key konfiguriert")
            return False
            
        try:
            response = await self.http_client.get(f"{self.base_url}/account_info")
            return isinstance(response, dict) and response.get('status') == 'active'
        except:
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Mining-Suche durch"""
        # Cache prüfen
        cache_key = query.dict()
        cached_results = await self.cache_manager.get("search", cache_key)
        if cached_results:
            self.logger.info(f"Cache Hit für {query.mine_name}")
            return cached_results
        
        results = []
        self.perf_logger.start_timer(f"brightdata_search_{query.mine_name}")
        
        try:
            # Mining-spezifische Queries und Domains
            mining_queries = get_mining_search_queries(
                query.mine_name, 
                query.region, 
                query.country
            )[:20]
            mining_domains = get_mining_domains()[:20]
            
            # Status-Update
            await self._update_status("Bright Data: Starte Enterprise Mining-Suche")
            
            # 1. URL-Sammlung
            urls = await self._collect_mining_urls(query, mining_queries, mining_domains)
            
            # 2. Parallel Scraping
            if urls:
                results = await self._scrape_urls(urls[:30], query, mining_queries)
            
            # 3. Spezialisierte Datensammlung
            specialized = await self._collect_specialized_data(query, mining_domains)
            results.extend(specialized)
            
            # Deduplizierung und Scoring
            results = self.result_processor.deduplicate_across_sources(results)
            for result in results:
                result.confidence = self.result_processor.calculate_relevance_score(
                    result, query
                )
            
            # Ergebnisse cachen
            await self.cache_manager.set("search", cache_key, results)
            
            # Performance logging
            self.perf_logger.end_timer(
                f"brightdata_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Statistiken aktualisieren
            self._update_stats(len(results))
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    async def _collect_mining_urls(self, 
                                  query: MineQuery, 
                                  mining_queries: List[str],
                                  mining_domains: List[str]) -> List[str]:
        """Sammelt Mining-URLs über SERP API"""
        urls = []
        
        for idx, search_query in enumerate(mining_queries):
            await self._update_status(f"Bright Data: Suche {idx+1}/{len(mining_queries)}")
            
            try:
                # Nutze Query Builder für strukturierte Queries
                structured_query = self.query_builder.build_advanced_query(
                    query,
                    exact_phrases=["mining", query.mining_type] if query.mining_type else ["mining"]
                )
                
                collector_params = {
                    "collector": "search_engine",
                    "query": structured_query,
                    "search_engine": "google",
                    "country": self._get_country_code(query.country),
                    "num_results": 30,
                    "include_domains": mining_domains[:10],
                    "language": self._get_language_code(query.languages)
                }
                
                response = await self.scraper.run_collector(collector_params)
                
                if response and 'organic_results' in response:
                    for result in response['organic_results']:
                        url = result.get('link')
                        title = result.get('title', '')
                        if url and self._is_mining_relevant(url, title, query):
                            urls.append(url)
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"URL Collection Fehler: {e}")
        
        return list(set(urls))  # Deduplizieren
    
    async def _scrape_urls(self, 
                          urls: List[str], 
                          query: MineQuery,
                          mining_queries: List[str]) -> List[SearchResult]:
        """Scraped URLs parallel"""
        tasks = []
        
        for idx, url in enumerate(urls):
            if idx % 5 == 0:
                await self._update_status(f"Bright Data: Scrape {idx+1}/{len(urls)} URLs")
            
            task = self._scrape_single_url(url, query)
            tasks.append(task)
        
        scraped_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for result in scraped_results:
            if isinstance(result, list):
                results.extend(result)
        
        return results
    
    async def _scrape_single_url(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Scraped eine einzelne URL"""
        try:
            # Scraping durchführen
            content = await self.scraper.scrape_url(
                url,
                proxy_type=self._select_proxy_type(url),
                country=self._get_country_code(query.country),
                render_js=self._needs_javascript(url)
            )
            
            if content:
                # Parsing mit spezialisiertem Parser
                extracted = self.parser.extract_mining_data(content, url, query)
                
                # In SearchResults konvertieren
                results = []
                for data in extracted:
                    result = self.result_processor.create_result(
                        title=data.get('title', ''),
                        url=url,
                        snippet=data.get('snippet', ''),
                        confidence=data.get('confidence', 0.5),
                        metadata=data.get('metadata', {}),
                        source_type=data.get('source_type', 'web')
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Scraping-Fehler für {url}: {e}")
            
        return []
    
    async def _collect_specialized_data(self, 
                                      query: MineQuery,
                                      mining_domains: List[str]) -> List[SearchResult]:
        """Sammelt spezialisierte Mining-Daten"""
        results = []
        
        # Spezialisierte Collector für Mining-Daten
        specialized_collectors = [
            {
                "collector": "business_data",
                "query": f"{query.mine_name} mining company",
                "data_type": "company_info"
            },
            {
                "collector": "news",
                "query": f"{query.mine_name} mining",
                "time_range": "last_year"
            },
            {
                "collector": "social_media",
                "query": query.mine_name,
                "platforms": ["linkedin", "twitter"]
            }
        ]
        
        for collector_config in specialized_collectors:
            try:
                response = await self.scraper.run_collector(collector_config)
                if response:
                    parsed = self.parser.parse_specialized_data(
                        response, 
                        collector_config['collector'],
                        query
                    )
                    
                    for item in parsed:
                        result = self.result_processor.create_result(
                            title=item['title'],
                            url=item['url'],
                            snippet=item['snippet'],
                            metadata=item.get('metadata', {}),
                            source_type=collector_config['collector']
                        )
                        results.append(result)
                        
            except Exception as e:
                self.logger.error(f"Specialized collection error: {e}")
        
        return results
    
    async def _update_status(self, message: str):
        """Sendet Status-Update"""
        if hasattr(self, 'status_callback') and self.status_callback:
            await self.status_callback(message)
    
    def _update_stats(self, results_found: int):
        """Aktualisiert Statistiken"""
        self.stats['total_requests'] += 1
        self.stats['successful_requests'] += 1 if results_found > 0 else 0
        self.stats['total_fields_found'] += results_found
    
    def _is_mining_relevant(self, url: str, title: str, query: MineQuery) -> bool:
        """Prüft Mining-Relevanz"""
        keywords = self.query_builder.extract_keywords(query)
        
        # URL und Titel prüfen
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Mindestens 2 Keywords müssen vorkommen
        matches = 0
        for keyword in keywords:
            if keyword in url_lower or keyword in title_lower:
                matches += 1
                if matches >= 2:
                    return True
        
        return False
    
    def _select_proxy_type(self, url: str) -> str:
        """Wählt Proxy-Typ basierend auf URL"""
        # Sensible Domains erfordern Residential Proxies
        sensitive_domains = ['linkedin.com', 'facebook.com', 'gov.']
        
        for domain in sensitive_domains:
            if domain in url:
                return 'residential'
        
        return 'datacenter'
    
    def _needs_javascript(self, url: str) -> bool:
        """Prüft ob JavaScript-Rendering benötigt wird"""
        js_sites = ['linkedin', 'facebook', 'twitter', 'maps', 'react', 'angular']
        return any(site in url.lower() for site in js_sites)
    
    def _get_country_code(self, country: Optional[str]) -> str:
        """Konvertiert Land zu Code"""
        country_map = {
            'Canada': 'ca',
            'USA': 'us',
            'Australia': 'au',
            'South Africa': 'za',
            'Chile': 'cl',
            'Peru': 'pe'
        }
        return country_map.get(country, 'us')
    
    def _get_language_code(self, languages: Optional[List[str]]) -> str:
        """Ermittelt Sprachcode"""
        if not languages:
            return 'en'
        
        lang_map = {
            'English': 'en',
            'French': 'fr',
            'Spanish': 'es',
            'German': 'de'
        }
        return lang_map.get(languages[0], 'en')
    
    def _get_accept_languages(self, languages: Optional[List[str]]) -> str:
        """Generiert Accept-Language Header"""
        if not languages:
            return 'en-US,en;q=0.9'
        
        lang_codes = []
        for lang in languages[:3]:
            code = self._get_language_code([lang])
            lang_codes.append(f"{code};q={0.9 - len(lang_codes) * 0.1}")
        
        return ','.join(lang_codes)
    
    async def close(self):
        """Schließt den Agenten"""
        await self.http_client.close()
        await super().close()


class BrightDataResultProcessor(ResultProcessor):
    """Spezialisierter Result Processor für Bright Data"""
    
    def _extract_result(self, raw: Dict[str, Any], query: MineQuery) -> Optional[SearchResult]:
        """Extrahiert SearchResult aus Bright Data Daten"""
        # Bright Data spezifisches Format
        title = raw.get('title', raw.get('name', ''))
        url = raw.get('url', raw.get('link', ''))
        snippet = raw.get('snippet', raw.get('description', ''))
        
        if not title or not url:
            return None
        
        # Metadaten sammeln
        metadata = {
            'proxy_type': raw.get('proxy_type', 'datacenter'),
            'scraped_at': raw.get('timestamp', datetime.now().isoformat()),
            'collector': raw.get('collector', 'web_scraper'),
            'title': title,
            'snippet': snippet,
            'mine_name': query.mine_name
        }
        
        # Zusätzliche Daten wenn vorhanden
        if 'company_data' in raw:
            metadata['company_info'] = raw['company_data']
        if 'social_metrics' in raw:
            metadata['social_metrics'] = raw['social_metrics']
        
        # SearchResult im korrekten Format erstellen
        return SearchResult(
            mine_name=query.mine_name,
            field_name='search_result',
            value=title,
            source=self.agent_name,
            source_url=url,
            source_date=raw.get('source_date'),
            confidence_score=raw.get('relevance_score', 0.5),
            agent_name=self.agent_name,
            timestamp=datetime.now(),
            metadata=metadata
        )