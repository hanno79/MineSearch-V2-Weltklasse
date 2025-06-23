"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Import-Wrapper für refaktoriertes deepseek_research Modul
"""

# ÄNDERUNG 22.06.2025: Modul in kleinere Komponenten aufgeteilt
# Re-exportiere alle Klassen vom refaktorierten Modul
from .deepseek_research import (
    DeepSeekResearchAgent,
    DeepSeekModel,
    ResearchStep,
    AdaptationStrategy,
    ResearchProcessor
)

__all__ = [
    'DeepSeekResearchAgent',
    'DeepSeekModel',
    'ResearchStep',
    'AdaptationStrategy',
    'ResearchProcessor'
]