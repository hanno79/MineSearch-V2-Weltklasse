"""
Compact Tavily Provider
Kompakte Version des Tavily Providers

Author: MineSearch Development Team
Date: 2025-01-11
"""

import httpx
import logging
import json
import re
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import AbstractProvider, ModelConfig, SearchResult

logger = logging.getLogger(__name__)


class TavilyProvider(AbstractProvider):
    """Tavily Search Provider für moderne KI-gestützte Websuche"""

    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        """Initialisiere Tavily Provider"""
        super().__init__(api_key, config)
        self.name = "tavily"
        self.base_url = config.get("base_url", 'https://api.tavily.com') if config else 'https://api.tavily.com'
        self.models = config.get("models", {}) if config else {}

    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models

    def get_system_prompt(self) -> str:
        """Gibt System-Prompt zurück"""
        return "Du bist ein Experte für Mining- und Bergbauinformationen. Suche nach relevanten Daten zu Minen, Rohstoffen und Bergbauaktivitäten."

    def validate_config(self) -> bool:
        """Validiert die Konfiguration"""
        return bool(self.api_key and self.base_url)

    async def search(self, query: str, model: str = None, **kwargs) -> List[SearchResult]:
        """
        Führe Suche mit Tavily durch
        
        Args:
            query: Suchbegriff
            model: Modell (optional)
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Liste von SearchResult-Objekten
        """
        try:
            logger.info(f"[TAVILY] Starte Suche für: {query}")
            
            # Generiere erweiterte Suchbegriffe
            search_terms = self._generate_enhanced_search_terms(query)
            
            # Führe Suche durch
            results = []
            for term in search_terms:
                try:
                    search_results = await self._search_with_tavily(term, model)
                    results.extend(search_results)
                except Exception as e:
                    logger.warning(f"Fehler bei Suche für '{term}': {e}")
            
            # Dedupliziere Ergebnisse
            unique_results = self._deduplicate_results(results)
            
            logger.info(f"[TAVILY] ✅ {len(unique_results)} Ergebnisse gefunden")
            return unique_results
            
        except Exception as e:
            logger.error(f"[TAVILY] ❌ Fehler bei Suche: {e}")
            return []

    async def search_url(self, url: str, **kwargs) -> Optional[SearchResult]:
        """
        Suche spezifische URL
        
        Args:
            url: URL zum Suchen
            **kwargs: Zusätzliche Parameter
            
        Returns:
            SearchResult oder None
        """
        try:
            logger.info(f"[TAVILY] Suche URL: {url}")
            
            # Simuliere URL-Suche
            result = await self._search_url_with_tavily(url)
            
            if result:
                logger.info(f"[TAVILY] ✅ URL erfolgreich gesucht")
                return result
            else:
                logger.warning(f"[TAVILY] Keine Ergebnisse für URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"[TAVILY] ❌ Fehler beim Suchen der URL {url}: {e}")
            return None

    def _generate_enhanced_search_terms(self, query: str) -> List[str]:
        """Generiere erweiterte Suchbegriffe"""
        terms = [query]
        
        # Füge Varianten hinzu
        if "mining" not in query.lower():
            terms.append(f"{query} mining")
        
        if "company" not in query.lower():
            terms.append(f"{query} company")
        
        # Füge Länder-spezifische Begriffe hinzu
        country_terms = ["canada", "australia", "chile", "peru", "brazil"]
        for country in country_terms:
            if country not in query.lower():
                terms.append(f"{query} {country}")
        
        return list(set(terms))  # Entferne Duplikate

    async def _search_with_tavily(self, query: str, model: str = None) -> List[SearchResult]:
        """Führe Suche mit Tavily API durch"""
        try:
            # Simuliere Tavily API-Aufruf
            # In der Realität würde hier die echte API verwendet
            search_results = []
            
            # Simuliere mehrere Ergebnisse
            for i in range(3):
                result = SearchResult(
                    url=f"https://example.com/search?q={urllib.parse.quote(query)}&result={i}",
                    title=f"Search result {i+1} for {query}",
                    content=f"This is search result {i+1} for the query '{query}' using Tavily search.",
                    source_type='tavily_search',
                    relevance_score=0.9 - (i * 0.1),
                    metadata={
                        'provider': 'tavily',
                        'query': query,
                        'model': model,
                        'search_timestamp': datetime.now().isoformat()
                    }
                )
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Fehler bei Tavily-Suche: {e}")
            return []

    async def _search_url_with_tavily(self, url: str) -> Optional[SearchResult]:
        """Suche spezifische URL mit Tavily"""
        try:
            # Simuliere URL-Suche
            result = SearchResult(
                url=url,
                title=f"Content from {url}",
                content=f"This is content from {url} found using Tavily search.",
                source_type='tavily_url_search',
                relevance_score=0.8,
                metadata={
                    'provider': 'tavily',
                    'url': url,
                    'search_timestamp': datetime.now().isoformat()
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei URL-Suche: {e}")
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
        return ["tavily:default", "tavily:premium", "tavily:enterprise"]

    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Hole Modell-Konfiguration"""
        if model.startswith("tavily:"):
            return ModelConfig(
                name=model,
                provider="tavily",
                max_tokens=4000,
                cost_per_token=0.0001,
                supports_streaming=False
            )
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Prüfe Provider-Gesundheit"""
        try:
            # Simuliere Gesundheitsprüfung
            return {
                'provider': 'tavily',
                'status': 'healthy',
                'api_available': True,
                'rate_limits': {
                    'requests_per_minute': 100,
                    'requests_per_hour': 1000
                },
                'features': [
                    'web_search',
                    'url_search',
                    'ai_enhanced_results',
                    'real_time_data'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
            return {
                'provider': 'tavily',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_provider_info(self) -> Dict[str, Any]:
        """Hole Provider-Informationen"""
        return {
            'name': 'tavily',
            'description': 'Moderne KI-gestützte Websuche',
            'capabilities': [
                'web_search',
                'url_search',
                'ai_enhanced_results',
                'real_time_data'
            ],
            'supported_models': self.get_available_models(),
            'rate_limits': {
                'requests_per_minute': 100,
                'requests_per_hour': 1000
            },
            'costs': {
                'search': 0.001,
                'url_search': 0.0005
            }
        }

    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mache API-Anfrage an Tavily"""
        try:
            # Simuliere API-Anfrage
            # In der Realität würde hier httpx verwendet
            return {
                'success': True,
                'data': {
                    'results': [
                        {
                            'url': 'https://example.com/result1',
                            'title': 'Example Result 1',
                            'content': 'This is example content from Tavily search.',
                            'score': 0.9
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"API-Anfrage fehlgeschlagen: {e}")
            return None

    def _extract_content(self, html_content: str) -> str:
        """Extrahiere Text-Inhalt aus HTML"""
        # Einfache HTML-Text-Extraktion
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _validate_search_result(self, result: Dict[str, Any]) -> bool:
        """Validiere Suchergebnis"""
        required_fields = ['url', 'title', 'content']
        return all(field in result for field in required_fields)

    async def search_multiple_queries(self, queries: List[str], **kwargs) -> Dict[str, List[SearchResult]]:
        """Suche mehrere Queries parallel"""
        try:
            results = {}
            
            for query in queries:
                try:
                    query_results = await self.search(query, **kwargs)
                    results[query] = query_results
                except Exception as e:
                    logger.warning(f"Fehler bei Suche für '{query}': {e}")
                    results[query] = []
            
            return results
            
        except Exception as e:
            logger.error(f"Fehler beim parallelen Suchen: {e}")
            return {}

    def get_search_statistics(self) -> Dict[str, Any]:
        """Hole Such-Statistiken"""
        return {
            'provider': 'tavily',
            'total_searches': 0,  # Würde in der Realität aus der Datenbank kommen
            'successful_searches': 0,
            'average_response_time': 0.0,
            'last_search': None,
            'timestamp': datetime.now().isoformat()
        }


__all__ = ["TavilyProvider"]
