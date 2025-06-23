"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Retry-Mechanismus für API-Aufrufe
"""

import asyncio
import functools
from typing import TypeVar, Callable, Any
from src.core.logger import get_logger

logger = get_logger("retry_utils")

T = TypeVar('T')


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator für Retry-Mechanismus bei async Funktionen
    
    Args:
        max_attempts: Maximale Anzahl von Versuchen
        delay: Initiale Wartezeit zwischen Versuchen
        backoff: Faktor für exponentielles Backoff
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Alle {max_attempts} Versuche fehlgeschlagen für {func.__name__}: {e}")
                        raise
                    
                    logger.warning(f"Versuch {attempt + 1}/{max_attempts} fehlgeschlagen für {func.__name__}: {e}")
                    logger.info(f"Warte {current_delay}s vor erneutem Versuch...")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator