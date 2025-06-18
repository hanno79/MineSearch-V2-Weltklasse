"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: GPT-4 Agent Implementation via OpenRouter
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class GPTAgent(BaseAgent):
    """GPT-4 Agent über OpenRouter API"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].openrouter_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-4-turbo-preview"
        self._rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="gpt4")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
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
                
            self.logger.info("GPT-4 Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein OpenRouter API-Key konfiguriert")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://minesearch.app",
                "X-Title": "MineSearch"
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
        """Führt erweiterte Mining-Suche mit GPT-4 durch"""
        results = []
        
        self.perf_logger.start_timer(f"gpt_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Erstelle mehrere spezialisierte Prompts
            prompts = self._create_mining_prompts(query, mining_queries, mining_domains)
            
            total_prompts = len(prompts)
            completed = 0
            
            # Führe erweiterte Suchen durch
            for prompt_type, prompt in prompts.items():
                self.logger.info(f"GPT-4 Mining-Suche ({completed + 1}/{total_prompts}): {prompt_type} für {query.mine_name}")
                
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"GPT-4: {prompt_type} Suche ({completed + 1}/{total_prompts})")
                
                response = await self._make_api_call(prompt)
                if response:
                    parsed_results = self._parse_response(response, query, prompt_type)
                    results.extend(parsed_results)
                
                completed += 1
                await asyncio.sleep(2)  # Respektiere Rate Limits
            
            self.perf_logger.end_timer(
                f"gpt_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_searches'] += 1
            self.stats['successful_searches'] += 1 if results else 0
            self.stats['fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_searches'] += 1
            
        return results
    
    def _create_mining_prompts(self, query: MineQuery, mining_queries: List[str], mining_domains: List[str]) -> Dict[str, str]:
        """Erstellt erweiterte Mining-spezifische Prompts"""
        prompts = {}
        
        # Umfassender Mining-Recherche-Prompt
        prompts['comprehensive'] = f"""You are an expert mining industry analyst with deep knowledge of mining operations, regulations, and databases.

Conduct a COMPREHENSIVE search for "{query.mine_name}" mine in {query.region}, {query.country}.

Use these search strategies:
{chr(10).join(['- ' + q for q in mining_queries[:10]])}

Prioritize these mining-specific sources:
{', '.join(mining_domains[:15])}

Find ALL of the following information with EXACT values and sources:

1. OWNERSHIP & OPERATIONS:
   - Current operator/owner company name
   - Parent company and ownership structure
   - Joint venture partners and percentages
   - Historical ownership changes

2. LOCATION & COORDINATES:
   - Precise GPS coordinates (decimal degrees)
   - Mining claims/concession numbers
   - Distance from nearest city/town
   - Access infrastructure

3. ENVIRONMENTAL COSTS:
   - Environmental bond/financial assurance amount (with currency and date)
   - Closure cost estimates
   - Remediation/restoration costs
   - Asset retirement obligations (ARO)
   - Water treatment costs

4. PRODUCTION DATA:
   - Annual production (tonnes/ounces with year)
   - Production capacity
   - Historical production data
   - Grade/quality of ore
   - Recovery rates

5. TECHNICAL DETAILS:
   - Mine type (open pit/underground/heap leach)
   - Commodities produced (primary and by-products)
   - Processing methods
   - Mine life remaining
   - Reserve/resource estimates

6. OPERATIONAL STATUS:
   - Current status (operating/suspended/closed/care & maintenance)
   - Status change dates and reasons
   - Number of employees
   - Contractors on site

7. REGULATORY & COMPLIANCE:
   - Environmental permits status
   - Mining licenses/permits
   - Recent inspections or violations
   - Compliance orders

Return ONLY factual data in this JSON format:
{{
  "results": [
    {{
      "field_name": "betreiber",
      "value": "Company Name Inc.",
      "source": "SEDAR filing Q3 2024",
      "source_url": "https://...",
      "source_date": 2024,
      "confidence": "high"
    }}
  ]
}}

IMPORTANT: Use ONLY verified information from official sources. Include specific dates and exact values."""
        
        # Technischer Daten-Prompt
        prompts['technical'] = f"""You are a mining technical specialist reviewing NI 43-101 and JORC reports.

Search for TECHNICAL DATA for "{query.mine_name}" mine in {query.region}, {query.country}.

Focus on technical reports and find:

1. RESOURCE ESTIMATES:
   - Measured & Indicated resources (tonnes, grade)
   - Inferred resources (tonnes, grade)
   - Proven & Probable reserves (tonnes, grade)
   - Cut-off grades
   - Resource categories by commodity

2. MINE ENGINEERING:
   - Mining method and design
   - Production rate (tonnes/day)
   - Mine dimensions (length, width, depth)
   - Strip ratio or development meters
   - Equipment fleet

3. PROCESSING:
   - Mill/plant capacity (tonnes/day)
   - Recovery rates by commodity (%)
   - Processing method (flotation, leaching, etc.)
   - Concentrate grades
   - Tailings management

4. INFRASTRUCTURE:
   - Power supply (MW) and source
   - Water supply and usage (m3/day)
   - Transportation (road/rail distances)
   - Port facilities
   - Camp capacity

Search in: NI 43-101 reports, JORC reports, feasibility studies, technical presentations.

Return data in JSON format with exact technical specifications and report references."""
        
        # Umwelt- und Finanz-Prompt  
        prompts['environmental_financial'] = f"""You are a mining finance and environmental specialist.

Search for FINANCIAL and ENVIRONMENTAL data for "{query.mine_name}" mine in {query.region}, {query.country}.

Find:

1. ENVIRONMENTAL LIABILITIES:
   - Environmental bonds/financial assurance (amount, currency, date)
   - Closure cost estimates (detailed breakdown)
   - Remediation cost estimates
   - Asset retirement obligations (ARO) on balance sheet
   - Historical environmental incidents and costs
   - Water treatment obligations

2. FINANCIAL DATA:
   - Mine acquisition cost/value
   - Annual revenue from mine
   - Operating costs ($/tonne or $/oz)
   - Capital expenditures
   - NPV and IRR from latest studies
   - Royalty obligations

3. OWNERSHIP STRUCTURE:
   - Current owner with percentage
   - Joint venture partners
   - Streaming/royalty agreements
   - Option agreements
   - Recent transactions

4. REGULATORY COMPLIANCE:
   - Environmental fines/penalties
   - Compliance orders
   - Permit violations
   - Community agreements

Search in: Annual reports, 10-K filings, SEDAR, environmental assessments, government databases.

Provide EXACT amounts with currencies and dates in JSON format."""
        
        # Operationeller Status-Prompt
        prompts['operational'] = f"""You are a mining operations specialist.

Search for CURRENT OPERATIONAL STATUS of "{query.mine_name}" mine in {query.region}, {query.country}.

Determine:

1. CURRENT STATUS:
   - Operational status (operating/suspended/closed/care & maintenance/exploration)
   - Last production date if not operating
   - Reasons for current status
   - Expected restart date (if applicable)

2. WORKFORCE:
   - Number of employees
   - Number of contractors
   - Recent layoffs or hiring
   - Union agreements

3. RECENT DEVELOPMENTS:
   - Production updates (last 12 months)
   - Operational challenges
   - Expansion projects
   - Equipment upgrades
   - Safety incidents

4. PRODUCTION METRICS:
   - Current production rate
   - Capacity utilization (%)
   - Recent production volumes
   - Commodity prices impact

Search in: Company press releases, quarterly reports, mining news sites, government reports.

Provide current operational data with dates in JSON format."""
        
        # Quebec-spezifischer Prompt (wenn relevant)
        if query.country == 'Canada' and query.region.lower() in ['quebec', 'québec']:
            prompts['quebec_specific'] = f"""Vous êtes un spécialiste minier du Québec.

Recherchez dans les BASES DE DONNÉES QUÉBÉCOISES pour la mine "{query.mine_name}" à {query.region}, {query.country}.

Consultez en priorité:
- GESTIM (Gestion des titres miniers)
- SIGEOM (Système d'information géominière)  
- MERN (Ministère de l'Énergie et Ressources naturelles)
- Registre public des mines
- Rapports BAPE (Bureau d'audiences publiques)

Trouvez:

1. TITRES MINIERS:
   - Numéros de claims (CM, CDC, CLD)
   - Titulaire des claims
   - Dates d'échéance
   - Superficie (hectares)

2. DONNÉES TECHNIQUES:
   - Substances visées
   - Type de gîte
   - Travaux statutaires déclarés
   - Rapports géologiques (GM)

3. OBLIGATIONS ENVIRONNEMENTALES:
   - Plan de restauration approuvé
   - Garantie financière déposée (CAD)
   - État du site minier
   - Certificats d'autorisation

4. LOCALISATION PRÉCISE:
   - Coordonnées MTM ou lat/long
   - Canton, rang, lots
   - MRC et municipalité
   - Feuillet SNRC

Fournissez les données OFFICIELLES du gouvernement du Québec en format JSON."""
        
        return prompts
    
    async def _make_api_call(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Macht API-Aufruf zu OpenRouter"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://minesearch.app",
            "X-Title": "MineSearch"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert mining industry analyst with specialized knowledge in:
- Mining engineering and operations
- Environmental remediation and closure planning  
- Mining finance and M&A
- Regulatory compliance and permits
- Resource estimation and technical reporting (NI 43-101, JORC)
- Government mining databases and registries
- Mining company reports and filings

You have deep expertise in searching:
- SEDAR/EDGAR filings
- Government mining registries (GESTIM, MNDM, etc.)
- Technical reports and feasibility studies
- Environmental assessments and closure plans
- Mining news and industry publications

Always provide ACCURATE, SPECIFIC information with EXACT sources and dates.
Focus on official, verifiable data from authoritative sources."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Sehr niedrige Temperatur für präzise Mining-Daten
            "max_tokens": 4000,  # Mehr Tokens für umfassende Mining-Informationen
            "response_format": {"type": "json_object"}
        }
        
        try:
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
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
    
    def _parse_response(self, response: Dict[str, Any], query: MineQuery, language: str) -> List[SearchResult]:
        """Parst API-Antwort zu SearchResult Objekten"""
        results = []
        
        try:
            # Extrahiere den generierten Text
            if 'choices' in response and response['choices']:
                content = response['choices'][0]['message']['content']
                
                # Parse JSON
                try:
                    data = json.loads(content)
                    if 'results' in data:
                        for item in data['results']:
                            if item.get('value') and item['value'] != 'nichts gefunden':
                                result = SearchResult(
                                    field_name=item.get('field_name', ''),
                                    value=item.get('value'),
                                    source=item.get('source', 'GPT-4'),
                                    source_url=item.get('source_url', ''),
                                    source_date=item.get('source_date', datetime.now().year),
                                    confidence=item.get('confidence', 'medium'),
                                    agent_name=self.name,
                                    search_language=language,
                                    found_at=datetime.now()
                                )
                                results.append(result)
                                self.logger.info(f"Gefunden: {result.field_name} = {result.value}")
                                
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON Parse Fehler: {e}")
                    # Versuche trotzdem Informationen zu extrahieren
                    # (Fallback parsing könnte hier implementiert werden)
                    
        except Exception as e:
            self.logger.error(f"Response Parse Fehler: {e}")
            
        return results
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("GPT-4 Agent beendet")