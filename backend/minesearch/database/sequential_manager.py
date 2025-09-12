"""
Compact Sequential Database Manager
Kompakte Version des Sequential Database Managers

Author: MineSearch Development Team
Date: 2025-01-11
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
    """Database Manager für Sequential Field Orchestrator"""

    def __init__(self):
        """Initialisiere Sequential Database Manager"""
        self.logger = logger

    async def create_source_discovery_session(
        self,
        session: Session,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> str:
        """Erstelle neue Source Discovery Session"""
        try:
            session_id = str(uuid.uuid4())
            
            discovery_session = SourceDiscoverySession(
                session_id=session_id,
                mine_name=mine_name,
                country=country,
                region=region,
                created_at=datetime.now(),
                status='active'
            )
            
            session.add(discovery_session)
            session.commit()
            
            self.logger.info(f"Source Discovery Session erstellt: {session_id}")
            return session_id
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler beim Erstellen der Session: {e}")
            raise

    async def save_sources(
        self,
        session: Session,
        session_id: str,
        sources: List[Dict[str, Any]]
    ) -> List[int]:
        """Speichere Quellen für eine Session"""
        try:
            source_ids = []
            
            for source_data in sources:
                # Prüfe ob Quelle bereits existiert
                existing_source = session.query(Source).filter(
                    Source.url == source_data.get('url')
                ).first()
                
                if existing_source:
                    source_ids.append(existing_source.id)
                    continue
                
                # Erstelle neue Quelle
                source = Source(
                    url=source_data.get('url'),
                    title=source_data.get('title', ''),
                    content=source_data.get('content', ''),
                    source_type=source_data.get('source_type', 'unknown'),
                    discovered_at=datetime.now(),
                    session_id=session_id
                )
                
                session.add(source)
                session.flush()
                source_ids.append(source.id)
            
            session.commit()
            self.logger.info(f"{len(source_ids)} Quellen für Session {session_id} gespeichert")
            return source_ids
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler beim Speichern der Quellen: {e}")
            raise

    async def save_model_contributions(
        self,
        session: Session,
        session_id: str,
        model_contributions: Dict[str, List[int]]
    ):
        """Speichere Modell-Beiträge zu Quellen"""
        try:
            for model_name, source_ids in model_contributions.items():
                for source_id in source_ids:
                    contribution = ModelSourceContribution(
                        session_id=session_id,
                        model_name=model_name,
                        source_id=source_id,
                        contribution_score=1.0,
                        created_at=datetime.now()
                    )
                    session.add(contribution)
            
            session.commit()
            self.logger.info(f"Modell-Beiträge für Session {session_id} gespeichert")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler beim Speichern der Modell-Beiträge: {e}")
            raise

    async def save_field_search_results(
        self,
        session: Session,
        session_id: str,
        field_results: Dict[str, Any]
    ):
        """Speichere Feld-Suchergebnisse"""
        try:
            for field_name, field_data in field_results.items():
                field_result = FieldSearchResult(
                    session_id=session_id,
                    field_name=field_name,
                    extracted_value=field_data.get('value', ''),
                    confidence_score=field_data.get('confidence', 0.0),
                    source_references=json.dumps(field_data.get('sources', [])),
                    created_at=datetime.now()
                )
                session.add(field_result)
            
            session.commit()
            self.logger.info(f"Feld-Suchergebnisse für Session {session_id} gespeichert")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler beim Speichern der Feld-Suchergebnisse: {e}")
            raise

    async def save_sequential_search_result(
        self,
        session: Session,
        session_id: str,
        consolidated_data: Dict[str, Any],
        execution_time: float
    ):
        """Speichere konsolidiertes Suchergebnis"""
        try:
            sequential_result = SequentialSearchResult(
                session_id=session_id,
                consolidated_data=json.dumps(consolidated_data),
                execution_time=execution_time,
                success=True,
                created_at=datetime.now()
            )
            session.add(sequential_result)
            session.commit()
            
            self.logger.info(f"Sequential Search Result für Session {session_id} gespeichert")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler beim Speichern des Sequential Search Results: {e}")
            raise

    async def get_session_statistics(self, session: Session, session_id: str) -> Dict[str, Any]:
        """Hole Session-Statistiken"""
        try:
            # Hole Session-Info
            discovery_session = session.query(SourceDiscoverySession).filter(
                SourceDiscoverySession.session_id == session_id
            ).first()
            
            if not discovery_session:
                return {}
            
            # Zähle Quellen
            source_count = session.query(Source).filter(
                Source.session_id == session_id
            ).count()
            
            # Zähle Feld-Ergebnisse
            field_count = session.query(FieldSearchResult).filter(
                FieldSearchResult.session_id == session_id
            ).count()
            
            # Hole Modell-Beiträge
            model_contributions = session.query(ModelSourceContribution).filter(
                ModelSourceContribution.session_id == session_id
            ).all()
            
            model_stats = {}
            for contribution in model_contributions:
                model_name = contribution.model_name
                if model_name not in model_stats:
                    model_stats[model_name] = 0
                model_stats[model_name] += 1
            
            return {
                'session_id': session_id,
                'mine_name': discovery_session.mine_name,
                'country': discovery_session.country,
                'region': discovery_session.region,
                'status': discovery_session.status,
                'created_at': discovery_session.created_at.isoformat(),
                'source_count': source_count,
                'field_count': field_count,
                'model_contributions': model_stats,
                'total_models': len(model_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Session-Statistiken: {e}")
            return {}

    async def get_recent_sessions(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Hole aktuelle Sessions"""
        try:
            sessions = session.query(SourceDiscoverySession).order_by(
                desc(SourceDiscoverySession.created_at)
            ).offset(offset).limit(limit).all()
            
            session_data = []
            for sess in sessions:
                stats = await self.get_session_statistics(session, sess.session_id)
                session_data.append(stats)
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Sessions: {e}")
            return []

    async def cleanup_old_sessions(
        self,
        session: Session,
        days_old: int = 30
    ) -> int:
        """Bereinige alte Sessions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Finde alte Sessions
            old_sessions = session.query(SourceDiscoverySession).filter(
                SourceDiscoverySession.created_at < cutoff_date
            ).all()
            
            deleted_count = 0
            for old_session in old_sessions:
                # Lösche abhängige Daten
                session.query(FieldSearchResult).filter(
                    FieldSearchResult.session_id == old_session.session_id
                ).delete()
                
                session.query(ModelSourceContribution).filter(
                    ModelSourceContribution.session_id == old_session.session_id
                ).delete()
                
                session.query(SequentialSearchResult).filter(
                    SequentialSearchResult.session_id == old_session.session_id
                ).delete()
                
                # Lösche Session
                session.delete(old_session)
                deleted_count += 1
            
            session.commit()
            self.logger.info(f"{deleted_count} alte Sessions bereinigt")
            return deleted_count
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Fehler bei der Bereinigung: {e}")
            raise

    async def get_database_health(self, session: Session) -> Dict[str, Any]:
        """Prüfe Datenbank-Gesundheit"""
        try:
            # Zähle verschiedene Entitäten
            session_count = session.query(SourceDiscoverySession).count()
            source_count = session.query(Source).count()
            field_result_count = session.query(FieldSearchResult).count()
            model_contribution_count = session.query(ModelSourceContribution).count()
            
            return {
                'status': 'healthy',
                'session_count': session_count,
                'source_count': source_count,
                'field_result_count': field_result_count,
                'model_contribution_count': model_contribution_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Globale Instanz für Kompatibilität
sequential_db_manager = SequentialDatabaseManager()

__all__ = ["SequentialDatabaseManager", "sequential_db_manager"]
