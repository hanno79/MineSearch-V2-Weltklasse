"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Async Utilities ohne globale SessionManager-Logik
# ÄNDERUNG 27.06.2025: Globale SessionManager-Logik entfernt
"""

import asyncio
import nest_asyncio
from typing import TypeVar, Coroutine, Any
from .logger import get_logger

# Erlaube nested event loops für Streamlit Kompatibilität
nest_asyncio.apply()

logger = get_logger("async_utils")

T = TypeVar('T')


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Führt eine Coroutine aus und gibt das Ergebnis zurück.
    Kompatibel mit Streamlit's Event Loop.
    
    Args:
        coro: Die auszuführende Coroutine
        
    Returns:
        Das Ergebnis der Coroutine
    """
    # ÄNDERUNG 23.06.2025: Nutze Event Loop Manager für robuste Ausführung
    from .event_loop_manager import run_async_safe
    return run_async_safe(coro)


async def gather_with_concurrency(n: int, *coros):
    """
    Führt mehrere Coroutines mit begrenzter Parallelität aus.
    
    Args:
        n: Maximale Anzahl gleichzeitiger Coroutines
        *coros: Die auszuführenden Coroutines
        
    Returns:
        Liste der Ergebnisse
    """
    semaphore = asyncio.Semaphore(n)
    
    async def sem_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*(sem_coro(c) for c in coros), return_exceptions=True)


# ÄNDERUNG 24.06.2025: Cleanup wird jetzt vom Session Manager selbst gehandhabt