"""
Orchestrator für die Koordination der Agenten
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import logging

from ..agents.base_agent import BaseAgent, MineQuery, SearchResult
from ..agents.factory import AgentFactory
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.staged_search import StagedSearchStrategy, SearchStage
from ..agents.research_orchestrator import ResearchOrchestrator
from ..data.aggregator import DataAggregator
from .config import Config
from .logger import get_logger


class MineSearchOrchestrator:
    """Koordiniert die Suche über mehrere Agenten"""
    
    def __init__(self, config: Config, status_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.active_agents: List[str] = []
        self.aggregator = DataAggregator()
        self.coordinator = AgentCoordinator(config)
        self.staged_search = StagedSearchStrategy(config)
        self.logger = get_logger("orchestrator")
        self._initialized = False
        self.status_callback = status_callback
        self.research_orchestrator = None  # Will be initialized when needed
        
    def _report_status(self, message: str):
        """Reports status to callback if available"""
        self.logger.info(message)
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
        
    async def initialize(self) -> bool:
        """Initialisiert alle verfügbaren Agenten"""
        if self._initialized:
            return True
            
        self._report_status("Initialisiere Orchestrator...")
        
        # Hole verfügbare Agenten
        available_agents = AgentFactory.get_available_agents(self.config)
        self._report_status(f"Gefunden: {len([a for a, v in available_agents.items() if v])} verfügbare Agenten")
        
        # Erstelle und initialisiere Agenten
        init_tasks = []
        for agent_type, is_available in available_agents.items():
            if is_available:
                try:
                    # Handle OpenRouter models
                    if agent_type.startswith("openrouter_"):
                        # Extract model ID from agent type
                        model_suffix = agent_type.replace("openrouter_", "")
                        # Find matching model
                        from ..agents.openrouter_agent import OpenRouterAgent
                        model_id = None
                        
                        # Search in both FREE_MODELS and PREMIUM_MODELS
                        all_models = {**OpenRouterAgent.FREE_MODELS, **OpenRouterAgent.PREMIUM_MODELS}
                        for mid, model in all_models.items():
                            # Handle models with :free suffix and other special cases
                            model_key = mid.split('/')[-1].split(':')[0]
                            if model_key == model_suffix:
                                model_id = mid
                                break
                        
                        if model_id:
                            agent = AgentFactory.create_agent(agent_type, self.config, model_id=model_id)
                        else:
                            self.logger.warning(f"Model ID not found for {agent_type}")
                            continue
                    else:
                        agent = AgentFactory.create_agent(agent_type, self.config)
                    
                    if agent:
                        self.agents[agent_type] = agent
                        init_tasks.append(self._init_agent(agent_type, agent))
                except Exception as e:
                    self.logger.error(f"Fehler beim Erstellen von Agent {agent_type}: {e}")
        
        # Initialisiere alle Agenten parallel
        if init_tasks:
            results = await asyncio.gather(*init_tasks, return_exceptions=True)
            
            # Prüfe Ergebnisse
            for i, (agent_type, result) in enumerate(zip(self.agents.keys(), results)):
                if isinstance(result, Exception):
                    self.logger.error(f"Agent {agent_type} Initialisierung fehlgeschlagen: {result}")
                    del self.agents[agent_type]
                elif result:
                    self.active_agents.append(agent_type)
                    self.logger.info(f"Agent {agent_type} erfolgreich initialisiert")
        
        self._initialized = True
        self.logger.info(f"Orchestrator initialisiert mit {len(self.active_agents)} aktiven Agenten")
        return True
    
    async def _init_agent(self, agent_type: str, agent: BaseAgent) -> bool:
        """Initialisiert einen einzelnen Agenten"""
        try:
            return await agent.initialize()
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung von {agent_type}: {e}")
            return False
    
    async def search_mine_staged(self, query: MineQuery, search_params: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Führt gestaffelte Suche durch für bessere Ergebnisse"""
        if not self._initialized:
            await self.initialize()
        
        self._report_status(f"🎯 Starte gestaffelte Suche für Mine: {query.mine_name}")
        self._report_status(f"📍 Region: {query.region}, {query.country}")
        
        # Bestimme benötigte Suchphasen
        needed_stages = self.staged_search.get_stages_for_fields(query.required_fields)
        self._report_status(f"📋 Geplant: {len(needed_stages)} Suchphasen mit {len(self.active_agents)} Agenten")
        
        all_results = []
        results_by_field = {}
        phase_counter = 0
        
        # Führe Suche phasenweise durch
        for stage in needed_stages:
            phase_counter += 1
            stage_info = self.staged_search.get_stage_info(stage)
            
            self._report_status(f"\n{'='*60}")
            self._report_status(f"📊 PHASE {phase_counter}/{len(needed_stages)}: {stage_info.name}")
            self._report_status(f"{'='*60}")
            
            # Bestimme Felder für diese Phase
            stage_fields = self.staged_search.get_fields_for_stage(stage, query.required_fields)
            if not stage_fields:
                continue
            
            self._report_status(f"🔍 Suche nach {len(stage_fields)} Feldern:")
            fields_display = ", ".join(stage_fields[:5])
            if len(stage_fields) > 5:
                fields_display += f" ... und {len(stage_fields) - 5} weitere"
            self._report_status(f"   {fields_display}")
                
            # Wähle beste Agenten für diese Phase
            stage_agents = self.staged_search.get_best_agents_for_stage(stage, self.active_agents)
            self._report_status(f"\n🤖 Aktiviere {len(stage_agents)} Agenten für diese Phase:")
            
            # Zeige Agenten in Gruppen
            for i in range(0, len(stage_agents), 5):
                batch = stage_agents[i:i+5]
                self._report_status(f"   • {', '.join(batch)}")
            
            # Erstelle Query für diese Phase
            stage_query = MineQuery(
                mine_name=query.mine_name,
                region=query.region,
                country=query.country,
                languages=query.languages,
                required_fields=stage_fields
            )
            
            # Führe Suche mit Agenten-Koordinator durch
            search_params_stage = {
                'active_agents': stage_agents,
                'timeout': stage_info.timeout,
                'use_coordinator': True,
                'phase_info': f"Phase {phase_counter}: {stage_info.name}"
            }
            
            self._report_status(f"\n⚡ Starte parallele Suche mit {len(stage_agents)} Agenten...")
            
            stage_results = await self.search_mine(stage_query, search_params_stage)
            all_results.extend(stage_results)
            
            # Sammle detaillierte Ergebnisse
            fields_found = {}
            agents_with_results = set()
            
            for result in stage_results:
                if result.field_name not in results_by_field:
                    results_by_field[result.field_name] = 0
                results_by_field[result.field_name] += 1
                
                if result.field_name not in fields_found:
                    fields_found[result.field_name] = []
                fields_found[result.field_name].append(result.agent_name)
                agents_with_results.add(result.agent_name)
            
            # Zeige Phase-Zusammenfassung
            self._report_status(f"\n✅ Phase {phase_counter} abgeschlossen:")
            self._report_status(f"   • {len(stage_results)} Ergebnisse gefunden")
            self._report_status(f"   • {len(fields_found)} von {len(stage_fields)} Feldern mit Daten")
            self._report_status(f"   • {len(agents_with_results)} Agenten lieferten Ergebnisse")
            
            # Zeige welche Felder gefunden wurden
            if fields_found:
                self._report_status(f"\n📌 Gefundene Felder:")
                for field, agents in list(fields_found.items())[:5]:
                    self._report_status(f"   • {field}: {len(agents)} Quellen")
                if len(fields_found) > 5:
                    self._report_status(f"   • ... und {len(fields_found) - 5} weitere Felder")
            
            # Prüfe ob zur nächsten Phase übergegangen werden soll
            if not self.staged_search.should_continue_to_next_stage(stage, results_by_field, query.required_fields):
                self._report_status("\n🎯 Genügend Ergebnisse gefunden, beende Suche")
                break
                
            # Kurze Pause zwischen Phasen
            if phase_counter < len(needed_stages):
                self._report_status(f"\n⏳ Kurze Pause vor nächster Phase...")
                await asyncio.sleep(2)
        
        self._report_status(f"\n{'='*60}")
        self._report_status(f"🏁 SUCHE ABGESCHLOSSEN")
        self._report_status(f"{'='*60}")
        self._report_status(f"📊 Gesamtergebnis: {len(all_results)} Datenpunkte gefunden")
        self._report_status(f"📈 Abdeckung: {len(results_by_field)} von {len(query.required_fields)} Feldern")
        
        return all_results
    
    async def search_mine(self, query: MineQuery, search_params: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Führt Suche mit optimierter Agentenzuweisung durch"""
        if not self._initialized:
            await self.initialize()
        
        # Phase info wenn verfügbar
        phase_info = search_params.get('phase_info', '') if search_params else ''
        if not phase_info:
            self._report_status(f"🔍 Starte Suche für Mine: {query.mine_name}")
        
        # Apply search parameters if provided
        timeout = 600  # Default 10 minutes for deeper searches
        use_coordinator = True  # Nutze Agenten-Koordinator standardmäßig
        
        if search_params:
            timeout = search_params.get('timeout', timeout)
            use_coordinator = search_params.get('use_coordinator', True)
            if 'active_agents' in search_params:
                # Override active agents for this search
                self.active_agents = [a for a in search_params['active_agents'] if a in self.agents]
        
        # Nutze AgentCoordinator für optimale Zuweisung
        if use_coordinator and query.required_fields:
            # Zeige nur kurze Info, keine Details
            self.logger.info("Optimiere Agentenzuweisung...")
            agent_assignments = self.coordinator.get_agent_assignment(
                fields=query.required_fields,
                available_agents=self.active_agents
            )
            
            # Log Zuweisungen (nur ins Log, nicht in UI)
            for agent, fields in agent_assignments.items():
                self.logger.info(f"Agent {agent} zugewiesen für: {', '.join(fields)}")
        else:
            # Fallback: Alle Agenten suchen alle Felder
            agent_assignments = {agent: query.required_fields for agent in self.active_agents}
        
        # Erstelle Such-Tasks mit spezialisierten Queries
        search_tasks = []
        for agent_type, assigned_fields in agent_assignments.items():
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                # Erstelle spezialisierte Query für diesen Agenten
                specialized_query = MineQuery(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    languages=query.languages,
                    required_fields=assigned_fields
                )
                search_tasks.append(self._search_with_agent(agent, specialized_query))
        
        # Führe Suchen parallel aus
        all_results = []
        if search_tasks:
            # Detaillierte Info nur wenn nicht in Phase
            if not phase_info:
                self._report_status(f"Führe {len(search_tasks)} parallele Suchen aus...")
            
            # Mit Timeout für alle Suchen
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*search_tasks, return_exceptions=True),
                    timeout=timeout
                )
                
                # Sammle alle erfolgreichen Ergebnisse
                successful_agents = 0
                failed_agents = 0
                
                for i, result in enumerate(results):
                    if isinstance(result, list):
                        all_results.extend(result)
                        if result:
                            successful_agents += 1
                        self.logger.debug(f"Agent {i+1}/{len(results)} lieferte {len(result)} Ergebnisse")
                    elif isinstance(result, Exception):
                        failed_agents += 1
                        self.logger.error(f"Agent-Suche fehlgeschlagen: {result}")
                
                # Kompakte Zusammenfassung
                if not phase_info:
                    self._report_status(f"✅ {successful_agents} Agenten erfolgreich, {failed_agents} fehlgeschlagen")
                        
            except asyncio.TimeoutError:
                self._report_status(f"⏱️ Such-Timeout nach {timeout} Sekunden")
                self.logger.error(f"Such-Timeout nach {timeout} Sekunden")
        
        # Aggregiere Ergebnisse
        if all_results:
            if not phase_info:
                self._report_status("📊 Aggregiere und dedupliziere Ergebnisse...")
            aggregated_results = self.aggregator.aggregate_results(all_results)
            if not phase_info:
                self._report_status(f"✅ Suche abgeschlossen: {len(aggregated_results)} finale Ergebnisse")
            return aggregated_results
        
        if not phase_info:
            self._report_status("❌ Keine Ergebnisse gefunden")
        return []
    
    async def _search_with_agent(self, agent: BaseAgent, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit einem einzelnen Agenten aus"""
        try:
            # Log nur, zeige nicht im UI
            self.logger.info(f"Starte Suche mit Agent {agent.name}...")
            results = await agent.execute_search(query)
            
            if results:
                self.logger.info(f"Agent {agent.name} lieferte {len(results)} Ergebnisse")
                # Log erste Ergebnisse für Debugging
                for i, result in enumerate(results[:2]):
                    self.logger.debug(f"{agent.name} Ergebnis {i+1}: {result.field_name} = {result.value[:50]}...")
            else:
                self.logger.info(f"Agent {agent.name} fand keine Ergebnisse")
                
            return results
        except Exception as e:
            self.logger.error(f"Fehler bei Agent {agent.name}: {type(e).__name__}: {str(e)}")
            return []
    
    async def cleanup(self):
        """Räumt alle Agenten auf"""
        self.logger.info("Räume Orchestrator auf...")
        
        cleanup_tasks = []
        for agent in self.agents.values():
            cleanup_tasks.append(agent.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.agents.clear()
        self.active_agents.clear()
        self._initialized = False
        self.logger.info("Orchestrator Cleanup abgeschlossen")
        
        # Clean up research orchestrator if exists
        if self.research_orchestrator:
            await self.research_orchestrator.cleanup()
            self.research_orchestrator = None
    
    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Gibt Statistiken aller Agenten zurück"""
        stats = {}
        for agent_type, agent in self.agents.items():
            stats[agent_type] = {
                'status': agent.status.value,
                'stats': agent.get_statistics(),
                'is_active': agent_type in self.active_agents
            }
        return stats
    
    def set_active_agents(self, agent_types: List[str]):
        """Setzt die aktiven Agenten für die nächste Suche"""
        self.active_agents = [a for a in agent_types if a in self.agents]
        self.logger.info(f"Aktive Agenten gesetzt: {self.active_agents}")
    
    async def search_mine_deep_research(self, query: MineQuery) -> List[SearchResult]:
        """Führt Deep Research mit Research Orchestrator durch"""
        if not self._initialized:
            await self.initialize()
        
        self._report_status(f"🔬 Starte Deep Research für Mine: {query.mine_name}")
        self._report_status(f"🌍 Region: {query.region}, {query.country}")
        self._report_status(f"🎯 Zielfelder: {len(query.required_fields)}")
        
        # Initialize Research Orchestrator if needed
        if not self.research_orchestrator:
            self.research_orchestrator = ResearchOrchestrator(
                self.config,
                self.active_agents
            )
        
        # Execute deep research
        try:
            results = await self.research_orchestrator.execute_research(query)
            
            self._report_status(f"✅ Deep Research abgeschlossen: {len(results)} Ergebnisse gefunden")
            
            # Log field coverage
            fields_found = set(r.field_name for r in results)
            coverage = len(fields_found) / len(query.required_fields) * 100 if query.required_fields else 0
            self._report_status(f"📊 Feldabdeckung: {coverage:.1f}% ({len(fields_found)}/{len(query.required_fields)} Felder)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Deep Research: {e}")
            self._report_status(f"❌ Fehler bei Deep Research: {str(e)}")
            return []