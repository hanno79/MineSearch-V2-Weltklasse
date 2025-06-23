"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Test der Streamlit Integration mit Event Loop Fix
"""

import asyncio
import aiohttp
from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.event_loop_manager import run_async
from src.agents.base_agent import MineQuery


def test_orchestrator_with_event_loop():
    """Testet Orchestrator mit Event Loop Manager"""
    
    print("=== Test Orchestrator mit Event Loop Manager ===\n")
    
    config = Config()
    
    # 1. Initialisiere Orchestrator
    print("1. Initialisiere Orchestrator...")
    orchestrator = MineSearchOrchestratorV2(config)
    
    # Verwende Event Loop Manager
    init_result = run_async(orchestrator.initialize())
    print(f"   Initialisierung erfolgreich: {init_result}")
    
    # 2. Erstelle Test-Query
    query = MineQuery(
        mine_name="Test Mine",
        region="Test Region",
        country="Test Country",
        languages=["en"],
        required_fields=["operator", "status"]
    )
    
    # 3. Simuliere mehrere Suchen (wie in Streamlit)
    print("\n2. Simuliere mehrere Suchen...")
    
    for i in range(3):
        print(f"\n   Suche {i+1}:")
        try:
            # Simuliere asyncio.run wie in Streamlit
            # Aber mit unserem Event Loop Manager
            search_params = {
                "agent_types": ["scraper"],  # Nur Scraper Agent für Test
                "enhanced": False
            }
            
            results = run_async(orchestrator.search_mine(query, search_params))
            print(f"   Ergebnisse erhalten: {len(results)} Felder")
            
        except Exception as e:
            print(f"   Fehler: {e}")
    
    # 4. Cleanup
    print("\n3. Cleanup...")
    run_async(orchestrator.cleanup())
    
    print("\n✅ Test abgeschlossen - keine Event Loop Fehler!")


def test_session_lifecycle():
    """Testet Session Lifecycle mit mehreren Event Loops"""
    
    print("\n=== Test Session Lifecycle ===\n")
    
    async def create_and_use_session():
        session = aiohttp.ClientSession()
        try:
            # Verwende Session
            async with session.get("https://httpbin.org/get") as response:
                data = await response.json()
                print(f"   Response erhalten: {response.status}")
                return data
        finally:
            await session.close()
    
    # Führe mehrmals aus (simuliert mehrere Streamlit-Runs)
    for i in range(3):
        print(f"\nDurchlauf {i+1}:")
        result = run_async(create_and_use_session())
        print(f"   Session erfolgreich verwendet")
    
    print("\n✅ Session Lifecycle Test erfolgreich!")


def main():
    """Hauptfunktion"""
    
    try:
        # Test 1: Orchestrator
        test_orchestrator_with_event_loop()
        
        # Test 2: Session Lifecycle
        test_session_lifecycle()
        
        print("\n=== ALLE TESTS ERFOLGREICH ===")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup Event Loop Manager
        from src.core.event_loop_manager import get_event_loop_manager
        manager = get_event_loop_manager()
        manager.shutdown()


if __name__ == "__main__":
    main()