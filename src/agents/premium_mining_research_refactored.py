"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Refactored Premium Mining Research System
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from .base_agent import BaseAgent, MineQuery, SearchResult
from .premium_components.phase_executor import PhaseExecutor
from .premium_components.result_aggregator import ResultAggregator
from .premium_components.research_phases import ResearchPhaseManager
from src.core.logger import get_logger


class PremiumMiningResearch(BaseAgent):
    """
    Refactored Premium Mining Research System
    
    Aufgeteilt in:
    - PhaseExecutor: Führt Research-Phasen aus
    - ResultAggregator: Aggregiert und konsolidiert Ergebnisse
    - ResearchPhaseManager: Verwaltet Research-Phasen
    """
    
    def __init__(self, name: str, config: Dict[str, Any], agents: Dict[str, BaseAgent] = None):
        super().__init__(name, config)
        self.agents = agents or {}
        self.logger = get_logger(f"agent.{name}", agent_type="premium_research")
        
        # Komponenten initialisieren
        self.phase_manager = ResearchPhaseManager()
        self.phase_executor = PhaseExecutor(self.agents, self.logger)
        self.result_aggregator = ResultAggregator(self.logger)
        
        # Caches
        self.results_cache = {}
        self.source_cache = {}
    
    async def initialize(self) -> bool:
        """Initialisiert den Premium Research Agent"""
        try:
            # Komponenten initialisieren
            await self.phase_executor.initialize()
            
            self.logger.info("Premium Mining Research erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialisierungsfehler: {e}")
            return False
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """BaseAgent kompatible Such-Methode"""
        research_result = await self.research_mine(query)
        
        # Konvertiere zu SearchResult Format
        return self._convert_to_search_results(research_result, query)
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search() - BaseAgent Kompatibilität"""
        return await self.search(query)
    
    async def validate_credentials(self) -> bool:
        """Validiert Credentials - Premium Research braucht keine spezielle Validierung"""
        return True
    
    async def research_mine(self, query: MineQuery) -> Dict[str, Any]:
        """
        Führt Premium-Recherche durch
        
        Koordiniert die verschiedenen Research-Phasen
        """
        research_id = self._generate_research_id(query)
        
        # Cache prüfen
        cache_key = query.get_cache_key()
        if cache_key in self.results_cache:
            self.logger.info(f"Cache Hit für {query.mine_name}")
            return self.results_cache[cache_key]
        
        self.logger.info(f"\n🚀 Starte Premium Mining Research für: {query.mine_name}")
        self.logger.info(f"Land: {query.country}, Region: {query.region}")
        
        start_time = datetime.now()
        all_results = []
        phase_results = {}
        
        try:
            # Research-Phasen durchführen
            phases = self.phase_manager.get_phases_for_query(query)
            
            for phase in phases:
                self.logger.info(f"\n📍 Phase: {phase.name}")
                
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Premium Research: {phase.name}")
                
                # Phase ausführen
                phase_result = await self.phase_executor.execute_phase(
                    phase=phase,
                    query=query,
                    previous_results=all_results,
                    source_cache=self.source_cache
                )
                
                # Ergebnisse sammeln
                phase_results[phase.name] = phase_result
                all_results.extend(phase_result.get('results', []))
                
                # Quellen-Cache aktualisieren
                if 'discovered_sources' in phase_result:
                    self._update_source_cache(query, phase_result['discovered_sources'])
                
                # Früh beenden wenn genug Ergebnisse
                if self._should_stop_early(all_results, query):
                    self.logger.info("Genügend Ergebnisse gefunden - beende früh")
                    break
            
            # Ergebnisse aggregieren
            final_result = await self.result_aggregator.aggregate_results(
                all_results=all_results,
                phase_results=phase_results,
                query=query,
                research_id=research_id
            )
            
            # Metadaten hinzufügen
            final_result['metadata'] = {
                'research_id': research_id,
                'duration': (datetime.now() - start_time).total_seconds(),
                'phases_completed': list(phase_results.keys()),
                'total_sources': len(self.source_cache.get(cache_key, {}))
            }
            
            # Cache speichern
            self.results_cache[cache_key] = final_result
            
            # Statistiken aktualisieren
            self._update_statistics(final_result)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Research-Fehler: {e}")
            return self._create_error_result(query, str(e))
    
    def _generate_research_id(self, query: MineQuery) -> str:
        """Generiert eindeutige Research-ID"""
        return f"{query.mine_name}_{query.country}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _update_source_cache(self, query: MineQuery, discovered_sources: Dict[str, Any]):
        """Aktualisiert Quellen-Cache"""
        cache_key = query.get_cache_key()
        
        if cache_key not in self.source_cache:
            self.source_cache[cache_key] = {}
        
        self.source_cache[cache_key].update(discovered_sources)
    
    def _should_stop_early(self, results: List[Any], query: MineQuery) -> bool:
        """Prüft ob früh gestoppt werden soll"""
        # Einfache Heuristik: Stoppe wenn alle required_fields gefunden
        if not query.required_fields:
            return False
        
        found_fields = set()
        for result in results:
            if hasattr(result, 'field_name'):
                found_fields.add(result.field_name)
        
        return len(found_fields) >= len(query.required_fields)
    
    def _convert_to_search_results(self, 
                                  research_result: Dict[str, Any],
                                  query: MineQuery) -> List[SearchResult]:
        """Konvertiert Research-Ergebnis zu SearchResult Liste"""
        search_results = []
        mine_data = research_result.get('mine_data', {})
        
        for field_name, field_data in mine_data.items():
            if isinstance(field_data, list):
                for item in field_data:
                    search_results.append(self._create_search_result(
                        query, field_name, item, research_result
                    ))
            else:
                search_results.append(self._create_search_result(
                    query, field_name, field_data, research_result
                ))
        
        return search_results
    
    def _create_search_result(self,
                            query: MineQuery,
                            field_name: str,
                            value: Any,
                            research_result: Dict[str, Any]) -> SearchResult:
        """Erstellt einzelnes SearchResult"""
        # Metadaten aus Research-Result extrahieren
        metadata = research_result.get('metadata', {})
        sources = research_result.get('sources', {})
        
        # Source-URL bestimmen
        source_url = None
        if field_name in sources:
            source_info = sources[field_name]
            if isinstance(source_info, dict):
                source_url = source_info.get('url')
            elif isinstance(source_info, list) and source_info:
                source_url = source_info[0].get('url') if isinstance(source_info[0], dict) else None
        
        return SearchResult(
            mine_name=query.mine_name,
            field_name=field_name,
            value=str(value),
            source="Premium Mining Research",
            source_url=source_url,
            source_date=datetime.now().year,
            confidence_score=0.85,
            agent_name=self.name,
            timestamp=datetime.now(),
            metadata={
                'research_id': metadata.get('research_id'),
                'phase': metadata.get('phase'),
                'extraction_method': metadata.get('extraction_method', 'premium_research')
            }
        )
    
    def _create_error_result(self, query: MineQuery, error: str) -> Dict[str, Any]:
        """Erstellt Fehler-Ergebnis"""
        return {
            'mine_data': {},
            'sources': {},
            'metadata': {
                'error': error,
                'mine_name': query.mine_name,
                'timestamp': datetime.now().isoformat()
            },
            'confidence_scores': {}
        }
    
    def _update_statistics(self, result: Dict[str, Any]):
        """Aktualisiert Agent-Statistiken"""
        self.stats['total_requests'] += 1
        
        mine_data = result.get('mine_data', {})
        if mine_data:
            self.stats['successful_requests'] += 1
            self.stats['total_fields_found'] += len(mine_data)
        else:
            self.stats['failed_requests'] += 1
    
    async def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Gibt Status einer laufenden Research zurück"""
        return self.phase_executor.get_execution_status(research_id)
    
    async def cancel_research(self, research_id: str) -> bool:
        """Bricht laufende Research ab"""
        return await self.phase_executor.cancel_execution(research_id)
    
    def clear_cache(self, mine_name: Optional[str] = None):
        """Leert Cache"""
        if mine_name:
            # Spezifische Mine
            keys_to_remove = [
                k for k in self.results_cache.keys()
                if mine_name in k
            ]
            for key in keys_to_remove:
                del self.results_cache[key]
                if key in self.source_cache:
                    del self.source_cache[key]
        else:
            # Gesamten Cache
            self.results_cache.clear()
            self.source_cache.clear()
        
        self.logger.info(f"Cache geleert für: {mine_name or 'alle'}")