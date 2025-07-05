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
        "timeout": 180,
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

# OpenRouter Modelle
OPENROUTER_MODELS = {
    'deepseek-free': {
        'id': 'deepseek/deepseek-chat',
        'name': 'DeepSeek Chat (Kostenlos)',
        'timeout': 120,
        'max_tokens': 3000,
        'description': 'Kostenloses Chat-Modell mit gutem Reasoning',
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
TAVILY_MODELS = {
    'search': {
        'id': 'tavily-search',
        'name': 'Tavily Search',
        'timeout': 60,
        'max_tokens': 5000,
        'description': 'Moderne KI-gestützte Websuche für aktuelle Informationen',
        'supports_web_search': True,
        'is_free': False
    },
    'deep-research': {
        'id': 'tavily-research',
        'name': 'Tavily Research',
        'timeout': 120,
        'max_tokens': 8000,
        'description': 'Tiefgehende Recherche mit mehreren Quellen',
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
        'id': 'exa-research',
        'name': 'Exa Research',
        'timeout': 120,
        'max_tokens': 10000,
        'description': 'Deep Research mit mehreren Suchen und umfassender Analyse',
        'supports_web_search': True,
        'supports_deep_research': True,
        'is_free': False
    },
    'research-pro': {
        'id': 'exa-research-pro',
        'name': 'Exa Research Pro',
        'timeout': 180,
        'max_tokens': 15000,
        'description': 'Maximale Qualität für komplexe Research-Aufgaben',
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

# Zusammenführung aller Modelle für einfachen Zugriff
MODELS_CONFIG = {
    'perplexity': PERPLEXITY_MODELS,
    'openrouter': OPENROUTER_MODELS,
    'abacus': ABACUS_MODELS,
    'tavily': TAVILY_MODELS,
    'exa': EXA_MODELS,
    'scrapingbee': SCRAPINGBEE_MODELS,
    'firecrawl': FIRECRAWL_MODELS,
    'brightdata': BRIGHTDATA_MODELS
}