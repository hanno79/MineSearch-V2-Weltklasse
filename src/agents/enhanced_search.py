"""
Author: rahn
Datum: 18.06.2025
Version: 2.1
Beschreibung: Enhanced search queries for deep mining information retrieval with dynamic source discovery
ÄNDERUNG 22.06.2025: Refaktoriert in Module unter enhanced_search/
"""

# Re-export alle Funktionen für Rückwärtskompatibilität
from .enhanced_search import (
    get_mining_search_queries,
    get_mining_domains,
    get_country_specific_domains,
    get_source_types,
    get_document_search_patterns,
    get_multilingual_queries,
    create_geographic_constraints,
    _create_geographic_constraints
)

__all__ = [
    'get_mining_search_queries',
    'get_mining_domains',
    'get_country_specific_domains',
    'get_source_types',
    'get_document_search_patterns',
    'get_multilingual_queries',
    'create_geographic_constraints',
    '_create_geographic_constraints'
]