"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Cancellation Token für sauberen Abbruch von Suchvorgängen
"""

import asyncio
import threading
from typing import Optional, Callable, Any, List
from datetime import datetime

from .logger import get_logger

logger = get_logger("cancellation")


class CancellationToken:
    """
    Thread-sicherer Cancellation Token für Abbruch von asynchronen Operationen.
    
    Ermöglicht sauberes Beenden von langläufigen Suchvorgängen mit
    vollständigem Cleanup aller Ressourcen.
    """
    
    def __init__(self, name: str = "default"):
        """
        Initialisiert einen neuen Cancellation Token.
        
        Args:
            name: Beschreibender Name für Logging
        """
        self.name = name
        self._cancelled = False
        self._cancel_time: Optional[datetime] = None
        self._cancel_reason: Optional[str] = None
        self._lock = threading.Lock()
        self._event = asyncio.Event()
        self._callbacks: list[Callable[[], Any]] = []
        
    def cancel(self, reason: str = "User requested cancellation"):
        """
        Setzt den Cancellation Token und löst alle Callbacks aus.
        
        Args:
            reason: Grund für den Abbruch
        """
        with self._lock:
            if self._cancelled:
                return  # Bereits abgebrochen
                
            self._cancelled = True
            self._cancel_time = datetime.now()
            self._cancel_reason = reason
            
            logger.info(f"CancellationToken '{self.name}' cancelled: {reason}")
            
            # Setze asyncio Event für async Waits
            try:
                # ÄNDERUNG 23.06.2025: Verwende get_running_loop statt get_event_loop
                # Event könnte in anderem Thread sein
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self._event.set)
            except RuntimeError:
                # Kein Event Loop im aktuellen Thread - versuche Event Loop Manager
                try:
                    from .event_loop_manager import get_event_loop_manager
                    manager = get_event_loop_manager()
                    if manager.is_running():
                        manager.get_loop().call_soon_threadsafe(self._event.set)
                except:
                    # Event Loop Manager nicht verfügbar
                    pass
            
            # Führe Callbacks aus
            for callback in self._callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cancellation callback: {e}")
    
    def is_cancelled(self) -> bool:
        """
        Prüft ob der Token abgebrochen wurde.
        
        Returns:
            True wenn abgebrochen, sonst False
        """
        with self._lock:
            return self._cancelled
    
    async def check_cancelled(self):
        """
        Async-Check mit Exception wenn abgebrochen.
        
        Raises:
            CancellationException: Wenn Token abgebrochen wurde
        """
        if self.is_cancelled():
            raise CancellationException(self._cancel_reason or "Operation cancelled")
    
    def check_cancelled_sync(self):
        """
        Synchroner Check mit Exception wenn abgebrochen.
        
        Raises:
            CancellationException: Wenn Token abgebrochen wurde
        """
        if self.is_cancelled():
            raise CancellationException(self._cancel_reason or "Operation cancelled")
    
    async def wait_for_cancellation(self):
        """
        Wartet asynchron bis der Token abgebrochen wird.
        """
        await self._event.wait()
    
    def register_callback(self, callback: Callable[[], Any]):
        """
        Registriert einen Callback der bei Abbruch aufgerufen wird.
        
        Args:
            callback: Funktion die bei Abbruch aufgerufen wird
        """
        with self._lock:
            self._callbacks.append(callback)
            # Falls bereits abgebrochen, rufe Callback sofort auf
            if self._cancelled:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cancellation callback: {e}")
    
    def get_cancel_info(self) -> Optional[dict]:
        """
        Gibt Informationen über den Abbruch zurück.
        
        Returns:
            Dict mit cancel_time und cancel_reason oder None
        """
        with self._lock:
            if not self._cancelled:
                return None
            return {
                "cancel_time": self._cancel_time,
                "cancel_reason": self._cancel_reason
            }
    
    def reset(self):
        """
        Setzt den Token zurück (nur für Tests/Entwicklung).
        """
        with self._lock:
            self._cancelled = False
            self._cancel_time = None
            self._cancel_reason = None
            self._event.clear()
    
    def cleanup(self):
        """
        ÄNDERUNG 21.06.2025: Cleanup-Methode für sauberes Beenden von Tasks
        """
        # Setze Event um wartende Tasks zu beenden
        self._event.set()
        # Markiere als abgebrochen für sauberen Cleanup
        with self._lock:
            if not self._cancelled:
                self._cancelled = True
                self._cancel_time = datetime.now()
                self._cancel_reason = "Cleanup"
            logger.debug(f"CancellationToken '{self.name}' reset")


class CancellationException(Exception):
    """Exception die bei Abbruch geworfen wird"""
    pass


class CancellationScope:
    """
    Context Manager für Cancellation Tokens.
    
    Ermöglicht automatisches Cleanup bei Abbruch.
    """
    
    def __init__(self, token: CancellationToken):
        self.token = token
        self._cleanup_callbacks: List[Callable] = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Bei Abbruch führe Cleanup aus
        if self.token.is_cancelled():
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")
        return False
    
    def add_cleanup(self, callback: Callable[[], Any]):
        """Fügt einen Cleanup-Callback hinzu"""
        self._cleanup_callbacks.append(callback)