"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Database Manager für Sequential Field Orchestrator
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import uuid
import json

from .models import (
    Source, SourceDiscoverySession, ModelSourceContribution,
    FieldSearchResult, SequentialSearchResult, FieldSearchSourceUsage
)

logger = logging.getLogger(__name__)


class SequentialDatabaseManager:
    """
    ÄNDERUNG 27.08.2025: Database Manager für Sequential Field Orchestrator
    
    Verwaltet alle Datenbankoperationen für den neuen Sequential Workflow:
    - Source Discovery Sessions
    - Model Source Contributions 
    - Field Search Results
    - Consolidated Sequential Results
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    # SOURCE DISCOVERY SESSION MANAGEMENT
    
    def create_discovery_session(
        self,
        mine_name: str,
        models_list: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        fields_to_search: Optional[List[str]] = None
    ) -> SourceDiscoverySession:
        """
        Erstelle eine neue Source Discovery Session
        
        Args:
            mine_name: Name der Mine
            models_list: Liste der zu verwendenden Modelle
            country: Land (optional)
            region: Region (optional)
            commodity: Rohstoff (optional)
            fields_to_search: Liste der zu suchenden Felder (optional)
            
        Returns:
            SourceDiscoverySession Objekt
        """
        session_id = str(uuid.uuid4())
        
        session = SourceDiscoverySession(
            session_id=session_id,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            total_models=len(models_list),
            models_list=models_list,
            fields_to_search=fields_to_search or []
        )
        
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        
        logger.info(f"[SequentialDatabaseManager] Discovery session created: {session_id} for mine: {mine_name}")
        
        return session
    
    def get_discovery_session(self, session_id: str) -> Optional[SourceDiscoverySession]:
        """
        Lade eine Discovery Session
        
        Args:
            session_id: ID der Session
            
        Returns:
            SourceDiscoverySession oder None
        """
        return self.session.query(SourceDiscoverySession).filter(
            SourceDiscoverySession.session_id == session_id
        ).first()
    
    def update_discovery_progress(
        self,
        session_id: str,
        current_model_index: int,
        sources_discovered: int,
        phase: str = 'source_discovery'
    ) -> bool:
        """
        Update Discovery Progress
        
        Args:
            session_id: ID der Session
            current_model_index: Aktueller Modell-Index
            sources_discovered: Anzahl entdeckter Quellen
            phase: Aktuelle Phase
            
        Returns:
            True wenn erfolgreich
        """
        session_obj = self.get_discovery_session(session_id)
        if not session_obj:
            logger.error(f"[SequentialDatabaseManager] Session not found: {session_id}")
            return False
        
        session_obj.current_model_index = current_model_index
        session_obj.sources_discovered_total = sources_discovered
        session_obj.phase = phase
        
        # Phase completion tracking
        if phase == 'source_discovery':
            session_obj.models_completed_discovery = current_model_index
        elif phase == 'field_search':
            if not session_obj.discovery_completed_at:
                session_obj.discovery_completed_at = datetime.now()
        elif phase == 'completed':
            session_obj.search_completed_at = datetime.now()
            session_obj.workflow_completed = True
            
            # Calculate total duration
            if session_obj.started_at:
                duration = (datetime.now() - session_obj.started_at).total_seconds()
                session_obj.total_duration_seconds = duration
        
        self.session.commit()
        return True
    
    def complete_discovery_phase(self, session_id: str) -> bool:
        """
        Markiere Discovery Phase als abgeschlossen
        
        Args:
            session_id: ID der Session
            
        Returns:
            True wenn erfolgreich
        """
        session_obj = self.get_discovery_session(session_id)
        if not session_obj:
            return False
        
        session_obj.phase = 'field_search'
        session_obj.discovery_completed_at = datetime.now()
        session_obj.models_completed_discovery = session_obj.total_models
        
        self.session.commit()
        logger.info(f"[SequentialDatabaseManager] Discovery phase completed for session: {session_id}")
        return True
    
    # SOURCE MANAGEMENT
    
    def add_or_update_source(
        self,
        url: str,
        domain: str,
        model_id: str,
        session_id: str,
        source_type: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        initial_quality: float = 50.0
    ) -> Tuple[Source, bool]:
        """
        Füge neue Quelle hinzu oder update bestehende
        
        Args:
            url: URL der Quelle
            domain: Domain der Quelle
            model_id: Modell das die Quelle entdeckt hat
            session_id: Discovery Session ID
            source_type: Typ der Quelle (optional)
            country: Land (optional)
            region: Region (optional)
            initial_quality: Initial Quality Score
            
        Returns:
            Tuple: (Source object, is_new_source)
        """
        # Versuche atomisches Insert, fall-back auf Update bei Unique-Constraint-Verletzung
        # Vorab: fehlende Felder ermitteln
        resolved_source_type = source_type or Source.classify_source_type(url, domain)
        resolved_country = country or Source.get_country_from_domain(url, domain)

        try:
            # Insert innerhalb einer Transaktion versuchen
            with self.session.begin():
                new_source = Source(
                    url=url,
                    domain=domain,
                    country=resolved_country,
                    region=region,
                    source_type=resolved_source_type,
                    reliability_score=initial_quality,
                    first_discovered_by=model_id,
                    # NORMALISIERUNG FIX 04.09.2025: discovery_models entfernt
                    discovery_count=1,
                    last_discovery_session=session_id,
                    cumulative_quality_score=initial_quality
                )
                self.session.add(new_source)
                # Flush für ID-Generierung vor dem Refresh/Return
                self.session.flush()
                # Optional die Tracking-Methode aufrufen, falls zusätzliche interne Felder gepflegt werden
                # (bei neuem Insert als neue Entdeckung markieren)
                if hasattr(new_source, 'update_discovery_tracking'):
                    new_source.update_discovery_tracking(model_id, session_id, is_new_discovery=True)
                # Sicherstellen, dass alle Änderungen in der Transaktion erfasst sind
                self.session.flush()

            # Nach Commit: Objekt frisch laden, dann Contribution loggen
            self.session.refresh(new_source)
            self._log_source_contribution(session_id, model_id, new_source.id, is_unique=True)
            logger.info(f"[SequentialDatabaseManager] New source added: {domain} by {model_id}")
            return new_source, True

        except IntegrityError:
            # Insert kollidierte (Unique-Constraint auf url) → bestehende Quelle updaten
            self.session.rollback()

            # Existierende Quelle neu laden und aktualisieren
            existing_source = self.session.query(Source).filter(Source.url == url).first()
            if not existing_source:
                # Sollte äußerst selten vorkommen (Race mit weiterer Rollback-Situation) → erneut versuchen
                # Alternativ: Exception erneut werfen
                with self.session.begin():
                    existing_source = self.session.query(Source).filter(Source.url == url).first()
                    if not existing_source:
                        raise

            with self.session.begin():
                # Update Discovery-Tracking innerhalb der Transaktion
                if hasattr(existing_source, 'update_discovery_tracking'):
                    existing_source.update_discovery_tracking(model_id, session_id, is_new_discovery=False)

                # Fehlende Felder setzen (nur ergänzen, nichts überschreiben)
                if resolved_country and not existing_source.country:
                    existing_source.country = resolved_country
                if region and not existing_source.region:
                    existing_source.region = region
                if resolved_source_type and existing_source.source_type == 'unknown':
                    existing_source.source_type = resolved_source_type

                self.session.flush()

            # Nach Commit: Objekt aktualisieren und Contribution loggen
            self.session.refresh(existing_source)
            self._log_source_contribution(session_id, model_id, existing_source.id, is_unique=False)
            return existing_source, False
    
    def _log_source_contribution(
        self,
        session_id: str,
        model_id: str,
        source_id: int,
        is_unique: bool
    ):
        """
        Log Model Source Contribution
        
        Args:
            session_id: Discovery Session ID
            model_id: Modell ID
            source_id: Source ID
            is_unique: Ob diese Quelle erstmals entdeckt wurde
        """
        # Berechne contribution order
        existing_contributions = self.session.query(ModelSourceContribution).filter(
            ModelSourceContribution.session_id == session_id
        ).count()
        
        contribution = ModelSourceContribution(
            session_id=session_id,
            model_id=model_id,
            source_id=source_id,
            contribution_order=existing_contributions + 1,
            is_unique_contribution=is_unique,
            discovery_method='search',
            initial_quality_score=50.0,
            contribution_value=10.0 if is_unique else 5.0  # Höherer Wert für neue Quellen
        )
        
        self.session.add(contribution)
        self.session.commit()
    
    def get_accumulated_sources(
        self,
        session_id: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Source]:
        """
        Lade alle akkumulierten Quellen einer Session
        
        Args:
            session_id: Discovery Session ID
            country: Filter nach Land
            region: Filter nach Region
            limit: Maximale Anzahl Quellen
            
        Returns:
            Liste von Source-Objekten, sortiert nach Qualität
        """
        # Basis-Query: Alle Quellen die in dieser Session oder früheren Sessions entdeckt wurden
        query = self.session.query(Source).join(
            ModelSourceContribution,
            Source.id == ModelSourceContribution.source_id
        ).filter(
            or_(
                ModelSourceContribution.session_id == session_id,
                Source.last_discovery_session == session_id
            )
        )
        
        # Filter anwenden
        if country:
            query = query.filter(Source.country == country)
        if region:
            query = query.filter(Source.region == region)
        
        # Sortierung nach kombiniertem Quality Score
        query = query.order_by(
            desc(Source.cumulative_quality_score),
            desc(Source.reliability_score),
            desc(Source.discovery_count)
        )
        
        if limit:
            query = query.limit(limit)
        
        sources = query.distinct().all()
        
        logger.info(f"[SequentialDatabaseManager] Retrieved {len(sources)} accumulated sources for session: {session_id}")
        
        return sources
    
    def get_all_accumulated_sources(
        self,
        country: Optional[str] = None,
        region: Optional[str] = None,
        min_quality_score: float = 0.0,
        limit: Optional[int] = None
    ) -> List[Source]:
        """
        Lade alle akkumulierten Quellen aus der gesamten Datenbank
        
        Args:
            country: Filter nach Land
            region: Filter nach Region
            min_quality_score: Minimum Quality Score
            limit: Maximale Anzahl Quellen
            
        Returns:
            Liste von Source-Objekten, sortiert nach Qualität
        """
        query = self.session.query(Source)
        
        # Filter anwenden
        if country:
            query = query.filter(Source.country == country)
        if region:
            query = query.filter(Source.region == region)
        if min_quality_score > 0:
            query = query.filter(Source.cumulative_quality_score >= min_quality_score)
        
        # Sortierung nach Quality
        query = query.order_by(
            desc(Source.cumulative_quality_score),
            desc(Source.reliability_score),
            desc(Source.field_extraction_success_rate),
            desc(Source.discovery_count)
        )
        
        if limit:
            query = query.limit(limit)
        
        sources = query.all()
        
        logger.info(f"[SequentialDatabaseManager] Retrieved {len(sources)} total accumulated sources")
        
        return sources
    
    # FIELD SEARCH RESULTS
    
    def log_field_search_result(
        self,
        session_id: str,
        model_id: str,
        field_name: str,
        sources_used: List[int],
        field_value: Optional[str] = None,
        confidence_score: Optional[float] = None,
        source_references: Optional[List[Dict[str, Any]]] = None,
        search_duration: Optional[float] = None,
        result_quality: str = 'unknown'
    ) -> FieldSearchResult:
        """
        Log Field Search Result
        
        Args:
            session_id: Discovery Session ID
            model_id: Modell ID
            field_name: Name des Feldes
            sources_used: Liste der verwendeten Source IDs
            field_value: Gefundener Wert (optional)
            confidence_score: Konfidenz (optional)
            source_references: Quellen-Referenzen (optional)
            search_duration: Such-Dauer in Sekunden
            result_quality: Qualitätsbewertung
            
        Returns:
            FieldSearchResult Objekt
        """
        # In einer Transaktion speichern, damit FieldSearchResult-ID für Assoziationen verfügbar ist
        with self.session.begin():
            field_result = FieldSearchResult(
                session_id=session_id,
                model_id=model_id,
                field_name=field_name,
                sources_used_count=len(sources_used),
                sources_used_ids=[int(s) for s in (sources_used or [])],
                field_value_found=field_value,
                confidence_score=confidence_score,
                source_references=source_references or [],
                search_duration_seconds=search_duration,
                result_quality=result_quality,
                search_successful=bool(field_value and str(field_value).strip()),
                value_found=bool(field_value and str(field_value).strip() and str(field_value).strip().upper() != 'X'),
                sources_matched=len(sources_used or []) > 0
            )
            self.session.add(field_result)
            # Flush, damit ID vergeben wird
            self.session.flush()
            # Assoziations-Einträge erstellen (UniqueConstraint verhindert Duplikate)
            for sid in set(int(s) for s in (sources_used or []) if s is not None):
                usage = FieldSearchSourceUsage(field_search_id=field_result.id, source_id=int(sid))
                self.session.add(usage)
        
        # Nach Transaktion Objekt refreshen
        self.session.refresh(field_result)
        
        # Update source statistics
        if field_result.value_found:
            with self.session.begin():
                for source_id in sources_used or []:
                    source = self.session.query(Source).get(int(source_id))
                    if source:
                        quality = confidence_score or 50.0
                        source.update_field_extraction_stats(field_name, True, quality)
        
        logger.info(f"[SequentialDatabaseManager] Field search result logged: {field_name} = {field_value}")
        
        return field_result
    
    def get_field_search_results(self, session_id: str) -> List[FieldSearchResult]:
        """
        Lade alle Field Search Results einer Session
        
        Args:
            session_id: Discovery Session ID
            
        Returns:
            Liste von FieldSearchResult-Objekten
        """
        return self.session.query(FieldSearchResult).filter(
            FieldSearchResult.session_id == session_id
        ).order_by(
            FieldSearchResult.field_name,
            FieldSearchResult.searched_at
        ).all()
    
    # CONSOLIDATED RESULTS
    
    def create_sequential_result(
        self,
        session_id: str,
        mine_name: str,
        final_data: Dict[str, Any],
        field_confidence: Dict[str, float],
        field_source_mapping: Dict[str, List[Dict[str, Any]]],
        quality_assessment: Dict[str, Any],
        performance_metrics: Dict[str, float],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None
    ) -> SequentialSearchResult:
        """
        Erstelle konsolidierten Sequential Search Result
        
        Args:
            session_id: Discovery Session ID
            mine_name: Name der Mine
            final_data: Finale strukturierte Daten
            field_confidence: Konfidenz-Scores pro Feld
            field_source_mapping: Quellen-Mapping pro Feld
            quality_assessment: Qualitätsbewertung
            performance_metrics: Performance-Metriken
            country: Land (optional)
            region: Region (optional) 
            commodity: Rohstoff (optional)
            
        Returns:
            SequentialSearchResult Objekt
        """
        # Berechne Statistiken
        total_models = performance_metrics.get('total_models_used', 0)
        total_sources = performance_metrics.get('total_sources_discovered', 0)
        total_fields = performance_metrics.get('total_fields_searched', 0)
        total_values = len([v for v in final_data.values() if v and str(v).strip() and str(v).strip().upper() != 'X'])
        
        result = SequentialSearchResult(
            session_id=session_id,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            total_models_used=total_models,
            total_sources_discovered=total_sources,
            total_fields_searched=total_fields,
            total_values_found=total_values,
            final_structured_data=final_data,
            field_confidence_scores=field_confidence,
            field_source_mapping=field_source_mapping,
            quality_assessment=quality_assessment,
            total_duration_seconds=performance_metrics.get('total_duration_seconds'),
            source_discovery_duration=performance_metrics.get('source_discovery_duration'),
            field_search_duration=performance_metrics.get('field_search_duration'),
            consolidation_duration=performance_metrics.get('consolidation_duration'),
            workflow_completed=True,
            completed_at=datetime.now()
        )
        
        # Berechne Quality Metrics
        result.calculate_quality_metrics()
        
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        
        logger.info(f"[SequentialDatabaseManager] Sequential result created: {session_id} with quality score: {result.overall_quality_score}")
        
        return result
    
    def get_sequential_result(self, session_id: str) -> Optional[SequentialSearchResult]:
        """
        Lade Sequential Search Result
        
        Args:
            session_id: Discovery Session ID
            
        Returns:
            SequentialSearchResult oder None
        """
        return self.session.query(SequentialSearchResult).filter(
            SequentialSearchResult.session_id == session_id
        ).first()
    
    # ANALYTICS & REPORTING
    
    def get_model_source_contributions(self, session_id: str) -> List[ModelSourceContribution]:
        """
        Lade Model Source Contributions für eine Session
        
        Args:
            session_id: Discovery Session ID
            
        Returns:
            Liste von ModelSourceContribution-Objekten
        """
        return self.session.query(ModelSourceContribution).filter(
            ModelSourceContribution.session_id == session_id
        ).order_by(
            ModelSourceContribution.contribution_order
        ).all()
    
    def get_model_effectiveness_stats(self, model_id: str, limit_days: int = 30) -> Dict[str, Any]:
        """
        Ermittle Effektivitäts-Statistiken für ein Modell
        
        Args:
            model_id: Modell ID
            limit_days: Zeitraum in Tagen
            
        Returns:
            Dictionary mit Statistiken
        """
        cutoff_date = datetime.now() - timedelta(days=limit_days)
        
        # Source Discovery Stats
        unique_sources = self.session.query(ModelSourceContribution).filter(
            ModelSourceContribution.model_id == model_id,
            ModelSourceContribution.discovered_at >= cutoff_date,
            ModelSourceContribution.is_unique_contribution == True
        ).count()
        
        total_contributions = self.session.query(ModelSourceContribution).filter(
            ModelSourceContribution.model_id == model_id,
            ModelSourceContribution.discovered_at >= cutoff_date
        ).count()
        
        # Field Search Stats
        successful_field_searches = self.session.query(FieldSearchResult).filter(
            FieldSearchResult.model_id == model_id,
            FieldSearchResult.searched_at >= cutoff_date,
            FieldSearchResult.value_found == True
        ).count()
        
        total_field_searches = self.session.query(FieldSearchResult).filter(
            FieldSearchResult.model_id == model_id,
            FieldSearchResult.searched_at >= cutoff_date
        ).count()
        
        # Average Performance
        avg_field_duration = self.session.query(func.avg(FieldSearchResult.search_duration_seconds)).filter(
            FieldSearchResult.model_id == model_id,
            FieldSearchResult.searched_at >= cutoff_date
        ).scalar() or 0.0
        
        return {
            'model_id': model_id,
            'unique_sources_discovered': unique_sources,
            'total_source_contributions': total_contributions,
            'source_discovery_effectiveness': (unique_sources / total_contributions * 100) if total_contributions > 0 else 0,
            'successful_field_searches': successful_field_searches,
            'total_field_searches': total_field_searches,
            'field_search_success_rate': (successful_field_searches / total_field_searches * 100) if total_field_searches > 0 else 0,
            'avg_field_search_duration': avg_field_duration,
            'period_days': limit_days,
            'calculated_at': datetime.now().isoformat()
        }
    
    def get_source_utilization_stats(self, limit_days: int = 30) -> List[Dict[str, Any]]:
        """
        Ermittle Source Utilization Statistiken
        
        Args:
            limit_days: Zeitraum in Tagen
            
        Returns:
            Liste mit Source-Statistiken
        """
        cutoff_date = datetime.now() - timedelta(days=limit_days)
        
        sources = self.session.query(Source).filter(
            Source.updated_at >= cutoff_date
        ).order_by(desc(Source.cumulative_quality_score)).limit(50).all()
        
        stats = []
        for source in sources:
            recent_usage = self.session.query(FieldSearchSourceUsage).join(
                FieldSearchResult,
                FieldSearchSourceUsage.field_search_id == FieldSearchResult.id
            ).filter(
                FieldSearchResult.searched_at >= cutoff_date,
                FieldSearchSourceUsage.source_id == source.id
            ).count()
            
            stats.append({
                'source_id': source.id,
                'url': source.url,
                'domain': source.domain,
                'source_type': source.source_type,
                'reliability_score': source.reliability_score,
                'cumulative_quality_score': source.cumulative_quality_score,
                'field_extraction_success_rate': source.field_extraction_success_rate,
                'times_used_in_field_search': source.times_used_in_field_search,
                'recent_usage_count': recent_usage,
                # NORMALISIERUNG FIX 04.09.2025: JSON-Spalten entfernt
                'discovery_models': [],
                'field_specialization': {},
                'mine_specialization': {}
            })
        
        return stats
    
    # CLEANUP & MAINTENANCE
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Bereinige alte Sessions
        
        Args:
            days_old: Sessions älter als X Tage löschen
            
        Returns:
            Anzahl gelöschter Sessions
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        old_sessions = self.session.query(SourceDiscoverySession).filter(
            SourceDiscoverySession.started_at < cutoff_date,
            SourceDiscoverySession.phase == 'completed'
        ).all()
        
        count = len(old_sessions)
        
        # Alle Löschoperationen atomar in einer Transaktion ausführen
        with self.session.begin():
            for session in old_sessions:
                # Lösche abhängige Datensätze
                self.session.query(ModelSourceContribution).filter(
                    ModelSourceContribution.session_id == session.session_id
                ).delete()
                
                self.session.query(FieldSearchResult).filter(
                    FieldSearchResult.session_id == session.session_id
                ).delete()
                
                # Lösche Session
                self.session.delete(session)
        
        logger.info(f"[SequentialDatabaseManager] Cleaned up {count} old sessions")
        
        return count