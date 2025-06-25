"""
Author: rahn
Datum: 25.06.2025
Version: 1.0
Beschreibung: Async Wrapper speziell für Streamlit Umgebung
"""

import asyncio
import threading
from typing import TypeVar, Coroutine, Any, Optional, Callable
import streamlit as st
from src.core.logger import get_logger
import nest_asyncio

# Enable nested event loops
nest_asyncio.apply()

logger = get_logger("streamlit_async")

T = TypeVar('T')


class StreamlitEventLoopManager:
    """Verwaltet Event Loops speziell für Streamlit"""
    
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def _ensure_loop(self):
        """Stellt sicher, dass ein funktionierender Event Loop existiert"""
        with self._lock:
            # Prüfe ob ein Event Loop existiert und läuft
            if self._loop is None or self._loop.is_closed():
                logger.debug("Erstelle neuen Event Loop für Streamlit")
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                
                # Starte Loop in separatem Thread
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
                
    def _run_loop(self):
        """Läuft im separaten Thread"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        
    def run_coroutine(self, coro: Coroutine[Any, Any, T]) -> T:
        """Führt eine Coroutine aus und gibt das Ergebnis zurück"""
        self._ensure_loop()
        
        # Submit coroutine to the loop
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        try:
            # Wait for result with timeout
            result = future.result(timeout=300)  # 5 Minuten Timeout
            return result
        except asyncio.TimeoutError:
            logger.error("Async operation timed out")
            raise
        except Exception as e:
            logger.error(f"Error in async operation: {e}")
            raise
            
    def cleanup(self):
        """Cleanup resources"""
        with self._lock:
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=1)
                self._loop.close()
                self._loop = None
                self._thread = None


# Globale Instanz für Streamlit
_streamlit_loop_manager = StreamlitEventLoopManager()


def streamlit_run_async(
    coro: Coroutine[Any, Any, T],
    error_callback: Optional[Callable[[Exception], None]] = None
) -> T:
    """
    Führt eine async Funktion in Streamlit aus.
    
    Diese Funktion behandelt Event Loop Probleme die in Streamlit auftreten können:
    - Event Loop ist geschlossen
    - Event Loop läuft bereits
    - Thread-Konflikte
    
    Args:
        coro: Die auszuführende Coroutine
        error_callback: Optional callback für Fehlerbehandlung
        
    Returns:
        Das Ergebnis der Coroutine
    """
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Versuche die Coroutine auszuführen
            return _streamlit_loop_manager.run_coroutine(coro)
            
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.warning(f"Event loop war geschlossen, Versuch {attempt + 1}/{max_retries}")
                # Force cleanup und neuer Versuch
                _streamlit_loop_manager.cleanup()
                last_error = e
                continue
            else:
                # Andere RuntimeErrors direkt werfen
                if error_callback:
                    error_callback(e)
                raise
                
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der async Funktion: {e}")
            if error_callback:
                error_callback(e)
            raise
    
    # Wenn alle Versuche fehlschlagen
    error_msg = f"Konnte async Funktion nach {max_retries} Versuchen nicht ausführen"
    logger.error(error_msg)
    if last_error:
        raise RuntimeError(error_msg) from last_error
    else:
        raise RuntimeError(error_msg)


@st.cache_resource
def get_streamlit_event_loop_manager():
    """Gibt den globalen StreamlitEventLoopManager zurück"""
    return _streamlit_loop_manager


# Context Manager für sicheren async Kontext
class StreamlitAsyncContext:
    """Context Manager für sichere async Operationen in Streamlit"""
    
    def __init__(self, show_errors: bool = True):
        self.show_errors = show_errors
        self.manager = get_streamlit_event_loop_manager()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and self.show_errors:
            st.error(f"Async Fehler: {exc_val}")
        return False
        
    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Führt eine Coroutine im Context aus"""
        def error_handler(e):
            if self.show_errors:
                st.error(f"Fehler: {str(e)}")
        
        return streamlit_run_async(coro, error_callback=error_handler)


# Cleanup bei App-Ende
import atexit
atexit.register(lambda: _streamlit_loop_manager.cleanup())