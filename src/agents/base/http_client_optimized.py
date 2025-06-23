"""
Author: rahn
Datum: 23.06.2025
Version: 2.0
Beschreibung: Optimierter HTTP Client mit Connection Pooling und Retry-Optimierung
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlencode
import json
import time
from contextlib import asynccontextmanager

from src.core.logger import get_logger


class OptimizedHTTPClient:
    """
    Optimierter HTTP Client mit:
    - Connection Pooling
    - Smart Retry Logic
    - Request Batching
    - Response Caching
    """
    
    def __init__(self, 
                 base_url: Optional[str] = None,
                 default_headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 pool_size: int = 100,
                 pool_connections_per_host: int = 30):
        
        self.logger = get_logger(self.__class__.__name__)
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        
        # Connection Pool mit optimierten Einstellungen
        self.connector = aiohttp.TCPConnector(
            limit=pool_size,
            limit_per_host=pool_connections_per_host,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=False,
            keepalive_timeout=30
        )
        
        # Session mit Connection Pool
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout,
            headers=self.default_headers,
            connector_owner=True
        )
        
        # Request-Statistiken
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries': 0,
            'total_time': 0.0
        }
        
        # Response Cache (einfacher In-Memory Cache)
        self._response_cache = {}
        self._cache_ttl = 300  # 5 Minuten
    
    async def get(self, 
                  endpoint: str, 
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  use_cache: bool = True) -> Dict[str, Any]:
        """Optimierter GET Request mit Caching"""
        # Cache-Key generieren
        cache_key = f"{endpoint}?{urlencode(params or {})}"
        
        # Check Cache
        if use_cache and cache_key in self._response_cache:
            cached_data, cached_time = self._response_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                self.logger.debug(f"Cache hit for {endpoint}")
                return cached_data
        
        # Führe Request aus
        result = await self._request('GET', endpoint, params=params, headers=headers)
        
        # Cache Ergebnis
        if use_cache and result:
            self._response_cache[cache_key] = (result, time.time())
            # Bereinige alten Cache
            self._cleanup_cache()
        
        return result
    
    async def post(self,
                   endpoint: str,
                   json_data: Optional[Dict[str, Any]] = None,
                   data: Optional[Any] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """POST Request"""
        return await self._request(
            'POST', 
            endpoint, 
            json_data=json_data,
            data=data,
            headers=headers
        )
    
    async def post_batch(self,
                        endpoint: str,
                        batch_data: List[Dict[str, Any]],
                        batch_size: int = 10,
                        headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Batch POST Requests für bessere Performance"""
        results = []
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            
            # Parallele Requests für Batch
            batch_tasks = [
                self.post(endpoint, json_data=item, headers=headers)
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Verarbeite Ergebnisse
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch request failed: {result}")
                    results.append({'error': str(result)})
                else:
                    results.append(result)
            
            # Kleine Pause zwischen Batches
            if i + batch_size < len(batch_data):
                await asyncio.sleep(0.1)
        
        return results
    
    async def _request(self,
                      method: str,
                      endpoint: str,
                      params: Optional[Dict[str, Any]] = None,
                      json_data: Optional[Dict[str, Any]] = None,
                      data: Optional[Any] = None,
                      headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Interner Request mit Smart Retry Logic"""
        url = self._build_url(endpoint)
        headers = {**self.default_headers, **(headers or {})}
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self._stats['total_requests'] += 1
                
                # Exponential Backoff bei Retries
                if attempt > 0:
                    wait_time = min(2 ** attempt, 30)  # Max 30 Sekunden
                    self.logger.info(f"Retry {attempt}/{self.max_retries} nach {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    self._stats['retries'] += 1
                
                # Request ausführen
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=headers
                ) as response:
                    # Rate Limit Headers prüfen
                    self._check_rate_limits(response)
                    
                    # Erfolgreiche Response
                    if response.status < 400:
                        result = await self._parse_response(response)
                        self._stats['successful_requests'] += 1
                        self._stats['total_time'] += time.time() - start_time
                        return result
                    
                    # Client-Fehler (4xx) - meist kein Retry sinnvoll
                    elif 400 <= response.status < 500:
                        if response.status == 429:  # Rate Limit
                            retry_after = response.headers.get('Retry-After', 60)
                            self.logger.warning(f"Rate limit erreicht. Warte {retry_after}s...")
                            await asyncio.sleep(int(retry_after))
                            continue
                        else:
                            error_text = await response.text()
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=error_text
                            )
                    
                    # Server-Fehler (5xx) - Retry sinnvoll
                    else:
                        last_exception = aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                        continue
                        
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Request timeout nach {self.timeout.total}s")
                self.logger.warning(f"Timeout bei {url}")
                
            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning(f"Client error bei {url}: {e}")
                
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unerwarteter Fehler bei {url}: {e}")
                break
        
        # Alle Versuche fehlgeschlagen
        self._stats['failed_requests'] += 1
        self._stats['total_time'] += time.time() - start_time
        
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"Request fehlgeschlagen nach {self.max_retries} Versuchen")
    
    def _build_url(self, endpoint: str) -> str:
        """Baut vollständige URL"""
        if endpoint.startswith('http'):
            return endpoint
        
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        return endpoint
    
    async def _parse_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Parsed Response abhängig vom Content-Type"""
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            return await response.json()
        elif 'text/' in content_type:
            text = await response.text()
            return {'text': text}
        else:
            # Binary content
            content = await response.read()
            return {'content': content, 'content_type': content_type}
    
    def _check_rate_limits(self, response: aiohttp.ClientResponse):
        """Prüft und loggt Rate Limit Headers"""
        rate_limit = response.headers.get('X-RateLimit-Limit')
        rate_remaining = response.headers.get('X-RateLimit-Remaining')
        rate_reset = response.headers.get('X-RateLimit-Reset')
        
        if rate_limit and rate_remaining:
            remaining_pct = int(rate_remaining) / int(rate_limit) * 100
            if remaining_pct < 20:
                self.logger.warning(
                    f"Rate Limit Warning: {rate_remaining}/{rate_limit} "
                    f"({remaining_pct:.1f}%) verbleibend"
                )
    
    def _cleanup_cache(self):
        """Bereinigt abgelaufene Cache-Einträge"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, cached_time) in self._response_cache.items()
            if current_time - cached_time > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._response_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        stats = self._stats.copy()
        
        if stats['successful_requests'] > 0:
            stats['avg_request_time'] = stats['total_time'] / stats['successful_requests']
        else:
            stats['avg_request_time'] = 0
        
        stats['success_rate'] = (
            stats['successful_requests'] / stats['total_requests'] 
            if stats['total_requests'] > 0 else 0
        )
        
        stats['cache_size'] = len(self._response_cache)
        stats['active_connections'] = len(self.connector._acquired)
        
        return stats
    
    async def health_check(self) -> bool:
        """Prüft ob der Client funktioniert"""
        try:
            # Einfacher Test-Request
            async with self.session.get('https://httpbin.org/get', timeout=5) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self):
        """Schließt Session und Connector"""
        if self.session:
            await self.session.close()
        
        # Warte auf Cleanup
        await asyncio.sleep(0.25)
        
        self.logger.info(f"HTTP Client geschlossen. Stats: {self.get_stats()}")