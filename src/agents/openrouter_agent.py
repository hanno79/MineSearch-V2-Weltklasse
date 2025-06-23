"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: OpenRouter Agent - Refactored Import
"""

# ÄNDERUNG 22.06.2025: Import aus modularisierter Struktur
from .openrouter import OpenRouterAgent, OpenRouterModel

__all__ = ['OpenRouterAgent', 'OpenRouterModel']