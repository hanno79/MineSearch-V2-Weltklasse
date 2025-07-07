"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: ScrapingBee Provider für Web-Scraping mit JavaScript-Rendering
"""

import asyncio
import aiohttp
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
                is_free=False
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
        
        async with aiohttp.ClientSession() as session:
            # Scrape nur URL-basierte Quellen
            url_sources = [s for s in sources if s.get('type') in ['url', 'website', None]]
            
            for source in url_sources[:10]:  # Limitiere auf 10 URLs
                url = source.get('url') or source.get('value', '')
                if not url or not url.startswith('http'):
                    continue
                    
                try:
                    result = await self._scrape_url(session, url, model_id, options)
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
        """Führt Web-Scraping mit ScrapingBee durch"""
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
            
            # Baue Suchquery für Mining-Daten
            search_urls = await self._build_search_urls(query, options)
            
            # Scrape die gefundenen URLs
            scraped_data = []
            sources = []
            
            async with aiohttp.ClientSession() as session:
                for url in search_urls[:5]:  # Limitiere auf 5 URLs
                    try:
                        result = await self._scrape_url(session, url, model_id, options)
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
            
            # Verarbeite extrahierte Daten
            structured_data = await self._process_scraped_data(scraped_data, options)
            
            # Kombiniere Inhalte
            combined_content = "\n\n---\n\n".join(scraped_data)
            
            search_duration = (datetime.now() - start_time).total_seconds()
            
            return SearchResult(
                success=True,
                content=combined_content,
                structured_data=structured_data,
                sources=sources,
                metadata={
                    'provider': 'scrapingbee',
                    'model': model_id,
                    'search_duration': search_duration,
                    'urls_scraped': len(sources),
                    'credits_used': len(sources) * model_config.get('credits_cost', 1)
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
    
    async def _scrape_url(self, session: aiohttp.ClientSession, url: str, 
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
        
        # Spezielle Parameter für AI-Extract
        if model_id == 'ai-extract':
            params['extract_rules'] = json.dumps({
                'title': 'h1',
                'content': 'body',
                'tables': {
                    'selector': 'table',
                    'type': 'table'
                }
            })
            params['ai_extract'] = 'true'
            params['ai_query'] = self.get_system_prompt(options)
        
        # Entferne None-Werte
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.models[model_id]['timeout'])
            # Verwende GET-Request mit query parameters
            async with session.get(self.base_url, params=params, timeout=timeout) as response:
                if response.status == 200:
                    # Prüfe Content-Type für PDF-Handhabung
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/pdf' in content_type:
                        # PDF-Datei - speichere als Binary
                        logger.info(f"[ScrapingBee] PDF erkannt für {url}")
                        pdf_content = await response.read()  # Binary content
                        return {
                            'url': url,
                            'content': f"[PDF-Dokument gefunden - {len(pdf_content)} bytes]\nURL: {url}\n\nPDF-Analyse:\n- Größe: {len(pdf_content)/1024:.1f} KB\n- Typ: {content_type}\n\nHinweis: PDF müsste mit spezialisierten Tools extrahiert werden.",
                            'title': 'PDF Document',
                            'is_pdf': True,
                            'pdf_size': len(pdf_content)
                        }
                    elif model_id == 'ai-extract':
                        # JSON Response erwartet
                        try:
                            data = await response.json()
                            return {
                                'url': url,
                                'content': json.dumps(data) if isinstance(data, dict) else str(data),
                                'title': data.get('title', '') if isinstance(data, dict) else 'Mining Data'
                            }
                        except json.JSONDecodeError:
                            # Fallback auf Text
                            text_content = await response.text()
                            return {
                                'url': url,
                                'content': text_content,
                                'title': 'Mining Data'
                            }
                    else:
                        # Standard Text/HTML Response
                        try:
                            text_content = await response.text()
                            return {
                                'url': url,
                                'content': text_content,
                                'title': self._extract_title_from_html(text_content)
                            }
                        except UnicodeDecodeError:
                            # Binary content das kein PDF ist
                            binary_content = await response.read()
                            return {
                                'url': url,
                                'content': f"[Binary-Datei - {len(binary_content)} bytes]\nContent-Type: {content_type}",
                                'title': 'Binary File',
                                'is_binary': True
                            }
                else:
                    error_text = await response.text()
                    logger.error(f"[ScrapingBee] HTTP {response.status} für {url}: {error_text[:200]}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"[ScrapingBee] Timeout beim Scrapen von {url}")
            return None
        except Exception as e:
            logger.error(f"[ScrapingBee] Fehler beim Scrapen von {url}: {e}")
            return None
    
    async def _process_scraped_data(self, scraped_data: List[str], 
                                   options: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet die gescrapten Daten zu strukturierten Mining-Informationen"""
        
        # Basis-Struktur
        result = {
            'Name': options.get('mine_name', ''),
            'Country': options.get('country', ''),
            'Region': options.get('region', '-'),
            'Eigentümer': '-',
            'Betreiber': '-',
            'x-Koordinate': '-',
            'y-Koordinate': '-',
            'Aktivitätsstatus': '-',
            'Restaurationskosten': '-',
            'Jahr der Aufnahme der Kosten': '-',
            'Jahr der Erstellung des Dokumentes': '-',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': options.get('commodity', '-'),
            'Minentyp (Untertage/ Open-Pit/ usw.)': '-',
            'Produktionsstart': '-',
            'Produktionsende': '-',
            'Fördermenge/Jahr': '-',
            'Fläche der Mine in qkm': '-',
            'Quellenangaben': '-'
        }
        
        # Kombiniere alle Daten
        combined_text = "\n".join(scraped_data).lower()
        
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