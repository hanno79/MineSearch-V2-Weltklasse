"""
Author: rahn
Datum: 23.06.2025
Version: 2.0
Beschreibung: Optimized Cancellation Token für schnellere Reaktionszeiten
"""

import asyncio
import threading
from typing import Optional, Callable, Any, List, Set
from datetime import datetime
import weakref

from .logger import get_logger

logger = get_logger("cancellation_optimized")


class OptimizedCancellationToken:
    """
    Hochperformanter Thread-sicherer Cancellation Token mit minimaler Latenz.
    
    Features:
    - Sofortige Event-Propagierung ohne Delays
    - Lightweight checking ohne Locks wo möglich
    - Effiziente Task-Registrierung für automatisches Cancelling
    """
    
    def __init__(self, name: str = "default"):
        """
        Initialisiert einen optimierten Cancellation Token.
        
        Args:
            name: Beschreibender Name für Logging
        """
        self.name = name
        self._cancelled = threading.Event()  # Thread-safe event statt bool
        self._cancel_time: Optional[datetime] = None
        self._cancel_reason: Optional[str] = None
        self._callbacks: List[Callable[[], Any]] = []
        self._callback_lock = threading.Lock()
        self._registered_tasks: Set[weakref.ref] = set()
        self._task_lock = threading.Lock()
        
        # Async event für wartende Coroutines
        self._async_event: Optional[asyncio.Event] = None
        self._async_event_lock = threading.Lock()
        
    def cancel(self, reason: str = "User requested cancellation"):
        """
        Setzt den Cancellation Token mit sofortiger Propagierung.
        
        Args:
            reason: Grund für den Abbruch
        """
        if self._cancelled.is_set():
            return  # Bereits abgebrochen
            
        # Setze cancelled flag (thread-safe)
        self._cancelled.set()
        self._cancel_time = datetime.now()
        self._cancel_reason = reason
        
        logger.info(f"CancellationToken '{self.name}' cancelled: {reason}")
        
        # Setze async event falls vorhanden
        with self._async_event_lock:
            if self._async_event and not self._async_event.is_set():
                try:
                    loop = self._async_event._loop
                    if loop and not loop.is_closed():
                        loop.call_soon_threadsafe(self._async_event.set)
                except Exception as e:
                    logger.debug(f"Could not set async event: {e}")
        
        # Cancel registered tasks
        with self._task_lock:
            for task_ref in list(self._registered_tasks):
                task = task_ref()
                if task and not task.done():
                    try:
                        loop = task.get_loop()
                        if loop and not loop.is_closed():
                            loop.call_soon_threadsafe(task.cancel)
                    except Exception as e:
                        logger.debug(f"Could not cancel task: {e}")
        
        # Führe Callbacks aus (ohne Lock für Performance)
        callbacks = self._callbacks.copy()  # Kopie für Thread-Safety
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cancellation callback: {e}")
    
    def is_cancelled(self) -> bool:
        """
        Prüft ob der Token abgebrochen wurde (lock-free).
        
        Returns:
            True wenn abgebrochen, sonst False
        """
        return self._cancelled.is_set()
    
    async def check_cancelled(self):
        """
        Async-Check mit Exception wenn abgebrochen.
        Optimiert für häufige Aufrufe.
        
        Raises:
            CancellationException: Wenn Token abgebrochen wurde
        """
        if self._cancelled.is_set():
            raise CancellationException(self._cancel_reason or "Operation cancelled")
    
    def check_cancelled_sync(self):
        """
        Synchroner Check mit Exception wenn abgebrochen.
        
        Raises:
            CancellationException: Wenn Token abgebrochen wurde
        """
        if self._cancelled.is_set():
            raise CancellationException(self._cancel_reason or "Operation cancelled")
    
    async def wait_for_cancellation(self):
        """
        Wartet asynchron bis der Token abgebrochen wird.
        Erstellt Event nur bei Bedarf (lazy initialization).
        """
        # Lazy initialization des async events
        with self._async_event_lock:
            if self._async_event is None:
                self._async_event = asyncio.Event()
                # Falls bereits cancelled, setze sofort
                if self._cancelled.is_set():
                    self._async_event.set()
        
        await self._async_event.wait()
    
    def register_callback(self, callback: Callable[[], Any]):
        """
        Registriert einen Callback der bei Abbruch aufgerufen wird.
        
        Args:
            callback: Funktion die bei Abbruch aufgerufen wird
        """
        if self._cancelled.is_set():
            # Bereits abgebrochen, rufe Callback sofort auf
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cancellation callback: {e}")
        else:
            with self._callback_lock:
                self._callbacks.append(callback)
    
    def register_task(self, task: asyncio.Task):
        """
        Registriert einen asyncio Task für automatisches Cancelling.
        Verwendet weak references um Memory Leaks zu vermeiden.
        
        Args:
            task: Der zu registrierende Task
        """
        if self._cancelled.is_set():
            # Bereits cancelled, cancel task sofort
            task.cancel()
        else:
            with self._task_lock:
                # Cleanup alte task references
                self._registered_tasks = {ref for ref in self._registered_tasks if ref() is not None}
                # Füge neuen Task hinzu
                self._registered_tasks.add(weakref.ref(task))
    
    def get_cancel_info(self) -> Optional[dict]:
        """
        Gibt Informationen über den Abbruch zurück.
        
        Returns:
            Dict mit cancel_time und cancel_reason oder None
        """
        if not self._cancelled.is_set():
            return None
        return {
            "cancel_time": self._cancel_time,
            "cancel_reason": self._cancel_reason
        }
    
    def reset(self):
        """
        Setzt den Token zurück (nur für Tests/Entwicklung).
        """
        self._cancelled.clear()
        self._cancel_time = None
        self._cancel_reason = None
        
        with self._async_event_lock:
            if self._async_event:
                self._async_event.clear()
        
        with self._task_lock:
            self._registered_tasks.clear()
    
    def cleanup(self):
        """
        Cleanup-Methode für sauberes Beenden.
        """
        # Cancel all registered tasks
        with self._task_lock:
            for task_ref in list(self._registered_tasks):
                task = task_ref()
                if task and not task.done():
                    task.cancel()
            self._registered_tasks.clear()
        
        # Set event for waiting coroutines
        with self._async_event_lock:
            if self._async_event and not self._async_event.is_set():
                self._async_event.set()
        
        # Clear callbacks
        with self._callback_lock:
            self._callbacks.clear()
        
        logger.debug(f"CancellationToken '{self.name}' cleaned up")


class CancellationException(Exception):
    """Exception die bei Abbruch geworfen wird"""
    pass


class OptimizedCancellationScope:
    """
    Context Manager für Cancellation Tokens mit automatischer Task-Registrierung.
    """
    
    def __init__(self, token: OptimizedCancellationToken):
        self.token = token
        self._cleanup_callbacks: List[Callable] = []
        self._current_task: Optional[asyncio.Task] = None
    
    async def __aenter__(self):
        # Registriere aktuellen Task falls in async context
        try:
            self._current_task = asyncio.current_task()
            if self._current_task:
                self.token.register_task(self._current_task)
        except RuntimeError:
            pass  # Nicht in async context
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Führe Cleanup aus
        if self.token.is_cancelled() or exc_type == CancellationException:
            for callback in self._cleanup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")
        
        # Propagiere CancellationException
        if exc_type == CancellationException:
            return False
        
        return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Sync cleanup
        if self.token.is_cancelled():
            for callback in self._cleanup_callbacks:
                try:
                    if not asyncio.iscoroutinefunction(callback):
                        callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")
        return False
    
    def add_cleanup(self, callback: Callable[[], Any]):
        """Fügt einen Cleanup-Callback hinzu"""
        self._cleanup_callbacks.append(callback)


def create_linked_tokens(*tokens: OptimizedCancellationToken) -> OptimizedCancellationToken:
    """
    Erstellt einen neuen Token der mit anderen Tokens verlinkt ist.
    Wenn einer der verlinkten Tokens cancelled wird, wird auch der neue Token cancelled.
    
    Args:
        *tokens: Die zu verlinkenden Tokens
        
    Returns:
        Ein neuer verlinkter Token
    """
    linked_token = OptimizedCancellationToken("linked")
    
    def cancel_linked():
        # Check if any parent token is cancelled
        for token in tokens:
            if token.is_cancelled():
                info = token.get_cancel_info()
                reason = info.get("cancel_reason", "Parent token cancelled") if info else "Parent token cancelled"
                linked_token.cancel(f"Linked cancellation: {reason}")
                break
    
    # Registriere callback auf allen parent tokens
    for token in tokens:
        token.register_callback(cancel_linked)
    
    # Initial check falls bereits cancelled
    cancel_linked()
    
    return linked_token