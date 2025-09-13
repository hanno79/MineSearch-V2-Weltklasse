"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Provider-Konfiguration für MineSearch
"""

# DEFENSIVE IMPORT 15.07.2025: Verhindere AttributeError bei APIKeysConfig
try:
    from minesearch.config.api_keys import APIKeysConfig
except ImportError as e:
    print(f"WARNING: Could not import APIKeysConfig: {e}")
    # Fallback APIKeysConfig - Premium LLM Keys über OpenRouter verfügbar
    import os
    class APIKeysConfig:
        PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
        OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
        TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
        EXA_API_KEY = os.getenv('EXA_API_KEY', '')
        SCRAPINGBEE_API_KEY = os.getenv('SCRAPINGBEE_API_KEY', '')
        FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')
        BRIGHTDATA_API_KEY = os.getenv('BRIGHTDATA_API_KEY', '')
        # Premium LLM Keys über OpenRouter verfügbar - nicht mehr direkt benötigt
        # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        # ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
        # GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        # GROK_API_KEY = os.getenv('GROK_API_KEY', '')
        # DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

from minesearch.config.models import (
    PERPLEXITY_MODELS,
    OPENROUTER_MODELS,
    TAVILY_MODELS,
    EXA_MODELS,
    SCRAPINGBEE_MODELS,
    FIRECRAWL_MODELS,
    BRIGHTDATA_MODELS,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    GROK_MODELS,
    DEEPSEEK_MODELS  # REAKTIVIERT: DeepSeek als separater Provider
)

# Provider Konfiguration
# ÄNDERUNG 12.07.2025: Erweitert um Timeout-Konfigurationen und Retry-Mechanismus
PROVIDERS_CONFIG = {
    'perplexity': {
        # AKTIVIERT: Perplexity als separater Premium-Provider (über OpenRouter geroutet)
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
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
        'timeout': 300,  # KORRIGIERT: Weitere Erhöhung für minimax-m1 Timeout-Problem
        'retry_attempts': 3,
        'retry_delay': 10
    },
    'tavily': {
        'enabled': True,  # Aktiviert für umfassende Tests
        'api_key': APIKeysConfig.TAVILY_API_KEY,
        'base_url': 'https://api.tavily.com',
        'models': TAVILY_MODELS,
        'timeout': 600,  # REALISTISCHE TIMEOUTS 01.09.2025: 10 Minuten für umfangreiche Mining-Recherchen
        'retry_attempts': 2,
        'retry_delay': 5
    },
    'exa': {
        # PROVIDER-FIX 15.07.2025: Aktiviert für Exa Neural Search
        'enabled': True,
        'api_key': APIKeysConfig.EXA_API_KEY,
        'base_url': 'https://api.exa.ai',
        'models': EXA_MODELS,
        'timeout': 600,  # REALISTISCHE TIMEOUTS 01.09.2025: 10 Minuten für umfangreiche Neural Search
        'retry_attempts': 2,
        'retry_delay': 10
    },
    'scrapingbee': {
        'enabled': True,
        'api_key': APIKeysConfig.SCRAPINGBEE_API_KEY,
        'openrouter_api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Für AI-Extraktion
        'base_url': 'https://app.scrapingbee.com/api/v1',
        'models': SCRAPINGBEE_MODELS,
        'timeout': 180,  # Langsam für Scraping
        'retry_attempts': 2,
        'retry_delay': 15
    },
    'firecrawl': {
        'enabled': True,
        'api_key': APIKeysConfig.FIRECRAWL_API_KEY,
        'openrouter_api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Für AI-Extraktion
        'base_url': 'https://api.firecrawl.dev/v1',
        'models': FIRECRAWL_MODELS,
        'timeout': 200,  # Langsam für Crawling
        'retry_attempts': 2,
        'retry_delay': 20
    },
    'brightdata': {
        'enabled': True,
        'api_key': APIKeysConfig.BRIGHTDATA_API_KEY,
        'openrouter_api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Für AI-Extraktion
        'base_url': 'https://api.brightdata.com',
        'models': BRIGHTDATA_MODELS,
        'timeout': 150,  # Mittel für BrightData
        'retry_attempts': 3,
        'retry_delay': 10
    },
    'openai': {
        # AKTIVIERT 15.01.2025: Separate OpenAI-Kategorie für bessere Übersicht
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
        'models': OPENAI_MODELS,
        'timeout': 140,  # Premium Provider - längere Timeouts
        'retry_attempts': 3,
        'retry_delay': 12
    },
    'anthropic': {
        # AKTIVIERT 15.01.2025: Separate Anthropic-Kategorie für bessere Übersicht
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
        'models': ANTHROPIC_MODELS,
        'timeout': 150,  # Premium Provider - längere Timeouts
        'retry_attempts': 3,
        'retry_delay': 15
    },
    'gemini': {
        # AKTIVIERT 15.01.2025: Separate Google/Gemini-Kategorie für bessere Übersicht
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
        'models': GEMINI_MODELS,
        'timeout': 120,  # Meist schnell, aber variabel
        'retry_attempts': 3,
        'retry_delay': 8
    },
    'grok': {
        # AKTIVIERT: Grok als separater Premium-Provider (über OpenRouter geroutet)
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
        'models': GROK_MODELS,
        'timeout': 180,  # Langsamer wegen Web-Access
        'retry_attempts': 2,
        'retry_delay': 20
    },
    'deepseek': {
        # AKTIVIERT: DeepSeek als separater Premium-Provider (über OpenRouter geroutet)
        'enabled': True,
        'api_key': APIKeysConfig.OPENROUTER_API_KEY,  # Über OpenRouter geroutet
        'base_url': 'https://openrouter.ai/api/v1',
        'models': DEEPSEEK_MODELS,
        'timeout': 120,  # Mittlere Geschwindigkeit
        'retry_attempts': 2,
        'retry_delay': 15
    }
}
