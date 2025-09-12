"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Caching-Service für MineSearch zur Performance-Optimierung
"""

import time
import hashlib
import json
import logging
import threading
import weakref
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheService:
    """
    In-Memory Cache Service für MineSearch

    Features:
    - TTL (Time-To-Live) Unterstützung
    - LRU (Least Recently Used) Eviction
    - Cache-Statistiken
    """

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Args:
            max_size: Maximale Anzahl von Cache-Einträgen
            default_ttl: Standard TTL in Sekunden (1 Stunde)
        """
        # PERFORMANCE-FIX: OrderedDict für effiziente LRU-Operationen
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

        # MEMORY-LEAK-FIX: Thread-Lock für Thread-Safety
        self._lock = threading.RLock()

        # MEMORY-LEAK-FIX: Automatischer Cleanup-Timer
        self._cleanup_timer = None
        self._start_cleanup_timer()

        logger.info(f"[CACHE] Cache-Service initialisiert (max_size={max_size}, ttl={default_ttl}s)")

    def _generate_key(self, mine_name: str, country: str, model: str, **kwargs) -> str:
        """Generiere eindeutigen Cache-Key"""
        # Erstelle deterministischen Key aus Parametern
        key_parts = [
            f"mine:{mine_name.lower()}",
            f"country:{(country or 'any').lower()}",
            f"model:{model.lower()}"
        ]

        # Füge zusätzliche Parameter hinzu
        for k, v in sorted(kwargs.items()):
            if v:
                key_parts.append(f"{k}:{str(v).lower()}")

        key_string = "|".join(key_parts)

        # Erstelle Hash für kompakten Key
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, mine_name: str, country: str, model: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Hole Wert aus Cache

        Returns:
            Gecachter Wert oder None wenn nicht vorhanden/abgelaufen
        """
        key = self._generate_key(mine_name, country, model, **kwargs)

        with self._lock:
            if key in self.cache:
                entry = self.cache[key]

                # Prüfe ob abgelaufen
                if time.time() < entry['expires_at']:
                    # PERFORMANCE-FIX: OrderedDict move_to_end für LRU
                    self.cache.move_to_end(key)
                    self.stats['hits'] += 1

                    logger.info(f"[CACHE HIT] Mine: {mine_name}, Model: {model}")
                    return entry['value']
                else:
                    # Abgelaufen - entfernen
                    del self.cache[key]
                    # PERFORMANCE-FIX: Reduziere Debug-Logging
                    # logger.debug(f"[CACHE EXPIRED] Key: {key}")

            self.stats['misses'] += 1
            return None

    def set(self, mine_name: str, country: str, model: str, value: Dict[str, Any],
    """set - TODO: Dokumentation hinzufügen"""
            ttl: Optional[int] = None, **kwargs) -> None:
        """
        Speichere Wert im Cache

        Args:
            ttl: Time-to-live in Sekunden (überschreibt default_ttl)
        """
        key = self._generate_key(mine_name, country, model, **kwargs)
        ttl = ttl or self.default_ttl

        with self._lock:
            # PERFORMANCE-FIX: OrderedDict LRU-Eviction
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Entferne ältesten Eintrag (FIFO/LRU)
                oldest_key, oldest_entry = self.cache.popitem(last=False)
                self.stats['evictions'] += 1
                # PERFORMANCE-FIX: Reduziere Debug-Logging
                # logger.debug(f"[CACHE EVICT] Mine: {oldest_entry['mine_name']}, Model: {oldest_entry['model']}")

            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time(),
                'mine_name': mine_name,
                'model': model
            }

            # PERFORMANCE-FIX: Move to end für LRU
            self.cache.move_to_end(key)

            self.stats['sets'] += 1
            logger.info(f"[CACHE SET] Mine: {mine_name}, Model: {model}, TTL: {ttl}s")

    def _evict_lru(self) -> None:
        """Entferne am längsten nicht genutzten Eintrag"""
        if not self.cache:
            return

        # Finde ältesten Eintrag
        lru_key = min(self.cache.keys(),
                     key=lambda k: self.cache[k]['last_accessed'])

        entry = self.cache[lru_key]
        del self.cache[lru_key]
        self.stats['evictions'] += 1

        # PERFORMANCE-FIX: Reduziere Debug-Logging
        # logger.debug(f"[CACHE EVICT] Mine: {entry['mine_name']}, Model: {entry['model']}")

    def invalidate(self, mine_name: Optional[str] = None, model: Optional[str] = None) -> int:
        """
        Invalidiere Cache-Einträge

        Args:
            mine_name: Wenn angegeben, nur Einträge für diese Mine
            model: Wenn angegeben, nur Einträge für dieses Modell

        Returns:
            Anzahl invalidierter Einträge
        """
        if not mine_name and not model:
            # Clear all
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"[CACHE CLEAR] Alle {count} Einträge entfernt")
            return count

        # Selektives Löschen
        to_delete = []
        for key, entry in self.cache.items():
            if mine_name and entry['mine_name'].lower() != mine_name.lower():
                continue
            if model and entry['model'].lower() != model.lower():
                continue
            to_delete.append(key)

        for key in to_delete:
            del self.cache[key]

        logger.info(f"[CACHE INVALIDATE] {len(to_delete)} Einträge entfernt")
        return len(to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """Hole Cache-Statistiken"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }

    def cleanup_expired(self) -> int:
        """Entferne abgelaufene Einträge"""
        current_time = time.time()
        to_delete = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires_at']
        ]

        for key in to_delete:
            del self.cache[key]

        if to_delete:
            logger.info(f"[CACHE CLEANUP] {len(to_delete)} abgelaufene Einträge entfernt")

        return len(to_delete)

    def _start_cleanup_timer(self) -> None:
        """MEMORY-LEAK-FIX: Startet automatischen Cleanup-Timer"""
        self._cleanup_timer = threading.Timer(300.0, self._periodic_cleanup)  # 5 Minuten
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _periodic_cleanup(self) -> None:
        """MEMORY-LEAK-FIX: Periodischer Cleanup abgelaufener Einträge"""
        try:
            cleaned = self.cleanup_expired()
            if cleaned > 0:
                logger.info(f"[CACHE] Periodic cleanup: {cleaned} expired entries removed")
        except Exception as e:
            logger.error(f"[CACHE] Cleanup error: {e}")
        finally:
            # Nächsten Timer starten
            self._start_cleanup_timer()

    def __del__(self) -> None:
        """MEMORY-LEAK-FIX: Cleanup beim Löschen der Instanz"""
        if hasattr(self, '_cleanup_timer') and self._cleanup_timer:
            self._cleanup_timer.cancel()

    def shutdown(self) -> None:
        """MEMORY-LEAK-FIX: Explizites Shutdown für Cleanup"""
        if hasattr(self, '_cleanup_timer') and self._cleanup_timer:
            self._cleanup_timer.cancel()

        with self._lock:
            self.cache.clear()

        logger.info("[CACHE] Cache-Service heruntergefahren")


# Globale Cache-Instanz
_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Hole globale Cache-Service Instanz"""
    global _cache_instance
    if _cache_instance is None:
        # Konfiguration aus config.py
        from config import CACHE_CONFIG

        _cache_instance = CacheService(
            max_size=CACHE_CONFIG.get("max_size", 100),
            default_ttl=CACHE_CONFIG.get("default_ttl", 3600)
        )

    return _cache_instance


# ÄNDERUNG 05.07.2025: Cache-Decorator für einfache Nutzung
def cached_search(ttl: Optional[int] = None):
    """
    Decorator für gecachte Suchen

    Usage:
        @cached_search(ttl=1800)
        async def search_mine(...):
            ...
    """
    def decorator(func):
    """decorator - TODO: Dokumentation hinzufügen"""
        async def wrapper(self, mine_name: str, model: str, country: Optional[str] = None,
                         **kwargs):  # model als required parameter
            cache = get_cache_service()

            # Versuche aus Cache zu holen
            cached_result = cache.get(mine_name, country or "", model, **kwargs)
            if cached_result is not None:
                # Füge Cache-Info hinzu
                cached_result['from_cache'] = True
                cached_result['cache_timestamp'] = datetime.now().isoformat()
                return cached_result

            # Führe echte Suche durch
            result = await func(self, mine_name, country, model, **kwargs)

            # Cache nur erfolgreiche Ergebnisse
            if result.get('success') and result.get('data'):
                cache.set(mine_name, country or "", model, result, ttl=ttl, **kwargs)

            return result

        return wrapper
    return decorator
