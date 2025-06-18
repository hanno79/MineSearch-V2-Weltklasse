"""Claude Agent Implementation via OpenRouter"""
import aiohttp
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class ClaudeAgent(BaseAgent):
    """Claude-3 Agent über OpenRouter API"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].openrouter_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3-opus-20240229"
        self._rate_limiter = RateLimiter(rate=30, per=60.0)  # 30 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="claude")
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
                
            self.logger.info("Claude Agent erfolgreich initialisiert")
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
        """Führt erweiterte Mining-Suche mit Claude durch"""
        results = []
        
        self.perf_logger.start_timer(f"claude_search_{query.mine_name}")
        
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
                self.logger.info(f"Claude Mining-Suche ({completed + 1}/{total_prompts}): {prompt_type} für {query.mine_name}")
                
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Claude: {prompt_type} Suche ({completed + 1}/{total_prompts})")
                
                response = await self._make_api_call(prompt)
                if response:
                    parsed_results = self._parse_response(response, query, prompt_type)
                    results.extend(parsed_results)
                
                completed += 1
                await asyncio.sleep(2)  # Respektiere Rate Limits
            
            self.perf_logger.end_timer(
                f"claude_search_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Claude-Suche: {e}")
            return results
    
    def _create_mining_prompts(self, query: MineQuery, mining_queries: List[str], mining_domains: List[str]) -> Dict[str, str]:
        """Erstellt erweiterte Mining-spezifische Prompts"""
        prompts = {}
        
        # Umfassender Mining-Recherche-Prompt - VERBESSERT
        prompts['comprehensive'] = f"""
You are an expert mining researcher with UNLIMITED access to ALL mining databases, reports, and sources worldwide.

CRITICAL RESEARCH INSTRUCTIONS:
1. Search EXHAUSTIVELY - leave no source unchecked
2. Use ALL name variations and spellings
3. Search in ALL relevant languages for {query.country}
4. Look for PDFs, Excel files, presentations, not just web pages
5. Check historical records and archived documents
6. Cross-reference multiple sources for accuracy

TARGET: Mine "{query.mine_name}" in {query.region}, {query.country}

EXECUTE these search strategies:
{chr(10).join(['- ' + q for q in mining_queries[:20]])}

SEARCH these sources IN ORDER OF PRIORITY:
1. Government (Federal/State/Local):
   - Mining ministries and departments
   - Geological surveys
   - Environmental agencies
   - Mining registries and cadastres
   - Public archives

2. Company Sources:
   - Operator/owner websites
   - Investor presentations
   - Annual reports
   - Sustainability reports
   - Securities filings

3. Third-Party Sources:
   - NGOs and watchdog groups
   - Industry associations
   - News media (local and trade)
   - Academic research
   - Community groups

4. Technical Databases:
{', '.join(mining_domains[:20])}

Find ALL of the following information with EXACT values and sources:

1. OPERATOR/OWNER:
   - Current operating company name
   - Parent company (if applicable)
   - Ownership percentages
   - Joint venture partners

2. EXACT LOCATION:
   - Precise GPS coordinates (latitude, longitude)
   - Distance from nearest town/city
   - Access routes

3. ENVIRONMENTAL COSTS:
   - Environmental bond amount
   - Restoration/remediation costs
   - Closure cost estimates
   - Financial assurance amounts
   - Currency and year of estimates

4. OPERATIONAL STATUS:
   - Current status (operating/suspended/closed/care & maintenance)
   - Status change dates
   - Reasons for status changes

5. PRODUCTION DATA:
   - Annual production volumes
   - Production capacity
   - Historical production
   - Grade/quality of ore

6. MINE CHARACTERISTICS:
   - Mine type (open pit/underground/heap leach)
   - Commodities produced
   - Processing methods
   - Mine life remaining

7. TECHNICAL REPORTS:
   - NI 43-101 report dates
   - Resource/reserve estimates
   - Feasibility study results

For each piece of information:
- Provide the EXACT value (with units)
- Cite the SPECIFIC source (report name, website, database)
- Include the DATE of the information
- Rate confidence (0.0-1.0)

Format as JSON array with objects containing:
field_name, value, source, source_url, source_date, confidence_score

Be thorough and specific. Mining data requires precision."""
        
        # Technischer Daten-Prompt
        prompts['technical'] = f"""
Search for TECHNICAL mining data for "{query.mine_name}" mine in {query.region}, {query.country}.

Focus on NI 43-101 reports, JORC reports, and technical studies to find:

1. RESOURCE ESTIMATES:
   - Measured resources (tonnes, grade)
   - Indicated resources (tonnes, grade)
   - Inferred resources (tonnes, grade)
   - Proven reserves (tonnes, grade)
   - Probable reserves (tonnes, grade)

2. MINE SPECIFICATIONS:
   - Mine type and mining method
   - Processing capacity (tonnes/day)
   - Recovery rates (%)
   - Strip ratio (if open pit)
   - Mine depth (if underground)

3. INFRASTRUCTURE:
   - Power supply (MW)
   - Water sources and usage
   - Transportation (road/rail/port)
   - Processing facilities

4. MINE LIFE:
   - Remaining mine life (years)
   - Expansion potential
   - Exploration targets

Search in technical reports, feasibility studies, and mining databases.

Format as JSON array with precise technical data, sources, and dates."""
        
        # Umwelt- und Sanierungskosten-Prompt
        prompts['environmental'] = f"""
Search for ENVIRONMENTAL and CLOSURE COST data for "{query.mine_name}" mine in {query.region}, {query.country}.

Find specific financial information:

1. CLOSURE BONDS:
   - Environmental bond amount
   - Financial assurance value
   - Security deposits
   - Currency and date

2. REMEDIATION COSTS:
   - Total estimated closure costs
   - Restoration cost estimates
   - Tailings management costs
   - Water treatment costs
   - Post-closure monitoring costs

3. LIABILITIES:
   - Asset retirement obligations (ARO)
   - Environmental liabilities on balance sheet
   - Government-mandated cleanup costs
   - Historical contamination costs

4. REGULATORY COMPLIANCE:
   - Environmental permits status
   - Compliance orders
   - Fines or penalties
   - Remediation deadlines

Search in:
- Company annual reports (environmental liabilities section)
- Government environmental databases
- Securities filings (10-K, annual information forms)
- Environmental assessment reports
- Mining regulatory body reports

Provide EXACT amounts with currency, dates, and specific sources.

Format as JSON array."""
        
        # Eigentümer- und Finanz-Prompt
        prompts['financial'] = f"""
Search for OWNERSHIP and FINANCIAL data for "{query.mine_name}" mine in {query.region}, {query.country}.

Find:

1. OWNERSHIP STRUCTURE:
   - Current owner/operator company
   - Parent company
   - Ownership percentages
   - Joint venture partners
   - Recent ownership changes

2. FINANCIAL DATA:
   - Asset value
   - Annual revenue from mine
   - Operating costs
   - Capital expenditures
   - Royalty agreements

3. CORPORATE INFORMATION:
   - Stock exchange listings
   - Market capitalization
   - Recent M&A activity
   - Corporate headquarters

4. HISTORICAL OWNERSHIP:
   - Previous owners
   - Acquisition dates and prices
   - Ownership transfers

Search in:
- SEDAR/EDGAR filings
- Company websites and investor relations
- M&A databases
- Mining news and press releases
- Stock exchange announcements

Provide current data with dates and sources.

Format as JSON array."""
        
        # Französisch für Quebec (wenn relevant)
        if query.country == 'Canada' and query.region.lower() in ['quebec', 'québec']:
            prompts['quebec_french'] = f"""
Recherchez des informations DÉTAILLÉES sur la mine "{query.mine_name}" à {query.region}, {query.country}.

Consultez en priorité:
- GESTIM (système de gestion des titres miniers du Québec)
- MERN (Ministère de l'Énergie et des Ressources naturelles)
- SIGGEOM (système d'information géominière)
- Registre public des mines
- Rapports techniques NI 43-101

Trouvez:

1. TITULAIRE ET OPÉRATEUR:
   - Nom du titulaire des claims
   - Compagnie exploitante
   - Numéros de claims miniers

2. LOCALISATION PRÉCISE:
   - Coordonnées GPS (latitude, longitude)
   - Canton, rang, lots
   - MRC et région administrative

3. COÛTS ENVIRONNEMENTAUX:
   - Garantie financière pour restauration
   - Coûts estimés de fermeture
   - Plan de restauration approuvé
   - Montants en CAD avec année

4. DONNÉES TECHNIQUES:
   - Type de gîte (or, cuivre, zinc, etc.)
   - Méthode d'exploitation
   - Production annuelle
   - Réserves et ressources

5. STATUT:
   - État actuel (exploitation, fermée, suspendue)
   - Dates importantes
   - Permis et autorisations

Fournir les données EXACTES avec sources OFFICIELLES québécoises.

Format JSON avec: field_name, value, source, source_url, source_date, confidence_score"""
        
        return prompts
    
    async def _make_api_call(self, prompt: str) -> str:
        """Macht API-Aufruf zu OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mine-search",
            "X-Title": "Mine Search System"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert mining research specialist with deep expertise in:
- Mining engineering and operations
- Environmental remediation and closure planning
- Mining finance and M&A
- Regulatory compliance and permits
- Geological surveys and resource estimation
- Mining databases (SEDAR, EDGAR, government registries)
- Technical reports (NI 43-101, JORC)

CRITICAL INSTRUCTIONS:
1. Search BROADLY across ALL available sources - government, industry, NGO, news, academic
2. Look for information in MULTIPLE LANGUAGES based on the country
3. Search for DOCUMENTS (PDFs, reports, spreadsheets) not just web pages
4. Include data from:
   - Mine operator websites and investor relations
   - Regional government mining departments
   - Environmental NGOs and watchdog organizations
   - Local and industry news sources
   - Academic papers and theses
   - Historical archives and databases
5. For each data point, provide the EXACT source, date, and confidence level
6. If data conflicts between sources, report ALL versions with their sources
7. Search for alternative names, spellings, and historical names of the mine

Always provide ACCURATE, SPECIFIC information with EXACT sources.
Respond with valid JSON arrays containing factual mining data."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Niedrigere Temperatur für präzisere Fakten
            "max_tokens": 4000  # Mehr Tokens für umfassende Mining-Daten
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
                    return data['choices'][0]['message']['content']
                else:
                    self.logger.error(f"API-Fehler: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API-Timeout")
            return None
        except Exception as e:
            self.logger.error(f"API-Aufruf fehlgeschlagen: {e}")
            return None
    
    def _parse_response(self, response: str, query: MineQuery, language: str) -> List[SearchResult]:
        """Parst Claude-Antwort zu SearchResults"""
        results = []
        
        try:
            # Extrahiere JSON aus Antwort
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                for item in data:
                    # Mappe Feldnamen
                    field_mapping = {
                        'operator': 'betreiber',
                        'company': 'betreiber',
                        'coordinates': 'koordinaten',
                        'latitude': 'latitude',
                        'longitude': 'longitude',
                        'status': 'aktivitaetsstatus',
                        'restoration_costs': 'sanierungskosten',
                        'environmental_costs': 'sanierungskosten',
                        'closure_costs': 'sanierungskosten',
                        'remediation_costs': 'sanierungskosten',
                        'environmental_bond': 'sanierungskosten',
                        'financial_assurance': 'sanierungskosten',
                        'cost_year': 'kostenerfassungsjahr',
                        'resource_type': 'rohstofftyp',
                        'mine_type': 'minentyp',
                        'production_start': 'produktionsbeginn',
                        'annual_production': 'jahresproduktion',
                        'mine_area': 'minenflaeche'
                    }
                    
                    field_name = field_mapping.get(
                        item.get('field_name', '').lower(),
                        item.get('field_name', '')
                    )
                    
                    if field_name and item.get('value'):
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=item['value'],
                            source=item.get('source', 'Claude Research'),
                            source_url=None,
                            source_date=item.get('source_year'),
                            confidence_score=float(item.get('confidence_score', 0.8)),
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'language': language}
                        )
                        results.append(result)
                        
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON-Parsing fehlgeschlagen: {e}")
        except Exception as e:
            self.logger.error(f"Response-Parsing fehlgeschlagen: {e}")
            
        return results