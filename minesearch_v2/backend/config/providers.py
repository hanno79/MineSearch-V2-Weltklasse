"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Provider-Konfiguration für MineSearch
"""

from .api_keys import APIKeysConfig
from .models import (
    PERPLEXITY_MODELS,
    OPENROUTER_MODELS,
    ABACUS_MODELS,
    TAVILY_MODELS,
    EXA_MODELS,
    SCRAPINGBEE_MODELS,
    FIRECRAWL_MODELS,
    BRIGHTDATA_MODELS,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    GROK_MODELS,
    DEEPSEEK_MODELS
)

# Provider Konfiguration
# ÄNDERUNG 12.07.2025: Erweitert um Timeout-Konfigurationen und Retry-Mechanismus
PROVIDERS_CONFIG = {
    'perplexity': {
        'enabled': True,
        'api_key': APIKeysConfig.PERPLEXITY_API_KEY,
        'models': PERPLEXITY_MODELS,
        'timeout': 90,  # Schnelle Web-Search Provider
        'retry_attempts': 2,
        'retry_delay': 5
    },
    'openrouter': {
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,
        'base_url': 'https://openrouter.ai/api/v1',
        'models': OPENROUTER_MODELS,
        'timeout': 120,  # Standard für OpenRouter
        'retry_attempts': 3,
        'retry_delay': 10
    },
    'abacus': {
        'enabled': False,  # Deaktiviert bis API-Dokumentation verfügbar
        'api_key': APIKeysConfig.ABACUS_API_KEY,
        'base_url': 'https://api.abacus.ai',
        'models': ABACUS_MODELS
    },
    'tavily': {
        'enabled': True,  # Aktiviert für umfassende Tests
        'api_key': APIKeysConfig.TAVILY_API_KEY,
        'base_url': 'https://api.tavily.com',
        'models': TAVILY_MODELS,
        'timeout': 80,  # Schnell für Search Provider
        'retry_attempts': 2,
        'retry_delay': 5
    },
    'exa': {
        # ÄNDERUNG 09.07.2025: Deaktiviert wegen Domain-Format-Problemen
        'enabled': False,
        'api_key': APIKeysConfig.EXA_API_KEY,
        'base_url': 'https://api.exa.ai',
        'models': EXA_MODELS
    },
    'scrapingbee': {
        'enabled': True,
        'api_key': APIKeysConfig.SCRAPINGBEE_API_KEY,
        'base_url': 'https://app.scrapingbee.com/api/v1',
        'models': SCRAPINGBEE_MODELS,
        'timeout': 180,  # Langsam für Scraping
        'retry_attempts': 2,
        'retry_delay': 15
    },
    'firecrawl': {
        'enabled': True,
        'api_key': APIKeysConfig.FIRECRAWL_API_KEY,
        'base_url': 'https://api.firecrawl.dev/v1',
        'models': FIRECRAWL_MODELS,
        'timeout': 200,  # Langsam für Crawling
        'retry_attempts': 2,
        'retry_delay': 20
    },
    'brightdata': {
        'enabled': True,
        'api_key': APIKeysConfig.BRIGHTDATA_API_KEY,
        'base_url': 'https://api.brightdata.com',
        'models': BRIGHTDATA_MODELS,
        'timeout': 150,  # Mittel für BrightData
        'retry_attempts': 3,
        'retry_delay': 10
    },
    'openai': {
        'enabled': True,
        'api_key': APIKeysConfig.OPENAI_API_KEY,
        'base_url': 'https://api.openai.com/v1',
        'models': OPENAI_MODELS,
        'timeout': 140,  # Premium Provider - längere Timeouts
        'retry_attempts': 3,
        'retry_delay': 12
    },
    'anthropic': {
        'enabled': True,
        'api_key': APIKeysConfig.ANTHROPIC_API_KEY,
        'base_url': 'https://api.anthropic.com/v1',
        'models': ANTHROPIC_MODELS,
        'timeout': 150,  # Premium Provider - längere Timeouts
        'retry_attempts': 3,
        'retry_delay': 15
    },
    'gemini': {
        'enabled': True,
        'api_key': APIKeysConfig.GEMINI_API_KEY,
        'base_url': 'https://generativelanguage.googleapis.com/v1',
        'models': GEMINI_MODELS,
        'timeout': 120,  # Meist schnell, aber variabel
        'retry_attempts': 3,
        'retry_delay': 8
    },
    'grok': {
        'enabled': True,
        'api_key': APIKeysConfig.GROK_API_KEY,
        'base_url': 'https://api.x.ai/v1',
        'models': GROK_MODELS,
        'timeout': 180,  # Langsamer wegen Web-Access
        'retry_attempts': 2,
        'retry_delay': 20
    },
    'deepseek': {
        # ÄNDERUNG 09.07.2025: Deaktiviert um Duplikate zu vermeiden - DeepSeek-Modelle sind über OpenRouter verfügbar
        'enabled': False,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # DeepSeek nutzt OpenRouter als Proxy
        'base_url': 'https://openrouter.ai/api/v1',
        'models': DEEPSEEK_MODELS
    }
}