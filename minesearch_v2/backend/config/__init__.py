"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Config Package für MineSearch
"""

from .base import Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from .api_keys import APIKeysConfig
from .providers import PROVIDERS_CONFIG
from .models import MODELS_CONFIG
from .country_config import COUNTRY_CONFIG
from .source_sharing import SOURCE_SHARING_CONFIG

# Zentrale Config-Instanz
config = Config()

# Re-exportiere wichtige Konfigurationen
__all__ = [
    'config',
    'Config',
    'CSV_COLUMNS',
    'FIELDS_WITHOUT_SOURCES',
    'APIKeysConfig',
    'PROVIDERS_CONFIG',
    'MODELS_CONFIG',
    'COUNTRY_CONFIG',
    'SOURCE_SHARING_CONFIG'
]