"""
Author: rahn
Datum: 26.06.2025
Version: 1.0
Beschreibung: HTTP Request Utilities mit Cancellation Support
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import time

from src.core.cancellation import CancellationToken, CancellationException
from src.core.logger import get_logger

logger = get_logger("cancellable_http")


class CancellableHTTPClient:
    """HTTP Client mit eingebauter Cancellation-Unterstützung"""
    
    def __init__(self, session: aiohttp.ClientSession, default_timeout: int = 30):
        self.session = session
        self.default_timeout = default_timeout
    
    async def request(
        self,
        method: str,
        url: str,
        cancellation_token: Optional[CancellationToken] = None,
        timeout: Optional[int] = None,
        check_interval: float = 0.5,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Führt einen HTTP Request mit Cancellation-Support aus.
        
        Args:
            method: HTTP Methode (GET, POST, etc.)
            url: Ziel-URL
            cancellation_token: Optional CancellationToken
            timeout: Request timeout in Sekunden
            check_interval: Interval für Cancellation-Checks
            **kwargs: Weitere aiohttp request Parameter
            
        Returns:
            aiohttp.ClientResponse
            
        Raises:
            CancellationException: Wenn Request abgebrochen wurde
        """
        # Check cancellation vor Start
        if cancellation_token and cancellation_token.is_cancelled():
            raise CancellationException("Request cancelled before execution")
        
        # Timeout handling
        timeout_value = timeout or self.default_timeout
        if 'timeout' not in kwargs:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=timeout_value)
        
        # Erstelle Request Task
        request_task = asyncio.create_task(
            self.session.request(method, url, **kwargs)
        )
        
        # Falls kein Cancellation Token, führe normal aus
        if not cancellation_token:
            return await request_task
        
        # Mit Cancellation Token: Poll für Abbruch
        start_time = time.time()
        while not request_task.done():
            # Check cancellation
            if cancellation_token.is_cancelled():
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
                raise CancellationException(f"Request to {url} cancelled")
            
            # Check timeout
            if time.time() - start_time > timeout_value:
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
                raise asyncio.TimeoutError(f"Request to {url} timed out after {timeout_value}s")
            
            # Warte kurz bevor nächster Check
            try:
                await asyncio.wait_for(
                    asyncio.shield(request_task),
                    timeout=check_interval
                )
            except asyncio.TimeoutError:
                # Normal - request noch nicht fertig
                continue
        
        # Request ist fertig
        return await request_task
    
    @asynccontextmanager
    async def get(
        self,
        url: str,
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs
    ):
        """Convenience Method für GET requests"""
        response = await self.request(
            'GET', url, cancellation_token=cancellation_token, **kwargs
        )
        try:
            yield response
        finally:
            response.release()
    
    @asynccontextmanager
    async def post(
        self,
        url: str,
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs
    ):
        """Convenience Method für POST requests"""
        response = await self.request(
            'POST', url, cancellation_token=cancellation_token, **kwargs
        )
        try:
            yield response
        finally:
            response.release()


async def cancellable_fetch(
    session: Union[aiohttp.ClientSession, Any],
    url: str,
    cancellation_token: Optional[CancellationToken] = None,
    method: str = 'GET',
    timeout: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """
    Utility Funktion für einfache cancellable HTTP Requests.
    
    Returns:
        Dict mit status, text, headers
    """
    # Falls session ein SessionManager object ist, hole die echte Session
    if hasattr(session, 'get_session'):
        actual_session = await session.get_session()
    else:
        actual_session = session
    
    client = CancellableHTTPClient(actual_session, default_timeout=timeout)
    
    try:
        response = await client.request(
            method, url, 
            cancellation_token=cancellation_token,
            **kwargs
        )
        
        # Lese Response
        text = await response.text()
        
        return {
            'status': response.status,
            'text': text,
            'headers': dict(response.headers),
            'url': str(response.url)
        }
        
    except CancellationException:
        logger.info(f"Fetch to {url} was cancelled")
        raise
    except asyncio.TimeoutError:
        logger.warning(f"Fetch to {url} timed out")
        raise
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise


async def parallel_fetch_with_cancellation(
    urls: list[str],
    session: Union[aiohttp.ClientSession, Any],
    cancellation_token: Optional[CancellationToken] = None,
    max_concurrent: int = 5,
    timeout_per_request: int = 30
) -> list[Dict[str, Any]]:
    """
    Führt mehrere HTTP Requests parallel mit Cancellation-Support aus.
    
    Args:
        urls: Liste der URLs
        session: aiohttp Session oder SessionManager
        cancellation_token: Optional CancellationToken
        max_concurrent: Maximale gleichzeitige Requests
        timeout_per_request: Timeout pro Request
        
    Returns:
        Liste der Response Dicts (None für fehlgeschlagene Requests)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(url: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                # Check cancellation vor jedem Request
                if cancellation_token and cancellation_token.is_cancelled():
                    return None
                    
                return await cancellable_fetch(
                    session, url,
                    cancellation_token=cancellation_token,
                    timeout=timeout_per_request
                )
            except (CancellationException, asyncio.CancelledError):
                logger.debug(f"Request to {url} cancelled")
                return None
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                return None
    
    # Erstelle Tasks
    tasks = [fetch_with_semaphore(url) for url in urls]
    
    # Falls Cancellation Token vorhanden, registriere Cancel-Handler
    if cancellation_token:
        def cancel_all_tasks():
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        cancellation_token.register_callback(cancel_all_tasks)
    
    # Führe alle Tasks aus
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filtere Exceptions
    clean_results = []
    for result in results:
        if isinstance(result, Exception):
            clean_results.append(None)
        else:
            clean_results.append(result)
    
    return clean_results