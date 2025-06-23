"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Enhanced search module für Mining-Informationen
"""

# Hauptexport der Query-Generierung
from .query_generator import get_mining_search_queries, _get_geographic_exclusions

# Domain-Verwaltung
from .domain_manager import (
    get_mining_domains,
    get_country_specific_domains
)

# Such-Strategien
from .search_strategies import (
    get_source_types,
    get_document_search_patterns,
    get_multilingual_queries,
    create_geographic_constraints
)

# ÄNDERUNG 22.06.2025: Für Kompatibilität alte private Funktion auch exportieren
_create_geographic_constraints = create_geographic_constraints

__all__ = [
    'get_mining_search_queries',
    'get_mining_domains',
    'get_country_specific_domains',
    'get_source_types',
    'get_document_search_patterns',
    'get_multilingual_queries',
    'create_geographic_constraints',
    '_create_geographic_constraints',  # Für Rückwärtskompatibilität
    '_get_geographic_exclusions'
]