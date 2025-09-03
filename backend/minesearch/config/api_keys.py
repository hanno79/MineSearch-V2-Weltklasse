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
    
    # DEAKTIVIERT 03.09.2025: Premium LLM Provider API Keys über OpenRouter verfügbar
    # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    # ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    # GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    # GROK_API_KEY = os.getenv('GROK_API_KEY', '')
    # DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    
    @classmethod
    def get_all_keys(cls):
        """Alle API-Keys als Dictionary zurückgeben - Premium LLM Keys über OpenRouter"""
        return {
            'PERPLEXITY_API_KEY': cls.PERPLEXITY_API_KEY,
            'OPENROUTER_API_KEY': cls.OPENROUTER_API_KEY,
            'ABACUS_API_KEY': cls.ABACUS_API_KEY,
            'TAVILY_API_KEY': cls.TAVILY_API_KEY,
            'EXA_API_KEY': cls.EXA_API_KEY,
            'SCRAPINGBEE_API_KEY': cls.SCRAPINGBEE_API_KEY,
            'FIRECRAWL_API_KEY': cls.FIRECRAWL_API_KEY,
            'BRIGHTDATA_API_KEY': cls.BRIGHTDATA_API_KEY
            # Premium LLM Keys (OpenAI, Anthropic, Gemini, Grok, DeepSeek) über OpenRouter verfügbar
        }
    
    @classmethod
    def validate_key(cls, key_name: str, key_value: str) -> bool:
        """Einzelnen API-Key validieren"""
        if not key_value or key_value.strip() == '':
            return False
        
        # Mindestlänge prüfen
        if len(key_value) < 10:
            return False
            
        # Spezielle Validierungen per Provider
        if key_name == 'OPENROUTER_API_KEY':
            return key_value.startswith('sk-or-')
        elif key_name == 'PERPLEXITY_API_KEY':
            return key_value.startswith('pplx-')
        # Premium LLM Keys werden nicht mehr direkt validiert (über OpenRouter verfügbar)
        
        return True
    
    @classmethod
    def get_missing_keys(cls):
        """Liste der fehlenden API-Keys zurückgeben"""
        missing_keys = []
        all_keys = cls.get_all_keys()
        
        for key_name, key_value in all_keys.items():
            if not cls.validate_key(key_name, key_value):
                missing_keys.append(key_name)
        
        return missing_keys
    
    @classmethod
    def validate_all_keys(cls):
        """Alle API-Keys validieren und Bericht erstellen - nur noch aktive Keys"""
        missing_keys = cls.get_missing_keys()
        
        if missing_keys:
            # Filter heraus: Premium LLM Keys die über OpenRouter verfügbar sind
            filtered_missing = [key for key in missing_keys 
                              if key not in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'GROK_API_KEY', 'DEEPSEEK_API_KEY']]
            
            if filtered_missing:
                print(f"⚠️  WARNUNG: Fehlende oder ungültige API-Keys: {', '.join(filtered_missing)}")
                print("   Bitte .env Datei prüfen und fehlende Keys hinzufügen.")
                print("   (Premium LLM Keys werden über OpenRouter bereitgestellt)")
                return False
        
        print("✅ Alle benötigten API-Keys sind gesetzt und gültig. Premium LLMs über OpenRouter verfügbar.")
        return True