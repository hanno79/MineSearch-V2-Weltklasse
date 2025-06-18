"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Bright Data Web Scraping Agent Implementation
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class BrightDataAgent(BaseAgent):
    """Bright Data Agent für Enterprise-Level Web Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].brightdata_key
        self.base_url = "https://api.brightdata.com"
        self._rate_limiter = RateLimiter(rate=100, per=60.0)  # 100 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="brightdata")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
        # Bright Data Datacenter Proxies
        self.proxy_config = {
            'datacenter': True,
            'residential': False,  # Für sensible Seiten
            'mobile': False
        }
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Bright Data Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key und Proxy-Zugang"""
        if not self.api_key:
            self.logger.warning("Kein Bright Data API-Key konfiguriert")
            return False
            
        try:
            # Test Proxy-Verbindung
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.get(
                f"{self.base_url}/account_info",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweitertes Mining-spezifisches Web Scraping mit Bright Data durch"""
        results = []
        
        self.perf_logger.start_timer(f"brightdata_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen und Domains
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Bright Data: Starte Enterprise Mining-Suche")
            
            # 1. Erweiterte Web Search Collection
            search_urls = await self._collect_enhanced_mining_urls(query, mining_queries[:20], mining_domains[:20])
            
            # 2. Parallel Deep Scraping mit verschiedenen Proxy-Typen
            if search_urls:
                scraping_tasks = []
                for idx, url in enumerate(search_urls[:30]):  # Mehr URLs für Mining
                    # Status-Update
                    if hasattr(self, 'status_callback') and self.status_callback and idx % 5 == 0:
                        await self.status_callback(f"Bright Data: Scrape {idx+1}/{min(len(search_urls), 30)} URLs")
                    
                    scraping_tasks.append(self._deep_mining_scrape(url, query, mining_queries))
                
                scraped_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                for result in scraped_results:
                    if isinstance(result, list):
                        results.extend(result)
            
            # 3. Erweiterte spezialisierte Datensammlung
            specialized_results = await self._collect_enhanced_specialized_data(query, mining_domains)
            results.extend(specialized_results)
            
            self.perf_logger.end_timer(
                f"brightdata_search_{query.mine_name}",
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
    
    async def _collect_enhanced_mining_urls(self, query: MineQuery, mining_queries: List[str], mining_domains: List[str]) -> List[str]:
        """Sammelt erweiterte Mining-URLs über Bright Data Search Collector"""
        urls = []
        
        # Verwende erweiterte Mining-Queries
        for idx, search_query in enumerate(mining_queries):
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Bright Data: Suche {idx+1}/{len(mining_queries)}")
            try:
                # Nutze Bright Data's SERP API
                collector_params = {
                    "collector": "search_engine",
                    "query": search_query,
                    "search_engine": "google",
                    "country": self._get_country_code(query.country),  # Dynamisch basierend auf Query
                    "num_results": 30,  # Mehr Ergebnisse für Mining
                    "include_domains": mining_domains[:10],  # Fokus auf Mining-Domains
                    "language": self._get_language_code(query.languages)  # Dynamisch basierend auf Query
                }
                
                results = await self._run_collector(collector_params)
                
                if results:
                    for result in results.get('organic_results', []):
                        url = result.get('link')
                        if url and self._is_mining_relevant(url, result.get('title', '')):
                            urls.append(url)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Search Collection Fehler: {e}")
        
        return list(set(urls))  # Deduplizieren
    
    async def _deep_mining_scrape(self, url: str, query: MineQuery, mining_queries: List[str]) -> List[SearchResult]:
        """Führt Deep Mining Scrape mit Bright Data Enterprise Features durch"""
        results = []
        
        try:
            # Konfiguriere Proxy basierend auf URL
            proxy_type = self._select_proxy_type(url)
            
            scrape_params = {
                "url": url,
                "proxy_type": proxy_type,
                "country": self._get_country_code(query.country),  # Dynamisch
                "render_js": self._needs_javascript(url),
                "wait_for": "networkidle" if self._needs_javascript(url) else None,
                "timeout": 30000,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; MineSearchBot/1.0)",
                    "Accept-Language": self._get_accept_languages(query.languages)  # Dynamisch
                }
            }
            
            # Führe Scraping durch
            content = await self._execute_scraping(scrape_params)
            
            if content:
                # Extrahiere strukturierte Daten
                extracted = self._extract_mining_data(content, url, query)
                results.extend(extracted)
                
                # ÄNDERUNG 17.06.2025: Dynamische Regierungsseiten-Erkennung
                # Government-Seiten werden durch generische Muster erkannt
                if self._is_government_site(url):
                    gov_data = self._extract_government_data(content, url, query)
                    results.extend(gov_data)
        
        except Exception as e:
            self.logger.error(f"Proxy Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _collect_enhanced_specialized_data(self, query: MineQuery, mining_domains: List[str]) -> List[SearchResult]:
        """Sammelt erweiterte spezialisierte Mining-Daten über Bright Data Datasets"""
        results = []
        
        # Erweiterte Mining-spezifische Datasets
        dataset_types = [
            'mining_companies',
            'environmental_compliance',
            'government_permits',
            'financial_filings',
            'technical_reports'
        ]
        
        # ÄNDERUNG 17.06.2025: Entfernt hardcodierte Länder-spezifische Datasets
        # Datasets werden dynamisch basierend auf verfügbaren Datenquellen ausgewählt
        
        for dataset_type in dataset_types:
            try:
                dataset_params = {
                    "dataset": dataset_type,
                    "filters": {
                        "company_name": {"contains": query.mine_name},
                        "industry": {"in": ["mining", "minerals", "extraction"]},
                        "country": query.country
                    },
                    "fields": ["all"]
                }
                
                dataset_results = await self._query_dataset(dataset_params)
                
                if dataset_results:
                    # Parse Dataset-spezifische Felder
                    for record in dataset_results:
                        parsed = self._parse_dataset_record(record, dataset_type, query)
                        results.extend(parsed)
                
            except Exception as e:
                self.logger.error(f"Dataset Query Fehler: {e}")
        
        return results
    
    async def _run_collector(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Führt Bright Data Collector aus"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/datasets/trigger",
                headers=headers,
                json=params,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    # Warte auf Ergebnisse
                    collection_id = (await response.json()).get('collection_id')
                    if collection_id:
                        return await self._get_collection_results(collection_id)
                else:
                    error = await response.text()
                    self.logger.error(f"Collector Fehler: {error}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Collector Exception: {e}")
            return None
    
    async def _get_collection_results(self, collection_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
        """Holt Collector-Ergebnisse"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            try:
                async with self._session.get(
                    f"{self.base_url}/datasets/results/{collection_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'ready':
                            return data.get('data')
                    elif response.status == 404:
                        continue  # Noch nicht fertig
                        
            except Exception as e:
                self.logger.error(f"Results Check Fehler: {e}")
        
        return None
    
    async def _execute_scraping(self, params: Dict[str, Any]) -> Optional[str]:
        """Führt Scraping mit Proxy aus"""
        await self._rate_limiter.acquire()
        
        # Bright Data Web Unlocker API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/unlocker",
                headers=headers,
                json=params,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('html', '')
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Scraping Execution Fehler: {e}")
            return None
    
    async def _query_dataset(self, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fragt Bright Data Dataset ab"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/datasets/query",
                headers=headers,
                json=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Dataset Query Fehler: {e}")
            return None
    
    def _is_mining_relevant(self, url: str, title: str) -> bool:
        """Prüft ob URL/Title mining-relevant ist"""
        # Positive Indikatoren
        positive_keywords = [
            'mining', 'mine', 'mineral', 'resources', 'extraction',
            'operator', 'environmental', 'restoration', 'production',
            'mern', 'nrcan', 'gov', 'sedar'
        ]
        
        # Negative Indikatoren
        negative_keywords = [
            'jobs', 'careers', 'recruitment', 'stock', 'trading',
            'wikipedia', 'facebook', 'twitter', 'youtube'
        ]
        
        combined = (url + ' ' + title).lower()
        
        # Prüfe negative Keywords
        if any(neg in combined for neg in negative_keywords):
            return False
        
        # Prüfe positive Keywords
        return any(pos in combined for pos in positive_keywords)
    
    def _select_proxy_type(self, url: str) -> str:
        """Wählt optimalen Proxy-Typ basierend auf URL"""
        # ÄNDERUNG 17.06.2025: Dynamische Proxy-Auswahl
        # Regierungsseiten werden generisch erkannt
        if self._is_government_site(url):
            return 'residential'
        
        # Geschützte Datenbanken
        if any(db in url for db in ['gestim', 'sigeom', 'sedar']):
            return 'residential'
        
        # Standard-Seiten
        return 'datacenter'
    
    def _needs_javascript(self, url: str) -> bool:
        """Bestimmt ob JavaScript-Rendering nötig ist"""
        js_sites = [
            'gestim', 'sigeom', 'claimaps',
            'mining-technology.com', 'infomine.com'
        ]
        
        return any(site in url.lower() for site in js_sites)
    
    def _extract_mining_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Mining-Daten aus HTML mit kontextbasierter Extraktion"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Entferne Scripts und Styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Nutze kontextbasierte Extraktion für alle erforderlichen Felder
            for field in query.required_fields:
                extracted_values = self._extract_with_context(text, field)
                
                for value, confidence in extracted_values[:3]:  # Top 3 Ergebnisse
                    if confidence >= 0.4:  # Mindest-Konfidenz
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=value,
                            source=f"BrightData: {urlparse(url).netloc}",
                            source_url=url,
                            source_date=self._extract_year_from_text(text),
                            confidence_score=confidence,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                "extraction_method": "contextual",
                                "page_title": soup.title.string if soup.title else None
                            }
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {field} = {value} (Konfidenz: {confidence:.2f})")
            
            # Strukturierte Daten-Extraktion
            # Suche nach JSON-LD
            json_lds = soup.find_all('script', type='application/ld+json')
            for json_ld in json_lds:
                try:
                    data = json.loads(json_ld.string)
                    structured_results = self._extract_from_json_ld(data, url, query)
                    results.extend(structured_results)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"HTML Extraction Fehler: {e}")
        
        return results
    
    def _extract_government_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Spezielle Extraktion für Regierungsseiten"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Suche nach Government-spezifischen Strukturen
            # Oft in Tabellen oder Definition Lists
            
            # Tabellen mit Mining-Daten
            tables = soup.find_all('table')
            for table in tables:
                # Prüfe ob relevante Tabelle
                table_text = table.get_text().lower()
                if query.mine_name.lower() in table_text:
                    # Extrahiere Tabellenzeilen
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text().strip().lower()
                            value = cells[1].get_text().strip()
                            
                            # Mapping zu unseren Feldern
                            field_mapping = {
                                'operator': 'betreiber',
                                'exploitant': 'betreiber',
                                'titulaire': 'betreiber',
                                'coordinates': 'koordinaten',
                                'coordonnées': 'koordinaten',
                                'status': 'aktivitaetsstatus',
                                'statut': 'aktivitaetsstatus',
                                'commodity': 'rohstofftyp',
                                'substance': 'rohstofftyp',
                                'area': 'flaeche',
                                'superficie': 'flaeche'
                            }
                            
                            for key, field_name in field_mapping.items():
                                if key in label:
                                    result = SearchResult(
                                        mine_name=query.mine_name,
                                        field_name=field_name,
                                        value=value,
                                        source=f"Gov Data: {url.split('/')[2]}",
                                        source_url=url,
                                        source_date=datetime.now().year,
                                        confidence_score=0.9,
                                        agent_name=self.name,
                                        timestamp=datetime.now(),
                                        metadata={}
                                    )
                                    results.append(result)
                                    break
                                    
        except Exception as e:
            self.logger.error(f"Government Data Extraction Fehler: {e}")
        
        return results
    
    def _extract_from_json_ld(self, data: Dict[str, Any], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert aus JSON-LD strukturierten Daten"""
        results = []
        
        try:
            # Rekursive Suche nach relevanten Daten
            def extract_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['operator', 'owner'] and isinstance(value, (str, dict)):
                            org_name = value if isinstance(value, str) else value.get('name', '')
                            if org_name:
                                results.append(SearchResult(
                                    mine_name=query.mine_name,
                                    field_name='betreiber',
                                    value=org_name,
                                    source=f"Bright Data JSON-LD: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                ))
                        elif key == 'geo' and isinstance(value, dict):
                            lat = value.get('latitude')
                            lon = value.get('longitude')
                            if lat and lon:
                                results.append(SearchResult(
                                    mine_name=query.mine_name,
                                    field_name='koordinaten',
                                    value=f"{lat}, {lon}",
                                    source=f"Bright Data JSON-LD: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                ))
                        elif isinstance(value, (dict, list)):
                            extract_recursive(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for item in obj:
                        extract_recursive(item, path)
            
            extract_recursive(data)
            
        except Exception as e:
            self.logger.error(f"JSON-LD Extraction Fehler: {e}")
        
        return results
    
    def _parse_dataset_record(self, record: Dict[str, Any], dataset_type: str, query: MineQuery) -> List[SearchResult]:
        """Parst Dataset-Record zu SearchResults"""
        results = []
        
        # Dataset-spezifisches Mapping
        if dataset_type == 'canadian_business_registry':
            if 'company_name' in record and query.mine_name.lower() in record['company_name'].lower():
                if 'legal_name' in record:
                    results.append(SearchResult(
                        mine_name=query.mine_name,
                        field_name='betreiber',
                        value=record['legal_name'],
                        source="Bright Data Business Registry",
                        source_url="",
                        source_date=datetime.now().year,
                        confidence_score=0.9,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={}
                    ))
                    
        elif dataset_type == 'environmental_permits':
            if 'permit_holder' in record:
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='betreiber',
                    value=record['permit_holder'],
                    source="Bright Data Environmental Permits",
                    source_url="",
                    source_date=record.get('issue_date', datetime.now()).year,
                    confidence_score=0.9,
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={}
                ))
            
            if 'financial_assurance' in record:
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='sanierungskosten',
                    value=f"{record['financial_assurance']:,} CAD",
                    source="Bright Data Environmental Permits",
                    source_url="",
                    source_date=record.get('issue_date', datetime.now()).year,
                    confidence_score=0.9,
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={}
                ))
        
        return results
    
    def _clean_value(self, value: str, field_name: str) -> str:
        """Bereinigt extrahierte Werte"""
        # Entferne übermäßige Whitespaces
        value = re.sub(r'\s+', ' ', value).strip()
        
        if field_name == 'sanierungskosten':
            # Normalisiere Währungsbeträge
            value = value.replace(' ', '')
            if 'million' in value.lower() or 'M' in value:
                try:
                    num_match = re.search(r'([\d,\.]+)', value)
                    if num_match:
                        num = float(num_match.group(1).replace(',', ''))
                        value = f"{int(num * 1000000):,} CAD"
                except:
                    pass
        
        elif field_name == 'koordinaten':
            # Normalisiere Koordinaten
            if 'UTM' in value:
                # Konvertiere UTM zu Lat/Lon wenn möglich
                # (Implementierung würde UTM-Konvertierung benötigen)
                pass
            else:
                # Entferne Grad-Zeichen
                value = value.replace('°', '').replace("'", '').replace('"', '')
        
        return value
    
    def _is_government_site(self, url: str) -> bool:
        """Erkennt Regierungsseiten dynamisch"""
        # ÄNDERUNG 17.06.2025: Generische Regierungsseiten-Erkennung
        government_indicators = [
            '.gov', 'government', 'gouv', 'gobierno', 'regierung', 
            'ministry', 'ministere', 'ministerio', 'department',
            'federal', 'national', 'state', 'province'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in government_indicators)
    
    def _get_country_code(self, country: str) -> str:
        """Konvertiert Ländernamen zu ISO-Code"""
        # ÄNDERUNG 17.06.2025: Entfernt hardcodiertes Country-Mapping
        # Dynamische Lösung: Nutze Landesname direkt oder hole Code über Agent
        # Für Bright Data API wird der volle Landesname verwendet
        return country.lower()[:2] if country else "int"  # "int" für international
    
    def _get_language_code(self, languages: List[str]) -> str:
        """Gibt primären Sprachcode zurück"""
        if languages and len(languages) > 0:
            return languages[0][:2]  # Erste 2 Zeichen des ersten Sprachcodes
        return "en"  # Default Englisch
    
    def _get_accept_languages(self, languages: List[str]) -> str:
        """Erstellt Accept-Language Header"""
        if not languages:
            return "en-US,en;q=0.9"
        
        # Erstelle Header mit abnehmender Priorität
        parts = []
        for i, lang in enumerate(languages[:3]):  # Max 3 Sprachen
            if i == 0:
                parts.append(f"{lang}")
            else:
                parts.append(f"{lang};q={0.9 - i*0.1}")
        
        return ",".join(parts)
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Bright Data Agent beendet")