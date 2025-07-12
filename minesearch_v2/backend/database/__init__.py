"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Datenbank-Modul für MineSearch v2 - Aufgeteilt aus database.py für bessere Wartbarkeit
"""

# Import all models
from .models import (
    Base,
    Source,
    Mine,
    SearchResult,
    ModelStatistics,
    FieldConsistency,
    ModelSummary,
    FieldStatistics
)

# Import connection functions
from .connection import init_db, get_db, get_session

# Import database manager
from .manager import DatabaseManager

# Create global database manager instance
db_manager = DatabaseManager()

# Convenience exports for backward compatibility
__all__ = [
    'Base',
    'Source',
    'Mine', 
    'SearchResult',
    'ModelStatistics',
    'FieldConsistency',
    'ModelSummary',
    'FieldStatistics',
    'init_db',
    'get_db',
    'get_session',
    'DatabaseManager',
    'db_manager'
]