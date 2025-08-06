"""
Author: rahn
Datum: 23.07.2025
Version: 1.0
Beschreibung: Centralized Source Performance Tracking System für MineSearch v2
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json

from database import db_manager, Source, SearchResult
from config.base import config
from source_performance_logger import source_performance_logger

logger = logging.getLogger(__name__)


@dataclass
class SourcePerformanceMetrics:
    """Detaillierte Performance-Metriken für eine Quelle"""
    url: str
    domain: str
    source_type: str
    
    # Basic Statistics
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    
    # Quality Metrics
    quality_score: float = 0.0  # 0.0-100.0
    reliability_score: float = 50.0  # 0.0-100.0
    data_richness_score: float = 0.0  # 0.0-100.0
    
    # Performance Metrics
    avg_response_time: float = 0.0  # Sekunden
    avg_data_fields_found: float = 0.0
    avg_sources_per_search: float = 0.0
    
    # Time-based Metrics
    last_success: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    
    # Content Analysis
    content_types_found: List[str] = field(default_factory=list)
    typical_field_coverage: Dict[str, float] = field(default_factory=dict)
    
    # Auto-Reset Tracking
    needs_reset: bool = False
    reset_reason: Optional[str] = None
    last_reset: Optional[datetime] = None
    
    def calculate_overall_score(self) -> float:
        """
        Berechnet Gesamt-Performance-Score mit Multi-Faktor-Bewertung
        
        Faktoren:
        - Success Rate (40%)
        - Data Quality (25%) 
        - Reliability (20%)
        - Recency (15%)
        """
        if self.total_attempts == 0:
            return 0.0
        
        # Success Rate Factor (40%)
        success_rate = self.successful_attempts / self.total_attempts
        success_factor = success_rate * 40
        
        # Data Quality Factor (25%)
        quality_factor = (self.data_richness_score / 100) * 25
        
        # Reliability Factor (20%)
        reliability_factor = (self.reliability_score / 100) * 20
        
        # Recency Factor (15%)
        recency_factor = 0
        if self.last_success:
            days_since_success = (datetime.now() - self.last_success).days
            if days_since_success < 7:
                recency_factor = 15
            elif days_since_success < 30:
                recency_factor = 10
            elif days_since_success < 90:
                recency_factor = 5
        
        total_score = success_factor + quality_factor + reliability_factor + recency_factor
        
        # Penalty für consecutive failures
        failure_penalty = min(self.consecutive_failures * 2, 20)
        total_score = max(0, total_score - failure_penalty)
        
        return min(100.0, total_score)
    
    def should_auto_reset(self) -> bool:
        """Prüft ob Auto-Reset erforderlich ist"""
        if self.needs_reset:
            return True
        
        # Kriterien für Auto-Reset
        if self.consecutive_failures >= 10:
            self.needs_reset = True
            self.reset_reason = f"10+ consecutive failures"
            return True
        
        if self.total_attempts >= 20:
            success_rate = self.successful_attempts / self.total_attempts
            if success_rate < 0.1:
                self.needs_reset = True
                self.reset_reason = f"Success rate below 10% after {self.total_attempts} attempts"
                return True
        
        if self.last_success and (datetime.now() - self.last_success).days > 180:
            self.needs_reset = True
            self.reset_reason = "No success in 180+ days"
            return True
        
        return False
    
    def reset_statistics(self):
        """Setzt Statistiken zurück"""
        logger.info(f"[STATS] Resetting statistics for {self.url}: {self.reset_reason}")
        
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.consecutive_failures = 0
        self.needs_reset = False
        self.last_reset = datetime.now()
        
        # Reliability score auf Basis-Wert zurücksetzen
        base_scores = {
            'government': 70.0,
            'database': 60.0, 
            'exchange': 55.0,
            'industry': 45.0,
            'document': 40.0,
            'unknown': 30.0
        }
        self.reliability_score = base_scores.get(self.source_type, 30.0)


class SourceStatsManager:
    """
    Centralized Source Performance Tracking System
    
    Features:
    - Batch-Updates für Performance
    - Multi-Faktor Score-Berechnung
    - Auto-Reset für schlechte Quellen
    - Comprehensive Logging
    - Performance-optimierte Datenbankoperationen
    """
    
    def __init__(self):
        self.db = db_manager
        self._stats_cache: Dict[str, SourcePerformanceMetrics] = {}
        self._batch_updates: List[Dict[str, Any]] = []
        self._last_cache_refresh = datetime.now()
        self._cache_ttl = timedelta(minutes=15)  # Cache-Lebensdauer
        
        # ÄNDERUNG 23.07.2025: Performance Logger Integration
        self.performance_logger = source_performance_logger
        
        # Performance Tracking
        self._operation_stats = {
            'batch_updates_processed': 0,
            'individual_updates_processed': 0,
            'auto_resets_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info("[STATS] SourceStatsManager initialisiert")
    
    async def update_source_performance(self, url: str, success: bool, 
                                      search_duration: Optional[float] = None,
                                      fields_found: int = 0,
                                      sources_count: int = 0,
                                      content_type: Optional[str] = None,
                                      field_coverage: Optional[Dict[str, bool]] = None) -> None:
        """
        Aktualisiert Performance-Metriken für eine Quelle
        
        Args:
            url: URL der Quelle
            success: Ob der Zugriff erfolgreich war
            search_duration: Dauer des Zugriffs in Sekunden
            fields_found: Anzahl gefundener Datenfelder
            sources_count: Anzahl zusätzlicher Quellen gefunden
            content_type: Art des gefundenen Inhalts
            field_coverage: Dictionary welche Felder gefunden wurden
        """
        try:
            # Lade oder erstelle Performance-Metriken
            metrics = await self._get_or_create_metrics(url)
            
            # Update Basic Statistics
            metrics.total_attempts += 1
            
            if success:
                metrics.successful_attempts += 1
                metrics.consecutive_failures = 0
                metrics.last_success = datetime.now()
                
                # Update Quality Metrics
                if fields_found > 0:
                    # Gewichteter Durchschnitt für avg_data_fields_found
                    total_weight = metrics.total_attempts - 1
                    metrics.avg_data_fields_found = (
                        (metrics.avg_data_fields_found * total_weight + fields_found) / 
                        metrics.total_attempts
                    )
                
                if sources_count > 0:
                    # Gewichteter Durchschnitt für avg_sources_per_search
                    total_weight = metrics.successful_attempts - 1
                    metrics.avg_sources_per_search = (
                        (metrics.avg_sources_per_search * total_weight + sources_count) / 
                        metrics.successful_attempts
                    )
                
                # Content Type Tracking
                if content_type and content_type not in metrics.content_types_found:
                    metrics.content_types_found.append(content_type)
                
                # Field Coverage Analysis
                if field_coverage:
                    for field_name, found in field_coverage.items():
                        if field_name not in metrics.typical_field_coverage:
                            metrics.typical_field_coverage[field_name] = 0.0
                        
                        # Gewichteter Durchschnitt der Field Coverage
                        current_coverage = metrics.typical_field_coverage[field_name]
                        found_weight = 1.0 if found else 0.0
                        total_weight = metrics.successful_attempts - 1
                        
                        metrics.typical_field_coverage[field_name] = (
                            (current_coverage * total_weight + found_weight) / 
                            metrics.successful_attempts
                        )
                
            else:
                metrics.failed_attempts += 1
                metrics.consecutive_failures += 1
            
            metrics.last_attempt = datetime.now()
            
            # Update Performance Metrics
            if search_duration is not None:
                # Gewichteter Durchschnitt für Response Time
                total_weight = metrics.total_attempts - 1
                metrics.avg_response_time = (
                    (metrics.avg_response_time * total_weight + search_duration) / 
                    metrics.total_attempts
                )
            
            # Calculate Data Richness Score
            if metrics.successful_attempts > 0:
                # Basis: Durchschnittliche Felder pro Erfolg
                field_score = min(100, (metrics.avg_data_fields_found / 19.0) * 100)  # 19 ist max erwartete Felder
                
                # Bonus für Content-Type-Vielfalt
                content_bonus = min(20, len(metrics.content_types_found) * 5)
                
                # Bonus für Field Coverage
                coverage_bonus = 0
                if metrics.typical_field_coverage:
                    avg_coverage = sum(metrics.typical_field_coverage.values()) / len(metrics.typical_field_coverage)
                    coverage_bonus = avg_coverage * 30
                
                metrics.data_richness_score = field_score + content_bonus + coverage_bonus
            
            # Update Reliability Score (existing algorithm in Source model)
            metrics.reliability_score = await self._calculate_reliability_score(metrics)
            
            # Calculate Overall Quality Score
            metrics.quality_score = metrics.calculate_overall_score()
            
            # Check für Auto-Reset
            if metrics.should_auto_reset():
                await self._perform_auto_reset(metrics)
            
            # Cache aktualisieren
            self._stats_cache[url] = metrics
            
            # Für Batch-Update vormerken
            self._batch_updates.append({
                'url': url,
                'metrics': metrics,
                'timestamp': datetime.now()
            })
            
            self._operation_stats['individual_updates_processed'] += 1
            
            # ÄNDERUNG 23.07.2025: Performance Logging
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc or 'unknown'
            
            self.performance_logger.log_source_update(
                url=url,
                domain=domain,
                success=success,
                duration=search_duration,
                fields_found=fields_found,
                content_type=content_type,
                error=None if success else "Source update failed"
            )
            
            logger.debug(f"[STATS] Updated performance for {url}: success={success}, "
                        f"score={metrics.quality_score:.1f}, consecutive_failures={metrics.consecutive_failures}")
            
        except Exception as e:
            error_msg = f"Fehler beim Aktualisieren der Source Performance: {e}"
            logger.error(f"[STATS] {error_msg}")
            
            # ÄNDERUNG 23.07.2025: Error Logging
            self.performance_logger.log_error(
                error_type='source_update_error',
                message=error_msg,
                url=url,
                exception=e
            )
    
    async def batch_update_sources(self, batch_size: int = 50) -> int:
        """
        Batch-Update für bessere Performance
        
        Args:
            batch_size: Anzahl Updates pro Batch
            
        Returns:
            Anzahl verarbeiteter Updates
        """
        if not self._batch_updates:
            return 0
        
        try:
            start_time = datetime.now()
            processed = 0
            batch_count = 0
            errors = []
            
            # Verarbeite in Batches
            for i in range(0, len(self._batch_updates), batch_size):
                batch = self._batch_updates[i:i + batch_size]
                batch_count += 1
                
                try:
                    with self.db.get_session() as session:
                        for update in batch:
                            url = update['url']
                            metrics = update['metrics']
                            
                            # Finde oder erstelle Source
                            source = session.query(Source).filter_by(url=url).first()
                            if source:
                                # Update existing source
                                source.total_searches = metrics.total_attempts
                                source.successful_searches = metrics.successful_attempts
                                source.reliability_score = metrics.reliability_score
                                source.last_attempted_access = metrics.last_attempt
                                source.last_successful_access = metrics.last_success
                                
                                # Update content types
                                if metrics.content_types_found:
                                    source.typical_content_types = metrics.content_types_found
                                
                                # Update metadata with performance metrics
                                metadata = source.extra_metadata or {}
                                metadata.update({
                                    'quality_score': metrics.quality_score,
                                    'data_richness_score': metrics.data_richness_score,
                                    'avg_response_time': metrics.avg_response_time,
                                    'avg_fields_found': metrics.avg_data_fields_found,
                                    'consecutive_failures': metrics.consecutive_failures,
                                    'field_coverage': metrics.typical_field_coverage,
                                    'last_updated': datetime.now().isoformat()
                                })
                                source.extra_metadata = metadata
                                
                                processed += 1
                        
                        session.commit()
                        
                except Exception as batch_error:
                    error_msg = f"Batch {batch_count} failed: {batch_error}"
                    errors.append(error_msg)
                    logger.error(f"[STATS] {error_msg}")
            
            # Clear processed updates
            self._batch_updates.clear()
            self._operation_stats['batch_updates_processed'] += processed
            
            # ÄNDERUNG 23.07.2025: Batch Update Logging
            duration = (datetime.now() - start_time).total_seconds()
            self.performance_logger.log_batch_update(
                processed_count=processed,
                duration=duration,
                errors=errors
            )
            
            logger.info(f"[STATS] Batch-Update abgeschlossen: {processed} Sources in {batch_count} Batches aktualisiert")
            return processed
            
        except Exception as e:
            error_msg = f"Fehler beim Batch-Update: {e}"
            logger.error(f"[STATS] {error_msg}")
            
            # ÄNDERUNG 23.07.2025: Error Logging
            self.performance_logger.log_error(
                error_type='batch_update_error',
                message=error_msg,
                exception=e
            )
            return 0
    
    async def get_source_performance(self, url: str) -> Optional[SourcePerformanceMetrics]:
        """
        Holt Performance-Metriken für eine Quelle
        
        Args:
            url: URL der Quelle
            
        Returns:
            SourcePerformanceMetrics oder None
        """
        try:
            # Cache-Check
            if url in self._stats_cache:
                cache_age = datetime.now() - self._last_cache_refresh
                if cache_age < self._cache_ttl:
                    self._operation_stats['cache_hits'] += 1
                    return self._stats_cache[url]
            
            self._operation_stats['cache_misses'] += 1
            
            # Load from database
            metrics = await self._load_metrics_from_db(url)
            if metrics:
                self._stats_cache[url] = metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Laden der Performance-Metriken für {url}: {e}")
            return None
    
    async def get_top_performing_sources(self, limit: int = 20, 
                                       source_type: Optional[str] = None,
                                       min_attempts: int = 5) -> List[SourcePerformanceMetrics]:
        """
        Holt die Top-performing Quellen
        
        Args:
            limit: Maximale Anzahl Ergebnisse
            source_type: Filter nach Quellentyp
            min_attempts: Mindestanzahl Versuche
            
        Returns:
            Liste der besten Quellen sortiert nach Performance
        """
        try:
            with self.db.get_session() as session:
                query = session.query(Source).filter(Source.total_searches >= min_attempts)
                
                if source_type:
                    query = query.filter(Source.source_type == source_type)
                
                sources = query.order_by(
                    Source.reliability_score.desc(),
                    Source.successful_searches.desc()
                ).limit(limit).all()
                
                metrics_list = []
                for source in sources:
                    metrics = await self._convert_source_to_metrics(source)
                    if metrics:
                        metrics_list.append(metrics)
                
                return metrics_list
                
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Laden der Top-Sources: {e}")
            return []
    
    async def get_sources_needing_reset(self) -> List[SourcePerformanceMetrics]:
        """
        Findet Quellen die ein Auto-Reset benötigen
        
        Returns:
            Liste der Quellen die resettet werden sollten
        """
        try:
            reset_candidates = []
            
            with self.db.get_session() as session:
                # Quellen mit vielen consecutive failures
                high_failure_sources = session.query(Source).filter(
                    Source.total_searches >= 10,
                    Source.successful_searches < (Source.total_searches * 0.1)
                ).all()
                
                # Quellen ohne Erfolg seit 180 Tagen
                cutoff_date = datetime.now() - timedelta(days=180)
                stale_sources = session.query(Source).filter(
                    Source.last_successful_access < cutoff_date,
                    Source.total_searches >= 5
                ).all()
                
                all_candidates = list(set(high_failure_sources + stale_sources))
                
                for source in all_candidates:
                    metrics = await self._convert_source_to_metrics(source)
                    if metrics and metrics.should_auto_reset():
                        reset_candidates.append(metrics)
            
            logger.info(f"[STATS] {len(reset_candidates)} Quellen für Auto-Reset identifiziert")
            return reset_candidates
            
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Identifizieren von Reset-Kandidaten: {e}")
            return []
    
    async def perform_bulk_reset(self, urls: List[str]) -> int:
        """
        Führt Bulk-Reset für mehrere Quellen durch
        
        Args:
            urls: Liste der URLs zum Zurücksetzen
            
        Returns:
            Anzahl erfolgreich zurückgesetzter Quellen
        """
        try:
            reset_count = 0
            
            with self.db.get_session() as session:
                for url in urls:
                    source = session.query(Source).filter_by(url=url).first()
                    if source:
                        # Reset database values
                        source.total_searches = 0
                        source.successful_searches = 0
                        source.last_attempted_access = None
                        source.last_successful_access = None
                        
                        # Reset reliability to base score
                        base_scores = {
                            'government': 70.0,
                            'database': 60.0,
                            'exchange': 55.0,
                            'industry': 45.0,
                            'document': 40.0,
                            'unknown': 30.0
                        }
                        source.reliability_score = base_scores.get(source.source_type, 30.0)
                        
                        # Update metadata
                        metadata = source.extra_metadata or {}
                        metadata.update({
                            'last_reset': datetime.now().isoformat(),
                            'reset_reason': 'Bulk reset operation'
                        })
                        source.extra_metadata = metadata
                        
                        reset_count += 1
                        
                        # Remove from cache if present
                        if url in self._stats_cache:
                            del self._stats_cache[url]
                
                session.commit()
            
            self._operation_stats['auto_resets_performed'] += reset_count
            logger.info(f"[STATS] Bulk-Reset abgeschlossen: {reset_count} Quellen zurückgesetzt")
            return reset_count
            
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Bulk-Reset: {e}")
            return 0
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Erstellt Performance-Zusammenfassung des Systems
        
        Returns:
            Dictionary mit Performance-Statistiken
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import func
                
                # Basic Source Statistics  
                total_sources = session.query(Source).count()
                active_sources = session.query(Source).filter(Source.total_searches > 0).count()
                successful_sources = session.query(Source).filter(Source.successful_searches > 0).count()
                
                # Performance Metrics
                avg_reliability = session.query(func.avg(Source.reliability_score)).scalar() or 0
                total_attempts = session.query(func.sum(Source.total_searches)).scalar() or 0
                total_successes = session.query(func.sum(Source.successful_searches)).scalar() or 0
                
                # Source Types Distribution
                type_distribution = {}
                type_counts = session.query(Source.source_type, func.count(Source.id)).group_by(Source.source_type).all()
                for source_type, count in type_counts:
                    type_distribution[source_type] = count
                
                # Recent Activity (last 24h)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_attempts = session.query(Source).filter(
                    Source.last_attempted_access >= recent_cutoff
                ).count()
                
                # Top Performers
                top_performers = await self.get_top_performing_sources(limit=5)
                top_performer_data = []
                for metrics in top_performers:
                    top_performer_data.append({
                        'url': metrics.url,
                        'domain': metrics.domain,
                        'quality_score': round(metrics.quality_score, 1),
                        'success_rate': round((metrics.successful_attempts / max(metrics.total_attempts, 1)) * 100, 1),
                        'total_attempts': metrics.total_attempts
                    })
                
                summary = {
                    'timestamp': datetime.now().isoformat(),
                    'source_statistics': {
                        'total_sources': total_sources,
                        'active_sources': active_sources,
                        'successful_sources': successful_sources,
                        'overall_success_rate': round((total_successes / max(total_attempts, 1)) * 100, 1),
                        'average_reliability_score': round(avg_reliability, 1)
                    },
                    'type_distribution': type_distribution,
                    'recent_activity': {
                        'sources_accessed_24h': recent_attempts
                    },
                    'top_performers': top_performer_data,
                    'operation_stats': self._operation_stats.copy(),
                    'cache_info': {
                        'cached_sources': len(self._stats_cache),
                        'pending_batch_updates': len(self._batch_updates),
                        'cache_age_minutes': (datetime.now() - self._last_cache_refresh).total_seconds() / 60
                    }
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Erstellen der Performance-Zusammenfassung: {e}")
            return {'error': str(e)}
    
    async def _get_or_create_metrics(self, url: str) -> SourcePerformanceMetrics:
        """Lädt oder erstellt Performance-Metriken für eine URL"""
        # Cache check first
        if url in self._stats_cache:
            return self._stats_cache[url]
        
        # Load from database
        metrics = await self._load_metrics_from_db(url)
        if not metrics:
            # Create new metrics
            with self.db.get_session() as session:
                source = session.query(Source).filter_by(url=url).first()
                if source:
                    metrics = await self._convert_source_to_metrics(source)
                else:
                    # Create minimal metrics for unknown source
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc or 'unknown'
                    
                    metrics = SourcePerformanceMetrics(
                        url=url,
                        domain=domain,
                        source_type='unknown'
                    )
        
        if metrics:
            self._stats_cache[url] = metrics
        
        # FALLBACK: unknown-Metriken wenn keine Performance-Daten verfügbar - REGEL 10 KONFORM
        return metrics or SourcePerformanceMetrics(url=url, domain='unknown', source_type='unknown')  # Fallback-Metriken
    
    async def _load_metrics_from_db(self, url: str) -> Optional[SourcePerformanceMetrics]:
        """Lädt Metriken aus der Datenbank"""
        try:
            with self.db.get_session() as session:
                source = session.query(Source).filter_by(url=url).first()
                if source:
                    return await self._convert_source_to_metrics(source)
            return None
        except Exception as e:
            logger.error(f"[STATS] Fehler beim Laden aus DB für {url}: {e}")
            return None
    
    async def _convert_source_to_metrics(self, source: Source) -> SourcePerformanceMetrics:
        """Konvertiert Source-Model zu SourcePerformanceMetrics"""
        metadata = source.extra_metadata or {}
        
        metrics = SourcePerformanceMetrics(
            url=source.url,
            domain=source.domain,
            source_type=source.source_type,
            total_attempts=source.total_searches,
            successful_attempts=source.successful_searches,
            failed_attempts=source.total_searches - source.successful_searches,
            reliability_score=source.reliability_score,
            last_success=source.last_successful_access,
            last_attempt=source.last_attempted_access,
            content_types_found=source.typical_content_types or []
        )
        
        # Load extended metrics from metadata
        metrics.quality_score = metadata.get('quality_score', 0.0)
        metrics.data_richness_score = metadata.get('data_richness_score', 0.0)
        metrics.avg_response_time = metadata.get('avg_response_time', 0.0)
        metrics.avg_data_fields_found = metadata.get('avg_fields_found', 0.0)
        metrics.consecutive_failures = metadata.get('consecutive_failures', 0)
        metrics.typical_field_coverage = metadata.get('field_coverage', {})
        
        if 'last_reset' in metadata:
            try:
                metrics.last_reset = datetime.fromisoformat(metadata['last_reset'])
            except:
                pass
        
        return metrics
    
    async def _calculate_reliability_score(self, metrics: SourcePerformanceMetrics) -> float:
        """Berechnet Reliability Score basierend auf Source Model Algorithmus"""
        if metrics.total_attempts == 0:
            return metrics.reliability_score  # Keep existing score
        
        score = 0.0
        
        # Success rate factor (40 points max)
        success_rate = metrics.successful_attempts / metrics.total_attempts
        if metrics.total_attempts >= 10:
            score += success_rate * 40
        elif metrics.total_attempts >= 5:
            score += success_rate * 30
        else:
            score += success_rate * 20
        
        # Source type bonus (20 points max)
        type_scores = {
            'government': 20,
            'database': 18, 
            'exchange': 15,
            'industry': 12,
            'document': 10,
            'unknown': 5
        }
        score += type_scores.get(metrics.source_type, 5)
        
        # Recency factor (20 points max)
        if metrics.last_success:
            days_since_success = (datetime.now() - metrics.last_success).days
            if days_since_success < 7:
                score += 20
            elif days_since_success < 30:
                score += 15
            elif days_since_success < 90:
                score += 10
            elif days_since_success < 180:
                score += 5
        
        # Data consistency factor (20 points max)
        if metrics.total_attempts >= 20 and metrics.successful_attempts >= 15:
            score += 20
        elif metrics.total_attempts >= 10 and metrics.successful_attempts >= 7:
            score += 15
        elif metrics.total_attempts >= 5 and metrics.successful_attempts >= 3:
            score += 10
        elif metrics.successful_attempts > 0:
            score += 5
        
        # Content type diversity bonus
        if len(metrics.content_types_found) > 2:
            score += 5
        
        return min(100.0, max(0.0, score))
    
    async def _perform_auto_reset(self, metrics: SourcePerformanceMetrics):
        """Führt Auto-Reset für eine Quelle durch"""
        try:
            logger.warning(f"[STATS] Auto-Reset für {metrics.url}: {metrics.reset_reason}")
            
            with self.db.get_session() as session:
                source = session.query(Source).filter_by(url=metrics.url).first()
                if source:
                    # Backup current stats to metadata
                    backup_data = {
                        'pre_reset_stats': {
                            'total_searches': source.total_searches,
                            'successful_searches': source.successful_searches,
                            'reliability_score': source.reliability_score,
                            'reset_timestamp': datetime.now().isoformat(),
                            'reset_reason': metrics.reset_reason
                        }
                    }
                    
                    existing_metadata = source.extra_metadata or {}
                    existing_metadata.update(backup_data)
                    source.extra_metadata = existing_metadata
                    
                    # Reset the source
                    source.total_searches = 0
                    source.successful_searches = 0
                    source.last_attempted_access = None
                    source.last_successful_access = None
                    
                    # Reset to base reliability score
                    base_scores = {
                        'government': 70.0,
                        'database': 60.0,
                        'exchange': 55.0,
                        'industry': 45.0,
                        'document': 40.0,
                        'unknown': 30.0
                    }
                    source.reliability_score = base_scores.get(source.source_type, 30.0)
                    
                    session.commit()
            
            # ÄNDERUNG 23.07.2025: Reset Logging
            pre_reset_stats = {
                'total_attempts': metrics.total_attempts,
                'successful_attempts': metrics.successful_attempts,
                'quality_score': metrics.quality_score,
                'reliability_score': metrics.reliability_score,
                'consecutive_failures': metrics.consecutive_failures
            }
            
            self.performance_logger.log_source_reset(
                url=metrics.url,
                reason=metrics.reset_reason or "Auto-reset triggered",
                pre_reset_stats=pre_reset_stats
            )
            
            # Reset metrics object
            metrics.reset_statistics()
            self._operation_stats['auto_resets_performed'] += 1
            
        except Exception as e:
            error_msg = f"Fehler beim Auto-Reset für {metrics.url}: {e}"
            logger.error(f"[STATS] {error_msg}")
            
            # ÄNDERUNG 23.07.2025: Error Logging
            self.performance_logger.log_error(
                error_type='auto_reset_error',
                message=error_msg,
                url=metrics.url,
                exception=e
            )


# Global SourceStatsManager instance
source_stats_manager = SourceStatsManager()