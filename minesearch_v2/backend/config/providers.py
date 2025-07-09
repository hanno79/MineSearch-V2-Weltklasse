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
PROVIDERS_CONFIG = {
    'perplexity': {
        'enabled': True,
        'api_key': APIKeysConfig.PERPLEXITY_API_KEY,
        'models': PERPLEXITY_MODELS
    },
    'openrouter': {
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,
        'base_url': 'https://openrouter.ai/api/v1',
        'models': OPENROUTER_MODELS
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
        'models': TAVILY_MODELS
    },
    'exa': {
        'enabled': True,  # Aktiviert für umfassende Tests
        'api_key': APIKeysConfig.EXA_API_KEY,
        'base_url': 'https://api.exa.ai',
        'models': EXA_MODELS
    },
    'scrapingbee': {
        'enabled': True,
        'api_key': APIKeysConfig.SCRAPINGBEE_API_KEY,
        'base_url': 'https://app.scrapingbee.com/api/v1',
        'models': SCRAPINGBEE_MODELS
    },
    'firecrawl': {
        'enabled': True,
        'api_key': APIKeysConfig.FIRECRAWL_API_KEY,
        'base_url': 'https://api.firecrawl.dev/v1',
        'models': FIRECRAWL_MODELS
    },
    'brightdata': {
        'enabled': True,
        'api_key': APIKeysConfig.BRIGHTDATA_API_KEY,
        'base_url': 'https://api.brightdata.com',
        'models': BRIGHTDATA_MODELS
    },
    'openai': {
        'enabled': True,
        'api_key': APIKeysConfig.OPENAI_API_KEY,
        'base_url': 'https://api.openai.com/v1',
        'models': OPENAI_MODELS
    },
    'anthropic': {
        'enabled': True,
        'api_key': APIKeysConfig.ANTHROPIC_API_KEY,
        'base_url': 'https://api.anthropic.com/v1',
        'models': ANTHROPIC_MODELS
    },
    'gemini': {
        'enabled': True,
        'api_key': APIKeysConfig.GEMINI_API_KEY,
        'base_url': 'https://generativelanguage.googleapis.com/v1',
        'models': GEMINI_MODELS
    },
    'grok': {
        'enabled': True,
        'api_key': APIKeysConfig.GROK_API_KEY,
        'base_url': 'https://api.x.ai/v1',
        'models': GROK_MODELS
    },
    'deepseek': {
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # DeepSeek nutzt OpenRouter als Proxy
        'base_url': 'https://openrouter.ai/api/v1',
        'models': DEEPSEEK_MODELS
    }
}