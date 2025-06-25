"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Perplexity Agent Implementation
"""

import aiohttp
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from urllib.parse import urlparse

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from .enhanced_search import get_mining_search_queries, get_mining_domains
from src.core.logger import get_logger, PerformanceLogger
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list
from src.utils.session_manager import SessionManager


class PerplexityAgent(BaseAgent):
    """Perplexity Agent für Web-basierte Recherche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].perplexity_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-reasoning-pro"  # ÄNDERUNG 24.06.2025: Enhanced reasoning model für bessere Ergebnisse
        # ÄNDERUNG 23.06.2025: Reduziertes Rate Limit
        self._rate_limiter = RateLimiter(rate=5, per=60.0)  # Nur 5 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="perplexity")
        self.perf_logger = PerformanceLogger(self.logger)
        # Request-Cache zur Vermeidung von Duplikaten
        self._request_cache = {}
        self._cache_ttl = 300  # 5 Minuten Cache
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            loop_id = id(asyncio.get_running_loop())
            self.logger.debug(f"[PerplexityAgent] Initialisierung im Loop {loop_id}")
            # ÄNDERUNG 25.06.2025: Verwende SessionManager Instanz
            self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"perplexity_{self.name}", timeout=90)
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
            self.logger.info("Perplexity Agent erfolgreich initialisiert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        # ÄNDERUNG 25.06.2025: Robusteres Cleanup mit besserer Fehlerbehandlung
        try:
            loop_id = id(asyncio.get_running_loop())
            self.logger.debug(f"[PerplexityAgent] Cleanup im Loop {loop_id}")
        except RuntimeError:
            self.logger.debug("[PerplexityAgent] Cleanup ohne aktiven Event Loop")
        
        # Session cleanup
        if hasattr(self, '_session_manager') and self._session_manager:
            try:
                await self._session_manager.close_session(f"perplexity_{self.name}")
                self.logger.debug("Session erfolgreich geschlossen")
            except Exception as e:
                self.logger.warning(f"Fehler beim Session Cleanup: {e}")
        
        # Setze Session auf None
        self._robust_session = None
        
        # Rufe parent cleanup auf
        try:
            await super().cleanup()
        except Exception as e:
            self.logger.warning(f"Fehler beim parent cleanup: {e}")
        
        self.logger.info("Perplexity Agent beendet")
    
    async def _ensure_session(self):
        """ÄNDERUNG 25.06.2025: Stellt sicher, dass Session verfügbar ist - verbesserte Event Loop Behandlung"""
        # Robustere Event Loop Behandlung
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Kein laufender Event Loop, erstelle einen neuen
            self.logger.warning("[PerplexityAgent] Kein laufender Event Loop gefunden, erstelle neuen")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop_id = id(loop)
        self.logger.debug(f"[PerplexityAgent] _ensure_session im Loop {loop_id}")
        
        # ÄNDERUNG 25.06.2025: Verbesserte None-Prüfung für _robust_session
        # Prüfe ob Session existiert und zum aktuellen Loop gehört
        if (not hasattr(self, '_robust_session') or self._robust_session is None or 
            not hasattr(self, '_session_manager') or self._session_manager is None):
            self.logger.info(f"[PerplexityAgent] Session wird im neuen Loop {loop_id} neu initialisiert")
            if not hasattr(self, '_session_manager') or self._session_manager is None:
                self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"perplexity_{self.name}", timeout=90)
        else:
            # Prüfe ob die Session noch gültig ist
            if self._robust_session is not None:
                try:
                    session = await self._robust_session.get_session()
                    if session.closed:
                        self.logger.info(f"[PerplexityAgent] Session war geschlossen, erstelle neue")
                        self._robust_session = await self._session_manager.get_robust_session(f"perplexity_{self.name}", timeout=90)
                except Exception as e:
                    self.logger.warning(f"[PerplexityAgent] Session-Check fehlgeschlagen: {e}, erstelle neue")
                    self._robust_session = await self._session_manager.get_robust_session(f"perplexity_{self.name}", timeout=90)
            else:
                # Session ist None, erstelle neue
                self.logger.info(f"[PerplexityAgent] Session war None, erstelle neue")
                self._robust_session = await self._session_manager.get_robust_session(f"perplexity_{self.name}", timeout=90)
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Perplexity API-Key konfiguriert")
            return False
            
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Einfache Test-Anfrage
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 16  # ÄNDERUNG 24.06.2025: Minimum 16 für API-Kompatibilität
            }
            
            async with self._robust_session.request(
                'POST',
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.info("Perplexity API-Key erfolgreich validiert")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Perplexity Validierung fehlgeschlagen ({response.status}): {error_text}")
                    return False
                
        except aiohttp.ClientTimeout:
            self.logger.error("Perplexity Validierung Timeout - API antwortet nicht rechtzeitig")
            return False
        except Exception as e:
            self.logger.error(f"Perplexity Validierung fehlgeschlagen: {type(e).__name__}: {e}")
            return False
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search_mine - für Kompatibilität mit Source Discovery"""
        return await self.search_mine(query)
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit Perplexity durch"""
        results = []
        
        self.perf_logger.start_timer(f"perplexity_search_{query.mine_name}")
        
        try:
            # Get enhanced search queries
            search_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # ÄNDERUNG 23.06.2025: Reduzierte Query-Anzahl und Caching
            priority_queries = search_queries[:3]  # Nur Top 3 queries
            
            # Execute searches with different query strategies
            for idx, search_query in enumerate(priority_queries):
                # Check Cache
                cache_key = f"{query.mine_name}_{search_query[:50]}"
                if cache_key in self._request_cache:
                    cached_time, cached_response = self._request_cache[cache_key]
                    if (datetime.now() - cached_time).seconds < self._cache_ttl:
                        self.logger.info(f"Using cached response for query {idx+1}")
                        parsed_results = self._parse_response(cached_response, query, f"query_{idx+1}_cached")
                        results.extend(parsed_results)
                        continue
                
                self.logger.info(f"Perplexity-Suche {idx+1}/{len(priority_queries)}: {search_query[:100]}...")
                
                # Create prompt with search query and domain focus
                prompt = self._create_enhanced_prompt(query, search_query, mining_domains[:5])
                
                response = await self._make_api_call(prompt)
                if response:
                    # Cache successful response
                    self._request_cache[cache_key] = (datetime.now(), response)
                    parsed_results = self._parse_response(response, query, f"query_{idx+1}")
                    results.extend(parsed_results)
                    
                # Längere Pause zwischen Anfragen
                await asyncio.sleep(3)
            
            # Also use original specialized prompts
            prompts = self._create_prompts(query)
            for search_type, prompt in prompts.items():
                self.logger.info(f"Perplexity-Spezialisierte Suche: {search_type}")
                
                response = await self._make_api_call(prompt)
                if response:
                    parsed_results = self._parse_response(response, query, search_type)
                    results.extend(parsed_results)
                    
                await asyncio.sleep(1)
            
            self.perf_logger.end_timer(
                f"perplexity_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_requests'] += len(priority_queries) + len(prompts)
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    def _create_enhanced_prompt(self, query: MineQuery, search_query: str, priority_domains: List[str]) -> str:
        """Creates enhanced prompt using specific search queries and domains"""
        domains_str = ", ".join(priority_domains)
        
        # ÄNDERUNG 23.06.2025: Klarere Prompt-Struktur für bessere Antworten
        prompt = f"""Search for information about the {query.mine_name} mine in {query.region}, {query.country}.

IMPORTANT: Provide ONLY factual information found in your search results. Do not repeat the search query or instructions.

Focus on these sources: {domains_str}

Find and report these specific data points:
- Owner/Operator: [Company name that operates the mine]
- Location: [GPS coordinates or precise location]
- Status: [Current operational status]
- Commodities: [What minerals/metals are mined]
- Production: [Annual production volumes]
- Workforce: [Number of employees]
- Environmental costs: [Closure/remediation costs]
- Recent updates: [News from 2020-2025]

Format: Provide direct answers with source citations. Start with "Based on my search..." and list the findings."""
        
        return prompt
    
    def _create_prompts(self, query: MineQuery) -> Dict[str, str]:
        """Create optimized prompts for Perplexity's online search capabilities"""
        """Erstellt spezialisierte Prompts für Web-Recherche"""
        prompts = {}
        
        # Allgemeine Informationen - ERWEITERT
        general_prompt = f"""COMPREHENSIVE SEARCH REQUIRED: Find ALL available information about the {query.mine_name} mine in {query.region}, {query.country}.

SEARCH INSTRUCTIONS:
- Use ALL name variations and spellings
- Search in multiple languages relevant to {query.country}
- Look for official documents, PDFs, technical reports
- Check government databases, company filings, NGO reports
- Include historical and archived information

REQUIRED DATA:
1. OWNERSHIP:
   - Current operator/owner (full legal name)
   - Parent company and ownership structure
   - Historical ownership changes
   - Joint venture partners

2. LOCATION:
   - Exact GPS coordinates (latitude, longitude)
   - Physical address
   - Distance from nearest city/town
   - Access routes

3. OPERATIONAL:
   - Current status (active/suspended/closed/care & maintenance)
   - Status change dates and reasons
   - Mine type (open pit/underground/both)
   - Mining method details

4. PRODUCTION:
   - All commodities produced (primary and by-products)
   - Annual production volumes (with units)
   - Historical production data
   - Processing capacity

5. FINANCIAL:
   - Environmental bonds/financial assurance amounts
   - Closure cost estimates
   - Asset value
   - Recent investments

6. TECHNICAL:
   - Reserve/resource estimates
   - Mine life
   - Processing methods
   - Infrastructure

Provide EXACT values with SPECIFIC sources and dates. Include direct URLs."""

        prompts['general'] = general_prompt
        
        # Umwelt- und Finanzdaten
        environmental_prompt = f"""Search for environmental and financial information about the {query.mine_name} mine in {query.region}, {query.country}.

Specifically look for:
1. Rehabilitation/restoration costs (closure bonds, financial assurance)
2. Environmental liabilities
3. Water usage/consumption data
4. Energy consumption
5. Environmental certifications (ISO 14001, etc.)
6. Recent environmental incidents or violations
7. Community impact assessments
8. Sustainability reports

Focus on recent data (2020-2025) from official sources, government databases, and company reports.
Include specific numbers with currency and units."""

        prompts['environmental'] = environmental_prompt
        
        # Regierungsdatenbanken für Kanada
        if query.country.lower() == 'canada':
            gov_prompt = f"""Search Canadian government databases for {query.mine_name} in {query.region}:

Check these specific sources:
- Natural Resources Canada (NRCan) mine database
- Provincial mining registries (MERN for Quebec, Ontario Mining Registry, etc.)
- GESTIM database for Quebec mines
- Environmental assessment registries
- Securities commission filings (SEDAR)

Find official data on:
- Mining claims and permits
- Environmental bonds and financial assurances
- Production statistics
- Compliance reports
- Corporate registration details"""

            prompts['government'] = gov_prompt
        
        return prompts
    
    async def _make_api_call(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Macht API-Aufruf zu Perplexity"""
        loop_id = id(asyncio.get_running_loop())
        self.logger.debug(f"[PerplexityAgent] _make_api_call im Loop {loop_id}")
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a mining industry research specialist. Your responses must:

1. Provide ONLY factual data from your search results
2. Use this exact format for answers:
   - Owner: [company name only]
   - Status: [active/closed/suspended only]
   - Coordinates: [numbers only]
   - Production: [numbers with units]
   - Costs: [numbers with currency]

3. NEVER include:
   - The search query in your response
   - Phrases like "or owner company" or "extracted"
   - Incomplete sentences
   - Speculative information

4. If data is not found, say "Not found" - do not guess"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Sehr niedrig für faktische Genauigkeit
            "max_tokens": 2500,
            "web_search": True,  # Aktiviere Web-Suche
            "return_citations": True  # Gebe Quellen zurück
        }
        
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            async with self._robust_session.request(
                'POST',
                self.base_url,
                headers=headers,
                json=payload,
                timeout=90  # Extended timeout for deeper searches
            ) as response:
                if response.status == 200:
                    # ÄNDERUNG 20.06.2025: Sicheres JSON-Parsing
                    try:
                        data = await response.json()
                        # Prüfe ob Response ein Dictionary ist
                        if isinstance(data, dict):
                            return data
                        else:
                            self.logger.error(f"Unerwartetes Response-Format: {type(data)}")
                            return None
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        self.logger.error(f"JSON Parse Fehler: {e}, Response: {text[:200]}...")
                        # ÄNDERUNG 23.06.2025: Behandle String-Responses
                        if text:
                            return {"choices": [{"message": {"content": text}}], "type": "text_response"}
                        return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except asyncio.CancelledError:
            # Propagiere Cancellation
            self.logger.debug("API Anfrage wurde abgebrochen")
            raise
        except Exception as e:
            self.logger.error(f"API Anfrage Fehler: {type(e).__name__}: {str(e)}")
            # ÄNDERUNG 25.06.2025: Bei Event Loop Fehlern, versuche Session neu zu erstellen
            if "event loop" in str(e).lower() or "session" in str(e).lower():
                self.logger.info("Versuche Session neu zu erstellen nach Event Loop Fehler...")
                self._robust_session = None
                try:
                    await self._ensure_session()
                    self.logger.info("Session erfolgreich neu erstellt, bitte Anfrage wiederholen")
                except Exception as session_error:
                    self.logger.error(f"Konnte Session nicht neu erstellen: {session_error}")
            return None
    
    def _parse_response(self, response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Perplexity-Antwort mit Fokus auf Faktenextraktion"""
        results = []
        
        try:
            # ÄNDERUNG 23.06.2025: Vollständige Type-Checking und Response-Behandlung
            if response is None:
                self.logger.error("Response ist None")
                return results
            
            # Behandle verschiedene Response-Typen
            if isinstance(response, str):
                # Wenn Response ein String ist, konvertiere zu Dict-Format
                self.logger.warning(f"Response ist ein String, konvertiere zu Dict-Format")
                response = {
                    "choices": [{"message": {"content": response}}],
                    "type": "text_response"
                }
            elif hasattr(response, '__dict__'):
                # Wenn Response ein Objekt ist, konvertiere zu Dict
                self.logger.warning(f"Response ist ein Objekt vom Typ {type(response)}, konvertiere zu Dict")
                try:
                    response = response.__dict__
                except Exception as e:
                    self.logger.error(f"Konnte Objekt nicht zu Dict konvertieren: {e}")
                    return results
            
            # ÄNDERUNG 21.06.2025: Robustere Response-Behandlung
            if not isinstance(response, dict):
                self.logger.error(f"Response ist kein Dictionary: {type(response)}")
                return results
                
            # ÄNDERUNG 23.06.2025: Sichere Navigation durch Response-Struktur
            content = ""
            citations = []
            
            if safe_get(response, 'type') == 'text_response':
                # Direkte Text-Response
                choices = safe_get(response, 'choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = safe_get(first_choice, 'message', {})
                        if isinstance(message, dict):
                            content = safe_get(message, 'content', '')
                        elif isinstance(message, str):
                            content = message
                    elif isinstance(first_choice, str):
                        content = first_choice
            elif 'choices' in response and response['choices']:
                # Standard API Response
                choices = safe_get(response, 'choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = safe_get(first_choice, 'message', '')
                        if isinstance(message, str):
                            content = message
                        elif isinstance(message, dict):
                            content = safe_get(message, 'content', '')
                        else:
                            self.logger.error(f"Unerwarteter message Typ: {type(message)}")
                    
                citations = safe_get(response, 'citations', [])
                if not isinstance(citations, list):
                    citations = []
                
            # Nur wenn Content vorhanden ist, extrahiere Daten
            if content:
                # Extrahiere strukturierte Daten aus dem Text
                extracted_data = self._extract_structured_data(content, citations)
                
                for field_name, value_data in extracted_data.items():
                    if isinstance(value_data, dict) and safe_get(value_data, 'value') and value_data['value'] != 'nichts gefunden':
                        # ÄNDERUNG 20.06.2025: Korrekte Parameter für SearchResult
                        confidence_mapping = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
                        confidence_score = confidence_mapping.get(safe_get(value_data, 'confidence', 'medium'), 0.7)
                        
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=value_data['value'],
                            source=safe_get(value_data, 'source', 'Perplexity Web Search'),
                            source_url=safe_get(value_data, 'url', ''),
                            source_date=safe_get(value_data, 'year', datetime.now().year),
                            confidence_score=confidence_score,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'search_type': search_type, 'language': 'en'}
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {result.field_name} = {result.value}")
            else:
                self.logger.warning("Kein Content in Response gefunden")
                        
        except Exception as e:
            # ÄNDERUNG 23.06.2025: Erweiterte Fehlerdiagnose
            self.logger.error(f"Response Parse Fehler: {e}")
            self.logger.error(f"Response Type: {type(response)}")
            if isinstance(response, str):
                self.logger.error(f"Response String: {response[:200]}...")
            elif isinstance(response, dict):
                self.logger.error(f"Response Keys: {list(response.keys())}")
            import traceback
            self.logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            
        return results
    
    def _extract_structured_data(self, content: str, citations: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Extrahiert strukturierte Daten aus Perplexity-Antwort"""
        extracted = {}
        
        # ÄNDERUNG 23.06.2025: Entferne Prompt-Echo aus Response
        # Perplexity wiederholt manchmal den Search Query am Anfang
        if "Search Query:" in content or "extract:" in content.lower():
            # Versuche nur den tatsächlichen Antwort-Teil zu extrahieren
            parts = content.split("\n\n", 2)
            if len(parts) > 1:
                # Suche nach dem Start der tatsächlichen Antwort
                for i, part in enumerate(parts):
                    if any(keyword in part.lower() for keyword in ["based on", "according to", "found", "shows", "indicates"]):
                        content = "\n\n".join(parts[i:])
                        break
        
        # Patterns für verschiedene Datentypen
        patterns = {
            'betreiber': [
                r'operated by\s+([^,\.\n]+)',
                r'operator[:\s]+([^,\.\n]+)',
                r'owned by\s+([^,\.\n]+)',
                r'owner[:\s]+([^,\.\n]+)'
            ],
            'koordinaten': [
                r'coordinates[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'latitude[:\s]*([-\d\.]+).*longitude[:\s]*([-\d\.]+)',
                r'(\d+°\d+\'[\d\.]+\"[NS])[,\s]+(\d+°\d+\'[\d\.]+\"[EW])'
            ],
            'aktivitaetsstatus': [
                r'status[:\s]+(\w+)',
                r'currently\s+(\w+)',
                r'mine is\s+(\w+)',
                r'operations?\s+(?:are\s+)?(\w+)'
            ],
            'sanierungskosten': [
                r'rehabilitation cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'closure bond[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'financial assurance[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'restoration cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?'
            ],
            'rohstofftyp': [
                r'produces?\s+([^,\.\n]+(?:,\s*[^,\.\n]+)*)',
                r'commodit(?:y|ies)[:\s]+([^,\.\n]+(?:,\s*[^,\.\n]+)*)',
                r'extract(?:s|ing)?\s+([^,\.\n]+(?:,\s*[^,\.\n]+)*)'
            ],
            'flaeche': [
                r'area[:\s]+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)',
                r'covers?\s+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)',
                r'property size[:\s]+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)'
            ],
            'mitarbeiter': [
                r'employs?\s+([\d,]+)\s*(?:people|workers|employees)',
                r'([\d,]+)\s*employees',
                r'workforce[:\s]+([\d,]+)'
            ]
        }
        
        content_lower = content.lower()
        
        # ÄNDERUNG 23.06.2025: Verbesserte Pattern-Matching mit Validierung
        # Suche nach Mustern
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, content_lower, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if len(match.groups()) > 1:  # Für Koordinaten
                        value = f"{match.group(1)}, {match.group(2)}"
                    
                    # Bereinige Wert
                    value = value.strip()
                    
                    # ÄNDERUNG 23.06.2025: Erweiterte Validierung extrahierter Werte
                    # Vermeide Extraktion von Prompt-Fragmenten
                    invalid_values = [
                        "or owner company", "lac expanse", "quebec", "canada",
                        "extract", "search", "find", "look for", "provide",
                        "information", "data", "details", "based on", "according to",
                        "search query", "find information", "please provide",
                        "i need", "looking for", "tell me", "what is",
                        "comprehensive information", "search for", "extract:"
                    ]
                    
                    # Prüfe ob der Wert verdächtig aussieht
                    if any(invalid in value.lower() for invalid in invalid_values):
                        continue  # Skip diesen Match
                    
                    # Prüfe Mindestlänge für sinnvolle Werte
                    if len(value) < 3:
                        continue
                    
                    # ÄNDERUNG 23.06.2025: Zusätzliche Validierung für spezifische Felder
                    if field_name == 'betreiber':
                        # Betreiber sollte wie ein Firmenname aussehen
                        if not any(char.isupper() for char in value):
                            continue  # Sollte mindestens einen Großbuchstaben haben
                        if len(value.split()) > 10:
                            continue  # Zu lang für einen Firmennamen
                    
                    elif field_name == 'koordinaten':
                        # Koordinaten sollten Zahlen enthalten
                        if not any(char.isdigit() for char in value):
                            continue
                    
                    elif field_name == 'sanierungskosten':
                        # Kosten sollten Zahlen enthalten
                        if not any(char.isdigit() for char in value):
                            continue
                    
                    # Bestimme Quelle aus Citations
                    source = "Perplexity Web Search"
                    url = ""
                    if citations and isinstance(citations, list) and len(citations) > 0:
                        # Versuche die relevanteste Citation zu finden
                        first_citation = citations[0]
                        if isinstance(first_citation, dict):
                            source = safe_get(first_citation, 'title', source)
                            url = safe_get(first_citation, 'url', '')
                        elif isinstance(first_citation, str):
                            source = first_citation
                            url = ""
                    
                    extracted[field_name] = {
                        'value': value,
                        'source': source,
                        'url': url,
                        'year': datetime.now().year,
                        'confidence': 'high' if citations else 'medium'
                    }
                    break
        
        return extracted
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search_mine - für Kompatibilität mit Source Discovery"""
        return await self.search_mine(query)