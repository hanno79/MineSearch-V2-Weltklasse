"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Gemeinsamer Cache Manager für Agenten
"""

import asyncio
import json
import hashlib
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """Verwaltet Caching für Agent-Anfragen und Ergebnisse"""
    
    def __init__(self, 
                 cache_dir: str = "cache",
                 default_ttl: int = 3600,
                 max_cache_size_mb: int = 100):
        """
        Initialisiert den Cache Manager
        
        Args:
            cache_dir: Verzeichnis für Cache-Dateien
            default_ttl: Standard Time-to-Live in Sekunden
            max_cache_size_mb: Maximale Cache-Größe in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.max_cache_size_mb = max_cache_size_mb
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    def _generate_key(self, 
                     namespace: str,
                     data: Union[str, Dict, List]) -> str:
        """
        Generiert einen eindeutigen Cache-Key
        
        Args:
            namespace: Namespace für den Cache (z.B. Agent-Name)
            data: Daten für die der Key generiert wird
            
        Returns:
            Eindeutiger Cache-Key
        """
        # Daten zu String konvertieren
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Hash generieren
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{namespace}:{data_str}".encode())
        
        return hash_obj.hexdigest()
    
    async def get(self, 
                 namespace: str,
                 key_data: Union[str, Dict, List]) -> Optional[Any]:
        """
        Holt einen Wert aus dem Cache
        
        Args:
            namespace: Cache-Namespace
            key_data: Daten für Key-Generierung
            
        Returns:
            Gecachter Wert oder None
        """
        key = self._generate_key(namespace, key_data)
        
        # Zuerst Memory-Cache prüfen
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if self._is_valid(entry):
                logger.debug(f"Cache Hit (Memory): {namespace}/{key[:8]}...")
                return entry["data"]
            else:
                # Abgelaufenen Eintrag entfernen
                del self._memory_cache[key]
        
        # Dann File-Cache prüfen
        cache_file = self.cache_dir / f"{namespace}_{key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    content = f.read()
                    entry = pickle.loads(content)
                    
                if self._is_valid(entry):
                    # In Memory-Cache laden
                    self._memory_cache[key] = entry
                    logger.debug(f"Cache Hit (File): {namespace}/{key[:8]}...")
                    return entry["data"]
                else:
                    # Abgelaufene Datei löschen
                    os.unlink(cache_file)
                    
            except Exception as e:
                logger.warning(f"Cache-Lesefehler: {e}")
                # Korrupte Cache-Datei löschen
                if cache_file.exists():
                    os.unlink(cache_file)
        
        logger.debug(f"Cache Miss: {namespace}/{key[:8]}...")
        return None
    
    async def set(self,
                 namespace: str,
                 key_data: Union[str, Dict, List],
                 value: Any,
                 ttl: Optional[int] = None) -> None:
        """
        Speichert einen Wert im Cache
        
        Args:
            namespace: Cache-Namespace
            key_data: Daten für Key-Generierung
            value: Zu cachender Wert
            ttl: Time-to-Live in Sekunden
        """
        key = self._generate_key(namespace, key_data)
        ttl = ttl or self.default_ttl
        
        entry = {
            "data": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "created_at": datetime.now()
        }
        
        async with self._lock:
            # In Memory-Cache speichern
            self._memory_cache[key] = entry
            
            # In File-Cache speichern
            cache_file = self.cache_dir / f"{namespace}_{key}.cache"
            try:
                with open(cache_file, 'wb') as f:
                    f.write(pickle.dumps(entry))
                logger.debug(f"Cache Set: {namespace}/{key[:8]}...")
            except Exception as e:
                logger.warning(f"Cache-Schreibfehler: {e}")
            
            # Cache-Größe prüfen
            await self._check_cache_size()
    
    async def delete(self,
                    namespace: str,
                    key_data: Union[str, Dict, List]) -> None:
        """
        Löscht einen Eintrag aus dem Cache
        
        Args:
            namespace: Cache-Namespace
            key_data: Daten für Key-Generierung
        """
        key = self._generate_key(namespace, key_data)
        
        # Aus Memory-Cache entfernen
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Aus File-Cache entfernen
        cache_file = self.cache_dir / f"{namespace}_{key}.cache"
        if cache_file.exists():
            os.unlink(cache_file)
            
        logger.debug(f"Cache Delete: {namespace}/{key[:8]}...")
    
    async def clear(self, namespace: Optional[str] = None) -> None:
        """
        Löscht Cache-Einträge
        
        Args:
            namespace: Nur Einträge dieses Namespace löschen (optional)
        """
        async with self._lock:
            if namespace:
                # Nur spezifischen Namespace löschen
                # Memory-Cache
                keys_to_delete = [k for k in self._memory_cache.keys() 
                                 if k.startswith(namespace)]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                
                # File-Cache
                pattern = f"{namespace}_*.cache"
                for cache_file in self.cache_dir.glob(pattern):
                    os.unlink(cache_file)
                    
                logger.info(f"Cache cleared for namespace: {namespace}")
            else:
                # Gesamten Cache löschen
                self._memory_cache.clear()
                
                for cache_file in self.cache_dir.glob("*.cache"):
                    os.unlink(cache_file)
                    
                logger.info("Entire cache cleared")
    
    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """Prüft ob ein Cache-Eintrag noch gültig ist"""
        return datetime.now() < entry["expires_at"]
    
    async def _check_cache_size(self) -> None:
        """Prüft und bereinigt Cache bei Größenüberschreitung"""
        total_size = 0
        cache_files = []
        
        # Größe aller Cache-Dateien ermitteln
        for cache_file in self.cache_dir.glob("*.cache"):
            size = cache_file.stat().st_size
            mtime = cache_file.stat().st_mtime
            cache_files.append((cache_file, size, mtime))
            total_size += size
        
        # In MB konvertieren
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > self.max_cache_size_mb:
            logger.info(f"Cache-Größe ({total_size_mb:.1f}MB) überschreitet Limit ({self.max_cache_size_mb}MB)")
            
            # Nach Alter sortieren (älteste zuerst)
            cache_files.sort(key=lambda x: x[2])
            
            # Älteste Dateien löschen bis unter Limit
            for cache_file, size, _ in cache_files:
                os.unlink(cache_file)
                total_size_mb -= size / (1024 * 1024)
                
                if total_size_mb < self.max_cache_size_mb * 0.8:  # 80% als Ziel
                    break
            
            logger.info(f"Cache bereinigt auf {total_size_mb:.1f}MB")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken zurück
        
        Returns:
            Dictionary mit Cache-Statistiken
        """
        memory_entries = len(self._memory_cache)
        file_entries = len(list(self.cache_dir.glob("*.cache")))
        
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            "memory_entries": memory_entries,
            "file_entries": file_entries,
            "total_size_mb": round(total_size_mb, 2),
            "max_size_mb": self.max_cache_size_mb,
            "usage_percent": round((total_size_mb / self.max_cache_size_mb) * 100, 1)
        }
    
    def cached(self, 
              namespace: str,
              ttl: Optional[int] = None):
        """
        Decorator für automatisches Caching von Funktionen
        
        Args:
            namespace: Cache-Namespace
            ttl: Time-to-Live in Sekunden
            
        Usage:
            @cache_manager.cached("my_agent", ttl=3600)
            async def fetch_data(query):
                # Expensive operation
                return result
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Cache-Key aus Funktionsargumenten generieren
                cache_key = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Aus Cache holen
                cached_value = await self.get(namespace, cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Funktion ausführen
                result = await func(*args, **kwargs)
                
                # Ergebnis cachen
                await self.set(namespace, cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator