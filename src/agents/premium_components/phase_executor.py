"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Ausführung von Research-Phasen
"""

import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging

from .research_phases import ResearchPhase, PhaseType
from ..base_agent import BaseAgent, MineQuery
from ..dynamic_source_discovery import DynamicSourceDiscovery
from ..dynamic_keyword_generator import DynamicKeywordGenerator
from ..deep_web_crawler import DeepWebCrawler


class PhaseExecutor:
    """Führt Research-Phasen aus"""
    
    def __init__(self, agents: Dict[str, BaseAgent], logger: logging.Logger):
        self.agents = agents
        self.logger = logger
        
        # Spezialisierte Komponenten
        self.source_discovery = DynamicSourceDiscovery(agents) if agents else None
        self.keyword_generator = DynamicKeywordGenerator(agents) if agents else None
        
        # Web Crawler initialisieren
        scraper_agents = self._get_scraper_agents()
        self.web_crawler = DeepWebCrawler(
            name="web_crawler",
            config={},
            scraper_agents=scraper_agents
        ) if scraper_agents else None
        
        # Execution State
        self.active_executions = {}
        self.execution_history = []
    
    async def initialize(self):
        """Initialisiert Komponenten"""
        if self.web_crawler:
            await self.web_crawler.initialize()
    
    def _get_scraper_agents(self) -> Dict[str, BaseAgent]:
        """Filtert Scraper-Agenten"""
        if not self.agents:
            return {}
        
        scraper_names = ['scraper', 'brightdata', 'scrapingbee', 'apify', 'firecrawl']
        return {
            name: agent for name, agent in self.agents.items()
            if name in scraper_names
        }
    
    async def execute_phase(self,
                          phase: ResearchPhase,
                          query: MineQuery,
                          previous_results: List[Any],
                          source_cache: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine Research-Phase aus
        
        Returns:
            Dict mit results, discovered_sources, metrics
        """
        phase_id = f"{phase.name}_{datetime.now().timestamp()}"
        self.active_executions[phase_id] = {
            "phase": phase.name,
            "start_time": datetime.now(),
            "status": "running"
        }
        
        try:
            # Verfügbare Agenten für Phase filtern
            available_agents = self._filter_available_agents(phase.required_agents)
            
            if not available_agents:
                self.logger.warning(f"Keine Agenten verfügbar für Phase {phase.name}")
                return self._create_empty_result(phase)
            
            # Phase-spezifische Ausführung
            if phase.type == PhaseType.DISCOVERY:
                result = await self._execute_discovery_phase(
                    query, available_agents, phase
                )
            elif phase.type == PhaseType.DEEP_DIVE:
                result = await self._execute_deep_dive_phase(
                    query, available_agents, previous_results, source_cache, phase
                )
            elif phase.type == PhaseType.ANALYSIS:
                result = await self._execute_analysis_phase(
                    query, available_agents, previous_results, phase
                )
            elif phase.type == PhaseType.VERIFICATION:
                result = await self._execute_verification_phase(
                    query, available_agents, previous_results, phase
                )
            else:
                result = await self._execute_specialized_phase(
                    query, available_agents, previous_results, phase
                )
            
            # Metriken hinzufügen
            duration = (datetime.now() - self.active_executions[phase_id]["start_time"]).total_seconds()
            result["metrics"] = {
                "phase": phase.name,
                "duration": duration,
                "agents_used": list(available_agents.keys()),
                "results_count": len(result.get("results", []))
            }
            
            self.active_executions[phase_id]["status"] = "completed"
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Phase {phase.name} Timeout nach {phase.max_duration}s")
            return self._create_empty_result(phase, "timeout")
            
        except Exception as e:
            self.logger.error(f"Phase {phase.name} Fehler: {e}")
            return self._create_empty_result(phase, str(e))
            
        finally:
            if phase_id in self.active_executions:
                del self.active_executions[phase_id]
    
    async def _execute_discovery_phase(self,
                                     query: MineQuery,
                                     agents: Dict[str, BaseAgent],
                                     phase: ResearchPhase) -> Dict[str, Any]:
        """Discovery Phase: Quellen entdecken"""
        self.logger.info("Führe Discovery Phase aus...")
        
        results = []
        discovered_sources = {}
        
        # 1. Dynamische Keywords generieren
        if self.keyword_generator:
            keywords = await self.keyword_generator.generate_comprehensive_keywords(
                query.mine_name,
                query.country,
                query.region,
                query.languages
            )
            self.logger.info(f"Generierte {len(keywords.get('primary', []))} primäre Keywords")
        else:
            keywords = {"primary": [query.mine_name]}
        
        # 2. Quellen entdecken
        if self.source_discovery:
            sources = await self.source_discovery.discover_sources(
                mine_name=query.mine_name,
                country=query.country,
                region=query.region,
                required_fields=query.required_fields
            )
            discovered_sources = sources
            self.logger.info(f"Entdeckte {len(sources)} Quellen")
        
        # 3. Initiale Suche mit verfügbaren Agenten
        search_tasks = []
        for agent_name, agent in agents.items():
            if hasattr(agent, 'search_mine'):
                task = self._search_with_timeout(
                    agent.search_mine(query),
                    timeout=60,
                    agent_name=agent_name
                )
                search_tasks.append(task)
        
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            for result in search_results:
                if isinstance(result, list):
                    results.extend(result)
        
        return {
            "results": results,
            "discovered_sources": discovered_sources,
            "keywords": keywords
        }
    
    async def _execute_deep_dive_phase(self,
                                     query: MineQuery,
                                     agents: Dict[str, BaseAgent],
                                     previous_results: List[Any],
                                     source_cache: Dict[str, Any],
                                     phase: ResearchPhase) -> Dict[str, Any]:
        """Deep Dive Phase: Tiefes Crawling"""
        self.logger.info("Führe Deep Dive Phase aus...")
        
        results = []
        
        # URLs aus vorherigen Ergebnissen und Cache sammeln
        urls_to_crawl = self._extract_urls_for_crawling(
            previous_results,
            source_cache,
            limit=30
        )
        
        if not urls_to_crawl:
            self.logger.warning("Keine URLs zum Crawlen gefunden")
            return {"results": []}
        
        # Deep Web Crawling
        if self.web_crawler:
            self.logger.info(f"Crawle {len(urls_to_crawl)} URLs...")
            
            crawl_results = await self.web_crawler.crawl_sites(
                urls=urls_to_crawl,
                mine_query=query,
                max_depth=2
            )
            
            # Konvertiere Crawl-Ergebnisse
            for url, data in crawl_results.items():
                if data and "extracted_data" in data:
                    results.extend(data["extracted_data"])
        
        # Parallele Suche mit Scraper-Agenten
        scraper_tasks = []
        for agent_name, agent in agents.items():
            if agent_name in ['scraper', 'brightdata', 'firecrawl']:
                task = self._search_with_timeout(
                    agent.search_mine(query),
                    timeout=120,
                    agent_name=agent_name
                )
                scraper_tasks.append(task)
        
        if scraper_tasks:
            scraper_results = await asyncio.gather(*scraper_tasks, return_exceptions=True)
            for result in scraper_results:
                if isinstance(result, list):
                    results.extend(result)
        
        return {"results": results}
    
    async def _execute_analysis_phase(self,
                                    query: MineQuery,
                                    agents: Dict[str, BaseAgent],
                                    previous_results: List[Any],
                                    phase: ResearchPhase) -> Dict[str, Any]:
        """Analysis Phase: Komplexe Analyse"""
        self.logger.info("Führe Analysis Phase aus...")
        
        results = []
        
        # Nur AI-Agenten für Analyse
        ai_agents = {
            name: agent for name, agent in agents.items()
            if name in ['claude', 'gpt4', 'openrouter']
        }
        
        if not ai_agents:
            return {"results": []}
        
        # Kontext aus vorherigen Ergebnissen erstellen
        context = self._create_analysis_context(previous_results, query)
        
        # Parallele Analyse
        analysis_tasks = []
        for agent_name, agent in ai_agents.items():
            # Modifizierte Query mit Kontext
            analysis_query = MineQuery(
                mine_name=query.mine_name,
                region=query.region,
                country=query.country,
                languages=query.languages,
                required_fields=query.required_fields + ["analysis", "correlation", "insights"]
            )
            
            task = self._search_with_timeout(
                agent.search_mine(analysis_query),
                timeout=180,
                agent_name=agent_name
            )
            analysis_tasks.append(task)
        
        if analysis_tasks:
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            for result in analysis_results:
                if isinstance(result, list):
                    results.extend(result)
        
        return {"results": results, "context": context}
    
    async def _execute_verification_phase(self,
                                        query: MineQuery,
                                        agents: Dict[str, BaseAgent],
                                        previous_results: List[Any],
                                        phase: ResearchPhase) -> Dict[str, Any]:
        """Verification Phase: Ergebnisse verifizieren"""
        self.logger.info("Führe Verification Phase aus...")
        
        # Fakten zum Verifizieren extrahieren
        facts_to_verify = self._extract_facts_to_verify(previous_results)
        
        if not facts_to_verify:
            return {"results": []}
        
        results = []
        
        # Verifizierung mit schnellen Agenten
        verify_agents = {
            name: agent for name, agent in agents.items()
            if name in ['tavily', 'perplexity', 'claude']
        }
        
        # Batched Verification
        for i in range(0, len(facts_to_verify), 5):
            batch = facts_to_verify[i:i+5]
            
            verify_tasks = []
            for agent_name, agent in verify_agents.items():
                # Verifikations-Query
                verify_query = MineQuery(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    languages=query.languages,
                    required_fields=["verify: " + fact for fact in batch]
                )
                
                task = self._search_with_timeout(
                    agent.search_mine(verify_query),
                    timeout=60,
                    agent_name=agent_name
                )
                verify_tasks.append(task)
            
            if verify_tasks:
                verify_results = await asyncio.gather(*verify_tasks, return_exceptions=True)
                for result in verify_results:
                    if isinstance(result, list):
                        results.extend(result)
        
        return {"results": results, "verified_facts": len(facts_to_verify)}
    
    async def _execute_specialized_phase(self,
                                       query: MineQuery,
                                       agents: Dict[str, BaseAgent],
                                       previous_results: List[Any],
                                       phase: ResearchPhase) -> Dict[str, Any]:
        """Spezialisierte Phasen"""
        self.logger.info(f"Führe spezialisierte Phase aus: {phase.name}")
        
        # Generische Ausführung für spezialisierte Phasen
        results = []
        
        search_tasks = []
        for agent_name, agent in agents.items():
            if hasattr(agent, 'search_mine'):
                task = self._search_with_timeout(
                    agent.search_mine(query),
                    timeout=phase.max_duration // len(agents),
                    agent_name=agent_name
                )
                search_tasks.append(task)
        
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            for result in search_results:
                if isinstance(result, list):
                    results.extend(result)
        
        return {"results": results}
    
    async def _search_with_timeout(self, 
                                 coro,
                                 timeout: int,
                                 agent_name: str):
        """Führt Suche mit Timeout aus"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"{agent_name} Timeout nach {timeout}s")
            return []
        except Exception as e:
            self.logger.error(f"{agent_name} Fehler: {e}")
            return []
    
    def _filter_available_agents(self, 
                               required: List[str]) -> Dict[str, BaseAgent]:
        """Filtert verfügbare Agenten"""
        if not self.agents:
            return {}
        
        available = {}
        for req in required:
            if req in self.agents:
                available[req] = self.agents[req]
            # Partial matching
            else:
                for name, agent in self.agents.items():
                    if req in name or name in req:
                        available[name] = agent
        
        return available
    
    def _extract_urls_for_crawling(self,
                                 previous_results: List[Any],
                                 source_cache: Dict[str, Any],
                                 limit: int = 30) -> List[str]:
        """Extrahiert URLs zum Crawlen"""
        urls = set()
        
        # Aus Ergebnissen
        for result in previous_results:
            if hasattr(result, 'source_url') and result.source_url:
                urls.add(result.source_url)
            if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                if 'url' in result.metadata:
                    urls.add(result.metadata['url'])
        
        # Aus Source Cache
        for source_type, sources in source_cache.items():
            if isinstance(sources, list):
                for source in sources[:10]:  # Limit pro Typ
                    if isinstance(source, dict) and 'url' in source:
                        urls.add(source['url'])
        
        return list(urls)[:limit]
    
    def _create_analysis_context(self,
                               previous_results: List[Any],
                               query: MineQuery) -> str:
        """Erstellt Kontext für Analyse"""
        context_parts = [
            f"Mine: {query.mine_name}",
            f"Location: {query.country}, {query.region}",
            f"Previous findings: {len(previous_results)} results"
        ]
        
        # Zusammenfassung der bisherigen Ergebnisse
        field_summary = {}
        for result in previous_results[:20]:  # Limit für Kontext
            if hasattr(result, 'field_name'):
                field_name = result.field_name
                if field_name not in field_summary:
                    field_summary[field_name] = []
                field_summary[field_name].append(str(result.value)[:100])
        
        for field, values in field_summary.items():
            context_parts.append(f"{field}: {', '.join(values[:3])}")
        
        return "\n".join(context_parts)
    
    def _extract_facts_to_verify(self, 
                               previous_results: List[Any]) -> List[str]:
        """Extrahiert zu verifizierende Fakten"""
        facts = []
        
        # Wichtige numerische Werte
        for result in previous_results:
            if hasattr(result, 'field_name') and hasattr(result, 'value'):
                # Numerische Felder priorisieren
                if any(term in result.field_name.lower() for term in 
                      ['production', 'reserve', 'employee', 'depth', 'cost']):
                    facts.append(f"{result.field_name}: {result.value}")
        
        # Deduplizieren und limitieren
        return list(set(facts))[:20]
    
    def _create_empty_result(self, 
                           phase: ResearchPhase,
                           error: Optional[str] = None) -> Dict[str, Any]:
        """Erstellt leeres Ergebnis"""
        return {
            "results": [],
            "metrics": {
                "phase": phase.name,
                "duration": 0,
                "agents_used": [],
                "results_count": 0,
                "error": error
            }
        }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Gibt Status einer Ausführung zurück"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        return {"status": "not_found"}
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Bricht Ausführung ab"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = "cancelled"
            return True
        return False