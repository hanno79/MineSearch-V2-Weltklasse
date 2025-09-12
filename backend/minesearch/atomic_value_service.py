"""
SCHEMA-NORMALISIERUNG 28.08.2025: Service für atomische Feldwerte
Stellt Funktionen für den Zugriff auf normalisierte Feldwerte bereit

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_atomic_field_values(
    """get_atomic_field_values - TODO: Dokumentation hinzufügen"""
    session: Session,
    mine_name: str,
    field_name: str,
    model_filter: Optional[str] = None
) -> List[Tuple[str, int, float]]:
    """
    Holt atomische Werte für ein spezifisches Feld einer Mine

    Args:
        session: SQLAlchemy Session
        mine_name: Name der Mine
        field_name: Name des Feldes
        model_filter: Optional - nur Werte von diesem Modell

    Returns:
        Liste von (atomic_value, frequency, avg_confidence)
    """
    from minesearch.database.models import FieldValue, SearchResult

    try:
        # Basis-Query für atomische Werte
        query = session.query(
            FieldValue.atomic_value,
            func.count(FieldValue.id).label('frequency'),
            func.avg(FieldValue.confidence_score).label('avg_confidence')
        ).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name,
            FieldValue.atomic_value.isnot(None),
            FieldValue.atomic_value != ''
        )

        # Modell-Filter wenn angegeben
        if model_filter:
            query = query.filter(SearchResult.model_used == model_filter)

        # Gruppiere nach atomischen Werten
        results = query.group_by(FieldValue.atomic_value).order_by(
            func.count(FieldValue.id).desc(),
            func.avg(FieldValue.confidence_score).desc()
        ).all()

        return [(r.atomic_value, r.frequency, r.avg_confidence) for r in results]

    except Exception as e:
        logger.error(f"Fehler beim Abrufen atomischer Werte für {mine_name}.{field_name}: {e}")
        return []


def calculate_best_atomic_value(
    """calculate_best_atomic_value - TODO: Dokumentation hinzufügen"""
    session: Session,
    mine_name: str,
    field_name: str,
    fallback_to_json: bool = False  # REGEL 10: Kein Fallback mehr - nur echte Daten oder NULL
) -> Dict[str, Any]:
    """
    Berechnet den besten atomischen Wert für ein Feld basierend auf Häufigkeit und Confidence

    REGEL 10 KONFORM: Gibt NULL zurück wenn keine Daten vorhanden, kein Fallback!

    Args:
        session: SQLAlchemy Session
        mine_name: Name der Mine
        field_name: Name des Feldes
        fallback_to_json: DEPRECATED - wird ignoriert, immer False (REGEL 10)

    Returns:
        Dict mit best_value, confidence, frequency, sources etc. oder NULL-Dict
    """
    from minesearch.field_value_parser import build_display_value

    # Hole atomische Werte
    atomic_values = get_atomic_field_values(session, mine_name, field_name)

    if atomic_values:
        # Verwende Häufigkeits-Algorithmus für atomische Werte
        best_value, frequency, confidence = atomic_values[0]  # Bereits nach Häufigkeit sortiert

        # Hole Quellenreferenzen für diesen Wert
        source_refs = get_source_references_for_value(session, mine_name, field_name, best_value)

        # Baue Display-Wert mit Quellenreferenzen
        display_value = build_display_value(best_value, source_refs)

        return {
            'atomic_value': best_value,
            'display_value': display_value,
            'confidence_score': confidence,
            'frequency': frequency,
            'source_references': source_refs,
            'method': 'atomic_normalized',
            'alternative_values': [
                {
                    'value': val,
                    'frequency': freq,
                    'confidence': conf
                }
                for val, freq, conf in atomic_values[1:5]  # Bis zu 4 Alternativen
            ]
        }

    else:
        # REGEL 10: Kein Fallback - NULL zurückgeben wenn keine Daten
        logger.info(f"[REGEL 10] Keine atomischen Werte für {mine_name}.{field_name} - gebe NULL zurück")
        return {
            'atomic_value': None,  # NULL statt leerer String
            'display_value': None,  # NULL statt "Nichts gefunden"
            'confidence_score': None,  # NULL statt 0.0
            'frequency': 0,
            'source_references': [],
            'method': 'no_data'  # Klare Kennzeichnung: keine Daten vorhanden
        }


def get_source_references_for_value(
    """get_source_references_for_value - TODO: Dokumentation hinzufügen"""
    session: Session,
    mine_name: str,
    field_name: str,
    atomic_value: str
) -> List[int]:
    """
    Holt Quellenreferenzen für einen spezifischen atomischen Wert

    Returns:
        Liste von globalen Quellenreferenz-Nummern
    """
    from minesearch.database.models import FieldValue, FieldValueSource, SearchResult, Source

    try:
        # Query für Quellen dieses atomischen Wertes
        query = session.query(Source.id).join(FieldValueSource).join(FieldValue).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name,
            FieldValue.atomic_value == atomic_value
        ).distinct()

        source_ids = [r[0] for r in query.all()]

        # Mappe zu globalen Referenznummern (vereinfacht - könnte komplexer werden)
        return source_ids[:10]  # Maximal 10 Quellenreferenzen

    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Quellenreferenzen: {e}")
        return []


def calculate_best_value_from_json(
    """calculate_best_value_from_json - TODO: Dokumentation hinzufügen"""
    session: Session,
    mine_name: str,
    field_name: str
) -> Dict[str, Any]:
    """
    Fallback-Methode: Berechnet besten Wert aus JSON-Daten (Legacy-Kompatibilität)
    """
    from minesearch.database.models import SearchResult
    from minesearch.field_value_parser import extract_atomic_value_and_sources

    try:
        # Hole alle SearchResults für diese Mine
        results = session.query(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            SearchResult.structured_data.isnot(None)
        ).all()

        # Sammle Werte aus JSON
        values_with_sources = []
        for result in results:
            structured_data = result.structured_data or {}
            if field_name in structured_data:
                field_value = structured_data[field_name]
                if field_value:
                    atomic_value, source_refs = extract_atomic_value_and_sources(str(field_value))
                    if atomic_value.strip():
                        values_with_sources.append((atomic_value.strip(), source_refs))

        if values_with_sources:
            # Finde häufigsten Wert
            value_counts = Counter([val for val, _ in values_with_sources])
            best_value, frequency = value_counts.most_common(1)[0]

            # Sammle alle Quellenreferenzen für diesen Wert
            all_source_refs = []
            for val, refs in values_with_sources:
                if value == best_value:
                    all_source_refs.extend(refs)

            unique_refs = sorted(list(set(all_source_refs)))
            display_value = f"{best_value} [{','.join(map(str, unique_refs))}]" if unique_refs else best_value

            return {
                'atomic_value': best_value,
                'display_value': display_value,
                'confidence_score': min(75.0, frequency * 15),  # Confidence basierend auf Häufigkeit
                'frequency': frequency,
                'source_references': unique_refs,
                'method': 'json_fallback'
            }

    except Exception as e:
        logger.error(f"Fehler bei JSON-Fallback für {mine_name}.{field_name}: {e}")

    return {
        'atomic_value': '',
        'display_value': 'Nichts gefunden',
        'confidence_score': 0.0,
        'frequency': 0,
        'source_references': [],
        'method': 'fallback_failed'
    }


def get_field_statistics_atomic(
    """get_field_statistics_atomic - TODO: Dokumentation hinzufügen"""
    session: Session,
    mine_name: str,
    field_name: str
) -> Dict[str, Any]:
    """
    Statistiken für ein Feld basierend auf atomischen Werten
    """
    from minesearch.database.models import FieldValue, SearchResult, FieldValueSource

    try:
        # Anzahl eindeutiger atomischer Werte
        unique_values = session.query(func.count(func.distinct(FieldValue.atomic_value))).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name,
            FieldValue.atomic_value.isnot(None)
        ).scalar() or 0

        # Gesamtanzahl Einträge
        total_entries = session.query(func.count(FieldValue.id)).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name
        ).scalar() or 0

        # Anzahl verknüpfter Quellen
        source_count =
session.query(func.count(func.distinct(FieldValueSource.source_id))).join(FieldValue).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name
        ).scalar() or 0

        # Durchschnittliche Confidence
        avg_confidence = session.query(func.avg(FieldValue.confidence_score)).join(SearchResult).filter(
            SearchResult.mine_name == mine_name,
            FieldValue.field_name == field_name
        ).scalar() or 0.0

        return {
            'unique_atomic_values': unique_values,
            'total_entries': total_entries,
            'source_count': source_count,
            'avg_confidence': float(avg_confidence),
            'consistency_score': (1.0 / unique_values * 100) if unique_values > 0 else 100.0  # Je
weniger verschiedene Werte, desto konsistenter
        }

    except Exception as e:
        logger.error(f"Fehler bei Statistik-Berechnung für {mine_name}.{field_name}: {e}")
        return {
            'unique_atomic_values': 0,
            'total_entries': 0,
            'source_count': 0,
            'avg_confidence': 0.0,
            'consistency_score': 0.0
        }
