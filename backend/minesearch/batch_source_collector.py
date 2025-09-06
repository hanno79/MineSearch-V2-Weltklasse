"""
Author: rahn
Datum: 29.08.2025
Version: 1.0
Beschreibung: BatchSourceCollector für 2-Phasen Quellen-Sammlung im Batch-Workflow
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass

from minesearch.database import db_manager
from minesearch.providers.registry import provider_registry
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.utils import generate_name_variants
from minesearch.search_utils import get_country_config

logger = logging.getLogger(__name__)

@dataclass
class SourceCollectionResult:
    """Ergebnis der Quellen-Sammlung für ein Modell"""
    model_id: str
    success: bool
    sources_found: int
    new_sources_added: int
    error: Optional[str] = None
    duration: float = 0.0

class BatchSourceCollector:
    """
    Sammelt Quellen von allen Modellen und speichert sie dedupliziert in der Datenbank
    
    Implementiert 2-Phasen Workflow:
    Phase 1: Jedes Modell sucht Quellen → DB-Speicherung
    Phase 2: Alle Modelle nutzen ALLE DB-Quellen
    """
    
    def __init__(self):
        self.source_discovery = EnhancedSourceDiscovery()
        self._existing_sources_cache: Optional[Set[str]] = None
        
    async def collect_sources_from_all_models(
        self,
        mine_names: List[str], 
        models: List[str],
        max_concurrent_models: int = 5,
        timeout_seconds: int = 300
    ) -> Dict[str, SourceCollectionResult]:
        """
        PHASE 1: Sammelt Quellen von ALLEN ausgewählten Modellen
        
        Args:
            mine_names: Liste der Minen-Namen
            models: Liste der Modell-IDs
            max_concurrent_models: Max parallele Modell-Aufrufe
            timeout_seconds: Timeout für gesamte Quellen-Sammlung (DEFAULT: 300s = 5min)
            
        Returns:
            Dict mit SourceCollectionResult pro Modell
        """
        collection_start = datetime.now()
        logger.info(f"[BATCH-SOURCE-COLLECTOR] 🚀 Starte Quellen-Sammlung für {len(models)} Modelle über {len(mine_names)} Minen (Timeout: {timeout_seconds}s)")
        
        try:
            # TIMEOUT-WRAPPER für gesamte Source Collection
            return await asyncio.wait_for(
                self._collect_sources_internal(mine_names, models, max_concurrent_models, collection_start),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            total_duration = (datetime.now() - collection_start).total_seconds()
            logger.error(f"[BATCH-SOURCE-COLLECTOR] ⏰ TIMEOUT nach {total_duration:.2f}s ({timeout_seconds}s limit)")
            
            # Erstelle Error-Results für alle Modelle
            timeout_results = {}
            for model_id in models:
                timeout_results[model_id] = SourceCollectionResult(
                    model_id=model_id,
                    success=False,
                    sources_found=0,
                    new_sources_added=0,
                    error=f"Timeout nach {timeout_seconds}s erreicht",
                    duration=total_duration
                )
            return timeout_results
    
    async def _collect_sources_internal(
        self,
        mine_names: List[str], 
        models: List[str],
        max_concurrent_models: int = 5,
        collection_start: datetime = None
    ) -> Dict[str, SourceCollectionResult]:
        """
        Interne Source Collection Logik ohne Timeout-Wrapper
        """
        if collection_start is None:
            collection_start = datetime.now()
            
        # Cache existierende Quellen für Duplikat-Vermeidung
        await self._load_existing_sources_cache()
        
        # Gruppiere Modelle in Batches für kontrollierte Parallelität
        model_batches = [models[i:i+max_concurrent_models] for i in range(0, len(models), max_concurrent_models)]
        
        all_results: Dict[str, SourceCollectionResult] = {}
        
        for batch_idx, model_batch in enumerate(model_batches):
            logger.info(f"[BATCH-SOURCE-COLLECTOR] Processing batch {batch_idx+1}/{len(model_batches)} mit {len(model_batch)} Modellen")
            
            # Parallel Source Collection für diesen Batch
            batch_tasks = [
                self._collect_sources_for_single_model(model_id, mine_names)
                for model_id in model_batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for model_id, result in zip(model_batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ Modell {model_id} failed: {result}")
                        all_results[model_id] = SourceCollectionResult(
                            model_id=model_id,
                            success=False,
                            sources_found=0,
                            new_sources_added=0,
                            error=str(result)
                        )
                    else:
                        all_results[model_id] = result
                        
            except Exception as e:
                logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ Batch {batch_idx+1} failed: {e}")
                for model_id in model_batch:
                    all_results[model_id] = SourceCollectionResult(
                        model_id=model_id,
                        success=False,
                        sources_found=0,
                        new_sources_added=0,
                        error=f"Batch execution failed: {str(e)}"
                    )
        
        # Zusammenfassung der Sammlung
        total_duration = (datetime.now() - collection_start).total_seconds()
        successful_models = [r for r in all_results.values() if r.success]
        failed_models = [r for r in all_results.values() if not r.success]
        total_new_sources = sum(r.new_sources_added for r in successful_models)
        
        logger.info(f"[BATCH-SOURCE-COLLECTOR] 📊 SAMMLUNG ABGESCHLOSSEN:")
        logger.info(f"[BATCH-SOURCE-COLLECTOR]   ✅ Erfolgreiche Modelle: {len(successful_models)}/{len(models)}")
        logger.info(f"[BATCH-SOURCE-COLLECTOR]   ❌ Fehlgeschlagene Modelle: {len(failed_models)}")
        logger.info(f"[BATCH-SOURCE-COLLECTOR]   🔗 Neue Quellen hinzugefügt: {total_new_sources}")
        logger.info(f"[BATCH-SOURCE-COLLECTOR]   ⏱️ Gesamtdauer: {total_duration:.2f}s")
        
        if failed_models:
            for result in failed_models[:3]:  # Erste 3 Fehler anzeigen
                logger.warning(f"[BATCH-SOURCE-COLLECTOR]   🚫 {result.model_id}: {result.error}")
        
        return all_results
    
    async def _collect_sources_for_single_model(
        self, 
        model_id: str, 
        mine_names: List[str]
    ) -> SourceCollectionResult:
        """
        Sammelt Quellen für ein einzelnes Modell über alle Minen
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"[BATCH-SOURCE-COLLECTOR] 🔍 Sammle Quellen für Modell: {model_id}")
            
            # Provider für dieses Modell holen
            provider = provider_registry.get_provider_for_model(model_id)
            if not provider:
                raise ValueError(f"Kein Provider für Modell {model_id} gefunden")
            
            all_sources_for_model = []
            
            # Für jede Mine Quellen sammeln
            for mine_name in mine_names:
                try:
                    # Source Discovery für diese Mine mit diesem Modell
                    mine_sources = await self._discover_sources_for_mine_with_model(
                        mine_name=mine_name,
                        model_id=model_id,
                        provider=provider
                    )
                    all_sources_for_model.extend(mine_sources)
                    
                except Exception as e:
                    logger.warning(f"[BATCH-SOURCE-COLLECTOR] ⚠️ Quellen-Sammlung für {mine_name} mit {model_id} fehlgeschlagen: {e}")
                    continue
            
            # Duplikate entfernen (innerhalb dieses Modells)
            unique_sources = self._deduplicate_sources(all_sources_for_model)
            
            # Neue Quellen in DB speichern (globale Duplikat-Vermeidung)
            new_sources_count = await self._save_new_sources_to_db(unique_sources, model_id)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"[BATCH-SOURCE-COLLECTOR] ✅ {model_id}: {len(unique_sources)} Quellen gefunden, {new_sources_count} neue hinzugefügt ({duration:.2f}s)")
            
            return SourceCollectionResult(
                model_id=model_id,
                success=True,
                sources_found=len(unique_sources),
                new_sources_added=new_sources_count,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ {model_id} fehlgeschlagen nach {duration:.2f}s: {e}")
            
            return SourceCollectionResult(
                model_id=model_id,
                success=False,
                sources_found=0,
                new_sources_added=0,
                error=str(e),
                duration=duration
            )
    
    async def _discover_sources_for_mine_with_model(
        self,
        mine_name: str,
        model_id: str,
        provider
    ) -> List[Dict[str, Any]]:
        """
        Nutzt Source Discovery um Quellen für eine Mine mit einem spezifischen Modell zu finden
        """
        try:
            # PHASE 1 FIX 29.08.2025: Nutze den bestehenden EnhancedSourceDiscovery mechanismus
            sources = self.source_discovery.discover_sources_for_mine(
                mine_name=mine_name
            )
            
            # Füge Metadaten hinzu
            for source in sources:
                source['discovered_by_model'] = model_id
                source['discovery_timestamp'] = datetime.now()
                
            return sources
            
        except Exception as e:
            logger.error(f"[BATCH-SOURCE-COLLECTOR] Source Discovery für {mine_name} mit {model_id} fehlgeschlagen: {e}")
            return []
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Entfernt Duplikate basierend auf URL/Titel-Kombinationen
        """
        seen_sources: Set[str] = set()
        unique_sources = []
        
        for source in sources:
            # Erstelle eindeutigen Identifier
            url = source.get('url', '').strip().lower()
            title = source.get('title', '').strip().lower()
            identifier = f"{url}|{title}"
            
            if identifier not in seen_sources and url:  # URL muss vorhanden sein
                seen_sources.add(identifier)
                unique_sources.append(source)
        
        logger.debug(f"[BATCH-SOURCE-COLLECTOR] Deduplizierung: {len(sources)} → {len(unique_sources)} einzigartige Quellen")
        return unique_sources
    
    async def _load_existing_sources_cache(self):
        """
        Lädt existierende Quellen-URLs in Cache für schnelle Duplikat-Prüfung
        """
        try:
            with db_manager.get_session() as session:
                from sqlalchemy import text
                result = session.execute(text("SELECT DISTINCT url FROM sources WHERE url IS NOT NULL AND url != ''"))
                existing_urls = {row[0].lower() for row in result.fetchall()}
                self._existing_sources_cache = existing_urls
                logger.info(f"[BATCH-SOURCE-COLLECTOR] 📋 Cache geladen: {len(existing_urls)} existierende Quellen-URLs")
        except Exception as e:
            logger.warning(f"[BATCH-SOURCE-COLLECTOR] ⚠️ Cache-Laden fehlgeschlagen: {e}")
            self._existing_sources_cache = set()
    
    async def _save_new_sources_to_db(self, sources: List[Dict[str, Any]], model_id: str) -> int:
        """
        Speichert neue Quellen in die Datenbank (vermeidet globale Duplikate)
        """
        if not sources:
            return 0
            
        new_sources_count = 0
        
        try:
            with db_manager.get_session() as session:
                for source in sources:
                    url = source.get('url', '').strip()
                    if not url:
                        continue
                        
                    # Prüfe gegen Cache (schnell)
                    if url.lower() in (self._existing_sources_cache or set()):
                        continue
                    
                    # Speichere neue Quelle in bestehende DB-Struktur
                    from sqlalchemy import text
                    insert_query = text("""
                        INSERT OR IGNORE INTO sources (url, domain, first_discovered_by, created_at, reliability_score, source_type)
                        VALUES (:url, :domain, :model, :created_at, :reliability, :source_type)
                    """)
                    
                    result = session.execute(insert_query, {
                        'url': url,
                        'domain': source.get('domain', '')[:100],
                        'model': model_id,
                        'created_at': datetime.now(),
                        'reliability': source.get('reliability_score', None),  # REGEL 10: NULL statt 0.5 Fallback
                        'source_type': source.get('type', 'unknown')
                    })
                    
                    if result.rowcount > 0:
                        new_sources_count += 1
                        # Update Cache
                        if self._existing_sources_cache is not None:
                            self._existing_sources_cache.add(url.lower())
                
                session.commit()
                
        except Exception as e:
            logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ DB-Speicherung fehlgeschlagen für {model_id}: {e}")
            return 0
        
        logger.debug(f"[BATCH-SOURCE-COLLECTOR] 💾 {new_sources_count} neue Quellen für {model_id} gespeichert")
        return new_sources_count
    
    def get_all_sources_from_db(self) -> List[Dict[str, Any]]:
        """
        PHASE 2: Lädt ALLE Quellen aus der Datenbank für Daten-Extraktion
        
        Returns:
            Liste aller verfügbaren Quellen (ohne Filter)
        """
        try:
            with db_manager.get_session() as session:
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        url, 
                        url as title,  -- Verwende URL als Titel (bestehende DB-Struktur)
                        domain,
                        first_discovered_by as discovered_by_model,  -- Anpassung an bestehende Spalte
                        created_at
                    FROM sources 
                    WHERE url IS NOT NULL 
                      AND url != ''
                      AND url NOT LIKE '%example.com%'
                    ORDER BY created_at DESC
                """)
                
                result = session.execute(query)
                sources = []
                
                for row in result.fetchall():
                    sources.append({
                        'url': row[0],
                        'title': row[1] or '',
                        'domain': row[2] or '',
                        'discovered_by_model': row[3] or '',
                        'created_at': row[4]
                    })
                
                logger.info(f"[BATCH-SOURCE-COLLECTOR] 📚 {len(sources)} Quellen aus DB geladen für Daten-Extraktion")
                return sources
                
        except Exception as e:
            logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ Fehler beim Laden aller DB-Quellen: {e}")
            return []
    
    def get_sources_stats(self) -> Dict[str, Any]:
        """
        Liefert Statistiken über die Quellen in der Datenbank
        """
        try:
            with db_manager.get_session() as session:
                from sqlalchemy import text
                
                stats_query = text("""
                    SELECT 
                        COUNT(*) as total_sources,
                        COUNT(DISTINCT domain) as unique_domains,
                        COUNT(DISTINCT first_discovered_by) as contributing_models  -- Anpassung
                    FROM sources 
                    WHERE url IS NOT NULL AND url != ''
                """)
                
                result = session.execute(stats_query)
                row = result.fetchone()
                
                return {
                    'total_sources': row[0] if row else 0,
                    'unique_domains': row[1] if row else 0,
                    'contributing_models': row[2] if row else 0
                }
                
        except Exception as e:
            logger.error(f"[BATCH-SOURCE-COLLECTOR] ❌ Fehler beim Laden der Quellen-Statistiken: {e}")
            return {'total_sources': 0, 'unique_domains': 0, 'contributing_models': 0}