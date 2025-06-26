"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Event Loop Manager für stabile async Operationen
"""

import asyncio
import threading
import weakref
import atexit
import signal
import sys
from typing import Optional, Coroutine, TypeVar, Any, Dict, Set
import nest_asyncio
from .logger import get_logger

# Enable nested event loops
nest_asyncio.apply()

logger = get_logger("event_loop_manager")

T = TypeVar('T')


class EventLoopManager:
    """
    Verwaltet Event Loops für verschiedene Threads und Kontexte.
    Stellt sicher, dass immer ein funktionierender Event Loop verfügbar ist.
    """
    
    _instance: Optional['EventLoopManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._loops: Dict[int, asyncio.AbstractEventLoop] = {}  # Thread ID -> Event Loop mapping
            self._main_loop: Optional[asyncio.AbstractEventLoop] = None
            self._running_tasks: Set[asyncio.Task] = set()
            self._cleanup_registered = False
            self._register_cleanup_handlers()
            
    def get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """
        Holt oder erstellt einen Event Loop für den aktuellen Thread.
        ÄNDERUNG: Verbesserte Event Loop Verwaltung mit automatischer Wiederherstellung
        """
        thread_id = threading.current_thread().ident
        
        # Check if we have a valid loop for this thread
        if thread_id in self._loops:
            loop = self._loops[thread_id]
            if not loop.is_closed():
                return loop
            else:
                # Loop is closed, remove it and log
                logger.warning(f"Event loop für Thread {thread_id} war geschlossen, erstelle neuen")
                del self._loops[thread_id]
        
        # Try to get current running loop
        try:
            loop = asyncio.get_running_loop()
            if not loop.is_closed():
                self._loops[thread_id] = loop
                logger.debug(f"Verwende laufenden Event Loop für Thread {thread_id}")
                return loop
        except RuntimeError:
            # No running loop - this is normal
            pass
        
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Create new loop policy to reset the loop
                logger.info(f"Event Loop war geschlossen, erstelle neue Policy für Thread {thread_id}")
                asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            self._loops[thread_id] = loop
            return loop
            
        except RuntimeError:
            # No event loop exists - create new one
            logger.info(f"Kein Event Loop vorhanden, erstelle neuen für Thread {thread_id}")
            
        # Create new event loop with fresh policy
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loops[thread_id] = loop
        
        # Store as main loop if this is the main thread
        if threading.current_thread() is threading.main_thread():
            self._main_loop = loop
            
        logger.info(f"Neuer Event Loop erstellt für Thread {thread_id}")
        return loop
    
    async def run_async(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Führt eine Coroutine aus, egal ob ein Event Loop läuft oder nicht.
        ÄNDERUNG: Verbesserte Fehlerbehandlung und Task-Tracking
        """
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            
            # Prüfe ob Loop geschlossen ist
            if loop.is_closed():
                logger.warning("Laufender Event Loop ist geschlossen, erstelle neuen")
                loop = self.get_or_create_loop()
                return loop.run_until_complete(coro)
            
            # We're in a running loop, create task and track it
            task = asyncio.create_task(coro)
            self._running_tasks.add(task)
            task.add_done_callback(self._running_tasks.discard)
            return await task
            
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # No loop running - create one and run
                loop = self.get_or_create_loop()
                try:
                    return loop.run_until_complete(coro)
                except RuntimeError as run_error:
                    if "This event loop is already running" in str(run_error):
                        # Loop wurde zwischen Checks gestartet - nutze nest_asyncio
                        task = asyncio.create_task(coro)
                        self._running_tasks.add(task)
                        task.add_done_callback(self._running_tasks.discard)
                        return await task
                    raise
            raise
    
    def run_sync(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Führt eine Coroutine synchron aus.
        ÄNDERUNG: Robustere Ausführung mit besserer Thread-Verwaltung
        """
        # Spezialbehandlung für Streamlit/Jupyter Umgebungen
        if self._is_in_interactive_environment():
            # In interaktiven Umgebungen nutze asyncio.run in separatem Thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_in_new_loop, coro)
                return future.result()
        
        loop = self.get_or_create_loop()
        
        # Prüfe ob Loop geschlossen ist - erstelle neuen wenn nötig
        if loop.is_closed():
            logger.warning("Event Loop war geschlossen, erstelle neuen")
            loop = self.get_or_create_loop()
        
        # If loop is running, use thread pool
        if loop.is_running():
            # Prüfe ob wir im gleichen Thread sind
            if threading.current_thread().ident in self._loops and self._loops[threading.current_thread().ident] == loop:
                # Gleicher Thread - führe in neuem Thread aus um Deadlock zu vermeiden
                return self._run_in_new_loop(coro)
            else:
                # Anderer Thread - führe in neuem Event Loop aus
                return self._run_in_new_loop(coro)
        else:
            # Loop not running, we can run directly
            try:
                return loop.run_until_complete(coro)
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    # Loop wurde gestartet - nutze Thread Pool
                    return self._run_in_new_loop(coro)
                elif "Event loop is closed" in str(e):
                    # Loop wurde geschlossen - erstelle neuen
                    logger.warning("Event Loop wurde während der Ausführung geschlossen, erstelle neuen")
                    self.cleanup()
                    return self._run_in_new_loop(coro)
                raise
    
    def cleanup(self):
        """
        Schließt alle Event Loops sauber.
        ÄNDERUNG: Verbesserte Cleanup-Logik mit Task-Cancellation
        """
        logger.info("Starte Event Loop Cleanup...")
        
        # Cancel all tracked running tasks first
        for task in list(self._running_tasks):
            if not task.done():
                task.cancel()
        
        # Cleanup loops
        for thread_id, loop in list(self._loops.items()):
            if loop.is_closed():
                continue
                
            try:
                # Get all tasks for this loop
                if sys.version_info >= (3, 9):
                    pending = asyncio.all_tasks(loop)
                else:
                    pending = asyncio.Task.all_tasks(loop)
                
                # Cancel all pending tasks
                for task in pending:
                    if not task.done():
                        task.cancel()
                
                # Give tasks time to cancel
                if pending and not loop.is_running():
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                
                # Stop the loop if running
                if loop.is_running():
                    loop.call_soon_threadsafe(loop.stop)
                
                # Close the loop
                loop.close()
                logger.info(f"Event Loop für Thread {thread_id} erfolgreich geschlossen")
                
            except Exception as e:
                logger.error(f"Fehler beim Schließen des Event Loops für Thread {thread_id}: {e}")
            
        # Clear all references
        self._loops.clear()
        self._running_tasks.clear()
        self._main_loop = None
        
        logger.info("Event Loop Cleanup abgeschlossen")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            # Vermeide Cleanup in __del__ wenn bereits registriert
            if not self._cleanup_registered:
                self.cleanup()
        except:
            pass
    
    def _register_cleanup_handlers(self):
        """Registriert Cleanup-Handler für sauberes Beenden"""
        if self._cleanup_registered:
            return
            
        def cleanup_wrapper():
            try:
                self.cleanup()
            except Exception as e:
                logger.error(f"Fehler beim Event Loop Cleanup: {e}")
        
        # Registriere atexit Handler
        atexit.register(cleanup_wrapper)
        
        # Registriere Signal Handler
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} empfangen, führe Event Loop Cleanup durch...")
            cleanup_wrapper()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except:
            # Signal handling might not work in all environments
            pass
            
        self._cleanup_registered = True
    
    def _is_in_interactive_environment(self) -> bool:
        """Prüft ob wir in einer interaktiven Umgebung (Jupyter/Streamlit) sind"""
        try:
            # Check for Jupyter
            if 'ipykernel' in sys.modules or 'IPython' in sys.modules:
                return True
            # Check for Streamlit
            if 'streamlit' in sys.modules:
                return True
            return False
        except:
            return False
    
    def _run_in_new_loop(self, coro: Coroutine[Any, Any, T]) -> T:
        """Führt Coroutine in neuem Event Loop aus"""
        # Erstelle neuen Event Loop für diese Ausführung
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            try:
                # Cleanup des temporären Loops
                pending = asyncio.all_tasks(new_loop) if sys.version_info >= (3, 9) else asyncio.Task.all_tasks(new_loop)
                for task in pending:
                    task.cancel()
                if pending:
                    new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                new_loop.close()
            except Exception as cleanup_error:
                # ÄNDERUNG 24.06.2025: Fehler beim Cleanup loggen statt verschlucken
                logger.warning(f"Fehler beim Loop-Cleanup: {cleanup_error}")
            finally:
                # Stelle sicher, dass kein geschlossener Loop als current event loop gesetzt bleibt
                try:
                    asyncio.set_event_loop(None)
                except:
                    pass


# Global instance
_event_loop_manager = EventLoopManager()


def get_event_loop_manager() -> EventLoopManager:
    """Get the global EventLoopManager instance"""
    return _event_loop_manager


def run_async_safe(coro: Coroutine[Any, Any, T]) -> T:
    """
    Sicher eine Coroutine ausführen, unabhängig vom Event Loop Status.
    ÄNDERUNG: Bessere Fehlerbehandlung bei geschlossenen Event Loops
    """
    manager = get_event_loop_manager()
    
    # Maximal 3 Versuche
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return manager.run_sync(coro)
        except RuntimeError as e:
            last_error = e
            error_str = str(e)
            
            if "Event loop is closed" in error_str:
                logger.warning(f"Event Loop war geschlossen (Versuch {attempt + 1}/{max_retries}), erstelle neuen")
                # Force cleanup and retry
                manager.cleanup()
                # Kleine Pause zwischen Versuchen
                import time
                time.sleep(0.1)
                continue
            elif "Cannot run the event loop while another loop is running" in error_str:
                # Verwende direkt den neuen Loop
                logger.warning("Anderer Event Loop läuft bereits, verwende neuen Thread")
                return manager._run_in_new_loop(coro)
            else:
                raise
        except Exception as e:
            # ÄNDERUNG 24.06.2025: Besseres Exception Logging mit Details
            error_msg = str(e) if str(e) else f"{type(e).__name__}: (keine Nachricht)"
            logger.error(f"Unerwarteter Fehler in run_async_safe: {error_msg}")
            logger.error(f"Exception-Typ: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    # Wenn alle Versuche fehlschlagen
    if last_error:
        raise last_error
    else:
        raise RuntimeError(f"Konnte Coroutine nach {max_retries} Versuchen nicht ausführen")


async def ensure_event_loop_health() -> bool:
    """
    Prüft und stellt sicher, dass der Event Loop gesund ist.
    Gibt True zurück wenn Loop funktioniert, False wenn Probleme vorliegen.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            logger.error("Event Loop ist geschlossen!")
            return False
            
        # Teste Loop mit einfacher Operation
        await asyncio.sleep(0)
        return True
        
    except RuntimeError:
        logger.warning("Kein laufender Event Loop gefunden")
        return False
    except Exception as e:
        logger.error(f"Event Loop Health Check fehlgeschlagen: {e}")
        return False