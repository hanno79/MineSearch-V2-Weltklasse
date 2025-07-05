"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Firecrawl Provider für LLM-ready Web-Scraping und Crawling
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .base_provider import AbstractProvider, SearchResult, ModelConfig
from .utils.firecrawl_utils import FirecrawlExtractor, FirecrawlDataProcessor
from .utils.firecrawl_url_builder import FirecrawlURLBuilder
from .utils.firecrawl_api_client import FirecrawlAPIClient

logger = logging.getLogger(__name__)


class FirecrawlProvider(AbstractProvider):
    """Firecrawl Provider für fortgeschrittenes Web-Crawling mit Markdown-Konvertierung"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.base_url = config.get('base_url', 'https://api.firecrawl.dev/v1')
        self.models = config.get('models', {})
        self.api_client = FirecrawlAPIClient(api_key, self.base_url)
        
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Firecrawl Modelle zurück"""
        return {
            model_id: ModelConfig(
                id=model_id,
                name=model_info['name'],
                timeout=model_info['timeout'],
                max_tokens=model_info['max_tokens'],
                description=model_info['description'],
                provider='firecrawl',
                supports_web_search=model_info.get('supports_web_search', True),
                supports_deep_research=model_info.get('supports_deep_research', False),
                is_free=False
            )
            for model_id, model_info in self.models.items()
        }
    
    def validate_config(self) -> bool:
        """Validiert die Firecrawl Konfiguration"""
        if not self.api_key:
            logger.error("[Firecrawl] Kein API-Key konfiguriert")
            return False
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        ÄNDERUNG 05.07.2025: Implementierung für Cross-Provider Source Sharing
        Crawled und konvertiert die übergebenen URLs zu Markdown
        """
        
        if not sources:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error="Keine Quellen zum Crawlen"
            )
        
        start_time = datetime.now()
        crawled_data = []
        successful_sources = []
        
        # Extrahiere URLs aus sources
        url_sources = [s for s in sources if s.get('type') in ['url', 'website', None]]
        
        # Crawle URLs
        for source in url_sources[:8]:  # Limitiere auf 8 URLs
            url = source.get('url') or source.get('value', '')
            if not url or not url.startswith('http'):
                continue
                
            try:
                if model_id == 'scrape':
                    result = await self._scrape_single_url(url)
                elif model_id == 'crawl':
                    # Crawl mit Session
                    async with aiohttp.ClientSession() as crawl_session:
                        crawl_results = await self._crawl_website(crawl_session, url, {'mine_name': options.get('mine_name', '')})
                        if crawl_results:
                            # Aggregiere alle gecrawlten Seiten
                            result = {
                                'url': url,
                                'markdown': '\n\n'.join([r.get('markdown', '') for r in crawl_results]),
                                'title': crawl_results[0].get('title', 'Crawled Data') if crawl_results else 'Mining Data',
                                'tokens': sum(len(r.get('markdown', '').split()) for r in crawl_results)
                            }
                else:
                    result = await self._extract_from_url(url, options)
                
                if result and result.get('markdown'):
                    crawled_data.append(result)
                    successful_sources.append({
                        'id': f"source_{len(successful_sources)+1}",
                        'value': url,
                        'type': 'website',
                        'title': result.get('title', source.get('title', 'Mining Data'))
                    })
            except Exception as e:
                logger.error(f"[Firecrawl] Fehler beim Crawlen von {url}: {e}")
        
        # Verarbeite gecrawlte Daten
        structured_data = await self._process_crawled_data(crawled_data, options)
        
        # Kombiniere Markdown-Inhalte
        combined_content = "\n\n---\n\n".join([d.get('markdown', '') for d in crawled_data])
        
        search_duration = (datetime.now() - start_time).total_seconds()
        
        return SearchResult(
            success=True,
            content=combined_content,
            structured_data=structured_data,
            sources=successful_sources,
            metadata={
                'provider': 'firecrawl',
                'model': model_id,
                'search_duration': search_duration,
                'urls_crawled': len(successful_sources),
                'phase': 'source_sharing',
                'total_tokens': sum(d.get('tokens', 0) for d in crawled_data)
            }
        )
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Firecrawl AI-Extraktion"""
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        
        return f"""Extrahiere strukturierte Mining-Daten für "{mine_name}" in {country}.
        
        Fokussiere auf:
        - GPS-Koordinaten (Latitude/Longitude)
        - Eigentümer und Betreiber
        - Restaurations-/Schließungskosten (ARO, Environmental Liability)
        - Produktionsdaten (Start, Ende, Fördermengen)
        - Minentyp und Fläche
        - PDF-Links zu technischen Reports
        
        Suche nach Tabellen mit finanziellen Daten und technischen Spezifikationen.
        Extrahiere alle relevanten Zahlen mit Einheiten und Jahresangaben."""
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führt Web-Crawling mit Firecrawl durch"""
        start_time = datetime.now()
        
        try:
            if not self.validate_config():
                return SearchResult(
                    success=False,
                    content="",
                    structured_data={},
                    sources=[],
                    metadata={},
                    error="Firecrawl API-Key nicht konfiguriert"
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
            
            # Erstelle Mining-spezifische URLs
            urls = await self._build_target_urls(options)
            
            results = []
            sources = []
            
            async with aiohttp.ClientSession() as session:
                # Wähle API-Methode basierend auf Modell
                if model_id == 'scrape':
                    # Einzelseiten-Scraping
                    for url in urls[:3]:  # Limit für Einzelseiten
                        result = await self._scrape_single(session, url, options)
                        if result:
                            results.append(result)
                            sources.append({
                                'id': f"source_{len(sources)+1}",
                                'value': url,
                                'type': 'website',
                                'title': result.get('title', 'Mining Document')
                            })
                
                elif model_id == 'crawl':
                    # Website-Crawling
                    for base_url in urls[:1]:  # Nur eine Domain crawlen
                        crawl_results = await self._crawl_website(session, base_url, options)
                        results.extend(crawl_results)
                        for idx, result in enumerate(crawl_results):
                            sources.append({
                                'id': f"source_{len(sources)+1}",
                                'value': result.get('url', base_url),
                                'type': 'crawled_page',
                                'title': result.get('title', f'Page {idx+1}')
                            })
                
                elif model_id == 'extract':
                    # AI-Extraktion
                    for url in urls[:2]:  # Limit für AI-Extraktion
                        result = await self._extract_structured(session, url, options)
                        if result:
                            results.append(result)
                            sources.append({
                                'id': f"source_{len(sources)+1}",
                                'value': url,
                                'type': 'ai_extraction',
                                'title': 'Structured Data'
                            })
            
            # Verarbeite Ergebnisse
            structured_data = await self._process_results(results, options)
            
            # Kombiniere Markdown-Inhalte
            combined_content = self._combine_markdown_content(results)
            
            search_duration = (datetime.now() - start_time).total_seconds()
            
            return SearchResult(
                success=True,
                content=combined_content,
                structured_data=structured_data,
                sources=sources,
                metadata={
                    'provider': 'firecrawl',
                    'model': model_id,
                    'search_duration': search_duration,
                    'pages_processed': len(results),
                    'markdown_length': len(combined_content)
                }
            )
            
        except Exception as e:
            logger.error(f"[Firecrawl] Fehler bei der Suche: {e}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    async def _build_target_urls(self, options: Dict[str, Any]) -> List[str]:
        """Baut zielgerichtete URLs für Mining-Informationen"""
        url_builder = FirecrawlURLBuilder()
        return url_builder.build_target_urls(options)
    
    async def _scrape_single(self, session: aiohttp.ClientSession, 
                           url: str, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne Seite mit Firecrawl"""
        result = await self.api_client.scrape_single(session, url)
        if result:
            result['tables'] = []  # Tabellen-Extraktion wurde entfernt
        return result
    
    async def _crawl_website(self, session: aiohttp.ClientSession,
                           base_url: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawlt eine komplette Website"""
        mine_name = options.get('mine_name', '')
        
        # Erstelle Crawl-Parameter
        crawl_options = {
            'limit': 10,
            'maxDepth': 2
        }
        
        # Füge includePaths hinzu wenn Minenname vorhanden
        if mine_name:
            processor = FirecrawlDataProcessor()
            crawl_options = processor.build_crawl_params(base_url, options)
        
        # Starte Crawl
        job_id = await self.api_client.start_crawl(session, base_url, crawl_options)
        if not job_id:
            return []
        
        # Warte auf Completion
        return await self.api_client.wait_for_crawl_completion(session, job_id)
    
    
    async def _extract_structured(self, session: aiohttp.ClientSession,
                                url: str, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Führt AI-basierte strukturierte Extraktion durch"""
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Schema für Mining-Daten
        schema = {
            'type': 'object',
            'properties': {
                'coordinates': {
                    'type': 'object',
                    'properties': {
                        'latitude': {'type': 'number'},
                        'longitude': {'type': 'number'}
                    }
                },
                'ownership': {
                    'type': 'object',
                    'properties': {
                        'owner': {'type': 'string'},
                        'operator': {'type': 'string'}
                    }
                },
                'costs': {
                    'type': 'object',
                    'properties': {
                        'restoration_cost': {'type': 'string'},
                        'cost_year': {'type': 'string'},
                        'currency': {'type': 'string'}
                    }
                },
                'production': {
                    'type': 'object',
                    'properties': {
                        'start_year': {'type': 'string'},
                        'end_year': {'type': 'string'},
                        'annual_production': {'type': 'string'},
                        'commodity': {'type': 'string'}
                    }
                },
                'technical': {
                    'type': 'object',
                    'properties': {
                        'mine_type': {'type': 'string'},
                        'area_sqkm': {'type': 'number'},
                        'status': {'type': 'string'}
                    }
                }
            }
        }
        
        # ÄNDERUNG 05.07.2025: Minimale Struktur für Firecrawl v1
        payload = {
            'url': url
            # Extract als separater Endpoint nicht unterstützt
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            async with session.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'url': url,
                        'extracted': data.get('extract', {}),
                        'markdown': data.get('markdown', '')
                    }
                else:
                    error = await response.text()
                    logger.error(f"[Firecrawl] Extract fehlgeschlagen: {error}")
                    return None
                    
        except Exception as e:
            logger.error(f"[Firecrawl] Fehler bei Extract: {e}")
            return None
    
    
    def _combine_markdown_content(self, results: List[Dict[str, Any]]) -> str:
        """Kombiniert Markdown-Inhalte aus mehreren Quellen"""
        combined = []
        
        for idx, result in enumerate(results):
            if 'markdown' in result and result['markdown']:
                combined.append(f"## Quelle {idx + 1}: {result.get('title', result.get('url', 'Unbekannt'))}")
                combined.append(result['markdown'])
                combined.append("\n---\n")
            
            if 'extracted' in result and result['extracted']:
                combined.append(f"## Extrahierte Daten von {result.get('url', 'Unbekannt')}")
                combined.append("```json")
                combined.append(json.dumps(result['extracted'], indent=2, ensure_ascii=False))
                combined.append("```")
                combined.append("\n---\n")
        
        return '\n'.join(combined)
    
    async def _process_results(self, results: List[Dict[str, Any]], 
                             options: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet Firecrawl-Ergebnisse zu strukturierten Daten"""
        # Nutze FirecrawlDataProcessor für die Verarbeitung
        processor = FirecrawlDataProcessor()
        mine_name = options.get('mine_name', '')
        
        # Wenn results bereits strukturierte Daten enthalten, verwende diese
        if results and any('extracted' in r for r in results):
            # Aggregiere extrahierte Daten
            aggregated_data = processor.process_crawled_data(results, mine_name)
            # Füge zusätzliche Optionen hinzu
            aggregated_data['Country'] = options.get('country', '')
            aggregated_data['Region'] = options.get('region', '-')
            aggregated_data['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'] = options.get('commodity', '-')
            return aggregated_data
        
        # Fallback: Verarbeite Markdown-Inhalte
        return processor.process_crawled_data(results, mine_name)
    
    async def _scrape_single_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne URL mit Firecrawl"""
        async with aiohttp.ClientSession() as session:
            return await self.api_client.scrape_single(session, url)
    
    async def _process_crawled_data(self, crawled_data: List[Dict[str, Any]], 
                                   options: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet gecrawlte Daten zu strukturierten Mining-Informationen"""
        processor = FirecrawlDataProcessor()
        return processor.process_crawled_data(crawled_data, options.get('mine_name', ''))
    
    async def _extract_from_url(self, url: str, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI-basierte Extraktion mit Fallback auf normales Scraping"""
        result = await self._scrape_single_url(url)
        
        if result and result.get('markdown'):
            extractor = FirecrawlExtractor()
            mine_name = options.get('mine_name', '')
            extracted_data = extractor.extract_mining_data(result['markdown'], mine_name)
            result['extracted'] = extracted_data
        
        return result