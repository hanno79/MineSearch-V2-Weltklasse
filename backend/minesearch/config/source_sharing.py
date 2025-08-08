"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Source Sharing und Cache Konfiguration
"""

# Cache-Konfiguration
CACHE_CONFIG = {
    'max_size': 100,  # Maximale Anzahl Cache-Einträge
    'default_ttl': 3600,  # 1 Stunde Standard TTL
    'deep_research_ttl': 7200  # 2 Stunden für Deep Research
}

# Performance-Optimierungen für Source Sharing
SOURCE_SHARING_CONFIG = {
    'enabled': True,
    'max_urls_per_provider': 10,  # Limitiere URLs pro Provider
    'phase1_timeout': 30,  # Timeout für Phase 1 in Sekunden
    'phase2_timeout': 60,  # Timeout für Phase 2 in Sekunden
    'parallel_requests': 5,  # Maximale parallele Requests pro Provider
    'cache_sources': True,  # Cache gefundene Quellen
    'source_cache_ttl': 21600,  # 6 Stunden
    'dedupe_strategy': 'url_normalize',  # Strategie für Deduplizierung
    'max_total_sources': 30,  # Maximale Gesamtanzahl Quellen
    'source_ranking': True,  # Ranke Quellen nach Relevanz
    'batch_size': 5  # Batch-Größe für Provider-Anfragen
}