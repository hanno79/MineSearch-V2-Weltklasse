"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Test Perplexity Agent in UI-ähnlichem Thread-Kontext
"""

import asyncio
import concurrent.futures
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.base_agent import MineQuery
from src.utils.session_manager import SessionManager

def run_in_new_loop(coro):
    """Simuliert StreamlitEventLoopManager Verhalten"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def test_perplexity_in_thread():
    """Test Perplexity Agent wie in UI"""
    print("🔧 Teste Perplexity in Thread-Kontext (simuliert UI)")
    
    # Config laden
    config = Config()
    
    # SessionManager erstellen
    session_manager = SessionManager()
    
    # Config mit session_manager erweitern
    agent_config = {
        'api_config': config.api,
        'session_manager': session_manager
    }
    
    # Agent erstellen
    agent = PerplexityAgent("test_perplexity", agent_config)
    
    # Initialisieren
    print("📌 Initialisiere Agent...")
    success = await agent.initialize()
    print(f"✅ Initialisierung: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
    
    if not success:
        print("❌ Konnte Agent nicht initialisieren")
        return
    
    # Test-Query
    query = MineQuery(
        mine_name="Quebec Gold Mine",
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
    await session_manager.close_all()
    print("\n✅ Test abgeschlossen")

def main():
    """Führt Test in separatem Thread aus (wie Streamlit)"""
    print("🚀 Starte Test in separatem Thread...")
    
    # Führe Test in Thread aus (simuliert Streamlit)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop, test_perplexity_in_thread())
        
        try:
            future.result(timeout=120)  # 2 Minuten Timeout
        except concurrent.futures.TimeoutError:
            print("⏱️ Test Timeout")
        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()