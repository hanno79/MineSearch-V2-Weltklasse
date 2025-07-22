"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Test ob API-Keys korrekt geladen werden
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.base import Config
from pathlib import Path

print("=== API KEY TEST ===")
print(f"\nAktuelles Verzeichnis: {os.getcwd()}")
print(f"ENV Pfad in config.py: {Path(__file__).parent.parent / '.env'}")

# Prüfe ob .env existiert
env_path = Path(__file__).parent.parent / '.env'
print(f"\n.env existiert: {env_path.exists()}")
print(f".env Pfad: {env_path.absolute()}")

# Zeige geladene Keys (versteckt für Sicherheit)
print("\nGeladene API-Keys:")
print(f"PERPLEXITY_API_KEY: {'✓' if Config.PERPLEXITY_API_KEY else '✗'} ({len(Config.PERPLEXITY_API_KEY)} Zeichen)")
print(f"OPENROUTER_API_KEY: {'✓' if Config.OPENROUTER_API_KEY else '✗'} ({len(Config.OPENROUTER_API_KEY)} Zeichen)")
print(f"SCRAPINGBEE_API_KEY: {'✓' if Config.SCRAPINGBEE_API_KEY else '✗'} ({len(Config.SCRAPINGBEE_API_KEY)} Zeichen)")
print(f"FIRECRAWL_API_KEY: {'✓' if Config.FIRECRAWL_API_KEY else '✗'} ({len(Config.FIRECRAWL_API_KEY)} Zeichen)")
print(f"BRIGHTDATA_API_KEY: {'✓' if Config.BRIGHTDATA_API_KEY else '✗'} ({len(Config.BRIGHTDATA_API_KEY)} Zeichen)")

# Zeige erste/letzte Zeichen zur Verifikation
if Config.SCRAPINGBEE_API_KEY:
    print(f"\nScrapingBee Key Start: {Config.SCRAPINGBEE_API_KEY[:10]}...")
    print(f"ScrapingBee Key Ende: ...{Config.SCRAPINGBEE_API_KEY[-10:]}")

if Config.FIRECRAWL_API_KEY:
    print(f"\nFirecrawl Key Start: {Config.FIRECRAWL_API_KEY[:10]}...")
    print(f"Firecrawl Key Ende: ...{Config.FIRECRAWL_API_KEY[-10:]}")

print("\n=== PROVIDER CONFIG ===")
for provider_name, provider_config in Config.PROVIDERS.items():
    if provider_config.get('enabled'):
        api_key = provider_config.get('api_key', '')
        print(f"{provider_name}: {'✓' if api_key else '✗'} API-Key ({len(api_key)} Zeichen)")