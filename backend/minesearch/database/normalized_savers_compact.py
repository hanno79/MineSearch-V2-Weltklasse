"""
Compact Normalized Savers
Kompakte Version der normalisierten Save-Funktionen

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def save_mine_field_data(
    manager_self,
    mine_id: int,
    search_result_id: int,
    structured_data: Dict[str, Any],
    model_used: str,
    sources: List[Dict[str, str]] = None,
    session_id: str = None,
    db_session: Optional[Session] = None,
    value_normalizer=None
) -> None:
    """Speichere Minen-Felddaten in normalisierter Form"""
    try:
        if not db_session:
            db_session = manager_self.get_session()
        
        # Importiere Modelle
        from .normalized_models import FieldValue, FieldValueSource, Source
        
        saved_count = 0
        skipped_count = 0
        
        for field_name, field_value in structured_data.items():
            try:
                # Normalisiere Feldwert
                normalized_value = _normalize_field_value(field_value, value_normalizer)
                
                if not normalized_value:
                    skipped_count += 1
                    continue
                
                # Erstelle FieldValue-Eintrag
                field_value_obj = FieldValue(
                    mine_id=mine_id,
                    search_result_id=search_result_id,
                    field_name=field_name,
                    atomic_value=normalized_value,
                    confidence_score=_calculate_confidence_score(normalized_value),
                    extraction_method=model_used
                )
                
                db_session.add(field_value_obj)
                db_session.flush()
                
                # Verknüpfe mit Quellen
                if sources:
                    _link_field_value_to_sources(
                        db_session, field_value_obj.id, sources, field_name
                    )
                
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"Fehler beim Speichern von {field_name}: {e}")
                skipped_count += 1
        
        db_session.commit()
        logger.info(f"✅ {saved_count} Feldwerte gespeichert, {skipped_count} übersprungen")
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Fehler beim Speichern der Felddaten: {e}")
        raise


def save_search_result_data(
    manager_self,
    mine_id: int,
    model_used: str,
    structured_data: Dict[str, Any],
    sources: List[Dict[str, str]] = None,
    execution_time: float = 0.0,
    db_session: Optional[Session] = None
) -> int:
    """Speichere Suchergebnis-Daten"""
    try:
        if not db_session:
            db_session = manager_self.get_session()
        
        # Importiere Modelle
        from .normalized_models import SearchResult
        
        # Erstelle SearchResult-Eintrag
        search_result = SearchResult(
            mine_id=mine_id,
            model_used=model_used,
            execution_time=execution_time,
            success=True,
            confidence_score=_calculate_overall_confidence(structured_data)
        )
        
        db_session.add(search_result)
        db_session.flush()
        
        # Speichere Felddaten
        save_mine_field_data(
            manager_self, mine_id, search_result.id, structured_data,
            model_used, sources, db_session=db_session
        )
        
        db_session.commit()
        return search_result.id
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Fehler beim Speichern der Suchergebnisse: {e}")
        raise


def save_source_data(
    manager_self,
    sources: List[Dict[str, str]],
    db_session: Optional[Session] = None
) -> Dict[str, int]:
    """Speichere Quellendaten"""
    try:
        if not db_session:
            db_session = manager_self.get_session()
        
        # Importiere Modelle
        from .normalized_models import Source
        
        source_url_to_id = {}
        
        for source_data in sources:
            url = source_data.get('url')
            if not url:
                continue
            
            # Prüfe ob Quelle bereits existiert
            existing_source = db_session.query(Source).filter(
                Source.url == url
            ).first()
            
            if existing_source:
                source_url_to_id[url] = existing_source.id
                continue
            
            # Erstelle neue Quelle
            source = Source(
                url=url,
                title=source_data.get('title', ''),
                content=source_data.get('content', ''),
                source_type=source_data.get('source_type', 'unknown'),
                domain=_extract_domain(url),
                discovered_at=datetime.now()
            )
            
            db_session.add(source)
            db_session.flush()
            source_url_to_id[url] = source.id
        
        db_session.commit()
        return source_url_to_id
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Fehler beim Speichern der Quellen: {e}")
        raise


def save_mine_data(
    manager_self,
    mine_name: str,
    country: str = None,
    region: str = None,
    commodity: str = None,
    db_session: Optional[Session] = None
) -> int:
    """Speichere Minen-Daten"""
    try:
        if not db_session:
            db_session = manager_self.get_session()
        
        # Importiere Modelle
        from .normalized_models import Mine, Country
        
        # Finde oder erstelle Land
        country_id = None
        if country:
            country_obj = db_session.query(Country).filter(
                Country.name == country
            ).first()
            
            if not country_obj:
                country_obj = Country(name=country)
                db_session.add(country_obj)
                db_session.flush()
            
            country_id = country_obj.id
        
        # Prüfe ob Mine bereits existiert
        existing_mine = db_session.query(Mine).filter(
            Mine.name == mine_name
        ).first()
        
        if existing_mine:
            return existing_mine.id
        
        # Erstelle neue Mine
        mine = Mine(
            name=mine_name,
            country_id=country_id,
            region=region,
            commodity=commodity,
            operational_status='unknown'
        )
        
        db_session.add(mine)
        db_session.flush()
        
        db_session.commit()
        return mine.id
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Fehler beim Speichern der Mine: {e}")
        raise


def _normalize_field_value(field_value: Any, value_normalizer=None) -> Optional[str]:
    """Normalisiere Feldwert"""
    if not field_value:
        return None
    
    # Konvertiere zu String
    value_str = str(field_value).strip()
    
    if not value_str:
        return None
    
    # Prüfe auf Template-Werte
    if _is_template_value(value_str):
        return None
    
    # Verwende Normalizer falls verfügbar
    if value_normalizer:
        try:
            normalized = value_normalizer.normalize(value_str)
            return normalized if normalized else None
        except Exception:
            pass
    
    return value_str


def _is_template_value(value: str) -> bool:
    """Prüfe ob Wert ein Template ist"""
    if not value:
        return True
    
    value_lower = value.lower().strip()
    
    template_indicators = [
        'template:', 'not specified', 'no data', 'n/a', 'unknown',
        'not available', 'not found', 'tbd', 'to be determined',
        'keine angabe', 'nicht verfügbar', 'unbekannt'
    ]
    
    return any(indicator in value_lower for indicator in template_indicators)


def _calculate_confidence_score(value: str) -> float:
    """Berechne Confidence-Score für Wert"""
    if not value:
        return 0.0
    
    # Basis-Score
    score = 0.5
    
    # Länge-basierte Bewertung
    if len(value) > 50:
        score += 0.2
    elif len(value) > 20:
        score += 0.1
    
    # Spezifitäts-Bewertung
    if any(char.isdigit() for char in value):
        score += 0.1
    
    if any(char.isupper() for char in value):
        score += 0.1
    
    # Cap bei 1.0
    return min(score, 1.0)


def _calculate_overall_confidence(structured_data: Dict[str, Any]) -> float:
    """Berechne Gesamt-Confidence-Score"""
    if not structured_data:
        return 0.0
    
    scores = []
    for field_name, field_value in structured_data.items():
        if field_value:
            score = _calculate_confidence_score(str(field_value))
            scores.append(score)
    
    return sum(scores) / len(scores) if scores else 0.0


def _link_field_value_to_sources(
    db_session: Session,
    field_value_id: int,
    sources: List[Dict[str, str]],
    field_name: str
):
    """Verknüpfe Feldwert mit Quellen"""
    try:
        from .normalized_models import FieldValueSource, Source
        
        for source_data in sources:
            url = source_data.get('url')
            if not url:
                continue
            
            # Finde Source-ID
            source = db_session.query(Source).filter(
                Source.url == url
            ).first()
            
            if not source:
                continue
            
            # Erstelle Verknüpfung
            field_source = FieldValueSource(
                field_value_id=field_value_id,
                source_id=source.id,
                extraction_confidence=0.8,
                relevance_score=0.8
            )
            
            db_session.add(field_source)
            
    except Exception as e:
        logger.warning(f"Fehler beim Verknüpfen der Quellen: {e}")


def _extract_domain(url: str) -> str:
    """Extrahiere Domain aus URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def update_field_consistency(
    manager_self,
    mine_id: int,
    field_name: str,
    db_session: Optional[Session] = None
):
    """Aktualisiere Feld-Konsistenz"""
    try:
        if not db_session:
            db_session = manager_self.get_session()
        
        from .normalized_models import FieldValue, FieldConsistency
        
        # Hole alle Werte für dieses Feld
        field_values = db_session.query(FieldValue).filter(
            FieldValue.mine_id == mine_id,
            FieldValue.field_name == field_name
        ).all()
        
        if not field_values:
            return
        
        # Berechne Konsistenz
        values = [fv.atomic_value for fv in field_values]
        unique_values = set(values)
        most_common = max(set(values), key=values.count)
        consistency_score = len(unique_values) / len(values) if values else 0.0
        
        # Aktualisiere oder erstelle Konsistenz-Eintrag
        consistency = db_session.query(FieldConsistency).filter(
            FieldConsistency.mine_id == mine_id,
            FieldConsistency.field_name == field_name
        ).first()
        
        if not consistency:
            consistency = FieldConsistency(
                mine_id=mine_id,
                field_name=field_name
            )
            db_session.add(consistency)
        
        consistency.unique_values_count = len(unique_values)
        consistency.most_common_value = most_common
        consistency.consistency_score = consistency_score
        consistency.last_analyzed = datetime.now()
        
        db_session.commit()
        
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Feld-Konsistenz: {e}")


__all__ = [
    "save_mine_field_data",
    "save_search_result_data", 
    "save_source_data",
    "save_mine_data",
    "update_field_consistency"
]
