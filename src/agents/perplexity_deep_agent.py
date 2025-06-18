"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: Perplexity Deep Research Agent - Erweiterte Deep Research Funktionalität
"""

import aiohttp
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult
from ..core.logger import get_logger, PerformanceLogger


class PerplexityDeepAgent(BaseAgent):
    """
    Perplexity Deep Research Agent
    
    Nutzt Perplexity's Deep Research Mode für:
    - Dutzende automatische Suchen
    - Lesen von Hunderten von Quellen
    - Iterative Verfeinerung der Suche
    - Umfassende Berichtserstellung
    """
    
    def __init__(self, api_key: str, use_deep_research: bool = True):
        """Initialize Perplexity Deep Research Agent"""
        super().__init__(name="perplexity_deep_research")
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.use_deep_research = use_deep_research
        
        # Modelle für verschiedene Aufgaben
        self.models = {
            "deep_research": "pplx-deep-research",  # Hypothetisches Deep Research Modell
            "reasoning": "pplx-reasoning",  # Reasoning Modell
            "online": "pplx-70b-online",  # Standard Online Modell
            "sonar": "sonar-small-32k-online"  # Sonar für schnelle Suchen
        }
        
        self.logger = get_logger(__name__)
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Deep Research spezifische Einstellungen
        self.max_search_iterations = 5
        self.sources_per_iteration = 20
        self.min_confidence_threshold = 0.7
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """
        Führt Deep Research Suche durch
        
        Der Prozess:
        1. Erstellt Research Plan
        2. Führt iterative Suchen durch
        3. Verfeinert basierend auf Erkenntnissen
        4. Konsolidiert in umfassenden Bericht
        """
        all_results = []
        
        self.perf_logger.start_timer("perplexity_deep_research")
        
        try:
            if self.use_deep_research:
                # Deep Research Mode
                results = await self._deep_research_search(query)
                all_results.extend(results)
            else:
                # Standard Search Mode (schneller, weniger umfassend)
                results = await self._standard_search(query)
                all_results.extend(results)
            
            self.logger.info(
                f"Perplexity Deep Research completed with {len(all_results)} results"
            )
            self.perf_logger.end_timer(
                "perplexity_deep_research",
                results_found=len(all_results)
            )
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Perplexity Deep Research error: {str(e)}")
            self.perf_logger.end_timer("perplexity_deep_research", error=str(e))
            return all_results
    
    async def _deep_research_search(self, query: MineQuery) -> List[SearchResult]:
        """Führt Deep Research Prozess durch"""
        
        # Phase 1: Initial Research Plan
        research_context = {
            "mine_name": query.mine_name,
            "location": f"{query.region}, {query.country}",
            "required_fields": query.required_fields,
            "discovered_info": {},
            "sources_checked": set(),
            "search_iterations": 0
        }
        
        all_results = []
        
        # Iterative Deep Research
        for iteration in range(self.max_search_iterations):
            self.logger.info(f"Deep Research Iteration {iteration + 1}/{self.max_search_iterations}")
            
            # Status Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(
                    f"Perplexity Deep Research: Iteration {iteration + 1}/{self.max_search_iterations}"
                )
            
            # Erstelle adaptive Suchanfrage basierend auf bisherigen Erkenntnissen
            search_prompt = self._create_adaptive_search_prompt(query, research_context)
            
            # Führe Suche durch
            iteration_results = await self._execute_deep_search(
                search_prompt,
                research_context
            )
            
            # Parse und sammle Ergebnisse
            parsed_results = self._parse_deep_research_results(
                iteration_results,
                query,
                f"iteration_{iteration + 1}"
            )
            
            # Update Research Context
            for result in parsed_results:
                research_context["discovered_info"][result.field_name] = result.value
            
            all_results.extend(parsed_results)
            
            # Prüfe ob genug Informationen gefunden wurden
            if self._is_research_complete(research_context, query):
                self.logger.info("Research objectives met, ending early")
                break
            
            # Kurze Pause zwischen Iterationen
            await asyncio.sleep(2)
        
        # Final Synthesis
        if all_results:
            synthesis_results = await self._synthesize_findings(
                query, research_context, all_results
            )
            all_results.extend(synthesis_results)
        
        return all_results
    
    def _create_adaptive_search_prompt(
        self,
        query: MineQuery,
        context: Dict[str, Any]
    ) -> str:
        """Erstellt adaptive Suchanfrage basierend auf bisherigen Erkenntnissen"""
        
        # Was wir bereits wissen
        known_info = "\n".join([
            f"- {field}: {value}"
            for field, value in context["discovered_info"].items()
        ])
        
        # Was noch fehlt
        missing_fields = [
            field for field in query.required_fields
            if field not in context["discovered_info"]
        ]
        
        # Erstelle fokussierte Suchanfrage
        if context["search_iterations"] == 0:
            # Erste Iteration - breite Suche
            prompt = f"""Conduct comprehensive research on {query.mine_name} mine in {query.region}, {query.country}.

Focus on finding:
1. Official government sources and mining registries
2. Current ownership and operational status
3. Technical reports and production data
4. Environmental assessments and closure costs
5. Recent news and updates (2020-2025)

Search multiple authoritative sources and provide specific data with references."""
        
        else:
            # Folge-Iterationen - gezielte Suche nach fehlenden Informationen
            prompt = f"""Continue deep research on {query.mine_name} mine in {query.region}, {query.country}.

Already discovered:
{known_info if known_info else "No confirmed data yet"}

Still needed:
{chr(10).join('- ' + field for field in missing_fields[:5])}

Search strategies:
1. Look for alternative sources not yet checked
2. Search in {', '.join(query.languages)} languages
3. Check specialized mining databases
4. Look for PDF reports and technical documents
5. Verify through cross-references

Provide new information not already found, with specific sources."""
        
        return prompt
    
    async def _execute_deep_search(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Führt eine Deep Search Anfrage aus"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Nutze Deep Research Endpoint wenn verfügbar
        endpoint = "/chat/completions"
        if self.use_deep_research:
            # Hypothetischer Deep Research Endpoint
            endpoint = "/deep-research" if "deep-research" in self.base_url else endpoint
        
        payload = {
            "model": self.models.get("deep_research", self.models["online"]),
            "messages": [
                {
                    "role": "system",
                    "content": """You are Perplexity Deep Research, designed to:
- Perform dozens of searches automatically
- Read and analyze hundreds of sources
- Reason through findings iteratively
- Provide comprehensive, fact-checked information
- Always cite specific sources with URLs when available"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "web_search": True,
            "return_citations": True,
            "search_domain_filter": ["gov", "org", "edu"],  # Prioritize official sources
            "search_recency_filter": "year",  # Focus on recent information
            "deep_research_mode": self.use_deep_research  # Enable deep research if available
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180)  # Longer timeout for deep research
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track sources
                        if "citations" in data:
                            for citation in data["citations"]:
                                context["sources_checked"].add(citation.get("url", ""))
                        
                        context["search_iterations"] += 1
                        return data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API error: {error_text}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"Deep search execution error: {str(e)}")
            return {}
    
    async def _standard_search(self, query: MineQuery) -> List[SearchResult]:
        """Standard Suche (nicht Deep Research)"""
        # Verwende existierende Perplexity Search Logik
        prompts = {
            "general": f"Search for comprehensive information about {query.mine_name} mine in {query.region}, {query.country}",
            "technical": f"Find technical and operational data for {query.mine_name} mine",
            "environmental": f"Search for environmental and closure costs for {query.mine_name} mine"
        }
        
        all_results = []
        
        for search_type, prompt in prompts.items():
            response = await self._execute_deep_search(
                prompt,
                {"sources_checked": set(), "search_iterations": 0, "discovered_info": {}}
            )
            
            if response:
                results = self._parse_deep_research_results(
                    response, query, search_type
                )
                all_results.extend(results)
            
            await asyncio.sleep(1)
        
        return all_results
    
    def _parse_deep_research_results(
        self,
        response: Dict[str, Any],
        query: MineQuery,
        source_tag: str
    ) -> List[SearchResult]:
        """Parst Deep Research Ergebnisse"""
        results = []
        
        if not response or 'choices' not in response:
            return results
        
        content = response['choices'][0]['message']['content']
        citations = response.get('citations', [])
        
        # Erweiterte Patterns für Deep Research
        patterns = {
            'betreiber': [
                r'(?:owner|operator|operated by|owned by)[:\s]+([A-Za-z0-9\s\.\&\-,]+?)(?:\s*[,\.]|\s*\n)',
                r'([A-Z][A-Za-z0-9\s\.\&\-]+?)\s+(?:operates|owns|is the operator)',
                r'current operator[:\s]+([^\n,]+)'
            ],
            'koordinaten': [
                r'coordinates[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'GPS[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'(\d+°\d+\'[\d\.]*\"[NS])[,\s]+(\d+°\d+\'[\d\.]*\"[EW])'
            ],
            'aktivitaetsstatus': [
                r'(?:operational\s+)?status[:\s]+(\w+)',
                r'mine is\s+currently\s+(\w+)',
                r'(?:production\s+)?status[:\s]+([^\n,]+)',
                r'currently\s+in\s+(\w+)\s+(?:status|phase)'
            ],
            'sanierungskosten': [
                r'(?:rehabilitation|closure|remediation)\s+(?:cost|bond)[s]?[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'financial assurance[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'environmental bond[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'closure liability[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)'
            ],
            'jahresproduktion': [
                r'annual production[:\s]+([^\n]+)',
                r'produces?\s+([\d,\.]+\s*(?:tonnes?|ounces?|oz|kg|tons?)\s*(?:per year|annually)?)',
                r'production capacity[:\s]+([^\n]+)',
                r'([\d,\.]+\s*(?:tonnes?|ounces?|oz)\s*(?:of\s+\w+\s+)?(?:per year|annually))'
            ],
            'rohstofftyp': [
                r'commodit(?:y|ies)[:\s]+([^\n,]+(?:,\s*[^\n,]+)*)',
                r'produces?\s+(?:primarily\s+)?([^\n,]+(?:,\s*[^\n,]+)*)',
                r'main minerals?[:\s]+([^\n,]+(?:,\s*[^\n,]+)*)',
                r'extract(?:s|ing)?\s+([^\n,]+(?:,\s*[^\n,]+)*)'
            ]
        }
        
        # Durchsuche Content mit erweiterten Patterns
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    value = match.group(1)
                    if len(match.groups()) > 1:  # Für Koordinaten
                        value = f"{match.group(1)}, {match.group(2)}"
                    
                    # Bereinige Wert
                    value = value.strip().rstrip('.,')
                    
                    # Finde relevante Citation
                    source = "Perplexity Deep Research"
                    source_url = ""
                    confidence = 0.8
                    
                    if citations:
                        # Versuche beste Citation zu finden
                        for citation in citations:
                            if field_name in str(citation.get('snippet', '')).lower():
                                source = citation.get('title', source)
                                source_url = citation.get('url', '')
                                confidence = 0.95
                                break
                    
                    # Extrahiere Datum wenn möglich
                    date_match = re.search(r'(20\d{2})', content[max(0, match.start()-100):match.end()+100])
                    source_date = date_match.group(1) if date_match else str(datetime.now().year)
                    
                    result = SearchResult(
                        field_name=field_name,
                        value=value,
                        source=source,
                        confidence_score=confidence,
                        agent_name=self.name,
                        found_at=datetime.now(),
                        mine_id=None,
                        metadata={
                            'url': source_url,
                            'search_mode': 'deep_research' if self.use_deep_research else 'standard',
                            'iteration': source_tag,
                            'source_date': source_date
                        }
                    )
                    
                    # Vermeide Duplikate
                    if not any(r.field_name == result.field_name and 
                              r.value == result.value for r in results):
                        results.append(result)
                        self.logger.info(
                            f"Deep Research found: {field_name} = {value} "
                            f"(confidence: {confidence:.2f})"
                        )
        
        return results
    
    def _is_research_complete(
        self,
        context: Dict[str, Any],
        query: MineQuery
    ) -> bool:
        """Prüft ob Research-Ziele erreicht wurden"""
        
        # Prüfe ob kritische Felder gefunden wurden
        critical_fields = ['betreiber', 'koordinaten', 'aktivitaetsstatus']
        found_critical = sum(
            1 for field in critical_fields
            if field in context["discovered_info"]
        )
        
        # Prüfe Gesamtabdeckung
        total_found = len(context["discovered_info"])
        total_required = len(query.required_fields)
        coverage = total_found / total_required if total_required > 0 else 0
        
        # Research ist komplett wenn:
        # - Alle kritischen Felder gefunden wurden, oder
        # - 80% der Felder gefunden wurden, oder
        # - Maximale Iterationen erreicht wurden
        return (
            found_critical == len(critical_fields) or
            coverage >= 0.8 or
            context["search_iterations"] >= self.max_search_iterations
        )
    
    async def _synthesize_findings(
        self,
        query: MineQuery,
        context: Dict[str, Any],
        all_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Synthetisiert alle Erkenntnisse in finalen Bericht"""
        
        # Erstelle Zusammenfassung aller Findings
        findings_summary = "\n".join([
            f"{field}: {value}"
            for field, value in context["discovered_info"].items()
        ])
        
        sources_summary = f"Checked {len(context['sources_checked'])} unique sources"
        
        synthesis_prompt = f"""Based on deep research of {query.mine_name} mine in {query.region}, {query.country}:

Findings:
{findings_summary}

{sources_summary}

Please:
1. Verify the accuracy of key data points
2. Identify any gaps or inconsistencies
3. Provide confidence assessment for each finding
4. Suggest additional sources if critical data is missing

Format verification results clearly with confidence levels."""
        
        response = await self._execute_deep_search(
            synthesis_prompt,
            context
        )
        
        if response:
            # Parse synthesis results
            synthesis_results = self._parse_deep_research_results(
                response, query, "synthesis"
            )
            
            # Mark as synthesis results
            for result in synthesis_results:
                result.metadata["synthesis"] = True
                result.metadata["total_sources"] = len(context["sources_checked"])
            
            return synthesis_results
        
        return []
    
    async def initialize(self) -> bool:
        """Initialize the agent"""
        try:
            # Test API connection
            test_payload = {
                "model": self.models["online"],
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            return False
    
    async def validate(self) -> bool:
        """Validate credentials"""
        return await self.initialize()
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Main search method for base agent compatibility"""
        return await self.search(query)