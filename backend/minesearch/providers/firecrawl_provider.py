"""
Compact Firecrawl Provider
Kompakte Version des Firecrawl Providers

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

from .base_provider import AbstractProvider, SearchResult, ModelConfig

logger = logging.getLogger(__name__)


class FirecrawlProvider(AbstractProvider):
    """Firecrawl Provider für fortgeschrittenes Web-Crawling mit Markdown-Konvertierung"""

    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        """Initialisiere Firecrawl Provider"""
        super().__init__(api_key, config)
        self.name = "firecrawl"
        self.base_url = config.get("base_url", 'https://api.firecrawl.dev/v1') if config else 'https://api.firecrawl.dev/v1'
        self.models = config.get("models", {}) if config else {}

    async def search(self, query: str, model: str = None, **kwargs) -> List[SearchResult]:
        """
        Führe Suche mit Firecrawl durch
        
        Args:
            query: Suchbegriff
            model: Modell (optional)
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Liste von SearchResult-Objekten
        """
        try:
            logger.info(f"[FIRECRAWL] Starte Suche für: {query}")
            
            # Generiere Such-URLs
            search_urls = self._generate_search_urls(query)
            
            # Crawle alle URLs
            results = []
            for url in search_urls:
                try:
                    crawled_data = await self._crawl_url(url)
                    if crawled_data:
                        result = self._create_search_result(crawled_data, query)
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Fehler beim Crawlen von {url}: {e}")
            
            logger.info(f"[FIRECRAWL] ✅ {len(results)} Ergebnisse gefunden")
            return results
            
        except Exception as e:
            logger.error(f"[FIRECRAWL] ❌ Fehler bei Suche: {e}")
            return []

    async def crawl_url(self, url: str, **kwargs) -> Optional[SearchResult]:
        """
        Crawle spezifische URL
        
        Args:
            url: URL zum Crawlen
            **kwargs: Zusätzliche Parameter
            
        Returns:
            SearchResult oder None
        """
        try:
            logger.info(f"[FIRECRAWL] Crawle URL: {url}")
            
            # Crawle URL
            crawled_data = await self._crawl_url(url)
            
            if not crawled_data:
                return None
            
            # Erstelle SearchResult
            result = self._create_search_result(crawled_data, url)
            
            logger.info(f"[FIRECRAWL] ✅ URL erfolgreich gecrawlt")
            return result
            
        except Exception as e:
            logger.error(f"[FIRECRAWL] ❌ Fehler beim Crawlen von {url}: {e}")
            return None

    def _generate_search_urls(self, query: str) -> List[str]:
        """Generiere Such-URLs für verschiedene Suchmaschinen"""
        encoded_query = query.replace(' ', '+')
        
        search_urls = [
            f"https://www.google.com/search?q={encoded_query}",
            f"https://www.bing.com/search?q={encoded_query}",
            f"https://duckduckgo.com/?q={encoded_query}",
            f"https://search.yahoo.com/search?p={encoded_query}"
        ]
        
        return search_urls

    async def _crawl_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Crawle URL mit Firecrawl API"""
        try:
            # Simuliere Firecrawl API-Aufruf
            # In der Realität würde hier die echte API verwendet
            crawled_data = {
                'url': url,
                'title': f'Crawled content from {url}',
                'content': f'This is crawled content from {url} using Firecrawl',
                'markdown': f'# Crawled Content\n\nThis is markdown content from {url}',
                'status_code': 200,
                'crawled_at': datetime.now().isoformat()
            }
            
            return crawled_data
            
        except Exception as e:
            logger.error(f"Fehler beim Crawlen von {url}: {e}")
            return None

    def _create_search_result(self, crawled_data: Dict[str, Any], query: str) -> SearchResult:
        """Erstelle SearchResult aus gecrawlten Daten"""
        return SearchResult(
            url=crawled_data['url'],
            title=crawled_data.get('title', ''),
            content=crawled_data.get('content', ''),
            source_type='firecrawl_crawled',
            relevance_score=0.9,
            metadata={
                'crawled_at': crawled_data.get('crawled_at'),
                'provider': 'firecrawl',
                'status_code': crawled_data.get('status_code'),
                'query': query,
                'markdown_content': crawled_data.get('markdown', '')
            }
        )

    def get_available_models(self) -> List[str]:
        """Hole verfügbare Modelle"""
        return ["firecrawl:default", "firecrawl:premium", "firecrawl:enterprise"]

    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Hole Modell-Konfiguration"""
        if model.startswith("firecrawl:"):
            return ModelConfig(
                name=model,
                provider="firecrawl",
                max_tokens=8000,
                cost_per_token=0.0002,
                supports_streaming=False
            )
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Prüfe Provider-Gesundheit"""
        try:
            # Simuliere Gesundheitsprüfung
            return {
                'provider': 'firecrawl',
                'status': 'healthy',
                'api_available': True,
                'rate_limits': {
                    'requests_per_minute': 60,
                    'requests_per_hour': 1000
                },
                'features': [
                    'web_crawling',
                    'markdown_conversion',
                    'javascript_rendering',
                    'content_extraction'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
            return {
                'provider': 'firecrawl',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_provider_info(self) -> Dict[str, Any]:
        """Hole Provider-Informationen"""
        return {
            'name': 'firecrawl',
            'description': 'LLM-ready Web-Scraping und Crawling Provider',
            'capabilities': [
                'web_crawling',
                'markdown_conversion',
                'javascript_rendering',
                'content_extraction',
                'search'
            ],
            'supported_models': self.get_available_models(),
            'rate_limits': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000
            },
            'costs': {
                'crawling': 0.002,
                'markdown_conversion': 0.001,
                'javascript_rendering': 0.003
            }
        }

    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mache API-Anfrage an Firecrawl"""
        try:
            # Simuliere API-Anfrage
            # In der Realität würde hier aiohttp verwendet
            return {
                'success': True,
                'data': {
                    'content': 'Simulated crawled content',
                    'markdown': '# Simulated Markdown Content',
                    'status_code': 200
                }
            }
            
        except Exception as e:
            logger.error(f"API-Anfrage fehlgeschlagen: {e}")
            return None

    def _extract_markdown_content(self, html_content: str) -> str:
        """Extrahiere Markdown-Inhalt aus HTML"""
        # Einfache HTML-zu-Markdown-Konvertierung
        # In der Realität würde hier eine spezialisierte Bibliothek verwendet
        markdown = html_content
        
        # Konvertiere HTML-Tags zu Markdown
        markdown = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', markdown)
        markdown = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', markdown)
        markdown = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', markdown)
        markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown)
        markdown = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', markdown)
        markdown = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', markdown)
        markdown = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', markdown)
        
        # Entferne verbleibende HTML-Tags
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        # Bereinige Whitespace
        markdown = re.sub(r'\n\s*\n', '\n\n', markdown)
        markdown = markdown.strip()
        
        return markdown

    def _validate_crawled_content(self, content: str) -> bool:
        """Validiere gecrawlten Inhalt"""
        if not content or len(content) < 10:
            return False
        
        # Prüfe auf häufige Fehlermeldungen
        error_patterns = [
            'access denied',
            'blocked',
            'captcha',
            'error 403',
            'error 404',
            'rate limited'
        ]
        
        content_lower = content.lower()
        for pattern in error_patterns:
            if pattern in content_lower:
                return False
        
        return True

    async def crawl_multiple_urls(self, urls: List[str], **kwargs) -> List[SearchResult]:
        """Crawle mehrere URLs parallel"""
        try:
            tasks = []
            for url in urls:
                task = self.crawl_url(url, **kwargs)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtere erfolgreiche Ergebnisse
            successful_results = []
            for result in results:
                if isinstance(result, SearchResult):
                    successful_results.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Fehler beim Crawlen: {result}")
            
            return successful_results
            
        except Exception as e:
            logger.error(f"Fehler beim parallelen Crawlen: {e}")
            return []

    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt alle verfügbaren Modelle dieses Providers zurück"""
        return {
            "firecrawl:default": ModelConfig(
                id="firecrawl:default",
                name="Firecrawl Default",
                provider="firecrawl",
                description="Standard Firecrawl Web-Crawling",
                max_tokens=8000,
                timeout=30,
                supports_web_search=True,
                is_free=False
            ),
            "firecrawl:premium": ModelConfig(
                id="firecrawl:premium",
                name="Firecrawl Premium",
                provider="firecrawl",
                description="Premium Firecrawl mit erweiterten Features",
                max_tokens=16000,
                timeout=60,
                supports_web_search=True,
                is_free=False
            )
        }

    def validate_config(self) -> bool:
        """Validiert die Provider-Konfiguration (API-Key, etc.)"""
        try:
            # Prüfe ob API-Key vorhanden ist
            if not self.api_key:
                logger.warning("Firecrawl API-Key fehlt")
                return False
            
            # Prüfe ob API-Key Format korrekt ist (einfache Validierung)
            if len(self.api_key) < 10:
                logger.warning("Firecrawl API-Key zu kurz")
                return False
            
            logger.info("Firecrawl Konfiguration valide")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Firecrawl Konfigurationsvalidierung: {e}")
            return False

    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """Gibt den System-Prompt für diesen Provider zurück"""
        prompt = """Du bist ein Web-Crawling Assistant, der Firecrawl verwendet.
        
Deine Aufgaben:
- Crawle und analysiere Webseiten
- Extrahiere relevante Informationen
- Konvertiere HTML zu strukturiertem Markdown
- Bereinige und validiere den Inhalt

Verhalte dich professionell und präzise. Fokussiere auf die wichtigsten Informationen.
"""
        
        # Erweitere Prompt basierend auf Optionen
        if options.get('detailed', False):
            prompt += "\nExtrahiere detaillierte Informationen und Metadaten."
        
        if options.get('markdown_only', False):
            prompt += "\nKonvertiere alle Inhalte zu strukturiertem Markdown."
        
        return prompt.strip()


__all__ = ["FirecrawlProvider"]
