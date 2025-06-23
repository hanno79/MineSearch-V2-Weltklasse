"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Gemeinsamer HTTP Client für alle Agenten
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Any, Union
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class BaseHTTPClient:
    """Basis HTTP Client mit gemeinsamen Features für alle Agenten"""
    
    def __init__(self, 
                 timeout: int = 30,
                 max_retries: int = 3,
                 rate_limit: Optional[float] = None,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialisiert den HTTP Client
        
        Args:
            timeout: Request timeout in Sekunden
            max_retries: Maximale Anzahl von Wiederholungen
            rate_limit: Minimale Zeit zwischen Requests in Sekunden
            headers: Standard-Headers für alle Requests
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.default_headers = headers or {}
        self._last_request_time = 0
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context Manager Entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        await self.close()
    
    async def start(self):
        """Startet die HTTP Session"""
        if not self._session:
            # ÄNDERUNG 23.06.2025: Stelle sicher, dass Session im aktuellen Event Loop erstellt wird
            try:
                loop = asyncio.get_running_loop()
                self._session = aiohttp.ClientSession(
                    timeout=self.timeout,
                    headers=self.default_headers,
                    loop=loop
                )
            except RuntimeError:
                # Kein laufender Event Loop - erstelle Session ohne expliziten Loop
                self._session = aiohttp.ClientSession(
                    timeout=self.timeout,
                    headers=self.default_headers
                )
    
    async def close(self):
        """Schließt die HTTP Session"""
        if self._session:
            # ÄNDERUNG 23.06.2025: Prüfe ob Session noch gültig ist bevor Schließen
            try:
                if not self._session.closed:
                    await self._session.close()
            except Exception as e:
                logger.warning(f"Fehler beim Schließen der Session: {e}")
            finally:
                self._session = None
    
    async def _apply_rate_limit(self):
        """Wendet Rate Limiting an"""
        if self.rate_limit:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self._last_request_time = time.time()
    
    async def request(self,
                     method: str,
                     url: str,
                     headers: Optional[Dict[str, str]] = None,
                     **kwargs) -> Union[Dict, str, bytes]:
        """
        Führt einen HTTP Request mit Retry-Logic aus
        
        Args:
            method: HTTP Methode (GET, POST, etc.)
            url: Ziel-URL
            headers: Zusätzliche Headers
            **kwargs: Weitere aiohttp Request Parameter
            
        Returns:
            Response als Dict, String oder Bytes
        """
        # ÄNDERUNG 23.06.2025: Prüfe ob Session gültig ist
        if not self._session or self._session.closed:
            await self.start()
        
        # Rate Limiting anwenden
        await self._apply_rate_limit()
        
        # Headers kombinieren
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with self._session.request(
                    method, 
                    url, 
                    headers=request_headers,
                    **kwargs
                ) as response:
                    # Erfolgreiche Response
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'application/json' in content_type:
                            return await response.json()
                        elif 'text' in content_type:
                            return await response.text()
                        else:
                            return await response.read()
                    
                    # Rate Limit erreicht
                    elif response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limit erreicht. Warte {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Andere Fehler
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"
                        logger.warning(f"Request fehlgeschlagen: {last_error}")
                        
            except asyncio.TimeoutError:
                last_error = f"Timeout nach {self.timeout.total}s"
                logger.warning(f"Request Timeout: {url}")
                
            except aiohttp.ClientError as e:
                last_error = f"Client Error: {str(e)}"
                logger.warning(f"Client Error: {str(e)}")
                
            except Exception as e:
                last_error = f"Unerwarteter Fehler: {str(e)}"
                logger.error(f"Unerwarteter Fehler: {str(e)}")
            
            # Exponential Backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Wiederhole Request in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # Alle Versuche fehlgeschlagen
        raise Exception(f"Request fehlgeschlagen nach {self.max_retries} Versuchen: {last_error}")
    
    async def get(self, url: str, **kwargs) -> Union[Dict, str]:
        """GET Request"""
        return await self.request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Union[Dict, str]:
        """POST Request"""
        return await self.request('POST', url, **kwargs)
    
    def with_retry(self, func):
        """Decorator für automatische Wiederholungen"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Wiederhole {func.__name__} in {wait_time}s...")
                        await asyncio.sleep(wait_time)
            raise last_error
        return wrapper