#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.06.2025
Version: 1.0
Beschreibung: Test Script für Cancel Button und F5-Refresh Funktionalität
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.cancellation import CancellationToken
from src.core.global_cancellation_registry import get_global_cancellation_registry, RegisteredSearch
from src.core.logger import get_logger

logger = get_logger("test_cancel")


async def simulate_long_running_task(name: str, duration: int, cancellation_token: CancellationToken):
    """Simuliert eine lang laufende Aufgabe mit Cancellation Support"""
    logger.info(f"Task {name} gestartet (Dauer: {duration}s)")
    
    for i in range(duration):
        # Check cancellation
        if cancellation_token.is_cancelled():
            logger.warning(f"Task {name} wurde nach {i}s abgebrochen!")
            raise asyncio.CancelledError(f"Task {name} cancelled")
        
        await asyncio.sleep(1)
        logger.debug(f"Task {name}: {i+1}/{duration}s")
    
    logger.info(f"Task {name} erfolgreich beendet")
    return f"Result from {name}"


async def test_global_cancellation():
    """Testet die globale Cancellation Registry"""
    logger.info("=== Test Global Cancellation Registry ===")
    
    registry = get_global_cancellation_registry()
    
    # Test 1: Einzelne Suche mit Cancellation
    logger.info("\nTest 1: Einzelne Suche mit Cancellation")
    search_id = "test_search_1"
    token = CancellationToken(f"search_{search_id}")
    
    with RegisteredSearch(search_id, token) as search:
        # Starte Task
        task = asyncio.create_task(simulate_long_running_task("Task1", 10, token))
        search.register_task(task)
        
        # Cancel nach 3 Sekunden
        await asyncio.sleep(3)
        logger.info("Cancelling search...")
        cancelled = registry.cancel_search(search_id, "Test cancellation")
        assert cancelled, "Search sollte erfolgreich abgebrochen werden"
        
        # Warte auf Task-Ende
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Task wurde erfolgreich abgebrochen")
    
    # Test 2: Mehrere parallele Suchen
    logger.info("\nTest 2: Mehrere parallele Suchen mit global cancel")
    
    searches = []
    for i in range(3):
        search_id = f"test_search_{i+2}"
        token = CancellationToken(f"search_{search_id}")
        registry.register_search(search_id, token)
        
        task = asyncio.create_task(
            simulate_long_running_task(f"Task{i+2}", 15, token)
        )
        registry.register_task(search_id, task)
        searches.append((search_id, task))
    
    # Status vor Cancel
    active = registry.get_active_searches()
    logger.info(f"Aktive Suchen vor Cancel: {len(active)}")
    
    # Warte 2 Sekunden
    await asyncio.sleep(2)
    
    # Cancel alle Suchen (simuliert F5-Refresh)
    logger.info("\nSimuliere F5-Refresh: Cancel alle Suchen")
    cancelled_count = registry.cancel_all_searches("Simulated page refresh")
    logger.info(f"Abgebrochen: {cancelled_count} Suchen")
    
    # Warte auf alle Tasks
    for search_id, task in searches:
        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"{search_id} wurde abgebrochen")
    
    # Status nach Cancel
    active = registry.get_active_searches()
    logger.info(f"Aktive Suchen nach Cancel: {len(active)}")
    assert len(active) == 0, "Keine Suchen sollten mehr aktiv sein"
    
    logger.info("\n✅ Alle Tests erfolgreich!")


async def test_cancellation_token():
    """Testet die CancellationToken Funktionalität"""
    logger.info("\n=== Test CancellationToken ===")
    
    token = CancellationToken("test_token")
    
    # Test Callbacks
    callback_called = False
    def test_callback():
        nonlocal callback_called
        callback_called = True
        logger.info("Callback wurde aufgerufen")
    
    token.register_callback(test_callback)
    
    # Cancel token
    token.cancel("Test reason")
    
    assert token.is_cancelled(), "Token sollte cancelled sein"
    assert callback_called, "Callback sollte aufgerufen worden sein"
    
    # Test async wait
    token2 = CancellationToken("test_token2")
    
    async def wait_for_cancel():
        await token2.wait_for_cancellation()
        logger.info("Cancellation detected via wait")
    
    wait_task = asyncio.create_task(wait_for_cancel())
    await asyncio.sleep(0.1)
    
    token2.cancel()
    await wait_task
    
    logger.info("✅ CancellationToken Tests erfolgreich!")


async def main():
    """Hauptfunktion"""
    logger.info("Starting Cancel Functionality Tests")
    
    try:
        # Test CancellationToken
        await test_cancellation_token()
        
        # Test Global Registry
        await test_global_cancellation()
        
        logger.info("\n🎉 Alle Tests erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Ensure clean event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    finally:
        # Cleanup
        loop.close()