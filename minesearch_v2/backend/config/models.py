"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Model-Konfigurationen für alle Provider
"""

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
    'cypher-alpha-free': {
        'id': 'openrouter/cypher-alpha:free',
        'name': 'Cypher Alpha (Kostenlos)',
        'timeout': 60,
        'max_tokens': 3000,
        'description': 'Kostenloses experimentelles Modell für Mining-Datenextraktion',
        'supports_web_search': False,
        'is_free': True
    },
    'minimax-m1': {
        'id': 'minimax/minimax-m1',
        'name': 'MiniMax M1',
        'timeout': 90,
        'max_tokens': 5000,
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
    }
}

# Abacus Modelle
ABACUS_MODELS = {
    'deep-agent': {
        'id': 'deep-agent',
        'name': 'Deep Agent Research',
        'timeout': 300,
        'max_tokens': 10000,
        'description': 'Deep Research Agent für umfassende Mining-Analysen',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    }
}

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

# ÄNDERUNG 06.07.2025: Premium LLM Modelle für verbesserte Restaurationskosten-Extraktion

# OpenAI Modelle
OPENAI_MODELS = {
    'o3-deep-research': {
        'id': 'o3-deep-research',
        'name': 'O3 Deep Research',
        'timeout': 300,
        'max_tokens': 16000,
        'description': 'Maximale Intelligenz für komplexe Research-Aufgaben',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    },
    'gpt-4.1': {
        'id': 'gpt-4.1-2025-04-14',
        'name': 'GPT-4.1 (April 2025)',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Beste Performance für komplexe Finanzanalysen',
        'supports_web_search': False,
        'supports_deep_research': False,
        'is_free': False
    },
    'o3': {
        # ÄNDERUNG 10.07.2025: O3 ist noch nicht veröffentlicht, nutze GPT-4 Turbo als Fallback
        'id': 'gpt-4-turbo-2024-04-09',
        'name': 'O3 (GPT-4 Turbo Fallback)',
        'timeout': 180,
        'max_tokens': 12000,
        'description': 'O3 noch nicht verfügbar - nutzt GPT-4 Turbo als Fallback',
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
    }
}

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
        'id': 'claude-opus-4-20250514',
        'name': 'Claude Opus 4',
        'timeout': 180,
        'max_tokens': 12000,
        'description': 'Maximum Intelligence für komplexe Mining-Dokumente',
        'supports_web_search': False,
        'supports_deep_research': True,
        'is_free': False
    }
}

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
    }
}

# xAI Grok Modelle
GROK_MODELS = {
    'grok-3': {
        'id': 'grok-3',
        'name': 'Grok 3',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Real-time Informationen mit X/Twitter Integration',
        'supports_web_search': True,
        'supports_deep_research': False,
        'is_free': False
    },
    'grok-3-mini': {
        'id': 'grok-3-mini',
        'name': 'Grok 3 Mini',
        'timeout': 60,
        'max_tokens': 4000,
        'description': 'Kosteneffiziente Version',
        'supports_web_search': True,
        'is_free': False
    },
    'grok-3-fast': {
        'id': 'grok-3-fast',
        'name': 'Grok 3 Fast',
        'timeout': 30,
        'max_tokens': 2000,
        'description': 'Ultra-schnelle Suche mit Web-Zugriff',
        'supports_web_search': True,
        'is_free': False
    }
}

# ÄNDERUNG 06.07.2025: DeepSeek Modelle hinzugefügt
# DeepSeek Modelle (via OpenRouter)
DEEPSEEK_MODELS = {
    'deepseek-chat': {
        'id': 'deepseek/deepseek-chat',
        'name': 'DeepSeek Chat',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Fortgeschrittenes Chat-Modell mit gutem Reasoning',
        'supports_web_search': False,
        'supports_deep_research': False,
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
    }
}

# Zusammenführung aller Modelle für einfachen Zugriff
MODELS_CONFIG = {
    'perplexity': PERPLEXITY_MODELS,
    'openrouter': OPENROUTER_MODELS,
    'abacus': ABACUS_MODELS,
    'tavily': TAVILY_MODELS,
    'exa': EXA_MODELS,
    'scrapingbee': SCRAPINGBEE_MODELS,
    'firecrawl': FIRECRAWL_MODELS,
    'brightdata': BRIGHTDATA_MODELS,
    'openai': OPENAI_MODELS,
    'anthropic': ANTHROPIC_MODELS,
    'gemini': GEMINI_MODELS,
    'grok': GROK_MODELS,
    'deepseek': DEEPSEEK_MODELS
}