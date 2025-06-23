"""
Datenaggregator für Mining Research System
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from src.agents.base_agent import MineQuery, SearchResult
from src.agents.factory import AgentFactory
from src.core.config import Config
from src.core.database import get_db_manager
from src.core.scoring import ScoringEngine
from src.core.logger import get_logger, PerformanceLogger


class DataAggregator:
    """Koordiniert Agenten und aggregiert Ergebnisse"""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = get_db_manager()
        self.scoring_engine = ScoringEngine()
        self.logger = get_logger("data_aggregator")
        self.perf_logger = PerformanceLogger(self.logger)
        self.agents = {}
        
    async def initialize_agents(self, selected_agents: List[str]) -> Dict[str, Dict[str, Any]]:
        """Initialisiert ausgewählte Agenten und gibt Status zurück"""
        self.logger.info(f"Initialisiere Agenten: {selected_agents}")
        
        agent_status = {}
        
        # Prüfe ob Agenten ausgewählt wurden
        if not selected_agents:
            self.logger.warning("Keine Agenten ausgewählt")
            return agent_status
        
        for agent_type in selected_agents:
            try:
                # Handle OpenRouter model types
                if agent_type.startswith('openrouter_'):
                    model_name = agent_type.replace('openrouter_', '')
                    # Map to actual model IDs
                    model_map = {
                        'claude': 'anthropic/claude-3.5-sonnet-20241022',
                        'gpt4': 'openai/gpt-4o',
                        'deepseek': 'deepseek/deepseek-chat',
                        'qwen': 'qwen/qwen-2.5-72b-instruct',
                        'gemini': 'google/gemini-2.0-flash-exp:free'
                    }
                    model_id = model_map.get(model_name, 'deepseek/deepseek-chat')
                    agent = AgentFactory.create_agent(agent_type, self.config, model_id=model_id)
                else:
                    agent = AgentFactory.create_agent(agent_type, self.config)
                
                if agent:
                    initialized = await agent.initialize()
                    if initialized:
                        self.agents[agent_type] = agent
                        self.logger.info(f"Agent {agent_type} erfolgreich initialisiert")
                        agent_status[agent_type] = {
                            'status': 'active',
                            'message': 'Bereit'
                        }
                    else:
                        # Versuche spezifischen Fehler zu ermitteln
                        error_msg = await self._get_agent_error_details(agent, agent_type)
                        self.logger.warning(f"Agent {agent_type} konnte nicht initialisiert werden: {error_msg}")
                        agent_status[agent_type] = {
                            'status': 'failed',
                            'message': error_msg
                        }
                else:
                    agent_status[agent_type] = {
                        'status': 'failed',
                        'message': 'Agent konnte nicht erstellt werden'
                    }
                    
            except Exception as e:
                self.logger.error(f"Fehler bei Initialisierung von {agent_type}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                agent_status[agent_type] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return agent_status
    
    async def _get_agent_error_details(self, agent, agent_type: str) -> str:
        """Ermittelt spezifische Fehlerdetails für einen Agenten"""
        try:
            # Prüfe ob API-Key fehlt
            if hasattr(agent, 'api_key'):
                if not agent.api_key:
                    return "API-Key fehlt"
            
            # Versuche spezifische Validierung
            if hasattr(agent, 'validate_credentials'):
                # Mache einen erweiterten Test für verschiedene Agenten
                if hasattr(agent, '_session') and hasattr(agent, 'api_key'):
                    try:
                        # Tavily spezifisch
                        if agent_type == 'tavily':
                            payload = {
                                "api_key": agent.api_key,
                                "query": "test",
                                "max_results": 1
                            }
                            async with agent._session.post(
                                agent.base_url,
                                json=payload,
                                timeout=agent.timeout
                            ) as response:
                                if response.status == 429:
                                    return "Rate-Limit erreicht oder kein Budget mehr"
                                elif response.status == 401:
                                    return "Ungültiger API-Key"
                                elif response.status == 403:
                                    return "Zugriff verweigert - Möglicherweise kein Budget"
                                elif response.status != 200:
                                    text = await response.text()
                                    if "insufficient" in text.lower() or "quota" in text.lower() or "limit" in text.lower():
                                        return "Kein Budget mehr verfügbar"
                                    return f"API-Fehler: {response.status}"
                        
                        # Generische API-Fehlerbehandlung für andere Agenten
                        else:
                            # Versuche validate_credentials zu nutzen
                            result = await agent.validate_credentials()
                            if not result:
                                # Prüfe auf spezifische Fehlermeldungen im Logger
                                if hasattr(agent, 'logger'):
                                    return "API-Validierung fehlgeschlagen"
                                return "Credentials ungültig"
                    
                    except aiohttp.ClientError as e:
                        if "certificate" in str(e).lower():
                            return "SSL-Zertifikatsfehler"
                        return f"Verbindungsfehler: {type(e).__name__}"
                    except asyncio.TimeoutError:
                        return "Timeout - Service antwortet nicht"
                    except Exception as e:
                        error_str = str(e).lower()
                        if "rate" in error_str and "limit" in error_str:
                            return "Rate-Limit überschritten"
                        if "quota" in error_str or "budget" in error_str:
                            return "Kein Budget verfügbar"
                        if "unauthorized" in error_str or "forbidden" in error_str:
                            return "Keine Berechtigung - API-Key prüfen"
                        return f"Fehler: {str(e)[:100]}"
            
            return "Initialisierung fehlgeschlagen"
            
        except Exception as e:
            return f"Fehler bei Statusprüfung: {str(e)}"
    
    async def search_mine(self, mine_data: Dict[str, Any], 
                         selected_agents: Optional[List[str]] = None,
                         status_callback=None) -> Dict[str, Any]:
        """Führt Suche für eine Mine durch"""
        self.perf_logger.start_timer(f"search_{mine_data['name']}")
        
        # Erstelle oder hole Mine aus DB
        mine = self.db_manager.get_or_create_mine(
            name=mine_data['name'],
            region=mine_data['region'],
            country=mine_data['country'],
            languages=mine_data.get('languages', ['en'])
        )
        
        # Starte neuen Suchlauf
        agents_to_use = selected_agents or list(self.agents.keys())
        search = self.db_manager.create_search(
            mine_id=mine.id,
            agents=agents_to_use
        )
        
        # Erstelle Query
        query = MineQuery(
            mine_name=mine_data['name'],
            region=mine_data['region'],
            country=mine_data['country'],
            languages=mine_data.get('languages', ['en']),
            required_fields=mine_data.get('required_fields', [
                'betreiber', 'koordinaten', 'aktivitaetsstatus',
                'sanierungskosten', 'rohstofftyp', 'minentyp',
                'produktionsbeginn', 'jahresproduktion', 'minenflaeche'
            ])
        )
        
        # Set status callback for all agents
        if status_callback:
            for agent in self.agents.values():
                agent.status_callback = status_callback
        
        # Führe Suchen parallel aus
        search_tasks = []
        for agent_type, agent in self.agents.items():
            if agent_type in agents_to_use:
                search_tasks.append(
                    self._search_with_agent(agent, query, search.id, mine.id)
                )
        
        # Warte auf alle Ergebnisse
        all_results = []
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        for result in search_results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Suchfehler: {result}")
        
        # Aggregiere Ergebnisse
        aggregated = self.scoring_engine.aggregate_results(all_results)
        
        # Berechne Qualitätsmetriken
        metrics = self.scoring_engine.calculate_data_quality_metrics(aggregated)
        
        # Speichere aggregierte Daten
        if aggregated:
            self.db_manager.update_aggregated_data(
                mine_id=mine.id,
                aggregated_data=aggregated,
                quality_score=metrics['quality_score'],
                completeness_score=metrics['completeness_score']
            )
        
        # Markiere Suche als abgeschlossen
        self.db_manager.complete_search(search.id)
        
        self.perf_logger.end_timer(
            f"search_{mine_data['name']}",
            results_found=len(all_results),
            quality_score=metrics['quality_score']
        )
        
        return {
            'mine_id': mine.id,
            'search_id': search.id,
            'results': all_results,
            'aggregated': aggregated,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _search_with_agent(self, agent, query: MineQuery, 
                                search_id: int, mine_id: int) -> List[SearchResult]:
        """Führt Suche mit einzelnem Agent durch"""
        try:
            self.logger.info(f"Starte Suche mit {agent.name}")
            results = await agent.execute_search(query)
            
            # Speichere Ergebnisse in DB
            for result in results:
                self.db_manager.add_result(
                    search_id=search_id,
                    mine_id=mine_id,
                    result_data=result.to_dict()
                )
            
            self.logger.info(f"{agent.name} fand {len(results)} Ergebnisse")
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei {agent.name}: {e}")
            return []
    
    def aggregate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Aggregiert Suchergebnisse und entfernt Duplikate"""
        if not results:
            return []
        
        # Gruppiere nach field_name
        field_groups = {}
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        # Wähle bestes Ergebnis pro Feld
        aggregated = []
        for field_name, field_results in field_groups.items():
            # Sortiere nach Confidence Score
            sorted_results = sorted(field_results, key=lambda r: r.confidence_score, reverse=True)
            
            # Nimm das beste Ergebnis (höchster Confidence Score)
            best_result = sorted_results[0]
            
            # Optional: Merge mehrere Quellen für bessere Validierung
            if len(sorted_results) > 1:
                # Füge zusätzliche Quellen als Metadata hinzu
                additional_sources = []
                for r in sorted_results[1:3]:  # Max 2 zusätzliche Quellen
                    additional_sources.append({
                        'source': r.source,
                        'value': r.value,
                        'confidence': r.confidence_score
                    })
                best_result.metadata['additional_sources'] = additional_sources
            
            aggregated.append(best_result)
        
        return aggregated
    
    async def search_multiple_mines(self, mines_data: List[Dict[str, Any]], 
                                   selected_agents: Optional[List[str]] = None,
                                   max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Führt Suche für mehrere Minen durch"""
        results = []
        
        # Initialisiere Agenten einmal
        if not self.agents:
            await self.initialize_agents(selected_agents or self.config.get_active_agents())
        
        # Semaphore für Parallelität
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_limit(mine_data):
            async with semaphore:
                return await self.search_mine(mine_data, selected_agents)
        
        # Führe Suchen parallel aus
        search_tasks = [search_with_limit(mine) for mine in mines_data]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Filtere Fehler
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Fehler bei Mine {mines_data[i]['name']}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über alle Agenten zurück"""
        stats = {
            'agents': {},
            'total_searches': 0,
            'total_results': 0
        }
        
        for agent_type, agent in self.agents.items():
            agent_stats = agent.get_statistics()
            stats['agents'][agent_type] = agent_stats
            stats['total_searches'] += agent_stats['total_requests']
            stats['total_results'] += agent_stats['total_fields_found']
        
        return stats
    
    async def cleanup(self):
        """Cleanup aller Agenten"""
        cleanup_tasks = [agent.cleanup() for agent in self.agents.values()]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        self.logger.info("Alle Agenten beendet")