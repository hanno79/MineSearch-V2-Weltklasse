"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Adaptive Such-Strategien für dynamische Anpassung
"""

from typing import List, Optional, Any, Dict
from .models import SearchStrategy, SearchDepth, SearchProgress


class AdaptiveSearchManager:
    """Verwaltet adaptive Anpassungen von Such-Strategien"""
    
    def adapt_strategy(self, current_strategy: SearchStrategy,
                      current_results: List[Any], 
                      time_elapsed: float) -> Optional[SearchStrategy]:
        """
        Passt Strategie basierend auf bisherigen Ergebnissen an
        
        Ermöglicht dynamische Anpassung während der Suche
        """
        # Analysiere bisherige Ergebnisse
        result_quality = self.assess_result_quality(current_results)
        remaining_time = current_strategy.time_budget - time_elapsed
        
        # Entscheide über Anpassung
        if result_quality < 0.3 and remaining_time > 60:
            # Schlechte Ergebnisse - intensiviere
            return self._intensify_strategy(current_strategy)
        elif result_quality > 0.8 and remaining_time < 60:
            # Gute Ergebnisse und wenig Zeit - beende früh
            return self._simplify_strategy(current_strategy)
        
        return None
    
    def assess_result_quality(self, results: List[Any]) -> float:
        """Bewertet Qualität der bisherigen Ergebnisse"""
        if not results:
            return 0.0
        
        # Vereinfachte Qualitätsbewertung
        # (würde in Praxis komplexer sein)
        quality_indicators = {
            "high_confidence": sum(1 for r in results if hasattr(r, 'confidence_score') and r.confidence_score > 0.8),
            "diverse_sources": len(set(r.source for r in results if hasattr(r, 'source'))),
            "total_results": len(results)
        }
        
        quality_score = 0.0
        
        if quality_indicators["total_results"] > 0:
            quality_score += min(quality_indicators["high_confidence"] / quality_indicators["total_results"], 1.0) * 0.5
            quality_score += min(quality_indicators["diverse_sources"] / 10, 1.0) * 0.3
            quality_score += min(quality_indicators["total_results"] / 50, 1.0) * 0.2
        
        return quality_score
    
    def calculate_progress(self, strategy: SearchStrategy,
                         current_results: int, elapsed_time: float) -> SearchProgress:
        """Berechnet aktuellen Such-Fortschritt"""
        # Schätze basierend auf Strategie-Typ
        estimated_total_agents = len(strategy.agent_preferences)
        if strategy.agent_preferences[0] == "all":
            estimated_total_agents = 15  # Geschätzte Anzahl verfügbarer Agenten
        
        # Schätze abgeschlossene Agenten basierend auf Zeit
        progress_percentage = min(elapsed_time / strategy.time_budget, 1.0)
        completed_agents = int(estimated_total_agents * progress_percentage)
        
        # Schätze verbleibende Zeit
        if progress_percentage > 0:
            estimated_total_time = elapsed_time / progress_percentage
            estimated_time_remaining = max(estimated_total_time - elapsed_time, 0)
        else:
            estimated_time_remaining = strategy.time_budget
        
        # Bestimme aktuelle Phase
        if progress_percentage < 0.1:
            current_phase = "initialization"
        elif progress_percentage < 0.3:
            current_phase = "early_search"
        elif progress_percentage < 0.7:
            current_phase = "main_search"
        elif progress_percentage < 0.9:
            current_phase = "deep_search"
        else:
            current_phase = "finalization"
        
        return SearchProgress(
            total_agents=estimated_total_agents,
            completed_agents=completed_agents,
            total_results=current_results,
            elapsed_time=elapsed_time,
            estimated_time_remaining=estimated_time_remaining,
            current_phase=current_phase
        )
    
    def _intensify_strategy(self, strategy: SearchStrategy) -> SearchStrategy:
        """Intensiviert eine Such-Strategie"""
        # Erhöhe Such-Tiefe
        new_depth = SearchDepth.DEEP
        if strategy.depth == SearchDepth.DEEP:
            new_depth = SearchDepth.EXHAUSTIVE
        elif strategy.depth == SearchDepth.EXHAUSTIVE:
            # Bereits maximal - keine weitere Intensivierung
            return strategy
        
        # Erweitere Agent-Präferenzen
        enhanced_agents = strategy.agent_preferences.copy()
        if "claude" not in enhanced_agents:
            enhanced_agents.append("claude")
        if "gpt4" not in enhanced_agents:
            enhanced_agents.append("gpt4")
        if "brightdata" not in enhanced_agents:
            enhanced_agents.append("brightdata")
        
        intensified = SearchStrategy(
            name=f"{strategy.name} (Intensified)",
            scope=strategy.scope,
            depth=new_depth,
            time_budget=int(strategy.time_budget * 1.5),
            agent_preferences=enhanced_agents,
            keyword_strategy="comprehensive",
            parallel_searches=min(strategy.parallel_searches * 2, 30),
            retry_strategy={
                "max_retries": strategy.retry_strategy["max_retries"] + 2,
                "backoff": strategy.retry_strategy["backoff"]
            }
        )
        return intensified
    
    def _simplify_strategy(self, strategy: SearchStrategy) -> SearchStrategy:
        """Vereinfacht eine Such-Strategie"""
        simplified = SearchStrategy(
            name=f"{strategy.name} (Simplified)",
            scope=strategy.scope,
            depth=SearchDepth.SHALLOW,
            time_budget=60,
            agent_preferences=strategy.agent_preferences[:2],
            keyword_strategy="focused",
            parallel_searches=5,
            retry_strategy={
                "max_retries": 1,
                "backoff": 1
            }
        )
        return simplified
    
    def suggest_next_action(self, current_progress: SearchProgress,
                          result_quality: float) -> str:
        """Schlägt nächste Aktion basierend auf aktuellem Status vor"""
        if current_progress.current_phase == "initialization":
            return "continue_initialization"
        
        if result_quality < 0.3:
            if current_progress.current_phase in ["early_search", "main_search"]:
                return "expand_search_scope"
            else:
                return "try_alternative_sources"
        
        if result_quality > 0.7:
            if current_progress.estimated_time_remaining < 60:
                return "finalize_search"
            else:
                return "refine_results"
        
        return "continue_current_strategy"
    
    def optimize_parallel_searches(self, current_load: int,
                                 available_resources: int) -> int:
        """Optimiert Anzahl paralleler Suchen basierend auf Ressourcen"""
        # Einfache Optimierung basierend auf verfügbaren Ressourcen
        if available_resources > 20:
            return min(current_load * 2, 30)
        elif available_resources > 10:
            return current_load
        else:
            return max(int(current_load * 0.7), 3)
    
    def get_retry_recommendations(self, failed_attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gibt Empfehlungen für Wiederholungsversuche"""
        if not failed_attempts:
            return {"retry": False, "reason": "no_failures"}
        
        # Analysiere Fehlermuster
        error_types = {}
        for attempt in failed_attempts:
            error_type = attempt.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Empfehlungen basierend auf Fehlertypen
        if error_types.get("timeout", 0) > 2:
            return {
                "retry": True,
                "reason": "multiple_timeouts",
                "strategy": "increase_timeout",
                "timeout_multiplier": 2.0
            }
        
        if error_types.get("rate_limit", 0) > 0:
            return {
                "retry": True,
                "reason": "rate_limiting",
                "strategy": "exponential_backoff",
                "initial_delay": 5,
                "max_delay": 60
            }
        
        if error_types.get("connection", 0) > 1:
            return {
                "retry": True,
                "reason": "connection_issues",
                "strategy": "alternative_agent",
                "max_retries": 1
            }
        
        # Standard-Empfehlung
        return {
            "retry": True,
            "reason": "standard_retry",
            "strategy": "linear_backoff",
            "delay": 2,
            "max_retries": 3
        }