"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für Perplexity Deep Research Agent
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult
from .api_client import PerplexityAPIClient
from .research_planner import ResearchPlanner
from .search_executor import SearchExecutor
from src.core.logger import get_logger, PerformanceLogger

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
        # BaseAgent benötigt name und config
        config = {
            'api_config': type('obj', (object,), {'perplexity_key': api_key})(),
            'scraping_config': type('obj', (object,), {'user_agent': 'MineSearch/1.0'})(),
            'max_concurrent_requests': 5
        }
        super().__init__(name="perplexity_deep_research", config=config)
        self.api_key = api_key
        self.use_deep_research = use_deep_research
        
        # Initialisiere Komponenten
        self._session = None
        self.api_client = None
        self.research_planner = ResearchPlanner()
        self.search_executor = SearchExecutor()
        
        self.logger = get_logger(__name__)
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Deep Research spezifische Einstellungen
        self.max_search_iterations = 5
        self.sources_per_iteration = 20
        self.min_confidence_threshold = 0.7
    
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            self.api_client = PerplexityAPIClient(self.api_key, self._session)
            return await self.validate_credentials()
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Perplexity API-Key konfiguriert")
            return False
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """
        Führt Deep Research Suche durch
        
        Der Prozess:
        1. Erstellt Research Plan
        2. Führt iterative Suchen durch
        3. Verfeinert basierend auf Erkenntnissen
        4. Konsolidiert in umfassenden Bericht
        """
        all_results = []
        
        self.perf_logger.start_timer(f"perplexity_deep_research_{query.mine_name}")
        
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
                f"perplexity_deep_research_{query.mine_name}",
                results_found=len(all_results)
            )
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Perplexity Deep Research error: {str(e)}")
            self.perf_logger.end_timer(f"perplexity_deep_research_{query.mine_name}", error=str(e))
            return all_results
    
    async def _deep_research_search(self, query: MineQuery) -> List[SearchResult]:
        """Führt Deep Research Prozess durch"""
        
        # Phase 1: Create Research Plan
        research_plan = self.research_planner.create_research_plan(query)
        
        # Initialize Research Context
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
            
            # Erstelle adaptive Suchanfrage
            search_prompt = self.search_executor.create_adaptive_prompt(query, research_context)
            
            # Führe Suche durch
            iteration_results = await self._execute_deep_search(
                search_prompt,
                research_context
            )
            
            # Parse und sammle Ergebnisse
            parsed_results = self.search_executor.parse_search_results(
                iteration_results,
                query,
                f"iteration_{iteration + 1}"
            )
            
            # Update Research Context
            for result in parsed_results:
                research_context["discovered_info"][result.field_name] = result.value
            
            all_results.extend(parsed_results)
            
            # Prüfe ob genug Informationen gefunden wurden
            if self.search_executor.is_research_complete(
                research_context, query, self.max_search_iterations
            ):
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
    
    async def _execute_deep_search(self, prompt: str, 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine Deep Search Anfrage aus"""
        
        system_prompt = """You are Perplexity Deep Research, designed to:
- Perform dozens of searches automatically
- Read and analyze hundreds of sources
- Reason through findings iteratively
- Provide comprehensive, fact-checked information
- Always cite specific sources with URLs when available"""
        
        response = await self.api_client.deep_research_search(
            prompt, system_prompt
        )
        
        if response:
            # Track sources
            citations = self.api_client.parse_citations(response)
            for citation in citations:
                context["sources_checked"].add(citation.get("url", ""))
            
            context["search_iterations"] += 1
            return response
        
        return {}
    
    async def _standard_search(self, query: MineQuery) -> List[SearchResult]:
        """Standard Suche (nicht Deep Research)"""
        prompts = {
            "general": f"Search for comprehensive information about {query.mine_name} mine in {query.region}, {query.country}",
            "technical": f"Find technical and operational data for {query.mine_name} mine",
            "environmental": f"Search for environmental and closure costs for {query.mine_name} mine"
        }
        
        all_results = []
        
        for search_type, prompt in prompts.items():
            response = await self.api_client.standard_search(
                prompt,
                "You are a helpful research assistant focused on mining information."
            )
            
            if response:
                results = self.search_executor.parse_search_results(
                    response, query, search_type
                )
                all_results.extend(results)
            
            await asyncio.sleep(1)
        
        return all_results
    
    async def _synthesize_findings(self, query: MineQuery, context: Dict[str, Any],
                                 all_results: List[SearchResult]) -> List[SearchResult]:
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
            synthesis_results = self.search_executor.parse_search_results(
                response, query, "synthesis"
            )
            
            # Mark as synthesis results
            for result in synthesis_results:
                result.metadata["synthesis"] = True
                result.metadata["total_sources"] = len(context["sources_checked"])
            
            return synthesis_results
        
        return []
    
    async def validate(self) -> bool:
        """Validate credentials"""
        return await self.initialize()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()