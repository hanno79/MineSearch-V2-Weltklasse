"""
Compact Models Configuration
Kompakte Version der Model-Konfigurationen

Author: MineSearch Development Team
Date: 2025-01-11
"""

# Hilfsfunktionen zur Normalisierung von Model-Konfigurationen
def _apply_defaults_to_models(models_dict, provider_category_default=None, default_supports_web_search=False):
    """Wende Standardwerte auf Model-Konfigurationen an"""
    for _model_key, _model in models_dict.items():
        if not isinstance(_model, dict):
            continue
        
        # Erkenne "free"-Modelle heuristisch
        _key_l = str(_model_key).lower()
        _id_l = str(_model.get("id", '')).lower()
        _name_l = str(_model.get("name", '')).lower()
        _desc_l = str(_model.get("description", '')).lower()
        _is_free_marker = (
            ':free' in _id_l or '-free' in _key_l or 'free' in _key_l or 'free' in _name_l
            or 'kostenlos' in _name_l or 'kostenfrei' in _name_l or 'gratis' in _name_l
            or 'kostenlos' in _desc_l or 'kostenfrei' in _desc_l or 'gratis' in _desc_l
        )
        
        # Pflicht-/Basisfelder sicherstellen
        _model.setdefault('id', None)
        _model.setdefault('name', None)
        _model.setdefault('timeout', None)
        _model.setdefault('max_tokens', None)
        _model.setdefault('supports_web_search', default_supports_web_search)
        _model.setdefault('is_free', _is_free_marker)
        _model.setdefault('cost_per_token', 0.0 if _is_free_marker else 0.001)
        _model.setdefault('provider_category', provider_category_default)
        _model.setdefault('description', '')
        _model.setdefault('capabilities', [])
        _model.setdefault('rate_limits', {})
        
    return models_dict


# Provider-Kategorien
PROVIDER_CATEGORIES = {
    'openai': 'openai',
    'anthropic': 'anthropic', 
    'google': 'google',
    'meta': 'meta',
    'openrouter': 'openrouter',
    'perplexity': 'perplexity',
    'tavily': 'tavily',
    'exa': 'exa',
    'firecrawl': 'firecrawl',
    'brightdata': 'brightdata',
    'scrapingbee': 'scrapingbee'
}

# Basis-Model-Konfigurationen
BASE_MODELS = {
    'openai': {
        'gpt-4o': {
            'id': 'gpt-4o',
            'name': 'GPT-4o',
            'description': 'OpenAI GPT-4o Model',
            'max_tokens': 4096,
            'supports_web_search': False,
            'is_free': False,
            'cost_per_token': 0.005,
            'capabilities': ['text_generation', 'reasoning']
        },
        'gpt-3.5-turbo': {
            'id': 'gpt-3.5-turbo',
            'name': 'GPT-3.5 Turbo',
            'description': 'OpenAI GPT-3.5 Turbo Model',
            'max_tokens': 4096,
            'supports_web_search': False,
            'is_free': False,
            'cost_per_token': 0.001,
            'capabilities': ['text_generation']
        }
    },
    'anthropic': {
        'claude-3-5-sonnet': {
            'id': 'claude-3-5-sonnet',
            'name': 'Claude 3.5 Sonnet',
            'description': 'Anthropic Claude 3.5 Sonnet',
            'max_tokens': 4096,
            'supports_web_search': False,
            'is_free': False,
            'cost_per_token': 0.003,
            'capabilities': ['text_generation', 'reasoning']
        }
    },
    'perplexity': {
        'llama-3.1-sonar': {
            'id': 'llama-3.1-sonar',
            'name': 'Llama 3.1 Sonar',
            'description': 'Perplexity Llama 3.1 Sonar with web search',
            'max_tokens': 4096,
            'supports_web_search': True,
            'is_free': False,
            'cost_per_token': 0.001,
            'capabilities': ['text_generation', 'web_search']
        }
    }
}

# Erweiterte Model-Konfigurationen
EXTENDED_MODELS = {
    'openrouter': {
        'meta-llama/llama-3.1-8b-instruct:free': {
            'id': 'meta-llama/llama-3.1-8b-instruct:free',
            'name': 'Llama 3.1 8B Instruct (Free)',
            'description': 'Free Llama 3.1 8B Instruct via OpenRouter',
            'max_tokens': 4096,
            'supports_web_search': False,
            'is_free': True,
            'cost_per_token': 0.0,
            'capabilities': ['text_generation']
        }
    },
    'tavily': {
        'tavily-search': {
            'id': 'tavily-search',
            'name': 'Tavily Search',
            'description': 'Tavily web search API',
            'max_tokens': 1000,
            'supports_web_search': True,
            'is_free': False,
            'cost_per_token': 0.001,
            'capabilities': ['web_search']
        }
    }
}

# Kombiniere alle Modelle
ALL_MODELS = {}
for provider, models in {**BASE_MODELS, **EXTENDED_MODELS}.items():
    ALL_MODELS[provider] = _apply_defaults_to_models(models, provider)

# Standard-Modell
DEFAULT_MODEL = 'openai:gpt-3.5-turbo'

# Kostenlose Modelle
FREE_MODELS = []
for provider, models in ALL_MODELS.items():
    for model_id, model_config in models.items():
        if model_config.get('is_free', False):
            FREE_MODELS.append(f"{provider}:{model_id}")

# Web-Search-fähige Modelle
WEB_SEARCH_MODELS = []
for provider, models in ALL_MODELS.items():
    for model_id, model_config in models.items():
        if model_config.get('supports_web_search', False):
            WEB_SEARCH_MODELS.append(f"{provider}:{model_id}")

# Spezifische Provider-Modelle für Import-Kompatibilität
PERPLEXITY_MODELS = ALL_MODELS.get('perplexity', {})
OPENROUTER_MODELS = ALL_MODELS.get('openrouter', {})
TAVILY_MODELS = ALL_MODELS.get('tavily', {})
EXA_MODELS = ALL_MODELS.get('exa', {})
BRIGHTDATA_MODELS = ALL_MODELS.get('brightdata', {})
SCRAPINGBEE_MODELS = ALL_MODELS.get('scrapingbee', {})
FIRECRAWL_MODELS = ALL_MODELS.get('firecrawl', {})
GEMINI_MODELS = ALL_MODELS.get('gemini', {})
ANTHROPIC_MODELS = ALL_MODELS.get('anthropic', {})
OPENAI_MODELS = ALL_MODELS.get('openai', {})
GROK_MODELS = ALL_MODELS.get('grok', {})
DEEPSEEK_MODELS = ALL_MODELS.get('deepseek', {})

# Alias für Kompatibilität
MODELS_CONFIG = ALL_MODELS

# Exportiere alle Konfigurationen
__all__ = [
    'ALL_MODELS', 'DEFAULT_MODEL', 'FREE_MODELS', 'WEB_SEARCH_MODELS',
    'PROVIDER_CATEGORIES', '_apply_defaults_to_models', 'MODELS_CONFIG',
    'PERPLEXITY_MODELS', 'OPENROUTER_MODELS', 'TAVILY_MODELS', 'EXA_MODELS',
    'BRIGHTDATA_MODELS', 'SCRAPINGBEE_MODELS', 'FIRECRAWL_MODELS', 'GEMINI_MODELS',
    'ANTHROPIC_MODELS', 'OPENAI_MODELS', 'GROK_MODELS', 'DEEPSEEK_MODELS'
]
