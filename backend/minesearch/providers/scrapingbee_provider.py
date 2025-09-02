"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: ScrapingBee Provider für Web-Scraping mit JavaScript-Rendering
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
import re

from .base_provider import AbstractProvider, SearchResult, ModelConfig

logger = logging.getLogger(__name__)


class ScrapingBeeProvider(AbstractProvider):
    """ScrapingBee Provider für Web-Scraping mit JavaScript und AI-Extraktion"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.base_url = config.get('base_url', 'https://app.scrapingbee.com/api/v1')
        self.models = config.get('models', {})
        
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare ScrapingBee Modelle zurück"""
        return {
            model_id: ModelConfig(
                id=model_id,
                name=model_info['name'],
                timeout=model_info['timeout'],
                max_tokens=model_info['max_tokens'],
                description=model_info['description'],
                provider='scrapingbee',
                supports_web_search=model_info.get('supports_web_search', True),
                supports_deep_research=model_info.get('supports_deep_research', False),
                is_free=False,
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='scrapingbee'
            )
            for model_id, model_info in self.models.items()
        }
    
    def validate_config(self) -> bool:
        """Validiert die ScrapingBee Konfiguration"""
        if not self.api_key:
            logger.error("[ScrapingBee] Kein API-Key konfiguriert")
            return False
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        ÄNDERUNG 05.07.2025: Implementierung für Cross-Provider Source Sharing
        Scraped die übergebenen URLs direkt
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
        
        start_time = datetime.now()
        scraped_data = []
        successful_sources = []
        
        async with httpx.AsyncClient() as client:
            # Scrape nur URL-basierte Quellen
            url_sources = [s for s in sources if s.get('type') in ['url', 'website', None]]
            
            for source in url_sources[:10]:  # Limitiere auf 10 URLs
                url = source.get('url') or source.get('value', '')
                if not url or not url.startswith('http'):
                    continue
                    
                try:
                    result = await self._scrape_url(client, url, model_id, options)
                    if result:
                        scraped_data.append(result['content'])
                        successful_sources.append({
                            'id': f"source_{len(successful_sources)+1}",
                            'value': url,
                            'type': 'website',
                            'title': result.get('title', source.get('title', 'Mining Data'))
                        })
                except Exception as e:
                    logger.error(f"[ScrapingBee] Fehler beim Scrapen von {url}: {e}")
        
        # Verarbeite gescrapte Daten
        structured_data = await self._process_scraped_data(scraped_data, options)
        
        # Kombiniere Inhalte
        combined_content = "\n\n---\n\n".join(scraped_data)
        
        search_duration = (datetime.now() - start_time).total_seconds()
        
        return SearchResult(
            success=True,
            content=combined_content,
            structured_data=structured_data,
            sources=successful_sources,
            metadata={
                'provider': 'scrapingbee',
                'model': model_id,
                'search_duration': search_duration,
                'urls_scraped': len(successful_sources),
                'phase': 'source_sharing'
            }
        )
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für ScrapingBee AI-Extraktion"""
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        return f"""Du bist ein Experte für die Extraktion von Mining-Daten aus Webseiten.
        
        Extrahiere folgende Informationen über die Mine "{mine_name}" in {country}:
        
        1. Koordinaten (GPS/Latitude/Longitude)
        2. Eigentümer/Owner
        3. Betreiber/Operator  
        4. Restaurationskosten/Closure Costs/Reclamation Costs
        5. Jahr der Kostenaufnahme
        6. Produktionsstart und -ende
        7. Fördermenge pro Jahr
        8. Fläche der Mine
        9. Minentyp (Untertage/Open-Pit)
        10. Aktivitätsstatus
        
        Suche besonders nach:
        - Tabellen mit finanziellen Daten
        - PDF-Links zu technischen Reports
        - Koordinaten in verschiedenen Formaten
        - Asset Retirement Obligations (ARO)
        - Environmental Liabilities
        - Closure Bonds
        
        Gib die Daten im JSON-Format zurück."""
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führt Web-Scraping mit ScrapingBee durch - OPENROUTER WORKFLOW"""
        start_time = datetime.now()
        
        try:
            if not self.validate_config():
                return SearchResult(
                    success=False,
                    content="",
                    structured_data={},
                    sources=[],
                    metadata={},
                    error="ScrapingBee API-Key nicht konfiguriert"
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
            from minesearch.source_manager import EnhancedSourceDiscovery
            source_discovery = EnhancedSourceDiscovery()
            discovered_sources = options.get('discovered_sources', [])
            
            if not discovered_sources and not options.get('skip_discovery', False):
                logger.info(f"[SCRAPINGBEE] Starte Source Discovery für {mine_name}")
                discovered_sources = source_discovery.discover_sources_for_mine(mine_name, country, commodity, limit=15)
            
            # Baue Suchquery für Mining-Daten
            search_urls = await self._build_search_urls(query, options)
            
            # Scrape die gefundenen URLs
            scraped_data = []
            sources = []
            
            async with httpx.AsyncClient() as client:
                for url in search_urls[:5]:  # Limitiere auf 5 URLs
                    try:
                        result = await self._scrape_url(client, url, model_id, options)
                        if result:
                            scraped_data.append(result['content'])
                            sources.append({
                                'id': f"source_{len(sources)+1}",
                                'value': url,
                                'type': 'website',
                                'title': result.get('title', 'Mining Data')
                            })
                    except Exception as e:
                        logger.error(f"[ScrapingBee] Fehler beim Scrapen von {url}: {e}")
            
            # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
            raw_content = "\n\n---\n\n".join(scraped_data)
            
            logger.info(f"[SCRAPINGBEE] Sende Scraping-Ergebnisse durch AI-Modell für strukturierte Extraktion")
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
                        'provider': 'scrapingbee',
                        'model': model_id,
                        'error': 'Keine echten Daten gefunden - REGEL 10: Keine Dummy-Werte verwendet',
                        'unified_workflow': True
                    },
                    error="Keine strukturierten Daten extrahiert"
                )
            
            # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
            all_sources = sources  # ScrapingBee-Scraping-Quellen
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
                    'provider': 'scrapingbee',
                    'model': model_id,
                    'search_duration': search_duration,
                    'urls_scraped': len(sources),
                    'credits_used': len(sources) * model_config.get('credits_cost', 1),
                    'unified_workflow': True,  # Markierung für neuen Workflow
                    'ai_model': 'claude-3-haiku',  # Standard AI-Modell
                    'sources_discovered': len(discovered_sources)
                }
            )
            
        except Exception as e:
            logger.error(f"[ScrapingBee] Fehler bei der Suche: {e}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    async def _build_search_urls(self, query: str, options: Dict[str, Any]) -> List[str]:
        """Baut URLs für Mining-Daten auf"""
        mine_name = options.get('mine_name', query)
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        urls = []
        
        # ÄNDERUNG 05.07.2025: Korrigierte URLs die tatsächlich existieren
        # Regierungsseiten
        if country.lower() in ['kanada', 'canada']:
            urls.extend([
                "https://mern.gouv.qc.ca",  # Hauptseite statt Suchseite
                "https://www.nrcan.gc.ca",
                "https://www.sedar.com"
            ])
        
        # Mining-Portale (ohne spezifische Suchpfade)
        urls.extend([
            "https://www.mining.com",
            "https://www.infomine.com",
            "https://www.northernminer.com"
        ])
        
        return urls
    
    async def _scrape_url(self, client: httpx.AsyncClient, url: str, 
                         model_id: str, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne URL mit ScrapingBee"""
        
        # ÄNDERUNG 05.07.2025: Optimierte ScrapingBee Parameter basierend auf Tests
        params = {
            'api_key': self.api_key,
            'url': url
        }
        
        # Model-spezifische Parameter
        if model_id == 'basic-scrape':
            params['render_js'] = 'false'
            params['premium_proxy'] = 'false'
        elif model_id == 'js-render':
            params['render_js'] = 'true'
            params['premium_proxy'] = 'true'
        elif model_id == 'ai-extract':
            params['render_js'] = 'true'
            params['stealth_proxy'] = 'true'  # Beste Erfolgsrate für schwierige Seiten
        
        # Spezielle Parameter für AI-Extract - FIX 02.09.2025
        if model_id == 'ai-extract':
            # ScrapingBee AI-Extract mit korrekten Parametern
            params['extract_rules'] = json.dumps({
                'mine_name': {'type': 'text', 'selector': 'body'},
                'coordinates': {'type': 'text', 'selector': 'body'},
                'owner': {'type': 'text', 'selector': 'body'},
                'operator': {'type': 'text', 'selector': 'body'},
                'costs': {'type': 'text', 'selector': 'body'},
                'production': {'type': 'text', 'selector': 'body'}
            })
            params['ai_extract'] = 'true'
            # FIX: 'instruction' Parameter statt 'ai_query' für ScrapingBee API
            params['instruction'] = f"""Extract structured mining data for the mine "{options.get('mine_name', '')}" from this webpage. 
            Find: GPS coordinates, owner/operator, restoration costs, production data, mine type, status.
            Return as JSON with fields: name, coordinates, owner, operator, costs, production, status."""
        
        # Entferne None-Werte
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            timeout = httpx.Timeout(self.models[model_id]['timeout'])
            # Verwende GET-Request mit query parameters
            response = await client.get(self.base_url, params=params, timeout=timeout)
            if response.status_code == 200:
                # Prüfe Content-Type für PDF-Handhabung
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/pdf' in content_type:
                    # PDF-Datei - speichere als Binary
                    logger.info(f"[ScrapingBee] PDF erkannt für {url}")
                    pdf_content = response.content  # Binary content
                    return {
                        'url': url,
                        'content': f"[PDF-Dokument gefunden - {len(pdf_content)} bytes]\nURL: {url}\n\nPDF-Analyse:\n- Größe: {len(pdf_content)/1024:.1f} KB\n- Typ: {content_type}\n\nHinweis: PDF müsste mit spezialisierten Tools extrahiert werden.",
                        'title': 'PDF Document',
                        'is_pdf': True,
                        'pdf_size': len(pdf_content)
                    }
                elif model_id == 'ai-extract':
                    # JSON Response erwartet - FIX 02.09.2025: Verbesserte Extraktion
                    try:
                        data = response.json()
                        # ScrapingBee AI-Extract kann verschiedene Formate zurückgeben
                        extracted_data = {}
                        if isinstance(data, dict):
                            # Direkte AI-Extract Ergebnisse verwenden
                            if 'extracted_data' in data:
                                extracted_data = data['extracted_data']
                            elif 'ai_extract' in data:
                                extracted_data = data['ai_extract'] 
                            else:
                                extracted_data = data
                                
                        return {
                            'url': url,
                            'content': response.text,  # Original HTML für Fallback-Parsing
                            'extracted': extracted_data,  # Strukturierte AI-Daten
                            'title': extracted_data.get('title', '') if extracted_data else 'Mining Data',
                            'has_ai_extraction': bool(extracted_data)
                        }
                    except json.JSONDecodeError:
                        # Fallback: HTML mit lokalem NLP verarbeiten
                        text_content = response.text
                        return {
                            'url': url,
                            'content': text_content,
                            'title': 'Mining Data (HTML Fallback)',
                            'needs_local_processing': True
                        }
                else:
                    # Standard Text/HTML Response
                    try:
                        text_content = response.text
                        return {
                            'url': url,
                            'content': text_content,
                            'title': self._extract_title_from_html(text_content)
                        }
                    except UnicodeDecodeError:
                        # Binary content das kein PDF ist
                        binary_content = response.content
                        return {
                            'url': url,
                            'content': f"[Binary-Datei - {len(binary_content)} bytes]\nContent-Type: {content_type}",
                            'title': 'Binary File',
                            'is_binary': True
                        }
            else:
                error_text = response.text
                logger.error(f"[ScrapingBee] HTTP {response.status_code} für {url}: {error_text[:200]}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"[ScrapingBee] Timeout beim Scrapen von {url}")
            return None
        except Exception as e:
            logger.error(f"[ScrapingBee] Fehler beim Scrapen von {url}: {e}")
            return None
    
    async def _process_scraped_data(self, scraped_data: List[str], 
                                   options: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet die gescrapten Daten zu strukturierten Mining-Informationen - FIX 02.09.2025"""
        
        # REGEL 10 FIX: Keine Dummy-Werte "-" verwenden - None statt Placeholder
        result = {
            'Name': options.get('mine_name', ''),
            'Country': options.get('country', ''),
            'Region': options.get('region'),  # None wenn nicht vorhanden
            'Eigentümer': None,
            'Betreiber': None,
            'x-Koordinate': None,
            'y-Koordinate': None,
            'Aktivitätsstatus': None,
            'Restaurationskosten': None,
            'Jahr der Aufnahme der Kosten': None,
            'Jahr der Erstellung des Dokumentes': None,
            'Rohstoffabbau': options.get('commodity'),  # None wenn nicht vorhanden
            'Minentyp': None,
            'Produktionsstart': None,
            'Produktionsende': None,
            'Fördermenge/Jahr': None,
            'Fläche der Mine in qkm': None,
            'Quellenangaben': None
        }
        
        # FIX 02.09.2025: Prüfe auf strukturierte AI-Extract Daten
        ai_extracted_data = []
        html_data = []
        
        for data in scraped_data:
            # Wenn es ein Dictionary ist (von AI-Extract), verwende strukturierte Daten
            if isinstance(data, dict) and data.get('extracted'):
                ai_extracted_data.append(data['extracted'])
                html_data.append(data.get('content', ''))
            elif isinstance(data, dict) and data.get('has_ai_extraction'):
                ai_extracted_data.append(data.get('extracted', {}))
                html_data.append(data.get('content', ''))
            else:
                # Standard String-Daten
                html_data.append(str(data) if not isinstance(data, str) else data)
        
        # Verarbeite AI-Extract Ergebnisse zuerst (höhere Qualität)
        for ai_data in ai_extracted_data:
            if isinstance(ai_data, dict):
                if ai_data.get('coordinates'):
                    coords = str(ai_data['coordinates'])
                    if ',' in coords:
                        parts = [p.strip() for p in coords.split(',')]
                        if len(parts) >= 2:
                            result['x-Koordinate'] = parts[1] if parts[1] != '-' else result['x-Koordinate'] 
                            result['y-Koordinate'] = parts[0] if parts[0] != '-' else result['y-Koordinate']
                
                if ai_data.get('owner'):
                    result['Eigentümer'] = str(ai_data['owner'])[:100]  # Begrenze Länge
                    
                if ai_data.get('operator'):
                    result['Betreiber'] = str(ai_data['operator'])[:100]
                    
                if ai_data.get('costs'):
                    result['Restaurationskosten'] = str(ai_data['costs'])[:50]
                    
                if ai_data.get('production'):
                    result['Fördermenge/Jahr'] = str(ai_data['production'])[:50]
                    
                if ai_data.get('status'):
                    result['Aktivitätsstatus'] = str(ai_data['status'])[:30]
        
        # Fallback: Kombiniere HTML-Daten für Pattern-Matching
        combined_text = "\n".join(html_data).lower()
        
        # Extraktionsmuster
        patterns = {
            'coordinates': [
                r'latitude[:\s]+(-?\d+\.?\d*)',
                r'longitude[:\s]+(-?\d+\.?\d*)',
                r'coordinates[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
                r'gps[:\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
            ],
            'owner': [
                r'owner[:\s]+([^,\n]+)',
                r'owned by[:\s]+([^,\n]+)',
                r'propriétaire[:\s]+([^,\n]+)'
            ],
            'operator': [
                r'operator[:\s]+([^,\n]+)',
                r'operated by[:\s]+([^,\n]+)',
                r'exploitant[:\s]+([^,\n]+)'
            ],
            'restoration_costs': [
                r'closure cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion)?',
                r'restoration cost[s]?[:\s]+\$?([0-9,\.]+)\s*(million|billion)?',
                r'aro[:\s]+\$?([0-9,\.]+)\s*(million|billion)?',
                r'environmental liability[:\s]+\$?([0-9,\.]+)\s*(million|billion)?'
            ]
        }
        
        # Suche nach Mustern
        for pattern_list in patterns['coordinates']:
            match = re.search(pattern_list, combined_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    result['x-Koordinate'] = match.group(1)
                    result['y-Koordinate'] = match.group(2)
                elif len(match.groups()) == 1:
                    if 'lat' in pattern_list:
                        result['x-Koordinate'] = match.group(1)
                    elif 'lon' in pattern_list:
                        result['y-Koordinate'] = match.group(1)
        
        for pattern in patterns['owner']:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                result['Eigentümer'] = match.group(1).strip().title()
                break
        
        for pattern in patterns['operator']:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                result['Betreiber'] = match.group(1).strip().title()
                break
        
        for pattern in patterns['restoration_costs']:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                unit = match.group(2) if len(match.groups()) > 1 else ''
                if unit:
                    result['Restaurationskosten'] = f"${value} {unit}"
                else:
                    result['Restaurationskosten'] = f"${value}"
                break
        
        return result
    
    def _extract_title_from_html(self, html: str) -> str:
        """Extrahiert den Titel aus HTML-Content"""
        # Versuche <title> Tag zu finden
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        # Fallback auf h1
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return 'Mining Data'
    
    async def scrape_sources(self, discovered_sources: List[Dict], model_id: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        ÄNDERUNG 08.07.2025: Neue Methode zum Scrapen von discovered_sources
        Scrapt eine Liste von URLs und extrahiert Mining-Daten
        """
        if not discovered_sources:
            return []
        
        mine_name = options.get('mine_name', '')
        scraped_results = []
        
        # Limitiere auf Top 10 Quellen um Credits zu sparen
        for source in discovered_sources[:10]:
            url = source.get('url', '')
            if not url:
                continue
                
            logger.info(f"[SCRAPINGBEE] Scraping {url} für {mine_name}")
            
            # Nutze die normale search Methode mit der URL als Query
            result = await self.search(
                query=f"Extract mining data from: {url}",
                model_id=model_id,
                options={**options, 'target_url': url}
            )
            
            if result.success and result.structured_data:
                scraped_results.append({
                    'url': url,
                    'data': result.structured_data,
                    'content': result.content[:1000],  # Erste 1000 Zeichen
                    'scraped_at': datetime.now().isoformat()
                })
        
        return scraped_results
    
    # OPENROUTER WORKFLOW HELPER METHODS (wie in Tavily/EXA/BrightData)
    async def _send_to_ai_model(
        self,
        content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        discovered_sources: List[Dict[str, Any]] = None
    ) -> str:
        """Sendet ScrapingBee Content durch AI-Modell für strukturierte Extraktion (wie OpenRouter)"""
        
        try:
            from minesearch.specialized_prompts_impl import SpecializedPrompts
            from minesearch.config.models import OPENROUTER_MODELS
            import httpx
            
            # Standard AI-Modell für alternative Provider
            model_name = "anthropic/claude-3-haiku-20240307"
            
            # Erstelle strukturierten Prompt (wie OpenRouter)
            system_prompt = SpecializedPrompts.get_universal_anti_template_instructions()
            system_prompt += f"""

🎯 SCRAPINGBEE MINING DATENEXTRAKTION
=============================================

Analysiere die folgenden ScrapingBee Web-Scraping Ergebnisse und extrahiere strukturierte Mining-Daten für die Mine "{mine_name}" in {country}.

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
"""
            
            user_prompt = f"""Analysiere die ScrapingBee Scraping-Ergebnisse und extrahiere Mining-Daten für "{mine_name}" in {country}.

{f"Rohstoff: {commodity}" if commodity else ""}
{f"Region: {region}" if region else ""}

Gib NUR das JSON-Objekt zurück.

SCRAPINGBEE CONTENT:
{content}"""
            
            # Sende an OpenRouter (wie andere AI-Provider)
            openrouter_key = self.config.get('openrouter_api_key')
            if not openrouter_key:
                logger.error("[SCRAPINGBEE-AI] OpenRouter API Key fehlt für AI-Extraktion")
                return content  # Fallback auf Raw Content
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "https://mining-data-extraction.com",
                        "X-Title": "MineSearch ScrapingBee AI Extraction",
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
                    logger.info(f"[SCRAPINGBEE-AI] Erfolgreiche AI-Extraktion mit {model_name}")
                    return ai_response
                else:
                    logger.error(f"[SCRAPINGBEE-AI] AI-API Fehler: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"[SCRAPINGBEE-AI] AI-Extraktion fehlgeschlagen: {e}")
        
        # Fallback: Originaler Content
        return content
    
    def _apply_quality_gates(self, extracted_data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """Wendet OpenRouter-ähnliche Quality Gates auf ScrapingBee-Ergebnisse an"""
        
        if not extracted_data or not extracted_data.get('data'):
            return extracted_data
            
        data = extracted_data['data']
        
        # Basis Quality Gate: Name sollte immer gesetzt sein
        if not data.get('Name'):
            data['Name'] = mine_name
            logger.debug(f"[SCRAPINGBEE-QG] Name ergänzt: {mine_name}")
        
        # Template-Detection für numerische Felder (wie in consolidated_field_utils.py)
        numeric_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 'Fördermenge/Jahr', 'Fläche der Mine in qkm']
        
        for field in numeric_fields:
            if field in data and data[field]:
                value_str = str(data[field])
                # Schutz vor Template-Detection für numerische Werte
                if any(char.isdigit() for char in value_str) or '$' in value_str or '€' in value_str:
                    logger.debug(f"[SCRAPINGBEE-QG] Numerisches Feld geschützt: {field} = {data[field]}")
                    continue  # Numerische Felder nicht durch Template-Detection entfernen
        
        # Entferne None-Werte und leere Strings (REGEL 10)
        cleaned_data = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned_data[key] = value
        
        extracted_data['data'] = cleaned_data
        
        logger.info(f"[SCRAPINGBEE-QG] Quality Gates angewendet für {mine_name}")
        return extracted_data