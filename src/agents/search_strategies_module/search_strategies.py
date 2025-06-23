"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für flexible Such-Strategien
"""

from typing import List, Dict, Optional, Any
from .models import SearchStrategy, SearchScope, SearchDepth, SearchProgress, SearchResult
from .strategy_builder import StrategyBuilder
from .adaptive_strategies import AdaptiveSearchManager


class SearchStrategies:
    """
    Verwaltung flexibler Such-Strategien
    
    - Adaptiv: Passt sich an verschiedene Szenarien an
    - Effizient: Optimiert Zeit und Ressourcen
    - Flexibel: Keine hardcodierten Annahmen
    """
    
    def __init__(self):
        self.builder = StrategyBuilder()
        self.adaptive_manager = AdaptiveSearchManager()
        self.strategies = self.builder.build_default_strategies()
        self.active_strategy = None
        self.search_history = []
        
    def select_strategy(self, mine_name: str, country: str, region: str,
                       required_fields: List[str], available_agents: List[str],
                       time_constraint: Optional[int] = None) -> SearchStrategy:
        """
        Wählt die beste Strategie basierend auf Kontext
        
        Vollständig dynamisch - keine hardcodierten Annahmen!
        """
        # Analysiere Anforderungen
        analysis = self.builder.analyze_requirements(
            mine_name, country, region, required_fields
        )
        
        # Berücksichtige Zeit-Constraint
        if time_constraint:
            suitable_strategies = [
                s for s in self.strategies.values()
                if s.time_budget <= time_constraint
            ]
        else:
            suitable_strategies = list(self.strategies.values())
        
        # Score Strategien
        strategy_scores = {}
        for strategy in suitable_strategies:
            score = self.builder.score_strategy(
                strategy, analysis, available_agents
            )
            strategy_scores[strategy.name] = (score, strategy)
        
        # Wähle beste Strategie
        if strategy_scores:
            best_strategy = max(
                strategy_scores.values(),
                key=lambda x: x[0]
            )[1]
        else:
            # Fallback zu Standard
            best_strategy = self.strategies["standard_search"]
        
        self.active_strategy = best_strategy
        return best_strategy
    
    def adapt_strategy(self, current_results: List[Any], 
                      time_elapsed: float) -> Optional[SearchStrategy]:
        """
        Passt Strategie basierend auf bisherigen Ergebnissen an
        
        Ermöglicht dynamische Anpassung während der Suche
        """
        if not self.active_strategy:
            return None
        
        return self.adaptive_manager.adapt_strategy(
            self.active_strategy, current_results, time_elapsed
        )
    
    def get_site_recommendations(self, field_type: str) -> List[str]:
        """
        Gibt feldspezifische Website-Empfehlungen zurück
        
        Dynamisch und erweiterbar - keine hardcodierten Annahmen!
        """
        return self.builder.get_site_recommendations(field_type)
    
    def get_keyword_strategy_params(self, strategy_type: str) -> Dict[str, Any]:
        """Gibt Parameter für Keyword-Strategie zurück"""
        return self.builder.get_keyword_strategy_params(strategy_type)
    
    def log_strategy_performance(self, strategy: SearchStrategy, 
                                results_count: int, time_taken: float,
                                quality_score: float):
        """Protokolliert Strategie-Performance für Lernen"""
        self.search_history.append({
            "strategy": strategy.name,
            "results": results_count,
            "time": time_taken,
            "quality": quality_score,
            "efficiency": results_count / time_taken if time_taken > 0 else 0
        })
    
    def get_specialized_queries(self, mine_name: str, fields: List[str], 
                               region: str, country: str, 
                               languages: List[str]) -> List[Dict[str, Any]]:
        """Erstellt spezialisierte Suchanfragen basierend auf Feldern"""
        return self.builder.create_specialized_queries(
            mine_name, fields, region, country, languages
        )
    
    def get_progress(self, current_results: int, elapsed_time: float) -> SearchProgress:
        """Gibt aktuellen Such-Fortschritt zurück"""
        if not self.active_strategy:
            return SearchProgress(
                total_agents=0,
                completed_agents=0,
                total_results=0,
                elapsed_time=0,
                estimated_time_remaining=0,
                current_phase="idle"
            )
        
        return self.adaptive_manager.calculate_progress(
            self.active_strategy, current_results, elapsed_time
        )
    
    def finalize_search(self, all_results: List[Any], total_time: float) -> SearchResult:
        """Finalisiert Suche und erstellt Zusammenfassung"""
        if not self.active_strategy:
            return SearchResult(
                strategy_name="unknown",
                total_results=0,
                unique_results=0,
                quality_score=0.0,
                execution_time=total_time,
                agents_used=[],
                fields_covered=[]
            )
        
        # Sammle Statistiken
        unique_sources = set()
        agents_used = set()
        fields_covered = set()
        
        for result in all_results:
            if hasattr(result, 'source'):
                unique_sources.add(result.source)
            if hasattr(result, 'agent'):
                agents_used.add(result.agent)
            if hasattr(result, 'fields'):
                fields_covered.update(result.fields)
        
        quality_score = self.adaptive_manager.assess_result_quality(all_results)
        
        return SearchResult(
            strategy_name=self.active_strategy.name,
            total_results=len(all_results),
            unique_results=len(unique_sources),
            quality_score=quality_score,
            execution_time=total_time,
            agents_used=list(agents_used),
            fields_covered=list(fields_covered)
        )