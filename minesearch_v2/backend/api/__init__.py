"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: API Module für MineSearch v2
"""

from .routes import router
from .middleware import setup_middleware
from .startup import setup_startup_events
from .handlers import setup_exception_handlers

__all__ = ['router', 'setup_middleware', 'setup_startup_events', 'setup_exception_handlers']