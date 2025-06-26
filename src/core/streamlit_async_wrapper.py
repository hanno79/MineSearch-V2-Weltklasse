"""
Author: rahn  
Datum: 25.06.2025
Version: 1.0
Beschreibung: Streamlit-spezifischer Async Wrapper für robuste Event Loop Verwaltung
"""

import asyncio
import streamlit as st
from typing import TypeVar, Coroutine, Any, Optional, Callable
from contextlib import contextmanager
import threading
import time

from .event_loop_manager import get_event_loop_manager, run_async_safe
from .logger import get_logger

logger = get_logger("streamlit_async_wrapper")

T = TypeVar('T')


class StreamlitAsyncWrapper:
    """
    Wrapper für sichere async Operationen in Streamlit.
    Behandelt Event Loop Probleme und bietet robuste Fehlerbehandlung.
    """
    
    def __init__(self):
        self.event_loop_manager = get_event_loop_manager()
        self._active_operations = set()
        
    def run_async(self, coro: Coroutine[Any, Any, T], 
                  error_callback: Optional[Callable[[Exception], None]] = None) -> T:
        """
        Führt eine Coroutine aus mit Streamlit-spezifischer Fehlerbehandlung.
        
        Args:
            coro: Die auszuführende Coroutine
            error_callback: Optional callback für Fehlerbehandlung
            
        Returns:
            Das Ergebnis der Coroutine
        """
        operation_id = id(coro)
        self._active_operations.add(operation_id)
        
        try:
            # Verwende den globalen run_async_safe mit zusätzlicher Fehlerbehandlung
            return run_async_safe(coro)
            
        except RuntimeError as e:
            error_msg = str(e)
            
            # Spezielle Behandlung für Streamlit-spezifische Fehler
            if "Event loop is closed" in error_msg:
                logger.warning("Event Loop geschlossen in Streamlit-Kontext, versuche Neustart")
                
                # Cleanup und neuer Versuch
                self.event_loop_manager.cleanup()
                time.sleep(0.1)  # Kurze Pause
                
                try:
                    return run_async_safe(coro)
                except Exception as retry_error:
                    logger.error(f"Neustart fehlgeschlagen: {retry_error}")
                    if error_callback:
                        error_callback(retry_error)
                    raise
                    
            elif "Cannot run the event loop while another loop is running" in error_msg:
                # Streamlit hat bereits einen laufenden Loop
                logger.info("Streamlit Event Loop erkannt, verwende Thread-basierte Ausführung")
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
                    
            else:
                if error_callback:
                    error_callback(e)
                raise
                
        except Exception as e:
            logger.error(f"Unerwarteter Fehler in StreamlitAsyncWrapper: {e}")
            if error_callback:
                error_callback(e)
            raise
            
        finally:
            self._active_operations.discard(operation_id)
    
    @contextmanager
    def async_context(self):
        """
        Context Manager für sichere async Operationen in Streamlit.
        Stellt sicher, dass Event Loops korrekt verwaltet werden.
        """
        # Prüfe ob wir in Streamlit sind
        in_streamlit = 'streamlit' in sys.modules
        
        if in_streamlit:
            logger.debug("In Streamlit-Kontext, verwende speziellen Event Loop Handling")
        
        try:
            yield self
        finally:
            # Cleanup bei Bedarf
            if self._active_operations:
                logger.warning(f"Noch {len(self._active_operations)} aktive Operationen bei Context-Exit")
    
    def ensure_healthy_loop(self) -> bool:
        """
        Stellt sicher, dass ein gesunder Event Loop verfügbar ist.
        
        Returns:
            True wenn Loop gesund ist, False sonst
        """
        try:
            # Teste Event Loop mit einfacher Operation
            test_coro = self._test_loop_health()
            self.run_async(test_coro)
            return True
            
        except Exception as e:
            logger.error(f"Event Loop Health Check fehlgeschlagen: {e}")
            return False
    
    async def _test_loop_health(self):
        """Einfache Test-Coroutine für Health Check"""
        await asyncio.sleep(0)
        return True
    
    def cleanup(self):
        """Führt Cleanup durch"""
        if self._active_operations:
            logger.warning(f"Cleanup mit {len(self._active_operations)} aktiven Operationen")
        
        self.event_loop_manager.cleanup()


# Global instance für Streamlit
_streamlit_async_wrapper = None


def get_streamlit_async_wrapper() -> StreamlitAsyncWrapper:
    """Holt oder erstellt den globalen StreamlitAsyncWrapper"""
    global _streamlit_async_wrapper
    
    if _streamlit_async_wrapper is None:
        _streamlit_async_wrapper = StreamlitAsyncWrapper()
    
    return _streamlit_async_wrapper


def streamlit_run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Convenience-Funktion für async Operationen in Streamlit.
    
    Verwendung:
        result = streamlit_run_async(my_async_function())
    """
    wrapper = get_streamlit_async_wrapper()
    
    # Error callback mit Streamlit-Anzeige
    def show_error(e: Exception):
        st.error(f"❌ Async Operation fehlgeschlagen: {str(e)}")
    
    return wrapper.run_async(coro, error_callback=show_error)


# Import für Kompatibilität
import sys