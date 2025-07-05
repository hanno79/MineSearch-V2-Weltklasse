"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Result Combiner für Source Sharing Ergebnisse
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from source_aggregator import SourceAggregator
from search_phases import SearchPhaseManager

logger = logging.getLogger(__name__)


class SearchResultCombiner:
    """Kombiniert Ergebnisse aus verschiedenen Such-Phasen"""
    
    def __init__(self):
        self.phase_manager = SearchPhaseManager()
    
    def combine_source_sharing_results(self, phase1_results: List[Dict], model_ids: List[str],
                                     phase2_results: List[Dict], start_time: datetime,
                                     unique_sources: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Kombiniere Ergebnisse aus beiden Phasen des Source Sharing"""
        
        best_data = {}
        confidence_scores = {}
        all_results = {}
        
        # Verarbeite Phase 1 Ergebnisse
        for model_id, result in zip(model_ids, phase1_results):
            if isinstance(result, dict) and result.get('success'):
                all_results[f"{model_id}_phase1"] = result
        
        # Verarbeite Phase 2 Ergebnisse wenn vorhanden
        if phase2_results:
            for i, result in enumerate(phase2_results):
                if isinstance(result, dict) and result.get('success'):
                    # Finde entsprechendes model_id
                    if i < len(model_ids):
                        all_results[f"{model_ids[i]}_phase2"] = result
        
        # Aggregiere beste Daten mit Konfidenz-Scoring
        aggregator = SourceAggregator()
        for result_key, result in all_results.items():
            if result.get('data'):
                aggregator.add_provider_result(result_key, result)
        
        # Hole beste aggregierte Daten
        best_data = aggregator.get_best_data()
        confidence_scores = aggregator.get_confidence_scores()
        
        # Berechne Statistiken
        total_sources_found = len(unique_sources) if unique_sources else 0
        phase1_coverage = self.phase_manager.calculate_average_coverage(
            [r for r in phase1_results if isinstance(r, dict)]
        )
        phase2_coverage = self.phase_manager.calculate_average_coverage(
            [r for r in phase2_results if isinstance(r, dict)]
        ) if phase2_results else 0
        
        improvement = phase2_coverage - phase1_coverage if phase2_results else 0
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "search_type": "source_sharing",
            "phases_completed": 2 if phase2_results else 1,
            "models_used": len(model_ids),
            "total_sources": total_sources_found,
            "data": best_data,
            "confidence_scores": confidence_scores,
            "sources": unique_sources[:20] if unique_sources else [],
            "statistics": {
                "phase1_coverage": f"{phase1_coverage:.1f}%",
                "phase2_coverage": f"{phase2_coverage:.1f}%" if phase2_results else "N/A",
                "coverage_improvement": f"+{improvement:.1f}%" if improvement > 0 else "0%",
                "total_duration": f"{duration:.1f}s",
                "sources_per_provider": total_sources_found / len(model_ids) if model_ids else 0
            },
            "timestamp": datetime.now().isoformat()
        }