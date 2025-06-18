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
from ..core.logger import get_logger, PerformanceLogger


class PerplexityAgent(BaseAgent):
    """Perplexity Agent für Web-basierte Recherche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].perplexity_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "pplx-70b-online"  # Online-Modell für aktuelle Daten
        self._rate_limiter = RateLimiter(rate=10, per=60.0)  # 10 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="perplexity")
        self.perf_logger = PerformanceLogger(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # Erstelle Session
            self._session = aiohttp.ClientSession()
            
            # Validiere Credentials
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Perplexity Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Perplexity API-Key konfiguriert")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Einfache Test-Anfrage
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit Perplexity durch"""
        results = []
        
        self.perf_logger.start_timer(f"perplexity_search_{query.mine_name}")
        
        try:
            # Get enhanced search queries
            search_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Limit to most relevant queries for Perplexity (to manage API costs)
            priority_queries = search_queries[:10]  # Top 10 queries
            
            # Execute searches with different query strategies
            for idx, search_query in enumerate(priority_queries):
                self.logger.info(f"Perplexity-Suche {idx+1}/{len(priority_queries)}: {search_query}")
                
                # Create prompt with search query and domain focus
                prompt = self._create_enhanced_prompt(query, search_query, mining_domains[:5])
                
                response = await self._make_api_call(prompt)
                if response:
                    parsed_results = self._parse_response(response, query, f"query_{idx+1}")
                    results.extend(parsed_results)
                    
                # Kurze Pause zwischen Anfragen
                await asyncio.sleep(1)
            
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
        
        prompt = f"""Execute the following search query and extract specific mining information:

Search Query: {search_query}

Focus on these priority sources: {domains_str}

For the {query.mine_name} mine in {query.region}, {query.country}, extract:
1. Current operator/owner company name
2. Exact GPS coordinates (latitude, longitude)
3. Current operational status (active/closed/suspended/care & maintenance)
4. Type of mine (open pit/underground/both)
5. Main commodities extracted (gold, silver, copper, etc.)
6. Annual production volumes with units and year
7. Number of employees/workforce size
8. Rehabilitation/closure costs in CAD or USD
9. Environmental bonds or financial assurances
10. Recent news, updates, or reports (2020-2025)

Provide specific facts with sources and URLs. Focus on official company reports, government databases, and reputable mining industry sources."""
        
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
                    "content": """You are a mining industry research specialist with expertise in:
- Global mining databases and registries
- Technical mining reports (NI 43-101, JORC)
- Environmental regulations and compliance
- Mining finance and economics
- Multiple languages relevant to mining regions

CRITICAL: 
- Search EXHAUSTIVELY across ALL available sources
- Include government, industry, NGO, news, and academic sources
- Look for PDFs, technical reports, and official documents
- Search in the local language(s) of the mining region
- Cross-reference multiple sources for accuracy
- Provide EXACT values with dates and specific sources"""
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
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)  # Extended timeout for deeper searches
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except Exception as e:
            self.logger.error(f"API Anfrage Fehler: {e}")
            return None
    
    def _parse_response(self, response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Perplexity-Antwort mit Fokus auf Faktenextraktion"""
        results = []
        
        try:
            if 'choices' in response and response['choices']:
                content = response['choices'][0]['message']['content']
                citations = response.get('citations', [])
                
                # Extrahiere strukturierte Daten aus dem Text
                extracted_data = self._extract_structured_data(content, citations)
                
                for field_name, value_data in extracted_data.items():
                    if value_data['value'] and value_data['value'] != 'nichts gefunden':
                        result = SearchResult(
                            field_name=field_name,
                            value=value_data['value'],
                            source=value_data.get('source', 'Perplexity Web Search'),
                            source_url=value_data.get('url', ''),
                            source_date=value_data.get('year', datetime.now().year),
                            confidence=value_data.get('confidence', 'medium'),
                            agent_name=self.name,
                            search_language='en',
                            found_at=datetime.now()
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {result.field_name} = {result.value}")
                        
        except Exception as e:
            self.logger.error(f"Response Parse Fehler: {e}")
            
        return results
    
    def _extract_structured_data(self, content: str, citations: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Extrahiert strukturierte Daten aus Perplexity-Antwort"""
        extracted = {}
        
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
                    
                    # Bestimme Quelle aus Citations
                    source = "Perplexity Web Search"
                    url = ""
                    if citations:
                        # Versuche die relevanteste Citation zu finden
                        source = citations[0].get('title', source)
                        url = citations[0].get('url', '')
                    
                    extracted[field_name] = {
                        'value': value,
                        'source': source,
                        'url': url,
                        'year': datetime.now().year,
                        'confidence': 'high' if citations else 'medium'
                    }
                    break
        
        return extracted
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Perplexity Agent beendet")