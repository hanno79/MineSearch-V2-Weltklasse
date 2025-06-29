"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Test für Perplexity Implementation mit SessionManager
"""

import asyncio
import sys
import os

# Force reload of modules
if 'src.utils.session_manager' in sys.modules:
    del sys.modules['src.utils.session_manager']
# SimpleSessionManager wurde entfernt
if 'src.agents.perplexity_agent' in sys.modules:
    del sys.modules['src.agents.perplexity_agent']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.base_agent import MineQuery
from src.utils.session_manager import SESSION_MANAGER_VERSION

async def test_perplexity():
    print(f"🔧 Teste Perplexity mit SessionManager v{SESSION_MANAGER_VERSION}")
    
    # Config laden
    config = Config()
    
    # Agent erstellen
    agent = PerplexityAgent("test_perplexity", {'api_config': config.api})
    
    # Initialisieren
    print("📌 Initialisiere Agent...")
    success = await agent.initialize()
    print(f"✅ Initialisierung: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
    
    if not success:
        print("❌ Konnte Agent nicht initialisieren")
        return
    
    # Test-Query
    query = MineQuery(
        mine_name="Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en", "fr"],
        required_fields=["betreiber", "koordinaten"]
    )
    
    print("\n🔍 Führe Testsuche durch...")
    try:
        results = await agent.search_mine(query)
        print(f"✅ Suche abgeschlossen: {len(results)} Ergebnisse")
        
        for result in results[:3]:
            print(f"\n📋 Ergebnis: {result.field_name}")
            print(f"   Wert: {result.value}")
            print(f"   Quelle: {result.source}")
            
    except Exception as e:
        print(f"❌ Fehler bei Suche: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await agent.cleanup()
    print("\n✅ Test abgeschlossen")

if __name__ == "__main__":
    # Keine nest_asyncio!
    asyncio.run(test_perplexity())