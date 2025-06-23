"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Import-Wrapper für refaktoriertes premium_mining_research Modul
"""

# ÄNDERUNG 22.06.2025: Modul in kleinere Komponenten aufgeteilt
# Re-exportiere alle Klassen vom refaktorierten Modul
from .premium_mining_research import (
    PremiumMiningResearch,
    ResearchPhase,
    ResearchMetadata,
    QualityIndicators,
    ResearchPhaseManager,
    QueryOptimizer
)

__all__ = [
    'PremiumMiningResearch',
    'ResearchPhase', 
    'ResearchMetadata',
    'QualityIndicators',
    'ResearchPhaseManager',
    'QueryOptimizer'
]