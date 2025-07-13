"""
Author: rahn
Datum: 05.07.2025
Version: 1.1
Beschreibung: Brightdata Provider für Enterprise Web-Scraping (bereinigt)
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import quote_plus

from .base_provider import AbstractProvider, SearchResult, ModelConfig
from .utils.brightdata_utils import BrightdataExtractor, BrightdataDataProcessor
from .utils.brightdata_api_client import BrightdataAPIClient
from .utils.brightdata_search_utils import BrightdataSearchUtils
from .utils.brightdata_scraper import BrightdataScraper

logger = logging.getLogger(__name__)


class BrightdataProvider(AbstractProvider):
    """Brightdata Provider für Enterprise-Grade Web-Scraping"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        # ÄNDERUNG 05.07.2025: Brightdata nutzt Customer ID in URL
        self.customer_id = api_key.split(':')[0] if ':' in api_key else api_key
        self.password = api_key.split(':')[1] if ':' in api_key else ''
        self.base_url = 'https://api.brightdata.com'
        self.models = config.get('models', {})
        self.api_client = BrightdataAPIClient(self.customer_id, self.password)
        self.extractor = BrightdataExtractor()
        self.processor = BrightdataDataProcessor()
        self.search_utils = BrightdataSearchUtils()
        self.scraper = BrightdataScraper(self.customer_id, self.password)
        
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Brightdata Modelle zurück"""
        return {
            model_id: ModelConfig(
                id=model_id,
                name=model_info['name'],
                timeout=model_info['timeout'],
                max_tokens=model_info['max_tokens'],
                description=model_info['description'],
                provider='brightdata',
                supports_web_search=model_info.get('supports_web_search', True),
                supports_deep_research=model_info.get('supports_deep_research', False),
                is_free=False
            )
            for model_id, model_info in self.models.items()
        }
    
    def validate_config(self) -> bool:
        """Validiert die Brightdata Konfiguration"""
        if not self.api_key:
            logger.error("[Brightdata] Kein API-Key konfiguriert")
            return False
        return True
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Brightdata Datenextraktion"""
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        return f"""Mining Data Extraction Task:
        
        Mine: {mine_name}
        Location: {country}
        Commodity: {commodity}
        
        Required Information:
        1. GPS Coordinates (Latitude/Longitude) - Check maps, technical reports
        2. Owner/Operator - Current ownership structure
        3. Restoration/Closure Costs - ARO, environmental liabilities, bonds
        4. Cost Year - When costs were estimated
        5. Production Timeline - Start/end years
        6. Annual Production - Tonnage or volume with units
        7. Mine Area - Square kilometers
        8. Mine Type - Underground/Open-pit/etc
        9. Activity Status - Operating/Closed/Care & Maintenance
        
        Focus on:
        - Government databases and registries
        - Technical reports (NI 43-101, JORC)
        - Financial statements and annual reports
        - Environmental assessments
        - Official mining portals
        
        Extract numerical data with units and dates."""
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führt Web-Scraping mit Brightdata durch"""
        start_time = datetime.now()
        
        try:
            if not self.validate_config():
                return SearchResult(
                    success=False,
                    content="",
                    structured_data={},
                    sources=[],
                    metadata={},
                    error="Brightdata API-Key nicht konfiguriert"
                )
            
            model_config = self.models.get(model_id)
            if not model_config:
                return SearchResult(
                    success=False,
                    content="",
                    structured_data={},
                    sources=[],
                    metadata={},
                    error=f"Unbekanntes Modell: {model_id}"
                )
            
            # Wähle Scraping-Methode basierend auf Modell
            if model_id == 'web-scraper':
                result = await self._web_scraper_search(query, options)
            elif model_id == 'browser-api':
                result = await self._browser_automation_search(query, options)
            elif model_id == 'serp':
                result = await self._search_engine_scraping(query, options)
            else:
                result = await self._web_scraper_search(query, options)
            
            search_duration = (datetime.now() - start_time).total_seconds()
            result.search_duration = search_duration
            
            return result
            
        except Exception as e:
            logger.error(f"[Brightdata] Fehler bei der Suche: {e}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    async def _web_scraper_search(self, query: str, options: Dict[str, Any]) -> SearchResult:
        """Standard Web Scraper mit Proxy-Rotation"""
        
        mine_name = options.get('mine_name', query)
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        # Baue Mining-spezifische URLs
        target_urls = await self._build_mining_urls(mine_name, country)
        
        # Scrape URLs
        scrape_results = await self.scraper.batch_scrape_urls(target_urls[:5], max_concurrent=3)
        
        # Verarbeite Ergebnisse
        scraped_data = []
        sources = []
        
        for result in scrape_results:
            if result['success'] and result['html']:
                extracted = self._extract_mining_data_from_html(result['html'], mine_name)
                if extracted:
                    scraped_data.append(extracted)
                    sources.append({
                        'id': f"source_{len(sources)+1}",
                        'value': result['url'],
                        'type': 'website',
                        'title': extracted.get('title', 'Mining Data')
                    })
        
        # Verarbeite und aggregiere Daten
        structured_data = self._aggregate_scraped_data(scraped_data, mine_name, country, commodity, options.get('region'))
        
        # Kombiniere Inhalte
        content = self._format_scraped_content(scraped_data)
        
        return SearchResult(
            success=True,
            content=content,
            structured_data=structured_data,
            sources=sources,  # KORRIGIERT: Sources werden in _web_scraping_search korrekt befüllt
            metadata={
                'provider': 'brightdata',
                'model': 'web-scraper',
                'urls_scraped': len(sources),
                'proxy_used': True
            }
        )
    
    async def _browser_automation_search(self, query: str, options: Dict[str, Any]) -> SearchResult:
        """Browser Automation mit CAPTCHA-Solving"""
        
        mine_name = options.get('mine_name', query)
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        # Baue Mining-spezifische URLs
        target_urls = await self._build_mining_urls(mine_name, country)
        
        # Scrape mit Browser API
        scrape_results = await self.scraper.batch_scrape_urls(target_urls[:3], max_concurrent=2, use_browser_api=True)
        
        # Verarbeite Ergebnisse
        scraped_data = []
        sources = []
        
        for result in scrape_results:
            if result['success'] and result['html']:
                extracted = self._extract_mining_data_from_html(result['html'], mine_name)
                if extracted:
                    # Erweiterte Extraktion für Browser API
                    extracted.update(self._extract_advanced_data(result['html'], options))
                    scraped_data.append(extracted)
                    sources.append({
                        'id': f"source_{len(sources)+1}",
                        'value': result['url'],
                        'type': 'browser_rendered',
                        'title': extracted.get('title', 'Mining Data')
                    })
        
        # Verarbeite und aggregiere Daten
        structured_data = self._aggregate_scraped_data(scraped_data, mine_name, country, commodity, options.get('region'))
        content = self._format_scraped_content(scraped_data)
        
        return SearchResult(
            success=True,
            content=content,
            structured_data=structured_data,
            sources=sources,
            metadata={
                'provider': 'brightdata',
                'model': 'browser-api',
                'urls_scraped': len(sources),
                'browser_rendered': True
            }
        )
    
    async def _search_engine_scraping(self, query: str, options: Dict[str, Any]) -> SearchResult:
        """Search Engine Scraping für Mining-Daten"""
        
        mine_name = options.get('mine_name', query)
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        # Baue Suchqueries
        search_queries = self._build_search_queries(mine_name, country, commodity)
        
        scraped_data = []
        sources = []
        
        async with aiohttp.ClientSession() as session:
            for search_query in search_queries[:3]:  # Limitiere auf 3 Suchqueries
                try:
                    # Brightdata SERP API (Search Engine Results Page)
                    # ÄNDERUNG 11.07.2025: Korrigiere Zone-Namen für SERP
                    proxy_url = f"http://brd-customer-{self.customer_id}-zone-datacenter_proxy:{self.password}@brd.superproxy.io:22225"
                    
                    # Encode search query
                    encoded_query = quote_plus(search_query)
                    search_url = f"https://www.google.com/search?q={encoded_query}"
                    
                    async with session.get(
                        search_url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Extrahiere Suchergebnisse
                            search_results = self._extract_search_results(html)
                            
                            # Scrape die gefundenen URLs
                            for result in search_results[:3]:  # Top 3 Ergebnisse pro Query
                                result_url = result.get('url')
                                if result_url:
                                    # Scrape die gefundene Seite
                                    page_data = await self._scrape_search_result(session, result_url, mine_name)
                                    if page_data:
                                        scraped_data.append(page_data)
                                        sources.append({
                                            'id': f"source_{len(sources)+1}",
                                            'value': result_url,
                                            'type': 'search_result',
                                            'title': result.get('title', 'Search Result'),
                                            'snippet': result.get('snippet', '')
                                        })
                        elif response.status == 407:
                            logger.error(f"[Brightdata] Authentication failed for SERP API")
                            break
                                
                except Exception as e:
                    logger.error(f"[Brightdata SERP] Fehler bei Suche '{search_query}': {e}")
        
        # Verarbeite und aggregiere Daten
        structured_data = self._aggregate_scraped_data(scraped_data, mine_name, country, commodity, options.get('region'))
        content = self._format_search_results(scraped_data, sources)
        
        return SearchResult(
            success=True,
            content=content,
            structured_data=structured_data,
            sources=sources,
            metadata={
                'provider': 'brightdata',
                'model': 'serp',
                'queries_executed': len(search_queries),
                'results_found': len(sources)
            }
        )
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        ÄNDERUNG 05.07.2025: Implementierung für Cross-Provider Source Sharing
        Nutzt Brightdata Proxies um die übergebenen URLs zu scrapen
        """
        
        if not sources:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error="Keine Quellen zum Scrapen"
            )
        
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        scraped_data = []
        successful_sources = []
        
        # Extrahiere URLs aus sources
        url_sources = [s for s in sources if s.get('type') in ['url', 'website', None]]
        
        async with aiohttp.ClientSession() as session:
            for source in url_sources[:10]:  # Limitiere auf 10 URLs
                url = source.get('url') or source.get('value', '')
                if not url or not url.startswith('http'):
                    continue
                
                try:
                    # Nutze Brightdata Proxy
                    if self.customer_id and self.password:
                        proxy_url = f"http://brd-customer-{self.customer_id}-zone-web_unlocker:{self.password}@brd.superproxy.io:22225"
                        
                        async with session.get(
                            url,
                            proxy=proxy_url,
                            timeout=aiohttp.ClientTimeout(total=30),
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                        ) as response:
                            if response.status == 200:
                                html = await response.text()
                                extracted = self._extract_mining_data_from_html(html, mine_name)
                                if extracted:
                                    scraped_data.append(extracted)
                                    successful_sources.append({
                                        'id': f"source_{len(successful_sources)+1}",
                                        'value': url,
                                        'type': 'website',
                                        'title': source.get('title', 'Mining Data')
                                    })
                                    
                except Exception as e:
                    logger.error(f"[Brightdata] Fehler beim Scrapen von {url}: {e}")
        
        # Verarbeite Daten
        structured_data = self._aggregate_scraped_data(scraped_data, mine_name, country, commodity, options.get('region'))
        content = self._format_scraped_content(scraped_data)
        
        return SearchResult(
            success=True,
            content=content,
            structured_data=structured_data,
            sources=successful_sources,
            metadata={
                'provider': 'brightdata',
                'model': model_id,
                'urls_scraped': len(successful_sources),
                'phase': 'source_sharing'
            }
        )
    
    async def _build_mining_urls(self, mine_name: str, country: str) -> List[str]:
        """Erstelle Mining-spezifische URLs"""
        return self.processor.build_search_urls(mine_name, country)
    
    def _extract_mining_data_from_html(self, html: str, mine_name: str) -> Dict[str, Any]:
        """Extrahiere Mining-Daten aus HTML"""
        options = {'mine_name': mine_name}
        return self.extractor.extract_mining_data(html, options)
    
    def _aggregate_scraped_data(self, scraped_data: List[Dict], mine_name: str, 
                               country: str, commodity: str, region: str) -> Dict[str, Any]:
        """Aggregiere gescrapte Daten zu strukturiertem Format"""
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region
        }
        return self.processor.process_search_results(scraped_data, options)
    
    def _format_scraped_content(self, scraped_data: List[Dict]) -> str:
        """Formatiere gescrapte Daten als lesbaren Content"""
        return self.search_utils.format_scraped_content(scraped_data)
    
    def _extract_advanced_data(self, html: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Erweiterte Datenextraktion für Browser API"""
        return self.search_utils.extract_advanced_data(html, options)
    
    def _build_search_queries(self, mine_name: str, country: str, commodity: str) -> List[str]:
        """Erstellt optimierte Suchqueries für Mining-Daten"""
        return self.search_utils.build_search_queries(mine_name, country, commodity)
    
    def _extract_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Extrahiert Suchergebnisse aus Google SERP HTML"""
        return self.search_utils.extract_search_results(html)
    
    async def _scrape_search_result(self, session: aiohttp.ClientSession, 
                                   url: str, mine_name: str) -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne Suchergebnis-URL"""
        try:
            # Nutze Standard Web Unlocker für Suchergebnisse
            proxy_url = f"http://brd-customer-{self.customer_id}-zone-web_unlocker:{self.password}@brd.superproxy.io:22225"
            
            async with session.get(
                url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=20),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; MiningBot/1.0)'}
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._extract_mining_data_from_html(html, mine_name)
        except Exception as e:
            logger.debug(f"[Brightdata] Konnte {url} nicht scrapen: {e}")
        
        return None
    
    def _format_search_results(self, scraped_data: List[Dict], sources: List[Dict]) -> str:
        """Formatiert Suchergebnisse für bessere Lesbarkeit"""
        content = "BRIGHTDATA SEARCH ENGINE ERGEBNISSE\n" + "="*50 + "\n\n"
        
        # Gruppiere nach Datentyp
        coords_found = False
        owner_found = False
        costs_found = False
        
        for data in scraped_data:
            if data.get('latitude') or data.get('longitude'):
                coords_found = True
            if data.get('owner_operator'):
                owner_found = True
            if data.get('restoration_costs') or data.get('table_cost'):
                costs_found = True
        
        content += f"Gefundene Datentypen:\n"
        content += f"- Koordinaten: {'✓' if coords_found else '✗'}\n"
        content += f"- Eigentümer/Betreiber: {'✓' if owner_found else '✗'}\n"
        content += f"- Kosten: {'✓' if costs_found else '✗'}\n\n"
        
        # Detaillierte Ergebnisse
        content += "Detaillierte Funde:\n" + "-"*30 + "\n"
        for i, (data, source) in enumerate(zip(scraped_data, sources), 1):
            if data:
                content += f"\nQuelle {i}: {source.get('title', 'N/A')}\n"
                content += f"URL: {source.get('value', 'N/A')}\n"
                
                for key, value in data.items():
                    if value and key != 'mine_name' and key != 'title':
                        content += f"- {key}: {value}\n"
        
        return content