"""
Compact Brightdata Provider
Kompakte Version des Brightdata Providers

Author: MineSearch Development Team
Date: 2025-01-11
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import quote_plus
import os

from .base_provider import AbstractProvider, SearchResult, ModelConfig
from .utils.brightdata_utils import BrightdataExtractor, BrightdataDataProcessor
from .utils.brightdata_api_client import BrightdataAPIClient
from .utils.brightdata_search_utils import BrightdataSearchUtils
from .utils.brightdata_scraper import BrightdataScraper

logger = logging.getLogger(__name__)


class BrightdataProvider(AbstractProvider):
    """Brightdata Provider für Enterprise Web-Scraping"""

    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        """Initialisiere Brightdata Provider"""
        super().__init__(api_key, config)
        self.name = "brightdata"
        self.api_key = api_key
        self.config = config or {}
        try:
            self.api_client = BrightdataAPIClient("", "")
            self.extractor = BrightdataExtractor()
            self.processor = BrightdataDataProcessor()
            self.search_utils = BrightdataSearchUtils()
            self.scraper = BrightdataScraper("", "")
        except Exception:
            # Fallback bei Initialisierungsfehlern
            self.api_client = None
            self.extractor = None
            self.processor = None
            self.search_utils = None
            self.scraper = None

    async def search(self, query: str, model: str = None, **kwargs) -> List[SearchResult]:
        """
        Führe Suche mit Brightdata durch
        
        Args:
            query: Suchbegriff
            model: Modell (optional)
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Liste von SearchResult-Objekten
        """
        try:
            logger.info(f"[BRIGHTDATA] Starte Suche für: {query}")
            
            # Generiere Suchbegriffe
            search_terms = self.search_utils.generate_search_terms(query)
            
            # Führe Suche durch
            results = []
            for term in search_terms:
                try:
                    # Scrape Ergebnisse
                    scraped_data = await self.scraper.scrape_search_results(term)
                    
                    # Verarbeite Daten
                    processed_data = self.processor.process_scraped_data(scraped_data)
                    
                    # Extrahiere relevante Informationen
                    extracted_results = self.extractor.extract_search_results(processed_data, term)
                    
                    results.extend(extracted_results)
                    
                except Exception as e:
                    logger.warning(f"Fehler bei Suche für '{term}': {e}")
            
            # Dedupliziere Ergebnisse
            unique_results = self._deduplicate_results(results)
            
            logger.info(f"[BRIGHTDATA] ✅ {len(unique_results)} Ergebnisse gefunden")
            return unique_results
            
        except Exception as e:
            logger.error(f"[BRIGHTDATA] ❌ Fehler bei Suche: {e}")
            return []

    async def scrape_url(self, url: str, **kwargs) -> Optional[SearchResult]:
        """
        Scrape spezifische URL
        
        Args:
            url: URL zum Scrapen
            **kwargs: Zusätzliche Parameter
            
        Returns:
            SearchResult oder None
        """
        try:
            logger.info(f"[BRIGHTDATA] Scrape URL: {url}")
            
            # Scrape URL
            scraped_data = await self.scraper.scrape_url(url)
            
            if not scraped_data:
                return None
            
            # Verarbeite Daten
            processed_data = self.processor.process_scraped_data(scraped_data)
            
            # Erstelle SearchResult
            result = SearchResult(
                url=url,
                title=processed_data.get('title', ''),
                content=processed_data.get('content', ''),
                source_type='brightdata_scraped',
                relevance_score=0.8,
                metadata={
                    'scraped_at': datetime.now().isoformat(),
                    'provider': 'brightdata',
                    'processing_method': 'direct_scrape'
                }
            )
            
            logger.info(f"[BRIGHTDATA] ✅ URL erfolgreich gescraped")
            return result
            
        except Exception as e:
            logger.error(f"[BRIGHTDATA] ❌ Fehler beim Scrapen von {url}: {e}")
            return None

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Entferne Duplikate aus Suchergebnissen"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results

    def get_available_models(self) -> List[str]:
        """Hole verfügbare Modelle"""
        return ["brightdata:default", "brightdata:premium"]

    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Hole Modell-Konfiguration"""
        if model.startswith("brightdata:"):
            return ModelConfig(
                name=model,
                provider="brightdata",
                max_tokens=4000,
                cost_per_token=0.0001,
                supports_streaming=False
            )
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Prüfe Provider-Gesundheit"""
        try:
            # Prüfe API-Verbindung
            api_status = await self.api_client.check_health()
            
            # Prüfe Scraper-Status
            scraper_status = await self.scraper.check_health()
            
            return {
                'provider': 'brightdata',
                'status': 'healthy' if api_status['connected'] and scraper_status['working'] else 'unhealthy',
                'api': api_status,
                'scraper': scraper_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
            return {
                'provider': 'brightdata',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_models(self) -> List[str]:
        """Abstrakte Methode: Hole verfügbare Modelle"""
        return self.get_available_models()
    
    def validate_config(self) -> bool:
        """Abstrakte Methode: Validiere Provider-Konfiguration"""
        try:
            return hasattr(self, 'api_client') and hasattr(self, 'scraper')
        except Exception:
            return False
    
    def get_system_prompt(self) -> str:
        """Abstrakte Methode: System-Prompt für Brightdata"""
        return "Du bist ein professioneller Web-Scraping Assistant für Mining-Recherchen."

    def get_provider_info(self) -> Dict[str, Any]:
        """Hole Provider-Informationen"""
        return {
            'name': 'brightdata',
            'description': 'Enterprise Web-Scraping Provider',
            'capabilities': ['web_scraping', 'search', 'url_scraping'],
            'supported_models': self.get_available_models(),
            'rate_limits': {
                'requests_per_minute': 100,
                'requests_per_hour': 1000
            },
            'costs': {
                'search': 0.01,
                'scraping': 0.005
            }
        }


__all__ = ["BrightdataProvider"]
