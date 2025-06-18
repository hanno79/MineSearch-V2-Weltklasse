"""
Rate Limiting für API-Anfragen
"""
import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token Bucket Rate Limiter"""
    
    def __init__(self, rate: int, per: float = 60.0):
        """
        Args:
            rate: Anzahl erlaubter Anfragen
            per: Zeitraum in Sekunden (default: 60 = 1 Minute)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1):
        """Wartet bis Token verfügbar"""
        async with self._lock:
            while tokens > self.allowance:
                # Berechne wie lange gewartet werden muss
                elapsed = time.monotonic() - self.last_check
                self.allowance += elapsed * (self.rate / self.per)
                
                if self.allowance > self.rate:
                    self.allowance = self.rate
                
                self.last_check = time.monotonic()
                
                if tokens > self.allowance:
                    # Warte bis genug Tokens verfügbar
                    sleep_time = (tokens - self.allowance) * (self.per / self.rate)
                    await asyncio.sleep(sleep_time)
            
            self.allowance -= tokens