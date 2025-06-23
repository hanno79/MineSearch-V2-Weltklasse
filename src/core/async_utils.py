"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Async Utilities für Streamlit-kompatible Ausführung
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
    try:
        # Versuche den aktuellen Event Loop zu bekommen
        loop = asyncio.get_event_loop()
        
        # Wenn der Loop bereits läuft (in Streamlit), nutze nest_asyncio
        if loop.is_running():
            # nest_asyncio erlaubt uns asyncio.run innerhalb eines laufenden Loops
            return asyncio.run(coro)
        else:
            # Ansonsten normal ausführen
            return loop.run_until_complete(coro)
            
    except RuntimeError:
        # Kein Event Loop vorhanden, erstelle neuen
        return asyncio.run(coro)


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


class AsyncSessionManager:
    """
    Verwaltet aiohttp Sessions für Agenten.
    Stellt sicher, dass Sessions korrekt erstellt und geschlossen werden.
    """
    
    def __init__(self):
        self.sessions = {}
        self._lock = asyncio.Lock()
        
    async def get_session(self, agent_id: str):
        """Holt oder erstellt eine Session für einen Agenten"""
        import aiohttp
        
        async with self._lock:
            # ÄNDERUNG 23.06.2025: Robustere Session-Verwaltung mit Event Loop Check
            try:
                # Prüfe ob Event Loop noch läuft
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    logger.error(f"Event Loop ist geschlossen, kann keine Session für {agent_id} erstellen")
                    raise RuntimeError("Event loop is closed")
                
                if agent_id not in self.sessions or self.sessions[agent_id].closed:
                    # Schließe alte Session falls vorhanden
                    if agent_id in self.sessions:
                        try:
                            await self.sessions[agent_id].close()
                        except Exception as e:
                            logger.debug(f"Fehler beim Schließen alter Session: {e}")
                    
                    # Erstelle neue Session mit Timeout
                    timeout = aiohttp.ClientTimeout(total=60)
                    connector = aiohttp.TCPConnector(
                        limit=10, 
                        force_close=True,
                        enable_cleanup_closed=True  # ÄNDERUNG: Automatische Bereinigung
                    )
                    self.sessions[agent_id] = aiohttp.ClientSession(
                        timeout=timeout,
                        connector=connector
                    )
                    logger.debug(f"Neue Session erstellt für Agent: {agent_id}")
                
                return self.sessions[agent_id]
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen/Abrufen der Session für {agent_id}: {e}")
                raise
    
    async def close_session(self, agent_id: str):
        """Schließt die Session eines Agenten"""
        if agent_id in self.sessions:
            session = self.sessions[agent_id]
            if not session.closed:
                await session.close()
                logger.debug(f"Session geschlossen für Agent: {agent_id}")
            del self.sessions[agent_id]
    
    async def close_all(self):
        """Schließt alle offenen Sessions"""
        # ÄNDERUNG 23.06.2025: Robustere Session-Schließung
        close_tasks = []
        for agent_id in list(self.sessions.keys()):
            close_tasks.append(self.close_session(agent_id))
        
        if close_tasks:
            # Verwende gather mit return_exceptions=True um Fehler zu ignorieren
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self.sessions.clear()
        logger.info("Alle Sessions geschlossen")


# Globale Session Manager Instanz
_session_manager = AsyncSessionManager()


def get_session_manager() -> AsyncSessionManager:
    """Gibt die globale Session Manager Instanz zurück"""
    return _session_manager