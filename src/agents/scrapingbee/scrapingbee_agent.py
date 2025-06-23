"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Refaktorierte ScrapingBee Agent Hauptklasse
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
from .api_client import ScrapingBeeAPIClient
from .data_parser import ScrapingBeeDataParser


class ScrapingBeeAgent(BaseAgent):
    """ScrapingBee Agent für JavaScript-rendering und komplexes Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].scrapingbee_key
        self._rate_limiter = RateLimiter(rate=50, per=60.0)  # 50 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="scrapingbee")
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Initialisiere API Client und Data Parser
        self.api_client = ScrapingBeeAPIClient(
            api_key=self.api_key,
            rate_limiter=self._rate_limiter,
            logger=self.logger
        )
        self.data_parser = ScrapingBeeDataParser(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # Initialisiere API Client
            await self.api_client.initialize()
            
            # Validiere Credentials
            is_valid = await self.api_client.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("ScrapingBee Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
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
                
                html_content = await self.api_client.scrape_url(url, scrape_config)
                if html_content:
                    # Parse HTML und extrahiere Daten
                    extracted = self.data_parser.extract_mining_data(
                        html_content, url, query
                    )
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
                        'url': f"https://mern.gouv.qc.ca/mines/titres-miniers/recherche/?nom={self.api_client.quote(query.mine_name)}",
                        'config': {'render_js': True, 'wait': 3000}
                    },
                    {
                        'url': f"https://sigeom.mines.gouv.qc.ca/signet/classes/I1108_indexAccueil?l=F&mine={self.api_client.quote(query.mine_name)}",
                        'config': {'render_js': True}
                    }
                ])
            elif query.region.lower() == 'ontario':
                urls.extend([
                    {
                        'url': f"https://www.geologyontario.mines.gov.on.ca/minesite/?search={self.api_client.quote(query.mine_name)}",
                        'config': {'render_js': True}
                    }
                ])
            
            # Pan-kanadische Quellen
            urls.extend([
                {
                    'url': f"https://www.nrcan.gc.ca/mining-materials/mining/canadian-minerals-yearbook/search?name={self.api_client.quote(query.mine_name)}",
                    'config': {'render_js': False}
                },
                {
                    'url': f"https://mining.ca/our-members/?search={self.api_client.quote(query.mine_name)}",
                    'config': {'render_js': True}
                }
            ])
        
        # Allgemeine Mining-Portale
        urls.extend([
            {
                'url': f"https://www.mining.com/?s={self.api_client.quote(query.mine_name)}",
                'config': {'render_js': False}
            },
            {
                'url': f"https://www.infomine.com/search/mines.aspx?q={self.api_client.quote(query.mine_name)}",
                'config': {'render_js': True, 'wait': 2000}
            }
        ])
        
        return urls
    
    async def _google_search_scrape(self, query: MineQuery) -> List[SearchResult]:
        """Führt Google-Suche mit ScrapingBee durch"""
        results = []
        
        search_queries = [
            f'"{query.mine_name}" mine {query.region} operator company contact',
            f'"{query.mine_name}" environmental restoration costs bonds {query.country}',
            f'"{query.mine_name}" coordinates latitude longitude location'
        ]
        
        for search_query in search_queries:
            google_url = f"https://www.google.com/search?{self.api_client.urlencode({'q': search_query})}"
            
            config = {
                'render_js': False,  # Google funktioniert ohne JS
                'block_ads': True,
                'stealth_proxy': True
            }
            
            html_content = await self.api_client.scrape_url(google_url, config)
            if html_content:
                # Parse Google-Ergebnisse
                google_results = self.data_parser.parse_google_results(
                    html_content, google_url, query
                )
                results.extend(google_results)
            
            await asyncio.sleep(2)  # Respektiere Google
        
        return results
    
    async def _get_enhanced_mining_urls(self, query: MineQuery, mining_domains: List[str]) -> List[Dict[str, Any]]:
        """Erstellt URLs für Mining-spezifische Websites"""
        urls = []
        
        for domain in mining_domains:
            # Erstelle Such-URLs für verschiedene Mining-Websites
            if "sedar.com" in domain:
                urls.append({
                    'url': f"https://www.sedar.com/search/search_form_pc_en.htm?searchType=Company&searchText={self.api_client.quote(query.mine_name)}",
                    'config': {'render_js': True, 'wait': 3000}
                })
            elif "sec.gov" in domain:
                urls.append({
                    'url': f"https://www.sec.gov/edgar/search/#/q={self.api_client.quote(query.mine_name)}%20AND%20mining",
                    'config': {'render_js': True, 'wait': 2000}
                })
            elif "tsx.com" in domain:
                urls.append({
                    'url': f"https://www.tsx.com/listings/listing-with-us/listed-company-directory?name={self.api_client.quote(query.mine_name)}",
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
                    'url': f"https://{domain}/search?q={self.api_client.quote(query.mine_name)}",
                    'config': {'render_js': True}
                })
        
        return urls
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        await self.api_client.cleanup()
        self.logger.info("ScrapingBee Agent beendet")