"""
Author: rahn
Datum: 02.09.2025
Version: 1.0
Beschreibung: Asynchrone Datenbank-Tasks für bessere Performance
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

# Thread Pool für DB-Operationen
db_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="async_db")

class AsyncDBTaskManager:
    """Manager für asynchrone Datenbankoperationen"""
    
    def __init__(self):
        self._pending_tasks = []
    
    async def schedule_stats_update(self, model_id: str) -> None:
        """
        Plane Model Statistics Update asynchron
        
        Args:
            model_id: Modell-ID für Statistics-Update
        """
        try:
            logger.info(f"[ASYNC-DB] Scheduling statistics update for {model_id}")
            
            # Führe in separatem Thread aus um Hauptprocess nicht zu blockieren
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                db_executor, 
                self._update_model_statistics_sync, 
                model_id
            )
            
        except Exception as e:
            logger.error(f"[ASYNC-DB] Fehler bei async statistics update für {model_id}: {e}")
    
    def _update_model_statistics_sync(self, model_id: str) -> None:
        """
        Synchrone Statistics-Update Funktion (läuft in Thread)
        
        Args:
            model_id: Modell-ID
        """
        try:
            # Import hier um Circular Imports zu vermeiden
            from minesearch.database.manager import DatabaseManager
            
            db_manager = DatabaseManager()
            db_manager.update_model_statistics_comprehensive(model_id)
            logger.info(f"[ASYNC-DB] Statistics update completed for {model_id}")
            
        except Exception as e:
            logger.error(f"[ASYNC-DB] Sync statistics update failed for {model_id}: {e}")
    
    async def schedule_source_updates(self, sources: List[Dict[str, Any]], country: Optional[str] = None) -> None:
        """
        Plane Source-Updates asynchron
        
        Args:
            sources: Liste der zu updatenden Sources
            country: Land (optional)
        """
        try:
            if not sources:
                return
                
            logger.info(f"[ASYNC-DB] Scheduling source updates for {len(sources)} sources")
            
            # Führe in separatem Thread aus
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                db_executor,
                self._update_sources_sync,
                sources,
                country
            )
            
        except Exception as e:
            logger.error(f"[ASYNC-DB] Fehler bei async source updates: {e}")
    
    def _update_sources_sync(self, sources: List[Dict[str, Any]], country: Optional[str]) -> None:
        """
        Synchrone Source-Update Funktion (läuft in Thread)
        
        Args:
            sources: Sources zum Updaten
            country: Land
        """
        try:
            from minesearch.database.manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            for source in sources:
                if source.get('url'):
                    db_manager.add_or_update_source(
                        url=source.get('url'),
                        domain=source.get('domain', ''),
                        country=country,
                        source_type=source.get('type', 'unknown'),
                        metadata={
                            'title': source.get('title', ''),
                            'reliability': source.get('reliability')
                        }
                    )
            
            logger.info(f"[ASYNC-DB] Source updates completed for {len(sources)} sources")
            
        except Exception as e:
            logger.error(f"[ASYNC-DB] Sync source updates failed: {e}")
    
    async def shutdown(self):
        """Cleanup beim Shutdown"""
        logger.info("[ASYNC-DB] Shutting down async DB task manager")
        
        # Warte auf ausstehende Tasks
        if hasattr(self, '_pending_tasks') and self._pending_tasks:
            try:
                await asyncio.gather(*self._pending_tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"[ASYNC-DB] Error during shutdown: {e}")
        
        # Shutdown Thread Pool
        db_executor.shutdown(wait=True)
        logger.info("[ASYNC-DB] Async DB task manager shutdown completed")

# Global Instance
async_db_tasks = AsyncDBTaskManager()