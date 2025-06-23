"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Test für Event Loop Fix
"""

import asyncio
import aiohttp
from src.core.event_loop_manager import run_async, get_event_loop_manager
from src.core.config import Config
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.base_agent import MineQuery


async def test_event_loop_consistency():
    """Testet ob Event Loop konsistent bleibt"""
    
    print("1. Teste Event Loop Manager...")
    manager = get_event_loop_manager()
    assert manager.is_running(), "Event Loop sollte laufen"
    
    # Test 1: Mehrere async Operationen
    print("\n2. Teste mehrere async Operationen...")
    
    async def async_task(n):
        await asyncio.sleep(0.1)
        return f"Task {n} completed"
    
    # Führe mehrere Tasks aus
    results = []
    for i in range(3):
        result = run_async(async_task(i))
        results.append(result)
        print(f"   {result}")
    
    assert len(results) == 3, "Alle Tasks sollten ausgeführt werden"
    
    # Test 2: HTTP Session Management
    print("\n3. Teste HTTP Session Management...")
    
    async def test_session():
        session = aiohttp.ClientSession()
        try:
            # Teste ob Session funktioniert
            assert not session.closed, "Session sollte offen sein"
            return "Session works"
        finally:
            await session.close()
    
    result = run_async(test_session())
    print(f"   {result}")
    
    # Test 3: Agent mit Session
    print("\n4. Teste Agent mit Session...")
    config = Config()
    
    if config.api_config.perplexity_key:
        agent = PerplexityAgent("test_perplexity", config)
        
        # Initialisiere Agent
        init_result = run_async(agent.initialize())
        print(f"   Agent initialisiert: {init_result}")
        
        # Cleanup
        run_async(agent.cleanup())
        print("   Agent aufgeräumt")
    else:
        print("   Überspringe Agent-Test (kein API Key)")
    
    print("\n5. Test abgeschlossen - keine Event Loop Fehler!")
    return True


def main():
    """Hauptfunktion"""
    print("=== Event Loop Fix Test ===\n")
    
    try:
        # Führe Tests aus
        run_async(test_event_loop_consistency())
        
        print("\n✅ Alle Tests erfolgreich!")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        manager = get_event_loop_manager()
        manager.shutdown()
        print("\nEvent Loop Manager heruntergefahren")


if __name__ == "__main__":
    main()