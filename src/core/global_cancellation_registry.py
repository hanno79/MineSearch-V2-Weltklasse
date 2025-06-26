"""
Author: rahn
Datum: 26.06.2025
Version: 1.0
Beschreibung: Globale Registry für aktive Suchen und deren Cancellation
"""

import asyncio
import threading
import weakref
from typing import Dict, Optional, Set
from datetime import datetime
import streamlit as st

from .cancellation import CancellationToken
from .logger import get_logger

logger = get_logger("global_cancellation")


class GlobalCancellationRegistry:
    """
    Globale Registry für alle aktiven Suchen.
    Ermöglicht das Abbrechen ALLER Suchen bei F5-Refresh.
    """
    
    _instance = None
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
            self._active_searches: Dict[str, CancellationToken] = {}
            self._search_tasks: Dict[str, Set[asyncio.Task]] = {}
            self._cleanup_callbacks: Dict[str, list] = {}
            self._lock = threading.Lock()
            logger.info("GlobalCancellationRegistry initialisiert")
    
    def register_search(self, search_id: str, cancellation_token: CancellationToken) -> None:
        """Registriert eine neue Suche"""
        with self._lock:
            self._active_searches[search_id] = cancellation_token
            self._search_tasks[search_id] = set()
            self._cleanup_callbacks[search_id] = []
            logger.info(f"Suche {search_id} registriert")
    
    def register_task(self, search_id: str, task: asyncio.Task) -> None:
        """Registriert einen Task für eine Suche"""
        with self._lock:
            if search_id in self._search_tasks:
                self._search_tasks[search_id].add(task)
                # Automatisch entfernen wenn Task fertig ist
                task.add_done_callback(lambda t: self._remove_task(search_id, t))
    
    def register_cleanup(self, search_id: str, cleanup_callback) -> None:
        """Registriert einen Cleanup-Callback für eine Suche"""
        with self._lock:
            if search_id in self._cleanup_callbacks:
                self._cleanup_callbacks[search_id].append(cleanup_callback)
    
    def cancel_search(self, search_id: str, reason: str = "User requested") -> bool:
        """Bricht eine spezifische Suche ab"""
        with self._lock:
            if search_id not in self._active_searches:
                return False
            
            logger.info(f"Breche Suche {search_id} ab: {reason}")
            
            # Cancel token
            token = self._active_searches[search_id]
            token.cancel(reason)
            
            # Cancel all tasks
            for task in list(self._search_tasks.get(search_id, [])):
                if not task.done():
                    task.cancel()
            
            # Run cleanup callbacks
            for callback in self._cleanup_callbacks.get(search_id, []):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback())
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Fehler in Cleanup-Callback: {e}")
            
            # Entferne aus Registry
            self._unregister_search(search_id)
            return True
    
    def cancel_all_searches(self, reason: str = "Global cancellation") -> int:
        """Bricht ALLE aktiven Suchen ab"""
        with self._lock:
            active_count = len(self._active_searches)
            if active_count == 0:
                return 0
            
            logger.warning(f"Breche {active_count} aktive Suchen ab: {reason}")
            
            # Kopiere IDs um während Iteration zu modifizieren
            search_ids = list(self._active_searches.keys())
            
        # Cancel außerhalb des Locks um Deadlocks zu vermeiden
        cancelled = 0
        for search_id in search_ids:
            if self.cancel_search(search_id, reason):
                cancelled += 1
        
        return cancelled
    
    def is_search_active(self, search_id: str) -> bool:
        """Prüft ob eine Suche aktiv ist"""
        with self._lock:
            return search_id in self._active_searches
    
    def get_active_search_count(self) -> int:
        """Gibt die Anzahl aktiver Suchen zurück"""
        with self._lock:
            return len(self._active_searches)
    
    def get_active_searches(self) -> Dict[str, dict]:
        """Gibt Informationen über alle aktiven Suchen zurück"""
        with self._lock:
            result = {}
            for search_id, token in self._active_searches.items():
                result[search_id] = {
                    'is_cancelled': token.is_cancelled(),
                    'task_count': len(self._search_tasks.get(search_id, [])),
                    'active_tasks': sum(1 for t in self._search_tasks.get(search_id, []) if not t.done())
                }
            return result
    
    def _remove_task(self, search_id: str, task: asyncio.Task) -> None:
        """Entfernt einen fertigen Task"""
        with self._lock:
            if search_id in self._search_tasks:
                self._search_tasks[search_id].discard(task)
    
    def _unregister_search(self, search_id: str) -> None:
        """Entfernt eine Suche aus der Registry"""
        # Bereits im Lock, nicht nochmal locken
        if search_id in self._active_searches:
            del self._active_searches[search_id]
        if search_id in self._search_tasks:
            del self._search_tasks[search_id]
        if search_id in self._cleanup_callbacks:
            del self._cleanup_callbacks[search_id]
        logger.debug(f"Suche {search_id} aus Registry entfernt")
    
    def cleanup_finished_searches(self) -> int:
        """Räumt beendete Suchen auf"""
        with self._lock:
            to_remove = []
            
            for search_id in list(self._active_searches.keys()):
                # Prüfe ob alle Tasks fertig sind
                tasks = self._search_tasks.get(search_id, set())
                if all(task.done() for task in tasks):
                    to_remove.append(search_id)
            
            for search_id in to_remove:
                self._unregister_search(search_id)
            
            if to_remove:
                logger.info(f"{len(to_remove)} beendete Suchen aufgeräumt")
            
            return len(to_remove)


# Globale Instanz
_global_registry = GlobalCancellationRegistry()


def get_global_cancellation_registry() -> GlobalCancellationRegistry:
    """Gibt die globale Registry-Instanz zurück"""
    return _global_registry


# Streamlit-spezifische Funktionen
def cancel_all_on_refresh():
    """
    Wird bei jedem Streamlit-Refresh aufgerufen.
    Bricht alle aktiven Suchen ab.
    """
    registry = get_global_cancellation_registry()
    cancelled = registry.cancel_all_searches("Page refresh detected")
    
    if cancelled > 0:
        logger.warning(f"Page Refresh: {cancelled} aktive Suchen abgebrochen")
        
        # Setze Streamlit Session State zurück
        if 'search_in_progress' in st.session_state:
            st.session_state.search_in_progress = False
        if 'cancellation_token' in st.session_state:
            st.session_state.cancellation_token = None
    
    return cancelled


def register_streamlit_cleanup():
    """
    Registriert Cleanup-Handler für Streamlit.
    Sollte am Anfang der Streamlit-App aufgerufen werden.
    """
    # Nutze Streamlit's Session State um zu tracken ob wir bereits registriert sind
    if 'cancellation_registry_initialized' not in st.session_state:
        st.session_state.cancellation_registry_initialized = True
        
        # Bei jedem Script-Run: Cancel alle Suchen
        cancelled = cancel_all_on_refresh()
        if cancelled > 0:
            st.warning(f"🛑 {cancelled} laufende Suchen wurden durch Page Refresh abgebrochen")
        
        logger.info("Streamlit Cleanup-Handler registriert")


# Context Manager für sichere Suchen-Registrierung
class RegisteredSearch:
    """Context Manager für automatische Registrierung/Deregistrierung von Suchen"""
    
    def __init__(self, search_id: str, cancellation_token: CancellationToken):
        self.search_id = search_id
        self.cancellation_token = cancellation_token
        self.registry = get_global_cancellation_registry()
    
    def __enter__(self):
        self.registry.register_search(self.search_id, self.cancellation_token)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Bei Exception: Cancel die Suche
        if exc_type is not None:
            self.registry.cancel_search(self.search_id, f"Exception: {exc_type.__name__}")
        else:
            # Normale Beendigung: Cleanup
            self.registry.cleanup_finished_searches()
        return False
    
    def register_task(self, task: asyncio.Task):
        """Registriert einen Task für diese Suche"""
        self.registry.register_task(self.search_id, task)
    
    def register_cleanup(self, callback):
        """Registriert einen Cleanup-Callback"""
        self.registry.register_cleanup(self.search_id, callback)