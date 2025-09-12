"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Config Package für MineSearch
"""

# ÄNDERUNG 06.07.2025: Load .env file before importing configs
from dotenv import load_dotenv
load_dotenv()

from minesearch.config.base import Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.config.api_keys import APIKeysConfig
from minesearch.config.providers import PROVIDERS_CONFIG
from minesearch.config.models import MODELS_CONFIG
from minesearch.config.country_config import COUNTRY_CONFIG
from minesearch.config.source_sharing import SOURCE_SHARING_CONFIG, CACHE_CONFIG

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
    'SOURCE_SHARING_CONFIG',
    'CACHE_CONFIG'
]
