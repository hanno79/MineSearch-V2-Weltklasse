"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Import-Wrapper für refaktoriertes search_strategies Modul
"""

# ÄNDERUNG 22.06.2025: Modul in kleinere Komponenten aufgeteilt
# Re-exportiere alle Klassen vom refaktorierten Modul
from .search_strategies_module import (
    SearchStrategies,
    SearchStrategy,
    SearchScope,
    SearchDepth,
    StrategyBuilder,
    AdaptiveSearchManager,
    SearchProgress,
    SearchResult
)

__all__ = [
    'SearchStrategies',
    'SearchStrategy',
    'SearchScope',
    'SearchDepth',
    'StrategyBuilder',
    'AdaptiveSearchManager',
    'SearchProgress',
    'SearchResult'
]