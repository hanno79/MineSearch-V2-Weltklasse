"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: SessionManager ohne globale Instanz, nur noch pro Event Loop verwendbar
# ÄNDERUNG 27.06.2025: Globale Instanz entfernt, nur noch explizite SessionManager-Objekte
"""

import asyncio
import aiohttp
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import weakref
from contextlib import asynccontextmanager
from src.core.logger import get_logger

logger = get_logger("session_manager")


class RobustSession:
    """Wrapper für aiohttp ClientSession mit automatischer Wiederherstellung"""
    
    def __init__(self, session_id: str, timeout: int = 60, connector_limit: int = 10):
        self.session_id = session_id
        self.timeout = timeout
        self.connector_limit = connector_limit
        self._session: Optional[aiohttp.ClientSession] = None
        self._creation_time: Optional[datetime] = None
        self._usage_count = 0
        self._max_usage = 100  # Nach 100 Requests neue Session
        self._max_age = timedelta(minutes=30)  # Nach 30 Minuten neue Session
        self._lock = asyncio.Lock()
        
    async def _create_session(self) -> aiohttp.ClientSession:
        """Erstellt eine neue Session mit robusten Einstellungen"""
        # ÄNDERUNG 26.06.2025: Erstelle Session ohne default timeout,
        # um 'Timeout context manager should be used inside a task' zu vermeiden
        timeout = None  # Timeout wird pro Request gesetzt
        
        connector = aiohttp.TCPConnector(
            limit=self.connector_limit,
            limit_per_host=5,
            force_close=True,
            enable_cleanup_closed=True,
            ttl_dns_cache=300  # 5 Minuten DNS Cache
        )
        
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            connector_owner=True,
            raise_for_status=False
        )
        
        self._creation_time = datetime.now()
        self._usage_count = 0
        logger.debug(f"Neue Session erstellt für {self.session_id}")
        
        return session
    
    async def _should_recreate(self) -> bool:
        """Prüft ob Session neu erstellt werden sollte"""
        if not self._session or self._session.closed:
            return True
            
        if self._usage_count >= self._max_usage:
            logger.debug(f"Session {self.session_id} hat max. Requests erreicht")
            return True
            
        if self._creation_time and (datetime.now() - self._creation_time) > self._max_age:
            logger.debug(f"Session {self.session_id} ist zu alt")
            return True
            
        return False
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Gibt eine aktive Session zurück, erstellt bei Bedarf eine neue"""
        async with self._lock:
            if await self._should_recreate():
                # Schließe alte Session falls vorhanden
                if self._session and not self._session.closed:
                    try:
                        await self._session.close()
                        # Kurze Pause für sauberes Cleanup
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.debug(f"Fehler beim Schließen alter Session: {e}")
                
                # Erstelle neue Session
                self._session = await self._create_session()
            
            self._usage_count += 1
            return self._session
    
    async def close(self):
        """Schließt die Session explizit"""
        async with self._lock:
            if self._session and not self._session.closed:
                try:
                    await self._session.close()
                    await asyncio.sleep(0.1)
                    logger.debug(f"Session {self.session_id} geschlossen")
                except Exception as e:
                    logger.error(f"Fehler beim Schließen der Session {self.session_id}: {e}")
                finally:
                    self._session = None
    
    @asynccontextmanager
    async def request(self, method: str, url: str, **kwargs):
        """Context Manager für robuste Requests mit automatischer Session-Verwaltung"""
        session = await self.get_session()
        
        # ÄNDERUNG 26.06.2025: Verbesserte Timeout-Behandlung
        # Setze Timeout nur wenn wir in einem Task sind
        if 'timeout' in kwargs:
            timeout_value = kwargs.pop('timeout')
            if isinstance(timeout_value, (int, float)):
                try:
                    # Prüfe ob wir in einem Task sind
                    asyncio.current_task()
                    kwargs['timeout'] = aiohttp.ClientTimeout(total=timeout_value)
                except RuntimeError:
                    # Nicht in einem Task, verwende Session ohne Timeout
                    logger.debug("Nicht in einem Task, verwende Request ohne Timeout")
                    pass
        
        # ÄNDERUNG 26.06.2025: Unterstütze Cancellation Token
        cancellation_token = kwargs.pop('cancellation_token', None)
        
        try:
            # Prüfe Cancellation vor Request
            if cancellation_token and cancellation_token.is_cancelled():
                raise asyncio.CancelledError("Request cancelled before execution")
                
            async with session.request(method, url, **kwargs) as response:
                yield response
                
        except asyncio.CancelledError:
            logger.info(f"Request zu {url} wurde abgebrochen")
            raise
        except aiohttp.ClientError as e:
            # Bei bestimmten Fehlern Session neu erstellen
            if isinstance(e, (aiohttp.ServerDisconnectedError, aiohttp.ClientOSError)):
                logger.warning(f"Connection Error für {self.session_id}, erstelle neue Session")
                async with self._lock:
                    if self._session:
                        try:
                            await self._session.close()
                        except:
                            pass
                        self._session = None
            raise


class SessionManager:
    """Globaler Session Manager für alle Agenten"""
    
    def __init__(self):
        self._sessions: Dict[str, RobustSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        # Verwende WeakValueDictionary für automatisches Cleanup
        self._weak_sessions = weakref.WeakValueDictionary()
        # ÄNDERUNG 26.06.2025: Track Cancellation Tokens für Sessions
        self._cancellation_tokens: Dict[str, Any] = {}
        
    async def get_session(self, agent_id: str, **session_kwargs) -> aiohttp.ClientSession:
        logger.debug(f"[SessionManager] get_session({agent_id}) aufgerufen im Loop {id(asyncio.get_event_loop())}")
        async with self._lock:
            if agent_id not in self._sessions:
                logger.debug(f"[SessionManager] Erstelle neue RobustSession für {agent_id} im Loop {id(asyncio.get_event_loop())}")
                self._sessions[agent_id] = RobustSession(agent_id, **session_kwargs)
                self._weak_sessions[agent_id] = self._sessions[agent_id]
            robust_session = self._sessions[agent_id]
            return await robust_session.get_session()
    
    async def get_robust_session(self, agent_id: str, **session_kwargs) -> RobustSession:
        """Gibt die RobustSession Instanz zurück für erweiterte Kontrolle"""
        async with self._lock:
            if agent_id not in self._sessions:
                self._sessions[agent_id] = RobustSession(agent_id, **session_kwargs)
                self._weak_sessions[agent_id] = self._sessions[agent_id]
                
            return self._sessions[agent_id]
    
    def register_cancellation_token(self, agent_id: str, token):
        """ÄNDERUNG 26.06.2025: Registriert einen Cancellation Token für einen Agenten"""
        self._cancellation_tokens[agent_id] = token
    
    async def cancel_agent_session(self, agent_id: str, reason: str = "Cancelled"):
        """ÄNDERUNG 26.06.2025: Bricht die Session eines Agenten ab und schließt sie"""
        logger.info(f"Breche Session für {agent_id} ab: {reason}")
        await self.close_session(agent_id)
    
    async def close_session(self, agent_id: str):
        logger.debug(f"[SessionManager] close_session({agent_id}) im Loop {id(asyncio.get_event_loop())}")
        async with self._lock:
            if agent_id in self._sessions:
                try:
                    await self._sessions[agent_id].close()
                except Exception as e:
                    logger.error(f"Fehler beim Schließen der Session {agent_id}: {e}")
                finally:
                    del self._sessions[agent_id]
    
    async def close_all(self):
        logger.debug(f"[SessionManager] close_all() im Loop {id(asyncio.get_event_loop())}")
        async with self._lock:
            close_tasks = []
            for session_id, robust_session in list(self._sessions.items()):
                close_tasks.append(robust_session.close())
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            self._sessions.clear()
            self._cancellation_tokens.clear()  # ÄNDERUNG: Clear tokens
            logger.info("Alle Sessions geschlossen")
    
    async def start_cleanup_task(self):
        logger.debug(f"[SessionManager] start_cleanup_task() im Loop {id(asyncio.get_event_loop())}")
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop_cleanup_task(self):
        logger.debug(f"[SessionManager] stop_cleanup_task() im Loop {id(asyncio.get_event_loop())}")
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _periodic_cleanup(self):
        logger.debug(f"[SessionManager] _periodic_cleanup() gestartet im Loop {id(asyncio.get_event_loop())}")
        while True:
            try:
                await asyncio.sleep(300)
                async with self._lock:
                    to_remove = []
                    for agent_id in list(self._sessions.keys()):
                        # ÄNDERUNG: Prüfe auch ob Cancellation Token gesetzt und abgebrochen wurde
                        is_cancelled = False
                        if agent_id in self._cancellation_tokens:
                            token = self._cancellation_tokens[agent_id]
                            if hasattr(token, 'is_cancelled') and token.is_cancelled():
                                is_cancelled = True
                                
                        if agent_id not in self._weak_sessions or is_cancelled:
                            to_remove.append(agent_id)
                            
                    for agent_id in to_remove:
                        logger.debug(f"Cleanup: Entferne {'abgebrochene' if agent_id in self._cancellation_tokens else 'nicht mehr referenzierte'} Session {agent_id}")
                        try:
                            await self._sessions[agent_id].close()
                        except:
                            pass
                        del self._sessions[agent_id]
                        if agent_id in self._cancellation_tokens:
                            del self._cancellation_tokens[agent_id]
            except asyncio.CancelledError:
                logger.debug(f"[SessionManager] _periodic_cleanup() abgebrochen im Loop {id(asyncio.get_event_loop())}")
                break
            except Exception as e:
                logger.error(f"Fehler im Cleanup Task: {e}")