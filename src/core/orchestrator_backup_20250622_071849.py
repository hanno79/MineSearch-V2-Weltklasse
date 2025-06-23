"""
Orchestrator für die Koordination der Agenten
VERSION: 18.06.2025-15:45 NEUE VERSION
"""
import asyncio
import sys
from datetime import datetime
# ÄNDERUNG 18.06.2025: Entfernt print zu stderr - verursacht BrokenPipeError bei reload
from typing import List, Dict, Any, Optional, Callable
import logging

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult
from src.agents.factory import AgentFactory
from src.agents.agent_coordinator import AgentCoordinator
from src.agents.staged_search import StagedSearchStrategy
from src.agents.research_orchestrator import ResearchOrchestrator
from src.data.aggregator import DataAggregator
from .config import Config
from .logger import get_logger
from .source_manager import SourceManager, SourceInfo
from .cancellation import CancellationToken, CancellationException


class MineSearchOrchestrator:
    """Koordiniert die Suche über mehrere Agenten"""
    
    def __init__(self, config: Config, status_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.active_agents: List[str] = []
        self.aggregator = DataAggregator()
        self.coordinator = AgentCoordinator(config)
        self.staged_search = StagedSearchStrategy(config)
        self.source_manager = SourceManager()  # Neue Quellenverwaltung
        self.logger = get_logger("orchestrator")
        self._initialized = False
        self.status_callback = status_callback
        self.research_orchestrator = None  # Will be initialized when needed
        # ÄNDERUNG 21.06.2025: Datenbank-Manager hinzufügen
        from .database import get_db_manager
        self.db_manager = get_db_manager()
        
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
                        from src.agents.openrouter_agent import OpenRouterAgent
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
        
        # ÄNDERUNG 21.06.2025: Stelle sicher, dass Scraper immer verfügbar ist
        if "scraper" not in self.agents:
            try:
                self.logger.info("DEBUG: Scraper Agent nicht gefunden, füge manuell hinzu")
                scraper = AgentFactory.create_agent("scraper", self.config)
                if scraper:
                    self.agents["scraper"] = scraper
                    init_success = await self._init_agent("scraper", scraper)
                    if init_success:
                        self.active_agents.append("scraper")
                        self.logger.info("DEBUG: Scraper Agent erfolgreich manuell hinzugefügt")
                    else:
                        self.logger.error("DEBUG: Scraper Agent konnte nicht initialisiert werden")
            except Exception as e:
                self.logger.error(f"Fehler beim Hinzufügen des Scraper Agents: {e}")
        
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
    
    async def discover_sources(self, query: MineQuery, cancellation_token=None) -> List[SourceInfo]:
        """ÄNDERUNG 21.06.2025: Neue Methode für systematische Quellensammlung"""
        self._report_status("🔍 Starte systematische Quellensammlung...")
        
        # Hole oder erstelle Mine in DB
        # ÄNDERUNG 21.06.2025: get_or_create_mine gibt ID zurück, nicht Mine-Objekt
        mine_id = self.db_manager.get_or_create_mine(
            name=query.mine_name,
            region=query.region,
            country=query.country,
            languages=query.languages
        )
        
        # Erstelle spezielle Query für Quellensuche
        source_query = MineQuery(
            mine_name=query.mine_name,
            region=query.region,
            country=query.country,
            languages=query.languages,
            required_fields=["sources", "websites", "urls", "official_website", 
                           "government_database", "company_page", "mining_portal"]
        )
        
        # Nutze spezielle Source Discovery Agenten
        source_agents = ['tavily', 'exa', 'deep_web_crawler', 'scraper']
        available_source_agents = [a for a in source_agents if a in self.active_agents]
        
        # Suche nach Quellen
        search_params = {
            'active_agents': available_source_agents,
            'timeout': 60,  # Kurzes Timeout für Quellensuche
            'phase_info': 'Source Discovery'
        }
        
        # ÄNDERUNG 21.06.2025: Füge Cancellation Token hinzu wenn vorhanden
        if cancellation_token:
            search_params['cancellation_token'] = cancellation_token
        
        results = await self.search_mine(source_query, search_params)
        
        # Konvertiere zu SourceInfo Objekten und speichere in DB
        sources = []
        for result in results:
            if 'http' in result.value.lower() or '.com' in result.value.lower() or '.org' in result.value.lower():
                source_info = SourceInfo(
                    url=result.value,
                    source_type=self._determine_source_type(result.value, result.field_name),
                    relevance_score=result.confidence_score,
                    found_by_agents=[result.agent_name],
                    meta_data={
                        'source': result.source,
                        'confidence': result.confidence_score
                    }
                )
                self.source_manager.add_source(query.mine_name, source_info)
                sources.append(source_info)
                
                # Speichere in Datenbank
                source_data = {
                    'url': result.value,
                    'source_type': self._determine_source_type(result.value, result.field_name),
                    'discovered_by': result.agent_name,
                    'reliability_score': result.confidence_score,
                    'metadata': {
                        'source': result.source,
                        'field': result.field_name,
                        'timestamp': result.timestamp.isoformat() if result.timestamp else None
                    }
                }
                self.db_manager.add_source(mine_id, source_data)
        
        # Hole Top-Quellen
        top_sources = self.source_manager.get_top_sources(query.mine_name, limit=20)
        self._report_status(f"✅ {len(top_sources)} relevante Quellen gefunden und priorisiert")
        self._report_status(f"💾 {len(sources)} Quellen in Datenbank gespeichert")
        
        # ÄNDERUNG 21.06.2025: Debug-Logging für Quellenrückgabe
        self.logger.info(f"DEBUG: discover_sources gefunden: {len(sources)} Quellen")
        
        return top_sources
    
    def _determine_source_type(self, url: str, field_name: str) -> str:
        """Bestimmt den Typ einer Quelle basierend auf URL und Kontext"""
        url_lower = url.lower()
        
        if any(gov in url_lower for gov in ['.gov', '.gob', '.gouv', 'government']):
            return 'government'
        elif any(corp in url_lower for corp in ['company', 'corp', 'inc', 'ltd']):
            return 'company'
        elif any(news in url_lower for news in ['news', 'journal', 'times', 'post']):
            return 'news'
        elif any(tech in url_lower for tech in ['report', 'study', 'research', 'pdf']):
            return 'technical_report'
        elif 'database' in field_name.lower() or 'portal' in url_lower:
            return 'database'
        else:
            return 'website'
    
    async def search_mine_staged(self, query: MineQuery, search_params: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Führt gestaffelte Suche durch für bessere Ergebnisse"""
        if not self._initialized:
            await self.initialize()
        
        # ÄNDERUNG 19.06.2025: Cancellation Token Support
        cancellation_token = None
        if search_params and 'cancellation_token' in search_params:
            cancellation_token = search_params['cancellation_token']
            self.logger.info("Suche mit Cancellation Token gestartet")
        
        # ÄNDERUNG 18.06.2025: Setze aktive Agenten aus search_params wenn vorhanden
        if search_params and 'active_agents' in search_params:
            self.active_agents = [a for a in search_params['active_agents'] if a in self.agents]
            self._report_status(f"✅ Aktive Agenten aus search_params gesetzt: {len(self.active_agents)} Agenten")
        
        self._report_status(f"🎯 Starte gestaffelte Suche für Mine: {query.mine_name}")
        self._report_status(f"📍 Region: {query.region}, {query.country}")
        self._report_status("🆕 VERSION: 18.06.2025-13:30 mit Source Discovery DEBUG")
        self._report_status(f"🐛 DEBUG: File loaded from {__file__}")
        self._report_status(f"📊 DEBUG: Anzahl aktiver Agenten: {len(self.active_agents)}")
        self._report_status(f"🤖 DEBUG: Aktive Agenten: {', '.join(self.active_agents[:5])}...")
        
        # Bestimme benötigte Suchphasen
        needed_stages = self.staged_search.get_stages_for_fields(query.required_fields)
        # ÄNDERUNG 18.06.2025: Sichere Stage-Namen Extraktion ohne hasattr
        stage_names = []
        for s in needed_stages:
            try:
                # Direkt versuchen auf name zuzugreifen
                stage_names.append(s.name)
            except AttributeError:
                try:
                    # Fallback zu value
                    stage_names.append(f"Stage_{s.value}")
                except:
                    stage_names.append("Unknown Stage")
            except Exception:
                stage_names.append("Unknown Stage")
        self._report_status(f"🔍 DEBUG: Stages von get_stages_for_fields: {stage_names}")
        
        # ÄNDERUNG 18.06.2025: Source Discovery handling ohne Enum-Zugriff
        # Erstelle Source Discovery Stage manuell um Enum-Probleme zu vermeiden
        try:
            # Importiere SearchStage lokal um frische Referenz zu haben
            from src.agents.staged_search import SearchStage
            
            # Füge SOURCE_DISCOVERY als erste Stage hinzu wenn nicht bereits vorhanden
            has_source_discovery = False
            for stage in needed_stages:
                try:
                    if hasattr(stage, 'value') and stage.value == 0:
                        has_source_discovery = True
                        break
                except:
                    pass
            
            if not has_source_discovery:
                # Versuche SOURCE_DISCOVERY zu bekommen
                try:
                    source_stage = SearchStage(0)  # SOURCE_DISCOVERY hat value=0
                    needed_stages.insert(0, source_stage)
                    self._report_status("🔍 Phase 0: Source Discovery hinzugefügt")
                except Exception as e:
                    self.logger.debug(f"Konnte SOURCE_DISCOVERY nicht erstellen: {e}")
                    # Fallback: Füge eine "fake" Stage mit value=0 hinzu
                    class FakeStage:
                        value = 0
                        name = "SOURCE_DISCOVERY"
                    fake_stage = FakeStage()
                    needed_stages.insert(0, fake_stage)
                    self._report_status("🔍 Phase 0: Source Discovery hinzugefügt (Fallback)")
                    
        except Exception as e:
            # Falls alles fehlschlägt, arbeite ohne Source Discovery
            self.logger.debug(f"Source Discovery konnte nicht hinzugefügt werden: {e}")
        
        # Debug: Zeige welche Phasen geplant sind
        # ÄNDERUNG 18.06.2025: Sichere Stage-Info Extraktion
        stage_names = []
        stage_ids = []
        for stage in needed_stages:
            try:
                stage_info = self.staged_search.get_stage_info(stage)
                stage_names.append(stage_info.name if stage_info else "Unknown")
                try:
                    stage_ids.append(stage.value)
                except:
                    stage_ids.append("?")
            except:
                stage_names.append("Unknown Stage")
                stage_ids.append("?")
        
        self._report_status(f"📋 Geplante Phasen: {', '.join(stage_names)}")
        self._report_status(f"📋 DEBUG: Phasen-IDs: {stage_ids}")
        
        # Zeige finale Anzahl der Phasen
        self._report_status(f"📋 Finale Anzahl: {len(needed_stages)} Suchphasen mit {len(self.active_agents)} Agenten")
        
        all_results = []
        results_by_field = {}
        phase_counter = 0
        
        # Führe Suche phasenweise durch
        for stage in needed_stages:
            # ÄNDERUNG 19.06.2025: Check für Abbruch vor jeder Phase
            if cancellation_token and cancellation_token.is_cancelled():
                self._report_status("🛑 Suche wurde abgebrochen!")
                cancel_info = cancellation_token.get_cancel_info()
                self._report_status(f"❌ Grund: {cancel_info['cancel_reason']}")
                raise CancellationException("Suche vom Benutzer abgebrochen")
            
            phase_counter += 1
            stage_info = self.staged_search.get_stage_info(stage)
            
            self._report_status(f"\n{'='*60}")
            self._report_status(f"📊 PHASE {phase_counter}/{len(needed_stages)}: {stage_info.name}")
            self._report_status(f"{'='*60}")
            
            # Spezialbehandlung für Source Discovery (reload-sicher über value)
            stage_value = None
            try:
                stage_value = stage.value if hasattr(stage, 'value') else None
            except:
                stage_value = None
                
            if stage_value == 0:  # SOURCE_DISCOVERY
                self._report_status("🔍 PHASE 0: QUELLEN-DISCOVERY")
                self._report_status("=" * 40)
                self._report_status("🎯 Ziel: Finde relevante Informationsquellen")
                self._report_status("")
                self._report_status("📚 Suche nach:")
                self._report_status("   • Regierungsseiten und offizielle Datenbanken")
                self._report_status("   • Unternehmenswebsites und Betreiberinformationen")
                self._report_status("   • Technische Berichte und wissenschaftliche Publikationen")
                self._report_status("   • Nachrichtenquellen und Branchenportale")
                self._report_status("")
                
                # ÄNDERUNG 21.06.2025: Nutze neue discover_sources Methode
                discovered_sources = await self.discover_sources(query, cancellation_token)
                
                # Speichere Quellen für nachfolgende Phasen
                if search_params is None:
                    search_params = {}
                search_params['discovered_sources'] = discovered_sources
                
                # Erstelle spezielle Query für Quellensuche
                self._report_status(f"🔎 Suchparameter:")
                self._report_status(f"   • Mine: {query.mine_name}")
                self._report_status(f"   • Region: {query.region}, {query.country}")
                self._report_status(f"   • Gefundene Quellen: {len(discovered_sources)}")
                self._report_status("")
                
                # Zeige Top-Quellen
                if discovered_sources:
                    self._report_status("📌 TOP QUELLEN:")
                    for i, source in enumerate(discovered_sources[:5]):
                        self._report_status(f"   {i+1}. [{source.source_type}] {source.url[:60]}...")
                        self._report_status(f"      Relevanz: {source.relevance_score:.2f}")
                
                # Skip normale Agenten-Suche für Source Discovery
                continue
            else:
                # Normale Feldbehandlung für andere Phasen
                stage_fields = self.staged_search.get_fields_for_stage(stage, query.required_fields)
                if not stage_fields:
                    continue
                
                self._report_status(f"🔍 Suche nach {len(stage_fields)} Feldern:")
                fields_display = ", ".join(stage_fields[:5])
                if len(stage_fields) > 5:
                    fields_display += f" ... und {len(stage_fields) - 5} weitere"
                self._report_status(f"   {fields_display}")
                
                # Wähle beste Agenten für diese Phase
                # ÄNDERUNG 21.06.2025: Debug-Logging für Agent-Auswahl
                self.logger.info(f"DEBUG: Stage {stage_info.name}")
                self.logger.info(f"DEBUG: Verfügbare Agenten für Stage: {self.active_agents}")
                stage_agents = self.staged_search.get_best_agents_for_stage(stage, self.active_agents)
                self.logger.info(f"DEBUG: Ausgewählte Agenten für Stage: {stage_agents}")
            
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
            
            # ÄNDERUNG 21.06.2025: Gebe entdeckte Quellen an Agenten weiter
            if search_params and 'discovered_sources' in search_params:
                search_params_stage['discovered_sources'] = search_params['discovered_sources']
            
            # ÄNDERUNG 19.06.2025: Füge Cancellation Token hinzu
            if cancellation_token:
                search_params_stage['cancellation_token'] = cancellation_token
            
            self._report_status(f"\n⚡ Starte parallele Suche mit {len(stage_agents)} Agenten...")
            self._report_status(f"⏱️ Such-Timeout nach {stage_info.timeout} Sekunden")
            
            stage_results = await self.search_mine(stage_query, search_params_stage)
            
            # Spezialbehandlung für Source Discovery Ergebnisse
            # Vergleiche mit stage.value statt mit Enum oder Name (reload-sicher)
            if stage.value == 0:  # SOURCE_DISCOVERY
                # ÄNDERUNG 21.06.2025: Füge SOURCE_DISCOVERY Ergebnisse auch zu all_results hinzu
                all_results.extend(stage_results)
                
                sources_found = []
                for result in stage_results:
                    # Extrahiere URLs und Quelleninformationen
                    if 'url' in result.value.lower() or 'http' in result.value.lower():
                        source_info = SourceInfo(
                            url=result.value,
                            source_type=result.field_name,
                            found_by_agents=[result.agent_name],
                            meta_data={'confidence': result.confidence}
                        )
                        self.source_manager.add_source(query.mine_name, source_info)
                        sources_found.append(source_info)
                
                self._report_status(f"\n✅ QUELLENSUCHE ABGESCHLOSSEN")
                self._report_status("=" * 40)
                self._report_status(f"📊 Ergebnis: {len(sources_found)} relevante Quellen gefunden")
                self._report_status(f"💾 Gespeichert für nachfolgende Detailsuche")
                
                # Zeige Top-Quellen mit mehr Details
                if sources_found:
                    self._report_status(f"\n📌 GEFUNDENE QUELLEN:")
                    
                    # Gruppiere nach Typ
                    sources_by_type = {}
                    for source in sources_found:
                        if source.source_type not in sources_by_type:
                            sources_by_type[source.source_type] = []
                        sources_by_type[source.source_type].append(source)
                    
                    for source_type, type_sources in sources_by_type.items():
                        self._report_status(f"\n   {source_type.upper()} ({len(type_sources)} Quellen):")
                        for i, source in enumerate(type_sources[:3]):  # Zeige top 3 pro Typ
                            self._report_status(f"   {i+1}. {source.url[:80]}...")
                            if len(source.found_by_agents) > 1:
                                self._report_status(f"      (gefunden von {len(source.found_by_agents)} Agenten)")
                    
                    self._report_status(f"\n🎯 Diese Quellen werden in Phase 2 für Detailsuche verwendet!")
                
                # Setze agents_with_results für Konsistenz
                agents_with_results = set(result.agent_name for result in stage_results)
            else:
                # Normale Ergebnisbehandlung für andere Phasen
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
            
            # Zeige Phase-Zusammenfassung (außer für Source Discovery - bereits angezeigt)
            try:
                is_source_discovery = hasattr(stage, 'value') and stage.value == 0
            except:
                is_source_discovery = False
                
            if not is_source_discovery:  # Nicht SOURCE_DISCOVERY
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
        
        # Zeige Quellen-Statistik
        source_stats = self.source_manager.get_statistics()
        if source_stats['total_sources'] > 0:
            self._report_status(f"\n📚 Quellenstatistik:")
            self._report_status(f"   • {source_stats['total_sources']} Quellen insgesamt gefunden")
            self._report_status(f"   • {source_stats['global_sources']} globale Quellen (Regierung, etc.)")
            self._report_status(f"   • {source_stats['mine_specific_sources']} minenspezifische Quellen")
        
        return all_results
    
    async def search_mine(self, query: MineQuery, search_params: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Führt Suche mit optimierter Agentenzuweisung durch"""
        if not self._initialized:
            await self.initialize()
        
        # ÄNDERUNG 19.06.2025: Extrahiere Cancellation Token
        cancellation_token = None
        if search_params and 'cancellation_token' in search_params:
            cancellation_token = search_params['cancellation_token']
        
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
                
                # ÄNDERUNG 19.06.2025: Setze Cancellation Token für Agent
                if cancellation_token:
                    agent.set_cancellation_token(cancellation_token)
                
                # Erstelle spezialisierte Query für diesen Agenten
                specialized_query = MineQuery(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    languages=query.languages,
                    required_fields=assigned_fields
                )
                search_tasks.append(self._search_with_agent(agent, specialized_query, cancellation_token))
        
        # Führe Suchen parallel aus
        all_results = []
        if search_tasks:
            # Detaillierte Info nur wenn nicht in Phase
            if not phase_info:
                self._report_status(f"Führe {len(search_tasks)} parallele Suchen aus...")
            
            # Mit Timeout für alle Suchen
            try:
                # ÄNDERUNG 19.06.2025: Erstelle Task mit Cancellation Support
                if cancellation_token:
                    # Verwende die neue Helper-Methode
                    gather_task = asyncio.ensure_future(
                        self._gather_search_tasks(search_tasks)
                    )
                    
                    # Erstelle cancellation task
                    cancel_task = asyncio.create_task(
                        cancellation_token.wait_for_cancellation()
                    )
                    
                    # Warte auf das was zuerst fertig wird
                    done, pending = await asyncio.wait(
                        [gather_task, cancel_task],
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=timeout
                    )
                    
                    # Prüfe was fertig wurde
                    if cancel_task in done:
                        # Abbruch wurde angefordert
                        self.logger.info("Cancellation angefordert - breche alle Tasks ab")
                        gather_task.cancel()
                        
                        # ÄNDERUNG 21.06.2025: Aggressive Cancellation - breche ALLE laufenden Tasks ab
                        # Hinweis: search_tasks enthält Coroutines, nicht Tasks - skip diesen Teil
                        
                        # Warte kurz, damit die Tasks wirklich abbrechen
                        await asyncio.sleep(0.1)
                        
                        # Force-Cancel alle verbleibenden Tasks
                        try:
                            all_tasks = asyncio.all_tasks()
                        except AttributeError:
                            # Python < 3.9
                            all_tasks = asyncio.Task.all_tasks()
                        
                        for task in all_tasks:
                            if hasattr(task, 'done') and not task.done() and task != asyncio.current_task():
                                task.cancel()
                        
                        raise CancellationException("Suche vom Benutzer abgebrochen")
                    
                    results = await gather_task
                else:
                    # Normale Ausführung ohne Cancellation
                    results = await asyncio.wait_for(
                        self._gather_search_tasks(search_tasks),
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
            
            # ÄNDERUNG 21.06.2025: Speichere Ergebnisse in Datenbank
            if aggregated_results:
                self.logger.info(f"DEBUG: Speichere {len(aggregated_results)} Ergebnisse in Datenbank")
                for result in aggregated_results:
                    try:
                        # Hole oder erstelle Mine
                        # ÄNDERUNG 21.06.2025: Füge fehlenden languages Parameter hinzu
                        mine_id = self.db_manager.get_or_create_mine(
                            query.mine_name,
                            query.region,
                            query.country,
                            query.languages
                        )
                        
                        # Speichere Ergebnis
                        self.db_manager.add_result(
                            mine_id=mine_id,
                            agent_name=result.agent_name,
                            field_name=result.field_name,
                            value=result.value,
                            source=result.source,
                            source_url=result.source_url,
                            source_date=result.source_date,
                            confidence_score=result.confidence_score,
                            extra_data=result.metadata
                        )
                    except Exception as e:
                        self.logger.error(f"Fehler beim Speichern des Ergebnisses: {e}")
            
            if not phase_info:
                self._report_status(f"✅ Suche abgeschlossen: {len(aggregated_results)} finale Ergebnisse")
            return aggregated_results
        
        if not phase_info:
            self._report_status("❌ Keine Ergebnisse gefunden")
        return []
    
    async def _gather_search_tasks(self, tasks: List) -> List:
        """Helper method to gather search tasks with exception handling and batching"""
        # ÄNDERUNG 21.06.2025: Implementiere Batching für bessere Performance
        max_concurrent = 10  # Maximal 10 gleichzeitige Requests
        
        if len(tasks) <= max_concurrent:
            # Wenige Tasks - normal ausführen
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Viele Tasks - in Batches aufteilen
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            self.logger.debug(f"Führe Batch {i//max_concurrent + 1} mit {len(batch)} Tasks aus")
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            
            # Kurze Pause zwischen Batches
            if i + max_concurrent < len(tasks):
                await asyncio.sleep(0.5)
        
        return results
    
    async def _search_with_agent(self, agent: BaseAgent, query: MineQuery, cancellation_token=None) -> List[SearchResult]:
        """Führt Suche mit einem einzelnen Agenten aus"""
        try:
            # Log nur, zeige nicht im UI
            self.logger.info(f"Starte Suche mit Agent {agent.name}...")
            
            # ÄNDERUNG 21.06.2025: Wrapper mit Cancellation Support
            if cancellation_token:
                # Setze Cancellation Token im Agent
                agent.set_cancellation_token(cancellation_token)
                
                # Erstelle Agent-Task
                agent_task = asyncio.create_task(agent.execute_search(query))
                cancel_task = asyncio.create_task(cancellation_token.wait_for_cancellation())
                
                # Warte auf das erste fertige
                done, pending = await asyncio.wait(
                    [agent_task, cancel_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if cancel_task in done:
                    # Abbruch angefordert
                    self.logger.info(f"Agent {agent.name} wird abgebrochen...")
                    agent_task.cancel()
                    # Warte kurz für sauberen Abbruch
                    try:
                        await asyncio.wait_for(agent_task, timeout=1.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
                    return []
                
                # Agent war fertig
                results = await agent_task
            else:
                # Normale Ausführung
                results = await agent.execute_search(query)
            
            if results:
                self.logger.info(f"Agent {agent.name} lieferte {len(results)} Ergebnisse")
                # ÄNDERUNG 21.06.2025: Erweitere Logging für bessere Sichtbarkeit
                self._report_status(f"✅ {agent.name}: {len(results)} Ergebnisse gefunden")
                # Log erste Ergebnisse für Debugging
                for i, result in enumerate(results[:2]):
                    self.logger.debug(f"{agent.name} Ergebnis {i+1}: {result.field_name} = {result.value[:50]}...")
            else:
                self.logger.info(f"Agent {agent.name} fand keine Ergebnisse")
                self._report_status(f"❌ {agent.name}: Keine Ergebnisse")
                
            return results
        except asyncio.CancelledError:
            self.logger.info(f"Agent {agent.name} wurde abgebrochen")
            return []
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
        # ÄNDERUNG 21.06.2025: Erweiterte Debug-Ausgaben
        self.logger.info(f"DEBUG: set_active_agents aufgerufen mit: {agent_types}")
        self.logger.info(f"DEBUG: Verfügbare Agenten in self.agents: {list(self.agents.keys())}")
        
        self.active_agents = [a for a in agent_types if a in self.agents]
        
        filtered_out = [a for a in agent_types if a not in self.agents]
        if filtered_out:
            self.logger.warning(f"DEBUG: Folgende Agenten wurden rausgefiltert (nicht initialisiert): {filtered_out}")
        
        self.logger.info(f"DEBUG: Finale aktive Agenten: {self.active_agents} (von {len(agent_types)} angeforderten)")
    
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