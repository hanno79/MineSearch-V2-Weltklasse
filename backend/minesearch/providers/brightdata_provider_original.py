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
import os
import tempfile

from .base_provider import AbstractProvider, SearchResult, ModelConfig
from .utils.brightdata_utils import BrightdataExtractor, BrightdataDataProcessor
from .utils.brightdata_api_client import BrightdataAPIClient
from .utils.brightdata_search_utils import BrightdataSearchUtils
from .utils.brightdata_scraper import BrightdataScraper

# OPENROUTER WORKFLOW IMPORTS
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.source_discovery import extract_sources_from_content
from minesearch.utils import (
    generate_name_variants,
    get_country_config,
    generate_multilingual_search_terms,
)
from minesearch.specialized_prompts_impl import SpecializedPrompts

logger = logging.getLogger(__name__)

def _save_debug_html(html_content: str, url: str, mine_name: str = None) -> Optional[str]:  # REGEL
    """_save_debug_html - TODO: Dokumentation hinzufügen"""
10: NULL statt 'unknown' Fallback
    """
    DEBUGGING 30.08.2025: Speichere HTML für Debug-Analyse
    """
    try:
        # Erstelle Debug-Verzeichnis falls nicht vorhanden
        debug_dir = "/tmp/brightdata_debug_html"
        os.makedirs(debug_dir, exist_ok=True)

        # Erstelle filename aus URL und Mine
        safe_filename = re.sub(r'[^\w\-_.]', '_', f"{mine_name}_{url.split('/')[-1]}")[:100]
        filename = f"{datetime.now().strftime('%H%M%S')}_{safe_filename}.html"
        filepath = os.path.join(debug_dir, filename)

        # Speichere HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"[BrightData-DEBUG] HTML saved: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"[BrightData-DEBUG] Failed to save HTML: {e}")
        return None

class BrightdataProvider(AbstractProvider):
    """Brightdata Provider für Enterprise-Grade Web-Scraping"""

    def __init__(self, api_key: str, config: Dict[str, Any]):
    """__init__ - TODO: Dokumentation hinzufügen"""
        super().__init__(api_key, config)
        # ÄNDERUNG 05.07.2025: Brightdata nutzt Customer ID in URL
        self.customer_id = api_key.split(':')[0] if ':' in api_key else api_key
        self.password = api_key.split(':')[1] if ':' in api_key else ''
        self.base_url = 'https://api.brightdata.com'
        self.models = config.get("models", {})
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
                supports_web_search=model_info.get("supports_web_search", True),
                supports_deep_research=model_info.get("supports_deep_research", False),
                is_free=False,
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='brightdata'
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
        mine_name = options.get("mine_name", '')
        country = options.get("country", '')
        commodity = options.get("commodity", '')

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

            # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
            mine_name = options.get("mine_name", '')
            country = options.get('country')
            commodity = options.get('commodity')
            region = options.get('region')

            discovered_sources = options.get("discovered_sources", [])
            use_all_sources = options.get("use_all_sources", False)
            skip_discovery = options.get("skip_discovery", False)

            source_discovery = EnhancedSourceDiscovery()

            if not discovered_sources and not skip_discovery and mine_name:
                # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
                logger.info(f"[BRIGHTDATA] Starte eigene Source Discovery für {mine_name}")
                discovered_sources = source_discovery.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region
                )
                logger.info(f"[BRIGHTDATA] {len(discovered_sources)} Quellen selbst entdeckt")
            else:
                if use_all_sources:
                    logger.info(f"[BRIGHTDATA] 🔥 2-PHASEN WORKFLOW: Nutze ALLE
{len(discovered_sources)} übergebenen DB-Quellen ohne Filter")
                else:
                    logger.info(f"[BRIGHTDATA] Nutze {len(discovered_sources)} übergebene Quellen")

            # Generiere Sprachvarianten (wie OpenRouter)
            name_variants = generate_name_variants(mine_name) if mine_name else []
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)

            # Erweitere Options für Untermethoden
            enhanced_options = options.copy()
            enhanced_options.update({
                'discovered_sources': discovered_sources,
                'name_variants': name_variants,
                'multilingual_terms': multilingual_terms,
                'use_all_sources': use_all_sources
            })

            # Wähle Scraping-Methode basierend auf Modell
            if model_id == 'web-scraper':
                result = await self._web_scraper_search(query, enhanced_options)
            elif model_id == 'browser-api':
                result = await self._browser_automation_search(query, enhanced_options)
            elif model_id == 'serp':
                result = await self._search_engine_scraping(query, enhanced_options)
            else:
                try:
                    result = await self._web_scraper_search(query, enhanced_options)
                except Exception as e:
                    logger.error(f"[BrightData] DETAILED EXCEPTION in _web_scraper_search: {type(e).__name__}: {e}")
                    import traceback
                    logger.error(f"[BrightData] STACK TRACE: {traceback.format_exc()}")
                    raise

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

        mine_name = options.get("mine_name", query)
        country = options.get("country", '')
        commodity = options.get("commodity", '')

        # Baue Mining-spezifische URLs
        target_urls = await self._build_mining_urls(mine_name, country)

        # FIX 01.09.2025: Defensive Programming gegen NoneType target_urls
        if not target_urls:
            target_urls = []

        # Scrape URLs
        # FIX 01.09.2025: Defensive len() calls
        url_count = len(target_urls[:5]) if target_urls else 0
        logger.info(f"[BrightData-WebScraper] Scraping {url_count} target URLs")
        scrape_results = await self.scraper.batch_scrape_urls(target_urls[:5], max_concurrent=3)

        # FIX 01.09.2025: Defensive Programming gegen NoneType scrape_results
        if scrape_results is None:
            scrape_results = []

        # FIX 01.09.2025: Defensive len() calls
        result_count = len(scrape_results) if scrape_results else 0
        logger.info(f"[BrightData-WebScraper] Got {result_count} scrape results")

        # Verarbeite Ergebnisse
        scraped_data = []
        sources = []

        for result in scrape_results:
            # FIX 01.09.2025: Defensive len() calls
            html_content = result.get("html", '')
            html_length = len(html_content) if html_content else 0
            logger.debug(f"[BrightData-WebScraper] Processing result:
success={result.get('success')}, html_length={html_length}")
            if result['success'] and result['html']:
                # DEBUG: Speichere HTML zur Analyse
                _save_debug_html(result['html'], result['url'], mine_name)

                extracted = self._extract_mining_data_from_html(result['html'], mine_name)
                # FIX 01.09.2025: Defensive Programming gegen NoneType extracted
                if extracted is None:
                    extracted = {}
                logger.debug(f"[BrightData-WebScraper] Extracted data fields:
{list(extracted.keys()) if extracted else 'None'}")
                if extracted:
                    scraped_data.append(extracted)
                    sources.append({
                        'id': f"source_{len(sources)+1 if sources else 1}",
                        'value': result['url'],
                        'type': 'website',
                        'title': extracted.get("title", 'Mining Data')
                    })

        # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
        raw_content = self._format_scraped_content(scraped_data)
        discovered_sources = options.get("discovered_sources", [])

        logger.info(f"[BRIGHTDATA] Sende Scraping-Ergebnisse durch AI-Modell für strukturierte Extraktion")
        ai_response = await self._send_to_ai_model(
            content=raw_content,
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=options.get('region'),
            discovered_sources=discovered_sources
        )

        # OPENROUTER WORKFLOW STEP 3: DataExtractor auf AI-Response anwenden (wie OpenRouter)
        from minesearch.data_extraction import DataExtractor
        data_extractor = DataExtractor()
        extracted_data = data_extractor.extract_structured_data_with_sources(ai_response, mine_name, country)

        # OPENROUTER WORKFLOW STEP 4: Quality Gates (wie OpenRouter)
        extracted_data = self._apply_quality_gates(extracted_data, mine_name)

        # REGEL 10 COMPLIANCE: Prüfe auf None (keine Dummy-Werte)
        if not extracted_data.get('data'):
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={
                    'provider': 'brightdata',
                    'model': 'web-scraper',
                    'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet',
                    'unified_workflow': True
                },
                error="Keine strukturierten Daten extrahiert"
            )

        # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
        all_sources = sources  # BrightData-Scraping-Quellen
        for source in discovered_sources:  # Alle Discovery-Quellen hinzufügen
            all_sources.append({
                'url': source.get("url", ''),
                'title': source.get("title", source.get('url', '')),
                'type': source.get('type'),  # REGEL 10: NULL statt 'unknown' Fallback
                'reliability': source.get('reliability_score')  # REGEL 10: Keine 0.5 Fallbacks
            })

        return SearchResult(
            success=True,
            content=raw_content,
            structured_data=extracted_data['data'],  # AI-extrahierte Daten (wie OpenRouter)
            sources=all_sources,
            metadata={
                'provider': 'brightdata',
                'model': 'web-scraper',
                'urls_scraped': len(sources) if sources else 0,
                'proxy_used': True,
                'unified_workflow': True,  # Markierung für neuen Workflow
                'ai_model': 'claude-3-haiku',  # Standard AI-Modell
                'sources_discovered': len(discovered_sources)
            }
        )

    async def _browser_automation_search(self, query: str, options: Dict[str, Any]) -> SearchResult:
        """Browser Automation mit CAPTCHA-Solving - OPENROUTER WORKFLOW"""

        mine_name = options.get("mine_name", query)
        country = options.get("country", '')
        commodity = options.get("commodity", '')

        # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
        from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
        source_discovery = EnhancedSourceDiscovery()
        discovered_sources = options.get("discovered_sources", [])

        if not discovered_sources and not options.get("skip_discovery", False):
            logger.info(f"[BRIGHTDATA-BROWSER] Starte Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(mine_name, country,
region=None, commodity=commodity)

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
                # FIX 01.09.2025: Defensive Programming gegen NoneType extracted
                if extracted is None:
                    extracted = {}
                if extracted:
                    # Erweiterte Extraktion für Browser API
                    extracted.update(self._extract_advanced_data(result['html'], options))
                    scraped_data.append(extracted)
                    sources.append({
                        'id': f"source_{len(sources)+1 if sources else 1}",
                        'value': result['url'],
                        'type': 'browser_rendered',
                        'title': extracted.get("title", 'Mining Data')
                    })

        # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
        raw_content = self._format_scraped_content(scraped_data)

        logger.info(f"[BRIGHTDATA-BROWSER] Sende Browser-Scraping durch AI-Modell für strukturierte Extraktion")
        ai_response = await self._send_to_ai_model(
            content=raw_content,
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=options.get('region'),
            discovered_sources=discovered_sources
        )

        # OPENROUTER WORKFLOW STEP 3: DataExtractor auf AI-Response anwenden (wie OpenRouter)
        data_extractor = DataExtractor()
        extracted_data = data_extractor.extract_structured_data_with_sources(ai_response, mine_name, country)

        # OPENROUTER WORKFLOW STEP 4: Quality Gates (wie OpenRouter)
        extracted_data = self._apply_quality_gates(extracted_data, mine_name)

        # REGEL 10 COMPLIANCE: Prüfe auf None (keine Dummy-Werte)
        if not extracted_data.get('data'):
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={
                    'provider': 'brightdata',
                    'model': 'browser-api',
                    'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet'
                },
                error="Keine strukturierten Daten extrahiert"
            )

        # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
        all_sources = sources  # BrightData-Scraping-Quellen
        for source in discovered_sources:  # Alle Discovery-Quellen hinzufügen
            all_sources.append({
                'url': source.get("url", ''),
                'title': source.get("title", source.get('url', '')),
                'type': source.get('type'),  # REGEL 10: NULL statt 'unknown' Fallback
                'reliability': source.get('reliability_score')  # REGEL 10: Keine 0.5 Fallbacks
            })

        return SearchResult(
            success=True,
            content=raw_content,
            structured_data=extracted_data['data'],  # AI-extrahierte Daten (wie OpenRouter)
            sources=all_sources,
            metadata={
                'provider': 'brightdata',
                'model': 'browser-api',
                'urls_scraped': len(sources) if sources else 0,
                'browser_rendered': True,
                'unified_workflow': True,  # Markierung für neuen Workflow
                'ai_model': 'claude-3-haiku',  # Standard AI-Modell
                'sources_discovered': len(discovered_sources)
            }
        )

    async def _search_engine_scraping(self, query: str, options: Dict[str, Any]) -> SearchResult:
        """Search Engine Scraping für Mining-Daten"""

        mine_name = options.get("mine_name", query)
        country = options.get("country", '')
        commodity = options.get("commodity", '')

        # Baue Suchqueries
        search_queries = self._build_search_queries(mine_name, country, commodity)

        scraped_data = []
        sources = []

        async with aiohttp.ClientSession() as session:
            for search_query in search_queries[:3]:  # Limitiere auf 3 Suchqueries
                try:
                    # Brightdata SERP API (Search Engine Results Page)
                    # ÄNDERUNG 11.07.2025: Korrigiere Zone-Namen für SERP
                    proxy_url =
f"http://brd-customer-{self.customer_id}-zone-datacenter_proxy:{self.password}@brd.superproxy.io:22225"

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

                            # DEBUGGING 30.08.2025: Erweiterte Logging für SERP
                            # FIX 01.09.2025: Defensive len() calls
                            html_len = len(html) if html else 0
                            logger.info(f"[BrightData-SERP] Response status: {response.status},
Content length: {html_len}")
                            logger.debug(f"[BrightData-SERP] HTML preview: {html[:500]}...")

                            # DEBUG: Speichere SERP HTML zur Analyse
                            _save_debug_html(html, search_url, f"{mine_name}_SERP")

                            # Extrahiere Suchergebnisse
                            search_results = self._extract_search_results(html)
                            # FIX 01.09.2025: Defensive len() calls
                            results_count = len(search_results) if search_results else 0
                            logger.info(f"[BrightData-SERP] Extracted {results_count} search results from SERP")

                            # Scrape die gefundenen URLs
                            for result in search_results[:3]:  # Top 3 Ergebnisse pro Query
                                result_url = result.get('url')
                                if result_url:
                                    # Scrape die gefundene Seite
                                    page_data = await self._scrape_search_result(session, result_url, mine_name)
                                    if page_data:
                                        scraped_data.append(page_data)
                                        sources.append({
                                            'id': f"source_{len(sources)+1 if sources else 1}",
                                            'value': result_url,
                                            'type': 'search_result',
                                            'title': result.get("title", 'Search Result'),
                                            'snippet': result.get("snippet", '')
                                        })
                        elif response.status == 407:
                            logger.error(f"[Brightdata-SERP] Authentication failed - Response: {response.status}")
                            logger.error(f"[Brightdata-SERP] Proxy URL used: {proxy_url}")
                            response_text = await response.text()
                            logger.error(f"[Brightdata-SERP] Error response: {response_text[:200]}")
                            break
                        else:
                            logger.warning(f"[Brightdata-SERP] Non-200 response: {response.status}")
                            response_text = await response.text()
                            logger.debug(f"[Brightdata-SERP] Response text: {response_text[:200]}...")

                except Exception as e:
                    logger.error(f"[Brightdata SERP] Fehler bei Suche '{search_query}': {e}")

        # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
        source_discovery = EnhancedSourceDiscovery()
        discovered_sources = options.get("discovered_sources", [])

        if not discovered_sources and not options.get("skip_discovery", False):
            logger.info(f"[BRIGHTDATA-SERP] Starte Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(mine_name, country,
region=None, commodity=commodity)

        # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
        raw_content = self._format_search_results(scraped_data, sources)

        logger.info(f"[BRIGHTDATA-SERP] Sende SERP-Scraping durch AI-Modell für strukturierte Extraktion")
        ai_response = await self._send_to_ai_model(
            content=raw_content,
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=options.get('region'),
            discovered_sources=discovered_sources
        )

        # OPENROUTER WORKFLOW STEP 3: DataExtractor auf AI-Response anwenden (wie OpenRouter)
        data_extractor = DataExtractor()
        extracted_data = data_extractor.extract_structured_data_with_sources(ai_response, mine_name, country)

        # OPENROUTER WORKFLOW STEP 4: Quality Gates (wie OpenRouter)
        extracted_data = self._apply_quality_gates(extracted_data, mine_name)

        # REGEL 10 COMPLIANCE: Prüfe auf None (keine Dummy-Werte)
        if not extracted_data.get('data'):
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={
                    'provider': 'brightdata',
                    'model': 'serp',
                    'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet',
                    'unified_workflow': True
                },
                error="Keine strukturierten Daten extrahiert"
            )

        # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
        all_sources = sources  # BrightData-Scraping-Quellen
        for source in discovered_sources:  # Alle Discovery-Quellen hinzufügen
            all_sources.append({
                'url': source.get("url", ''),
                'title': source.get("title", source.get('url', '')),
                'type': source.get('type'),  # REGEL 10: NULL statt 'unknown' Fallback
                'reliability': source.get('reliability_score')  # REGEL 10: Keine 0.5 Fallbacks
            })

        return SearchResult(
            success=True,
            content=raw_content,
            structured_data=extracted_data['data'],  # AI-extrahierte Daten (wie OpenRouter)
            sources=all_sources,
            metadata={
                'provider': 'brightdata',
                'model': 'serp',
                'queries_executed': len(self._build_search_queries(mine_name, country, commodity)),
                'results_found': len(sources) if sources else 0,
                'unified_workflow': True,  # Markierung für neuen Workflow
                'ai_model': 'claude-3-haiku',  # Standard AI-Modell
                'sources_discovered': len(discovered_sources)
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

        mine_name = options.get("mine_name", '')
        country = options.get("country", '')
        commodity = options.get("commodity", '')

        scraped_data = []
        successful_sources = []

        # Extrahiere URLs aus sources
        url_sources = [s for s in sources if s.get('type') in ['url', 'website', None]]

        async with aiohttp.ClientSession() as session:
            for source in url_sources[:10]:  # Limitiere auf 10 URLs
                url = source.get('url') or source.get("value", '')
                if not url or not url.startswith('http'):
                    continue

                try:
                    # Nutze Brightdata Proxy
                    if self.customer_id and self.password:
                        proxy_url =
f"http://brd-customer-{self.customer_id}-zone-web_unlocker:{self.password}@brd.superproxy.io:22225"

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
                                # FIX 01.09.2025: Defensive Programming gegen NoneType extracted
                                if extracted is None:
                                    extracted = {}
                                if extracted:
                                    scraped_data.append(extracted)
                                    successful_sources.append({
                                        'id': f"source_{len(successful_sources)+1 if successful_sources else 1}",
                                        'value': url,
                                        'type': 'website',
                                        'title': source.get("title", 'Mining Data')
                                    })

                except Exception as e:
                    logger.error(f"[Brightdata] Fehler beim Scrapen von {url}: {e}")

        # Verarbeite Daten
        structured_data = self._aggregate_scraped_data(scraped_data, mine_name, country, commodity,
options.get('region'))

        # REGEL 10 COMPLIANCE: Prüfe auf None (keine Dummy-Werte)
        if structured_data is None:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={
                    'provider': 'brightdata',
                    'model': model_id,
                    'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet'
                },
                error="Keine strukturierten Daten extrahiert"
            )

        content = self._format_scraped_content(scraped_data)

        return SearchResult(
            success=True,
            content=content,
            structured_data=structured_data,
            sources=successful_sources,
            metadata={
                'provider': 'brightdata',
                'model': model_id,
                'urls_scraped': len(successful_sources) if successful_sources else 0,
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
    """_aggregate_scraped_data - TODO: Dokumentation hinzufügen"""
                               country: str, commodity: str, region: str) -> Dict[str, Any]:
        """
        TRANSPARENCY FIX 30.08.2025: Verbesserte Daten-Aggregation mit expliziter Struktur
        """
        try:
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region
            }

            # Basis-Aggregation über Processor
            aggregated = self.processor.process_search_results(scraped_data, options)

            # FIX 01.09.2025: Defensive Programming gegen NoneType aggregated
            if aggregated is None:
                aggregated = {}

            # REGEL 10 COMPLIANCE: Keine Dummy-Werte - bei fehlenden Daten SearchResult als failed markieren
            # FIX 01.09.2025: Defensive len() calls
            aggregated_len = len(aggregated) if aggregated else 0
            if not aggregated or aggregated_len == 0:
                logger.warning(f"[BrightData] Keine Daten extrahiert für {mine_name} - Suche als
fehlgeschlagen markieren (REGEL 10: Keine Dummy-Werte)")
                return None  # Führt zu success=False im SearchResult
            else:
                # ENHANCEMENT: Füge Metadaten zur Datenqualität hinzu
                # FIX 01.09.2025: Defensive len() calls
                values_list = list(aggregated.values()) if aggregated else []
                filled_fields = len([v for v in values_list if v and str(v).strip()])
                aggregated['data_quality_score'] = min(1.0, filled_fields / 15.0)  # Skala 0-1
                aggregated['extraction_source'] = 'brightdata_scraped'

            # FIX 01.09.2025: Defensive len() calls
            aggregated_field_count = len(aggregated) if aggregated else 0
            logger.info(f"[BrightData] Aggregierte Daten für {mine_name}: {aggregated_field_count}
Felder, Qualität: {aggregated.get("data_quality_score", 0):.2f}")
            return aggregated

        except Exception as e:
            logger.error(f"[BrightData] Fehler bei Datenaggregation für {mine_name}: {e}")
            # REGEL 10 COMPLIANCE: Keine Dummy-Werte bei Fehlern - SearchResult als failed markieren
            return None  # Führt zu success=False im SearchResult

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
            proxy_url =
f"http://brd-customer-{self.customer_id}-zone-web_unlocker:{self.password}@brd.superproxy.io:22225"

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
                content += f"\nQuelle {i}: {source.get("title", '')}\n"  # REGEL 10: NULL statt 'N/A'
                content += f"URL: {source.get("value", '')}\n"  # REGEL 10: NULL statt 'N/A'

                for key, value in data.items():
                    if value and key != 'mine_name' and key != 'title':
                        content += f"- {key}: {value}\n"

        return content

    # OPENROUTER WORKFLOW HELPER METHODS (wie in Tavily/EXA)
    async def _send_to_ai_model(
        self,
        content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        discovered_sources: List[Dict[str, Any]] = None
    ) -> str:
        """Sendet BrightData Content durch AI-Modell für strukturierte Extraktion (wie OpenRouter)"""

        try:
            from minesearch.specialized_prompts_impl import SpecializedPrompts
            from minesearch.config.models import OPENROUTER_MODELS
            import httpx

            # Standard AI-Modell für alternative Provider
            model_name = "anthropic/claude-3.5-haiku"

            # Erstelle strukturierten Prompt (wie OpenRouter)
            system_prompt = SpecializedPrompts.get_universal_anti_template_instructions()
            system_prompt += f"""

🎯 BRIGHTDATA MINING DATENEXTRAKTION
=============================================

Analysiere die folgenden BrightData Web-Scraping Ergebnisse und extrahiere strukturierte
Mining-Daten für die Mine "{mine_name}" in {country}.

AUSGABEFORMAT (JSON):
{{
    "Name": "{mine_name}",
    "Country": "{country} (normalisiert)",
    "Region": "spezifische Region",
    "Eigentümer": "aktueller Eigentümer",
    "Betreiber": "aktueller Betreiber",
    "x-Koordinate": "präzise Dezimalzahl",
    "y-Koordinate": "präzise Dezimalzahl",
    "Aktivitätsstatus": "Aktiv/Geschlossen/Geplant",
    "Restaurationskosten": "Betrag mit Währung",
    "Jahr der Aufnahme der Kosten": "YYYY",
    "Rohstoff": "Gold, Kupfer, etc.",
    "Minentyp": "Untertage/Tagebau",
    "Produktionsstart": "YYYY",
    "Produktionsende": "YYYY",
    "Fördermenge/Jahr Rohstoff": "Rohstoff-Produktion (oz Gold, t Kupfer etc.)",
    "Fördermenge/Jahr Abraum": "Gesamtmaterial (Millionen Tonnen, Material etc.)",
    "Fläche der Mine in qkm": "Fläche mit Einheit"
}}

KRITISCHE REGELN:
- NUR echte, verifizierbare Daten verwenden
- KEINE Template-Werte oder Schätzungen
- Bei Unsicherheit: Feld leer lassen
- Numerische Werte: Volle Präzision beibehalten
- Länder normalisieren (Canada → Kanada)
"""

            user_prompt = f"""Analysiere die BrightData Scraping-Ergebnisse und extrahiere
Mining-Daten für "{mine_name}" in {country}.

{f"Rohstoff: {commodity}" if commodity else ""}
{f"Region: {region}" if region else ""}

Gib NUR das JSON-Objekt zurück.

BRIGHTDATA CONTENT:
{content}"""

            # Sende an OpenRouter (wie andere AI-Provider)
            openrouter_key = self.config.get('openrouter_api_key')
            if not openrouter_key:
                logger.error("[BRIGHTDATA-AI] OpenRouter API Key fehlt für AI-Extraktion")
                return content  # Fallback auf Raw Content

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "https://mining-data-extraction.com",
                        "X-Title": "MineSearch BrightData AI Extraction",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.1
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    logger.info(f"[BRIGHTDATA-AI] Erfolgreiche AI-Extraktion mit {model_name}")
                    return ai_response
                else:
                    logger.error(f"[BRIGHTDATA-AI] AI-API Fehler: {response.status_code}")

        except Exception as e:
            logger.error(f"[BRIGHTDATA-AI] AI-Extraktion fehlgeschlagen: {e}")

        # Fallback: Originaler Content
        return content

    def _apply_quality_gates(self, extracted_data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """Wendet OpenRouter-ähnliche Quality Gates auf BrightData-Ergebnisse an"""

        if not extracted_data or not extracted_data.get('data'):
            return extracted_data

        data = extracted_data['data']

        # Basis Quality Gate: Name sollte immer gesetzt sein
        if not data.get('Name'):
            data['Name'] = mine_name
            logger.debug(f"[BRIGHTDATA-QG] Name ergänzt: {mine_name}")

        # Template-Detection für numerische Felder (wie in consolidated_field_utils.py)
        numeric_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 'Fördermenge/Jahr',
'Fläche der Mine in qkm']

        for field in numeric_fields:
            if field in data and data[field]:
                value_str = str(data[field])
                # Schutz vor Template-Detection für numerische Werte
                if any(char.isdigit() for char in value_str) or '$' in value_str or '€' in value_str:
                    logger.debug(f"[BRIGHTDATA-QG] Numerisches Feld geschützt: {field} = {data[field]}")
                    continue  # Numerische Felder nicht durch Template-Detection entfernen

        # Entferne None-Werte und leere Strings (REGEL 10)
        cleaned_data = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned_data[key] = value

        extracted_data['data'] = cleaned_data

        logger.info(f"[BRIGHTDATA-QG] Quality Gates angewendet für {mine_name}")
        return extracted_data
