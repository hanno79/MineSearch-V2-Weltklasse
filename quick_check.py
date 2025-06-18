#!/usr/bin/env python
"""
Schnell-Check für MineSearch System
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.agents.factory import AgentFactory
from src.data.models import Base
from sqlalchemy import create_engine
import pandas as pd

print("=== MineSearch System Check ===\n")

# 1. Check Configuration
print("1. Konfiguration:")
try:
    config = Config()
    print("   ✓ Config geladen")
    print(f"   - Log Level: {config.log_level}")
    print(f"   - Max Concurrent: {config.max_concurrent_requests}")
except Exception as e:
    print(f"   ✗ Fehler: {e}")

# 2. Check API Keys
print("\n2. API Keys Status:")
api_status = {
    "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY")),
    "Perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
    "Tavily": bool(os.getenv("TAVILY_API_KEY")),
    "Exa": bool(os.getenv("EXA_API_KEY")),
    "Apify": bool(os.getenv("APIFY_API_KEY")),
    "ScrapingBee": bool(os.getenv("SCRAPINGBEE_API_KEY")),
    "Firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
    "Bright Data": bool(os.getenv("BRIGHTDATA_API_KEY"))
}

for service, has_key in api_status.items():
    status = "✓" if has_key else "✗"
    print(f"   {status} {service}")

# 3. Check Available Agents
print("\n3. Verfügbare Agenten:")
agents = AgentFactory.get_available_agents(config)
for agent_name, is_available in agents.items():
    status = "✓" if is_available else "✗"
    print(f"   {status} {agent_name}")

# 4. Check Database
print("\n4. Datenbank:")
try:
    engine = create_engine('sqlite:///data/minesearch.db')
    
    # Check tables
    with engine.connect() as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print(f"   ✓ Datenbank verbunden")
        print(f"   - Tabellen: {[t[0] for t in tables]}")
        
        # Count records
        for table in ['mines', 'searches', 'search_results']:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").scalar()
            print(f"   - {table}: {count} Einträge")
except Exception as e:
    print(f"   ✗ Fehler: {e}")

# 5. Check File Structure
print("\n5. Dateistruktur:")
required_dirs = ['data', 'data/input', 'data/output', 'data/temp', 'logs', 'config']
for dir_path in required_dirs:
    exists = os.path.exists(dir_path)
    status = "✓" if exists else "✗"
    print(f"   {status} {dir_path}/")

# 6. Check Dependencies
print("\n6. Wichtige Dependencies:")
try:
    import streamlit
    print("   ✓ Streamlit")
except:
    print("   ✗ Streamlit")

try:
    import playwright
    print("   ✓ Playwright")
except:
    print("   ✗ Playwright")

try:
    import pandas
    print("   ✓ Pandas")
except:
    print("   ✗ Pandas")

print("\n=== Check abgeschlossen ===")

# Summary
total_agents = len([a for a in agents.values() if a])
total_apis = len([a for a in api_status.values() if a])

print(f"\nZusammenfassung:")
print(f"- {total_agents}/{len(agents)} Agenten verfügbar")
print(f"- {total_apis}/{len(api_status)} API Keys konfiguriert")
print(f"- Datenbank: {'✓ OK' if 'engine' in locals() else '✗ Fehler'}")

if total_agents == 0:
    print("\n⚠️  WARNUNG: Keine Agenten verfügbar! Bitte API Keys in .env eintragen.")
elif total_agents == 1:
    print("\n📝 HINWEIS: Nur Scraper Agent verfügbar (benötigt keine API Keys).")
else:
    print("\n✅ System bereit für erweiterte Suchen!")