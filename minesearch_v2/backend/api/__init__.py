"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: API Module für MineSearch v2
"""

# ÄNDERUNG 10.07.2025: Redundante startup.py entfernt - main.py nutzt eigene lifespan-Funktion
from .routes import router
from .middleware import setup_middleware
from .handlers import setup_exception_handlers

__all__ = ['router', 'setup_middleware', 'setup_exception_handlers']