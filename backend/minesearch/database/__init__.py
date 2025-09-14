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

# Lazy initialization - avoid creating database connection on import
_db_manager = None

def get_db_manager():
    """Get global database manager instance with lazy initialization"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# For backward compatibility - but prefer using get_db_manager()
def db_manager():
    """Backward compatibility function - returns database manager instance"""
    return get_db_manager()

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