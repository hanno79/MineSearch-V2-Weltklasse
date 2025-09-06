"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Model-Konfigurationen für alle Provider
"""

# Hilfsfunktionen zur Normalisierung von Model-Konfigurationen
def _apply_defaults_to_models(models_dict, provider_category_default=None, default_supports_web_search=False):
    for _model_key, _model in models_dict.items():
        if not isinstance(_model, dict):
            continue
        # Erkenne "free"-Modelle heuristisch aus Key/ID/Name/Beschreibung
        _key_l = str(_model_key).lower()
        _id_l = str(_model.get('id', '')).lower()
        _name_l = str(_model.get('name', '')).lower()
        _desc_l = str(_model.get('description', '')).lower()
        _is_free_marker = (
            ':free' in _id_l
            or '-free' in _key_l
            or 'free' in _key_l
            or 'free' in _name_l
            or 'kostenlos' in _name_l or 'kostenfrei' in _name_l or 'gratis' in _name_l
            or 'kostenlos' in _desc_l or 'kostenfrei' in _desc_l or 'gratis' in _desc_l
        )
        # Pflicht-/Basisfelder sicherstellen
        _model.setdefault('id', None)
        _model.setdefault('name', None)
        _model.setdefault('timeout', None)
        _model.setdefault('max_tokens', None)
        _model.setdefault('description', None)
        # Einheitliche optionale Felder mit Defaults
        _model.setdefault('supports_web_search', default_supports_web_search)
        _model['is_free'] = bool(_model.get('is_free', False) or _is_free_marker)
        _model.setdefault('provider_category', provider_category_default)
        _model.setdefault('supports_deep_research', False)

# Perplexity Modelle
PERPLEXITY_MODELS = {
    "sonar": {
        "id": "sonar",
        "name": "Basis Sonar (Schnell)",
        "timeout": 30,
        "max_tokens": 4000,
        "description": "Schnelle Suche mit guter Qualität"
    },
    "sonar-pro": {
        "id": "sonar-pro", 
        "name": "Sonar Pro (Empfohlen)",
        "timeout": 60,
        "max_tokens": 8000,
        "description": "Erweiterte Suche mit mehr Details und Quellen"
    },
    "sonar-deep-research": {
        "id": "sonar-deep-research",
        "name": "Deep Research",
        "timeout": 300,
        "max_tokens": 16000,
        "description": "Umfassende Recherche mit dutzenden Suchen und hunderten Quellen"
    },
    "sonar-reasoning": {
        "id": "sonar-reasoning",
        "name": "Sonar mit Reasoning",
        "timeout": 90,
        "max_tokens": 8000,
        "description": "Komplexe Analysen mit logischem Denken"
    }
}

# Normalisierung: fehlende Standardfelder für Perplexity-Modelle setzen
_apply_defaults_to_models(
    PERPLEXITY_MODELS,
    provider_category_default='perplexity',
    default_supports_web_search=True
)

# OpenRouter Modelle (DeepSeek wird jetzt separat geführt)
OPENROUTER_MODELS = {
    'deepseek-free': {
        'id': 'deepseek/deepseek-chat',
        'name': 'DeepSeek Chat (Kostenlos)',
        'timeout': 120,
        'max_tokens': 3000,
        'description': 'Kostenloses Chat-Modell mit gutem Reasoning',
        'supports_web_search': False,
        'is_free': True
    },
    'deepseek-chat': {
        'id': 'deepseek/deepseek-chat',
        'name': 'DeepSeek Chat',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Fortgeschrittenes Chat-Modell',
        'supports_web_search': False,
        'is_free': False
    },
    'deepseek-reasoner': {
        # ÄNDERUNG 09.07.2025: Korrigierte Model-ID für DeepSeek R1
        'id': 'deepseek/deepseek-r1-0528',
        'name': 'DeepSeek R1 (Reasoner) [BETA]',
        'timeout': 180,
        'max_tokens': 12000,
        'description': 'DeepSeek R1 - Experimentell: Niedriger Feldabdeckung, optimiert für Reasoning statt Datenextraktion',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    },
    # ÄNDERUNG 09.07.2025: Neue kostenlose OpenRouter-Modelle hinzugefügt
    'deepseek-chimera-free': {
        'id': 'tngtech/deepseek-r1t2-chimera:free',
        'name': 'DeepSeek R1 Chimera (Kostenlos)',
        'timeout': 120,
        'max_tokens': 4000,
        'description': 'Kostenlose DeepSeek R1 Chimera Variante für schnelle Mining-Analysen',
        'supports_web_search': False,
        'is_free': True
    },
    'mistral-small-free': {
        'id': 'mistralai/mistral-small-3.2-24b-instruct:free',
        'name': 'Mistral Small 3.2 (Kostenlos)',
        'timeout': 60,
        'max_tokens': 4000,
        'description': 'Kostenloses Mistral Small Modell - schnell und effizient',
        'supports_web_search': False,
        'is_free': True
    },
    # DEPRECATED 11.08.2025: horizon-beta entfernt - Modell deprecated
    'minimax-m1': {
        'id': 'minimax/minimax-m1',
        'name': 'MiniMax M1',
        'timeout': 180,  # FIXED 15.07.2025: Erhöhtes Timeout für langsamere Antworten
        'max_tokens': 6000,  # FIXED 15.07.2025: Erhöhte Token-Anzahl für umfassendere Extraktion
        'description': 'MiniMax M1 - Ausgewogenes Modell für Mining-Analysen',
        'supports_web_search': False,
        'is_free': True
    },
    'llama-3.3-nemotron-super': {
        'id': 'nvidia/llama-3.3-nemotron-super-49b-v1:free',
        'name': 'Llama 3.3 Nemotron Super 49B',
        'timeout': 90,
        'max_tokens': 8000,
        'description': 'NVIDIA Llama 3.3 Nemotron Super - Neuestes kostenloses NVIDIA-Modell',
        'supports_web_search': False,
        'is_free': True
    },
    'llama-3.1-nemotron-ultra': {
        'id': 'nvidia/llama-3.1-nemotron-ultra-253b-v1',  # WICHTIG: Ohne :free suffix!
        'name': 'Llama 3.1 Nemotron Ultra 253B',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'NVIDIA Llama 3.1 Nemotron Ultra - Hochleistungs-LLM mit 253B Parametern',
        'supports_web_search': False,
        'is_free': True
    },
    'kimi-k2': {
        'id': 'moonshotai/kimi-k2',
        'name': 'Kimi K2 (Kostenlos)',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Moonshot AI Kimi K2 - Kostenloses multilinguale Modell für Mining-Analysen',
        'supports_web_search': False,
        'is_free': True
    },
    # NEUE GLM-MODELLE 06.08.2025: Z-AI GLM-Serie hinzugefügt
    'glm-4.5': {
        'id': 'z-ai/glm-4.5',
        'name': 'GLM 4.5 (Z-AI)',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Z-AI GLM 4.5 - Hochleistungs-LLM für technische Mining-Analysen',
        'supports_web_search': False,
        'is_free': False
    },
    'glm-4.5-air-free': {
        'id': 'z-ai/glm-4.5-air:free',
        'name': 'GLM 4.5 Air (Kostenlos)',
        'timeout': 90,
        'max_tokens': 6000,
        'description': 'Z-AI GLM 4.5 Air - Kostenlose Version für schnelle Mining-Datenextraktion',
        'supports_web_search': False,
        'is_free': True
    },
    # NEUE OPENAI-MODELLE 06.08.2025: OpenAI OSS-Serie via OpenRouter
    'gpt-oss-20b': {
        'id': 'openai/gpt-oss-20b',
        'name': 'GPT OSS 20B',
        'timeout': 90,
        'max_tokens': 8000,
        'description': 'OpenAI GPT OSS 20B - Open Source Modell für Mining-Analysen',
        'supports_web_search': False,
        'is_free': False
    },
    'gpt-oss-120b': {
        'id': 'openai/gpt-oss-120b',
        'name': 'GPT OSS 120B',
        'timeout': 150,
        'max_tokens': 12000,
        'description': 'OpenAI GPT OSS 120B - Größtes Open Source Modell für komplexe Mining-Dokumente',
        'supports_web_search': False,
        'is_free': False
    },
    
    # ÄNDERUNG 24.08.2025: Premium-Modelle über OpenRouter - Anthropic Claude
    'claude-3.5-sonnet': {
        'id': 'anthropic/claude-3.5-sonnet-20241022',
        'name': 'Claude 3.5 Sonnet',
        'timeout': 180,
        'max_tokens': 8000,
        'description': 'Anthropic Claude 3.5 Sonnet - Top-Qualität für komplexe Mining-Analysen',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'anthropic'
    },
    'claude-3.5-haiku': {
        'id': 'anthropic/claude-3.5-haiku-20241022',
        'name': 'Claude 3.5 Haiku',
        'timeout': 90,
        'max_tokens': 6000,
        'description': 'Anthropic Claude 3.5 Haiku - Schnell und effizient für Mining-Daten',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'anthropic'
    },
    'claude-3-opus': {
        'id': 'anthropic/claude-3-opus',
        'name': 'Claude 3 Opus',
        'timeout': 240,
        'max_tokens': 10000,
        'description': 'Anthropic Claude 3 Opus - Höchste Qualität für komplexeste Mining-Dokumente',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'anthropic'
    },
    
    # AKTUALISIERT 06.09.2025: Neueste Google Gemini Modelle über OpenRouter
    'gemini-2.5-pro': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 Pro',
        'timeout': 180,
        'max_tokens': 10000,
        'description': 'Google Gemini 2.5 Pro - Neueste Generation für umfassende Mining-Analysen',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'gemini'
    },
    'gemini-2.5-flash': {
        'id': 'google/gemini-2.5-flash',
        'name': 'Gemini 2.5 Flash',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Google Gemini 2.5 Flash - Schnelle und präzise Mining-Datenverarbeitung',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'gemini'
    },
    'gemini-2.5-flash-lite': {
        'id': 'google/gemini-2.5-flash-lite',
        'name': 'Gemini 2.5 Flash Lite',
        'timeout': 90,
        'max_tokens': 6000,
        'description': 'Google Gemini 2.5 Flash Lite - Leichtgewichtig und effizient für Mining-Daten',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'gemini'
    },
    
    # ÄNDERUNG 24.08.2025: Premium-Modelle über OpenRouter - OpenAI GPT
    'gpt-4o': {
        'id': 'openai/gpt-4o',
        'name': 'GPT-4o',
        'timeout': 180,
        'max_tokens': 8000,
        'description': 'OpenAI GPT-4o - Neuestes multimodales Modell für Mining-Dokumentenanalyse',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'openai'
    },
    'gpt-4o-mini': {
        'id': 'openai/gpt-4o-mini',
        'name': 'GPT-4o Mini',
        'timeout': 90,
        'max_tokens': 6000,
        'description': 'OpenAI GPT-4o Mini - Kompakte Version für schnelle Mining-Datenextraktion',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'openai'
    },
    'gpt-4-turbo': {
        'id': 'openai/gpt-4-turbo',
        'name': 'GPT-4 Turbo',
        'timeout': 180,
        'max_tokens': 10000,
        'description': 'OpenAI GPT-4 Turbo - Erweiterte Version für komplexe Mining-Berichte',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'openai'
    },
    
    # AKTUALISIERT 06.09.2025: Neueste xAI Grok Modelle über OpenRouter
    'grok-3': {
        'id': 'x-ai/grok-3',
        'name': 'Grok 3',
        'timeout': 180,
        'max_tokens': 10000,
        'description': 'xAI Grok 3 - Neueste Generation mit verbesserter Mining-Datenextraktion',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'grok'
    },
    'grok-4': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4',
        'timeout': 200,
        'max_tokens': 12000,
        'description': 'xAI Grok 4 - Fortschrittlichstes Modell für komplexe Mining-Analysen',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'grok'
    },
    
    # ÄNDERUNG 24.08.2025: Premium-Modelle über OpenRouter - Perplexity
    'perplexity-sonar-pro': {
        'id': 'perplexity/sonar-pro',
        'name': 'Perplexity Sonar Pro',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Perplexity Sonar Pro - Web-basierte Mining-Recherche mit aktuellen Daten',
        'supports_web_search': True,
        'is_free': False,
        'provider_category': 'perplexity'
    },
    'perplexity-sonar': {
        'id': 'perplexity/sonar',
        'name': 'Perplexity Sonar',
        'timeout': 90,
        'max_tokens': 6000,
        'description': 'Perplexity Sonar - Schnelle web-basierte Mining-Suche',
        'supports_web_search': True,
        'is_free': False,
        'provider_category': 'perplexity'
    },
    
    # NEUE MODELLE 06.09.2025: Zusätzliche OpenRouter Modelle
    'mistral-codestral-2508': {
        'id': 'mistralai/codestral-2508',
        'name': 'Mistral Codestral 2508',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Mistral Codestral 2508 - Spezialisiert für Code und technische Dokumentation',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'mistral'
    },
    'hermes-4-405b': {
        'id': 'nousresearch/hermes-4-405b',
        'name': 'Hermes 4 405B',
        'timeout': 180,
        'max_tokens': 10000,
        'description': 'Nous Research Hermes 4 405B - Hochleistungsmodell für komplexe Analysen',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'nousresearch'
    },
    'qwen-3-max': {
        'id': 'qwen/qwen3-max',
        'name': 'Qwen 3 Max',
        'timeout': 150,
        'max_tokens': 8000,
        'description': 'Alibaba Qwen 3 Max - Fortschrittliches multilinguale Modell',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'qwen'
    },
    'kimi-k2-0905': {
        'id': 'moonshotai/kimi-k2-0905',
        'name': 'Kimi K2 0905',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Moonshot AI Kimi K2 0905 - Neueste Version mit verbesserten Fähigkeiten',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'moonshot'
    },
    'cogito-v2-preview': {
        'id': 'deepcogito/cogito-v2-preview-llama-109b-moe',
        'name': 'Cogito v2 Preview (109B MoE)',
        'timeout': 180,
        'max_tokens': 10000,
        'description': 'DeepCogito v2 Preview - 109B MoE Architektur für komplexe Reasoning',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'deepcogito'
    },
    'deepseek-chat-v3-1-free': {
        'id': 'deepseek/deepseek-chat-v3.1:free',
        'name': 'DeepSeek Chat v3.1 (Kostenlos)',
        'timeout': 120,
        'max_tokens': 4000,
        'description': 'DeepSeek Chat v3.1 - Neueste kostenlose Version mit verbesserter Performance',
        'supports_web_search': False,
        'is_free': True,
        'provider_category': 'deepseek'
    },
    'gpt-5-chat': {
        'id': 'openai/gpt-5-chat',
        'name': 'GPT-5 Chat',
        'timeout': 200,
        'max_tokens': 12000,
        'description': 'OpenAI GPT-5 Chat - Nächste Generation der GPT-Serie',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'openai'
    },
    'gpt-5': {
        'id': 'openai/gpt-5',
        'name': 'GPT-5',
        'timeout': 200,
        'max_tokens': 12000,
        'description': 'OpenAI GPT-5 - Neuestes Flaggschiff-Modell',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'openai'
    },
    'gpt-oss-120b-free': {
        'id': 'openai/gpt-oss-120b:free',
        'name': 'GPT OSS 120B (Kostenlos)',
        'timeout': 150,
        'max_tokens': 12000,
        'description': 'OpenAI GPT OSS 120B - Kostenlose Open Source Version',
        'supports_web_search': False,
        'is_free': True,
        'provider_category': 'openai'
    },
    'claude-opus-4-1': {
        'id': 'anthropic/claude-opus-4.1',
        'name': 'Claude Opus 4.1',
        'timeout': 240,
        'max_tokens': 12000,
        'description': 'Anthropic Claude Opus 4.1 - Erweiterte Version mit verbesserter Analyse',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False,
        'provider_category': 'anthropic'
    },
    'claude-sonnet-4': {
        'id': 'anthropic/claude-sonnet-4',
        'name': 'Claude Sonnet 4',
        'timeout': 180,
        'max_tokens': 8000,
        'description': 'Anthropic Claude Sonnet 4 - Neueste Sonnet-Generation',
        'supports_web_search': False,
        'is_free': False,
        'provider_category': 'anthropic'
    },
    'claude-3-7-sonnet-thinking': {
        'id': 'anthropic/claude-3.7-sonnet:thinking',
        'name': 'Claude 3.7 Sonnet (Thinking)',
        'timeout': 180,
        'max_tokens': 8000,
        'description': 'Anthropic Claude 3.7 Sonnet - Mit Thinking-Modus für komplexe Reasoning',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False,
        'provider_category': 'anthropic'
    }
}

# Normalisierung: fehlende Standardfelder für OpenRouter-Modelle setzen
_apply_defaults_to_models(
    OPENROUTER_MODELS,
    provider_category_default='openrouter',
    default_supports_web_search=False
)

# Abacus Modelle - ENTFERNT 02.09.2025: Abacus Provider komplett aus dem System entfernt
# ABACUS_MODELS = {
#     'deep-agent': {
#         'id': 'deep-agent',
#         'name': 'Deep Agent Research',
#         'timeout': 300,
#         'max_tokens': 10000,
#         'description': 'Deep Research Agent für umfassende Mining-Analysen',
#         'supports_web_search': True,
#         'supports_deep_research': True,
#         'is_free': False
#     }
# }

# Tavily Modelle
# WICHTIG: Tavily hat ein Query-Limit von 400 Zeichen
TAVILY_MODELS = {
    'search': {
        'id': 'tavily-search',
        'name': 'Tavily Search',
        'timeout': 60,
        'max_tokens': 5000,
        'description': 'Moderne KI-gestützte Websuche für aktuelle Informationen (400 Zeichen Query-Limit)',
        'supports_web_search': True,
        'is_free': False
    },
    'deep-research': {
        'id': 'tavily-research',
        'name': 'Tavily Research',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Tiefgehende Recherche mit mehreren Quellen (400 Zeichen Query-Limit)',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Tavily-Modelle setzen
_apply_defaults_to_models(
    TAVILY_MODELS,
    provider_category_default='tavily',
    default_supports_web_search=True
)

# Exa Modelle
EXA_MODELS = {
    'neural-search': {
        'id': 'exa-neural',
        'name': 'Exa Neural Search',
        'timeout': 60,
        'max_tokens': 5000,
        'description': 'Neuronale Suche für semantische Anfragen',
        'supports_web_search': True,
        'is_free': False
    },
    'research': {
        # ÄNDERUNG 09.07.2025: Research nutzt neural search mit erweiterten Parametern
        'id': 'neural',  # Nutze neural search endpoint
        'name': 'Exa Research (Neural Enhanced)',
        'timeout': 120,
        'max_tokens': 10000,
        'description': 'Erweiterte Neural Search mit Research-Fokus',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    },
    'research-pro': {
        # ÄNDERUNG 09.07.2025: Research Pro nutzt neural search mit maximalen Parametern
        'id': 'neural',  # Nutze neural search endpoint
        'name': 'Exa Research Pro (Neural Max)',
        'timeout': 180,
        'max_tokens': 15000,
        'description': 'Maximale Neural Search für komplexe Research-Aufgaben',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Exa-Modelle setzen
_apply_defaults_to_models(
    EXA_MODELS,
    provider_category_default='exa',
    default_supports_web_search=True
)

# ScrapingBee Modelle
SCRAPINGBEE_MODELS = {
    'basic-scrape': {
        'id': 'basic',
        'name': 'Basic Scraping (No JS)',
        'timeout': 30,
        'max_tokens': 10000,
        'description': 'Standard HTML-Scraping ohne JavaScript (1 Credit)',
        'supports_web_search': True,
        'is_free': False,
        'credits_cost': 1
    },
    'js-render': {
        'id': 'js-render',
        'name': 'JavaScript Rendering',
        'timeout': 60,
        'max_tokens': 10000,
        'description': 'Scraping mit JavaScript-Rendering (5 Credits)',
        'supports_web_search': True,
        'is_free': False,
        'credits_cost': 5
    },
    'ai-extract': {
        'id': 'ai-extract',
        'name': 'AI Data Extraction',
        'timeout': 90,
        'max_tokens': 10000,
        'description': 'AI-powered Datenextraktion (10 Credits)',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False,
        'credits_cost': 10
    }
}

# Normalisierung: fehlende Standardfelder für ScrapingBee-Modelle setzen
_apply_defaults_to_models(
    SCRAPINGBEE_MODELS,
    provider_category_default='scrapingbee',
    default_supports_web_search=True
)

# Firecrawl Modelle
FIRECRAWL_MODELS = {
    'scrape': {
        'id': 'scrape',
        'name': 'Single Page Scrape',
        'timeout': 60,
        'max_tokens': 50000,
        'description': 'Einzelseiten-Scraping mit Markdown-Konvertierung',
        'supports_web_search': True,
        'is_free': False
    },
    'crawl': {
        'id': 'crawl',
        'name': 'Website Crawl',
        'timeout': 300,
        'max_tokens': 100000,
        'description': 'Rekursives Website-Crawling für alle Unterseiten',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    },
    'extract': {
        'id': 'extract',
        'name': 'AI Extract (Beta)',
        'timeout': 120,
        'max_tokens': 50000,
        'description': 'AI-powered strukturierte Datenextraktion',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Firecrawl-Modelle setzen
_apply_defaults_to_models(
    FIRECRAWL_MODELS,
    provider_category_default='firecrawl',
    default_supports_web_search=True
)

# Brightdata Modelle
BRIGHTDATA_MODELS = {
    'web-scraper': {
        'id': 'web-scraper',
        'name': 'Web Scraper API',
        'timeout': 120,
        'max_tokens': 50000,
        'description': 'Standard Web Scraper mit Proxy-Rotation',
        'supports_web_search': True,
        'is_free': False
    },
    'browser-api': {
        'id': 'browser-api',
        'name': 'Browser Automation',
        'timeout': 180,
        'max_tokens': 100000,
        'description': 'Full Browser Automation mit CAPTCHA-Solving',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    },
    'serp': {
        'id': 'serp',
        'name': 'Search Engine Scraping',
        'timeout': 90,
        'max_tokens': 50000,
        'description': 'Google & andere Suchmaschinen-Scraping',
        'supports_web_search': True,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Brightdata-Modelle setzen
_apply_defaults_to_models(
    BRIGHTDATA_MODELS,
    provider_category_default='brightdata',
    default_supports_web_search=True
)

# ÄNDERUNG 06.07.2025: Premium LLM Modelle für verbesserte Restaurationskosten-Extraktion

# OpenAI Modelle
OPENAI_MODELS = {
    'o3-deep-research': {
        # KORRIGIERT 13.07.2025: O3 nicht verfügbar, nutze GPT-4o für Research
        'id': 'gpt-4o',
        'name': 'GPT-4o (O3 Deep Research Replacement)',
        'timeout': 300,
        'max_tokens': 16000,
        'description': 'GPT-4o als Research-Ersatz für nicht verfügbares O3',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    },
    'gpt-4.1': {
        # KORRIGIERT 13.07.2025: GPT-4.1 nicht verfügbar, nutze GPT-4o
        'id': 'gpt-4o',
        'name': 'GPT-4o (GPT-4.1 Replacement)',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'GPT-4o als Ersatz für nicht verfügbares GPT-4.1',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'o3': {
        # KORRIGIERT 13.07.2025: O3 nicht verfügbar, nutze korrekte GPT-4 Turbo Model-ID
        'id': 'gpt-4-turbo',
        'name': 'GPT-4 Turbo (O3 Replacement)',
        'timeout': 180,
        'max_tokens': 12000,
        'description': 'GPT-4 Turbo als Ersatz für nicht verfügbares O3',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'o4-mini': {
        'id': 'gpt-4o-mini',
        'name': 'GPT-4o Mini',
        'timeout': 60,
        'max_tokens': 4000,
        'description': 'Kosteneffiziente GPT-4 Variante für schnelle Mining-Analysen',
        'supports_web_search': False,
        'is_free': False
    },
    # MODEL-FIX 15.07.2025: Fehlende OpenAI-Modelle hinzugefügt
    'gpt-4o': {
        'id': 'gpt-4o',
        'name': 'GPT-4o',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'OpenAI GPT-4o - Neueste multimodale Generation',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gpt-4-turbo': {
        'id': 'gpt-4-turbo',
        'name': 'GPT-4 Turbo',
        'timeout': 90,
        'max_tokens': 8000,
        'description': 'OpenAI GPT-4 Turbo - Optimiert für schnelle Antworten',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gpt-3.5-turbo': {
        'id': 'gpt-3.5-turbo',
        'name': 'GPT-3.5 Turbo',
        'timeout': 60,
        'max_tokens': 4000,
        'description': 'OpenAI GPT-3.5 Turbo - Kosteneffizient für einfache Aufgaben',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gpt-3.5-turbo-16k': {
        'id': 'gpt-3.5-turbo-16k',
        'name': 'GPT-3.5 Turbo 16K',
        'timeout': 60,
        'max_tokens': 16000,
        'description': 'OpenAI GPT-3.5 Turbo mit erweiterten Kontext (16K Token)',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für OpenAI-Modelle setzen
_apply_defaults_to_models(
    OPENAI_MODELS,
    provider_category_default='openai',
    default_supports_web_search=False
)

# Anthropic Modelle
ANTHROPIC_MODELS = {
    'claude-sonnet-4': {
        'id': 'claude-sonnet-4-20250514',
        'name': 'Claude Sonnet 4',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Neueste Claude Generation für technische Analysen',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'claude-3.7-sonnet': {
        'id': 'claude-3-7-sonnet-latest',
        'name': 'Claude 3.7 Sonnet Latest',
        'timeout': 90,
        'max_tokens': 4000,
        'description': 'Schnellere Alternative mit gutem Preis-Leistungs-Verhältnis',
        'supports_web_search': False,
        'is_free': False
    },
    'claude-opus-4': {
        'id': 'claude-opus-4-1-20250805',
        'name': 'Claude Opus 4',
        'timeout': 180,
        'max_tokens': 12000,
        'description': 'Maximum Intelligence für komplexe Mining-Dokumente',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    },
    # MODEL-FIX 15.07.2025: Fehlende Anthropic-Modelle hinzugefügt
    'claude-3-haiku': {
        'id': 'claude-3-haiku-20240307',
        'name': 'Claude 3 Haiku',
        'timeout': 45,
        'max_tokens': 4000,
        'description': 'Schnellstes Claude-Modell für einfache Mining-Datenextraktion',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'claude-3-opus': {
        'id': 'claude-3-opus-20240229',
        'name': 'Claude 3 Opus',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Leistungsstärkstes Claude 3 Modell für komplexe Mining-Analysen',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Anthropic-Modelle setzen
_apply_defaults_to_models(
    ANTHROPIC_MODELS,
    provider_category_default='anthropic',
    default_supports_web_search=False
)

# Google Gemini Modelle
GEMINI_MODELS = {
    'gemini-2.5-pro': {
        'id': 'gemini-2.5-pro',
        'name': 'Gemini 2.5 Pro',
        'timeout': 180,
        'max_tokens': 30000,
        'description': '2M Token Kontext für große Dokumente, Multimodal',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gemini-2.5-flash': {
        'id': 'gemini-2.5-flash',
        'name': 'Gemini 2.5 Flash',
        'timeout': 60,
        'max_tokens': 10000,
        'description': 'Schnell und kosteneffizient',
        'supports_web_search': False,
        'is_free': False
    },
    'gemini-2.5-flash-lite': {
        'id': 'gemini-2.5-flash-lite-preview-06-17',
        'name': 'Gemini 2.5 Flash Lite Preview',
        'timeout': 30,
        'max_tokens': 5000,
        'description': 'Ultra-schnell für einfache Analysen',
        'supports_web_search': False,
        'is_free': False
    },
    # MODEL-FIX 15.07.2025: Fehlende Gemini-Modelle hinzugefügt
    'gemini-1.5-pro': {
        'id': 'gemini-1.5-pro',
        'name': 'Gemini 1.5 Pro',
        'timeout': 120,
        'max_tokens': 12000,
        'description': 'Google Gemini 1.5 Pro - Bewährtes Modell für komplexe Mining-Analysen',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gemini-1.5-flash': {
        'id': 'gemini-1.5-flash',
        'name': 'Gemini 1.5 Flash',
        'timeout': 60,
        'max_tokens': 8000,
        'description': 'Google Gemini 1.5 Flash - Schnell und kosteneffizient',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'gemini-2.0-flash': {
        'id': 'gemini-2.0-flash-experimental',
        'name': 'Gemini 2.0 Flash Experimental',
        'timeout': 60,
        'max_tokens': 8000,
        'description': 'Google Gemini 2.0 Flash - Experimentelle Version mit neuen Features',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    }
}

# Normalisierung: fehlende Standardfelder für Gemini-Modelle setzen
_apply_defaults_to_models(
    GEMINI_MODELS,
    provider_category_default='gemini',
    default_supports_web_search=False
)

# xAI Grok Modelle
GROK_MODELS = {
# ENTFERNT 02.09.2025: Doppelte Grok-Einträge mit falschen IDs - siehe Zeilen 300-319 für korrekte Konfiguration
    # DEPRECATED 11.08.2025: grok-2 entfernt - Modell deprecated
    # DEPRECATED 11.08.2025: grok-2-mini entfernt - Modell deprecated
    # DEPRECATED 11.08.2025: grok-beta entfernt - Modell deprecated
    # DEPRECATED 11.08.2025: grok-vision-beta entfernt - Modell deprecated
}

# Normalisierung: fehlende Standardfelder für Grok-Modelle setzen
_apply_defaults_to_models(
    GROK_MODELS,
    provider_category_default='grok',
    default_supports_web_search=True
)

# ENTFERNT 06.08.2025: DeepSeek-Duplikate eliminiert
# DeepSeek-Modelle werden nur noch über OpenRouter bereitgestellt

# Zusammenführung aller Modelle für einfachen Zugriff
# BEREINIGT 06.08.2025: DeepSeek-Duplikate entfernt
MODELS_CONFIG = {
    'perplexity': PERPLEXITY_MODELS,
    'openrouter': OPENROUTER_MODELS,
    # 'abacus': ABACUS_MODELS,  # ENTFERNT 02.09.2025: Abacus Provider komplett entfernt
    'tavily': TAVILY_MODELS,
    'exa': EXA_MODELS,
    'scrapingbee': SCRAPINGBEE_MODELS,
    'firecrawl': FIRECRAWL_MODELS,
    'brightdata': BRIGHTDATA_MODELS,
    'openai': OPENAI_MODELS,
    'anthropic': ANTHROPIC_MODELS,
    'gemini': GEMINI_MODELS,
    'grok': GROK_MODELS
    # 'deepseek': DEEPSEEK_MODELS  # ENTFERNT: Duplikate eliminiert, DeepSeek nur über OpenRouter
}