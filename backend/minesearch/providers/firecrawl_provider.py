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
                is_free=False,
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='firecrawl'
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
        """Führt Web-Crawling mit Firecrawl durch - OPENROUTER WORKFLOW"""
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
            
            mine_name = options.get('mine_name', query)
            country = options.get('country', '')
            commodity = options.get('commodity', '')
            
            # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
            from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
            source_discovery = EnhancedSourceDiscovery()
            discovered_sources = options.get('discovered_sources', [])
            
            if not discovered_sources and not options.get('skip_discovery', False):
                logger.info(f"[FIRECRAWL] Starte Source Discovery für {mine_name}")
                discovered_sources = source_discovery.discover_sources_for_mine(mine_name, country, region=None, commodity=commodity)
            
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
            
            # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
            raw_content = self._combine_markdown_content(results)
            
            logger.info(f"[FIRECRAWL] Sende Crawling-Ergebnisse durch AI-Modell für strukturierte Extraktion")
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
                        'provider': 'firecrawl',
                        'model': model_id,
                        'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet',
                        'unified_workflow': True
                    },
                    error="Keine strukturierten Daten extrahiert"
                )
            
            # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
            all_sources = sources  # Firecrawl-Crawling-Quellen
            for source in discovered_sources:  # Alle Discovery-Quellen hinzufügen
                all_sources.append({
                    'url': source.get('url', ''),
                    'title': source.get('title', source.get('url', '')),
                    'type': source.get('type', 'unknown'),
                    'reliability': source.get('reliability_score')  # REGEL 10: Keine 0.5 Fallbacks
                })
            
            search_duration = (datetime.now() - start_time).total_seconds()
            
            return SearchResult(
                success=True,
                content=raw_content,
                structured_data=extracted_data['data'],  # AI-extrahierte Daten (wie OpenRouter)
                sources=all_sources,
                metadata={
                    'provider': 'firecrawl',
                    'model': model_id,
                    'search_duration': search_duration,
                    'pages_processed': len(results),
                    'markdown_length': len(raw_content),
                    'unified_workflow': True,  # Markierung für neuen Workflow
                    'ai_model': 'claude-3-haiku',  # Standard AI-Modell
                    'sources_discovered': len(discovered_sources)
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
            aggregated_data['Rohstoffabbau'] = options.get('commodity', '-')
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
    
    async def crawl_sources(self, discovered_sources: List[Dict], model_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        ÄNDERUNG 08.07.2025: Neue Methode zum Crawlen von discovered_sources
        Crawlt Websites aus discovered_sources und extrahiert Mining-Daten
        """
        if not discovered_sources:
            return {'success': False, 'error': 'Keine Quellen zum Crawlen'}
        
        mine_name = options.get('mine_name', '')
        crawled_results = []
        
        # Gruppiere URLs nach Domain für effizientes Crawling
        domain_groups = {}
        for source in discovered_sources[:20]:  # Limitiere auf 20 Quellen
            url = source.get('url', '')
            if not url:
                continue
            
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(url)
            except ValueError as e:
                logger.debug(f"[FIRECRAWL] Ungültige URL '{url}': {e}")
                continue
            except ImportError as e:
                logger.error(f"[FIRECRAWL] urlparse Import-Fehler: {e}")
                continue
            except Exception as e:
                logger.warning(f"[FIRECRAWL] Unerwarteter URL-Parsing-Fehler für '{url}': {e}")
                continue
        
        # Crawle jede Domain
        for domain, urls in domain_groups.items():
            logger.info(f"[FIRECRAWL] Crawling {domain} mit {len(urls)} URLs für {mine_name}")
            
            # Wähle Haupt-URL für Domain-Crawl
            main_url = urls[0]
            
            # Nutze crawl Modell für Domain-weites Crawling
            if model_id == 'crawl':
                result = await self.search(
                    query=f"Crawl website for mining data: {main_url}",
                    model_id='crawl',
                    options={**options, 'target_url': main_url, 'max_pages': 10}
                )
            else:
                # Für scrape/extract nur einzelne URLs
                result = await self.search(
                    query=f"Extract mining data from: {main_url}",
                    model_id=model_id,
                    options={**options, 'target_url': main_url}
                )
            
            if result.success:
                crawled_results.append({
                    'domain': domain,
                    'urls': urls,
                    'data': result.structured_data,
                    'content_preview': result.content[:1000] if result.content else '',
                    'crawled_at': datetime.now().isoformat()
                })
        
        return {
            'success': True,
            'crawled_domains': len(crawled_results),
            'results': crawled_results,
            'mine_name': mine_name
        }
    
    # OPENROUTER WORKFLOW HELPER METHODS (wie in Tavily/EXA/BrightData/ScrapingBee)
    async def _send_to_ai_model(
        self,
        content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        discovered_sources: List[Dict[str, Any]] = None
    ) -> str:
        """Sendet Firecrawl Content durch AI-Modell für strukturierte Extraktion (wie OpenRouter)"""
        
        try:
            from minesearch.specialized_prompts_impl import SpecializedPrompts
            from minesearch.config.models import OPENROUTER_MODELS
            import httpx
            
            # Standard AI-Modell für alternative Provider
            model_name = "anthropic/claude-3.5-haiku"
            
            # Erstelle strukturierten Prompt (wie OpenRouter)
            system_prompt = SpecializedPrompts.get_universal_anti_template_instructions()
            system_prompt += f"""

🎯 FIRECRAWL MINING DATENEXTRAKTION
=============================================

Analysiere die folgenden Firecrawl Markdown-Crawling Ergebnisse und extrahiere strukturierte Mining-Daten für die Mine "{mine_name}" in {country}.

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
    "Rohstoffabbau": "Gold, Kupfer, etc.",
    "Minentyp": "Untertage/Tagebau",
    "Produktionsstart": "YYYY",
    "Produktionsende": "YYYY",
    "Fördermenge/Jahr": "Menge mit Einheit",
    "Fläche der Mine in qkm": "Fläche mit Einheit"
}}

KRITISCHE REGELN:
- NUR echte, verifizierbare Daten verwenden
- KEINE Template-Werte oder Schätzungen
- Bei Unsicherheit: Feld leer lassen
- Numerische Werte: Volle Präzision beibehalten
- Länder normalisieren (Canada → Kanada)
- Nutze Markdown-Struktur für präzise Navigation
"""
            
            user_prompt = f"""Analysiere die Firecrawl Markdown-Crawling-Ergebnisse und extrahiere Mining-Daten für "{mine_name}" in {country}.

{f"Rohstoff: {commodity}" if commodity else ""}
{f"Region: {region}" if region else ""}

Gib NUR das JSON-Objekt zurück.

FIRECRAWL MARKDOWN CONTENT:
{content}"""
            
            # Sende an OpenRouter (wie andere AI-Provider)
            openrouter_key = self.config.get('openrouter_api_key')
            if not openrouter_key:
                logger.error("[FIRECRAWL-AI] OpenRouter API Key fehlt für AI-Extraktion")
                return content  # Fallback auf Raw Content
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "https://mining-data-extraction.com",
                        "X-Title": "MineSearch Firecrawl AI Extraction",
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
                    logger.info(f"[FIRECRAWL-AI] Erfolgreiche AI-Extraktion mit {model_name}")
                    return ai_response
                else:
                    logger.error(f"[FIRECRAWL-AI] AI-API Fehler: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"[FIRECRAWL-AI] AI-Extraktion fehlgeschlagen: {e}")
        
        # Fallback: Originaler Content
        return content
    
    def _apply_quality_gates(self, extracted_data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """Wendet OpenRouter-ähnliche Quality Gates auf Firecrawl-Ergebnisse an"""
        
        if not extracted_data or not extracted_data.get('data'):
            return extracted_data
            
        data = extracted_data['data']
        
        # Basis Quality Gate: Name sollte immer gesetzt sein
        if not data.get('Name'):
            data['Name'] = mine_name
            logger.debug(f"[FIRECRAWL-QG] Name ergänzt: {mine_name}")
        
        # Template-Detection für numerische Felder (wie in consolidated_field_utils.py)
        numeric_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 'Fördermenge/Jahr', 'Fläche der Mine in qkm']
        
        for field in numeric_fields:
            if field in data and data[field]:
                value_str = str(data[field])
                # Schutz vor Template-Detection für numerische Werte
                if any(char.isdigit() for char in value_str) or '$' in value_str or '€' in value_str:
                    logger.debug(f"[FIRECRAWL-QG] Numerisches Feld geschützt: {field} = {data[field]}")
                    continue  # Numerische Felder nicht durch Template-Detection entfernen
        
        # Entferne None-Werte und leere Strings (REGEL 10)
        cleaned_data = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned_data[key] = value
        
        extracted_data['data'] = cleaned_data
        
        logger.info(f"[FIRECRAWL-QG] Quality Gates angewendet für {mine_name}")
        return extracted_data