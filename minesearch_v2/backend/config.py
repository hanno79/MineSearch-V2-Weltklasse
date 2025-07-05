"""
Author: rahn
Datum: 05.07.2025  
Version: 2.1
Beschreibung: Refactorierte Konfiguration - importiert aus config package
"""

# ÄNDERUNG 05.07.2025: Komplette Refaktorierung - alle Konfigurationen werden aus dem config package importiert
from config import (
    config,
    Config,
    CSV_COLUMNS,
    FIELDS_WITHOUT_SOURCES,
    PROVIDERS_CONFIG,
    MODELS_CONFIG,
    COUNTRY_CONFIG,
    SOURCE_SHARING_CONFIG
)

from config.source_sharing import CACHE_CONFIG

# Re-exportiere für Rückwärtskompatibilität
__all__ = [
    'config',
    'Config',
    'CSV_COLUMNS',
    'FIELDS_WITHOUT_SOURCES',
    'PROVIDERS_CONFIG',
    'MODELS_CONFIG',
    'COUNTRY_CONFIG',
    'SOURCE_SHARING_CONFIG',
    'CACHE_CONFIG'
]

# Legacy Support - für alten Code der direkt auf Config.PROVIDERS etc. zugreift
Config.PROVIDERS = PROVIDERS_CONFIG
Config.COUNTRY_CONFIGS = COUNTRY_CONFIG