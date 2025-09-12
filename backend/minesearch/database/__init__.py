"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Datenbank-Modul für MineSearch v2 - Aufgeteilt aus database.py für bessere Wartbarkeit
"""

# Import all models
from minesearch.database.models import (
    Base,
    Source,
    Mine,
    SearchResult,
    ModelStatistics,
    FieldConsistency,
    ModelSummary,
    FieldStatistics,
    ModelStatisticsComprehensive,
    ModelFieldConsistency
)

# Import connection functions
from minesearch.database.connection import init_db, get_db, get_session

# Import database manager
from minesearch.database.manager import DatabaseManager

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
    'ModelStatisticsComprehensive',
    'ModelFieldConsistency',
    'init_db',
    'get_db',
    'get_session',
    'DatabaseManager',
    'db_manager'
]
