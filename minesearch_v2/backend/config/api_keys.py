"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: API Keys Konfiguration
"""

import os

class APIKeysConfig:
    """API Keys Konfiguration"""
    
    # AI Provider API Keys
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    ABACUS_API_KEY = os.getenv('ABACUS_API_KEY', '')
    
    # Search Provider API Keys
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
    EXA_API_KEY = os.getenv('EXA_API_KEY', '')
    
    # Scraping Provider API Keys
    SCRAPINGBEE_API_KEY = os.getenv('SCRAPINGBEE_API_KEY', '')
    FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')
    BRIGHTDATA_API_KEY = os.getenv('BRIGHTDATA_API_KEY', '')