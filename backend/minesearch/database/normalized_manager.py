#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 2.0
Beschreibung: Refacturierter Normalisierter Database Manager (REGEL 1 konform: <500 Zeilen)
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from minesearch.database.manager import DatabaseManager
from minesearch.value_normalizer import value_normalizer
from minesearch.smart_value_extractor import SmartValueExtractor

# Import refactorierter Module
from .normalized_normalizers import (
    normalize_mine_name, normalize_company_name, normalize_mine_type,
    normalize_activity_status, calculate_confidence_score, detect_template_value
)
from .normalized_getters import (
    get_or_create_company, get_or_create_country, get_or_create_region,
    get_or_create_mine_type, get_or_create_commodity, get_or_create_activity_status,
    get_or_create_mine
)
from .normalized_savers import (
    save_mine_field_data, save_search_result_normalized,
    insert_mine_data_field_3nf, get_or_create_field_definition_id
)

logger = logging.getLogger(__name__)

class NormalizedDatabaseManager(DatabaseManager):
    """
    REFACTURIERTER Erweiterte Version des DatabaseManager für normalisiertes Schema

    REGEL 1 KONFORM: Reduziert von 1619 auf <500 Zeilen durch Modul-Aufspaltung
    """

    def __init__(self, *args, **kwargs):
    """__init__ - TODO: Dokumentation hinzufügen"""
        super().__init__(*args, **kwargs)
        self.smart_extractor = SmartValueExtractor()

    # NORMALIZATION FUNCTIONS (delegiert an normalized_normalizers.py)
    def normalize_mine_name(self, name: str) -> str:
        """Delegiert an normalized_normalizers.py"""
        return normalize_mine_name(name)

    def normalize_company_name(self, name: str) -> Optional[str]:
        """Delegiert an normalized_normalizers.py"""
        return normalize_company_name(name)

    def normalize_mine_type(self, type_name: str) -> Optional[str]:
        """Delegiert an normalized_normalizers.py"""
        return normalize_mine_type(type_name)

    def normalize_activity_status(self, status_name: str) -> Optional[str]:
        """Delegiert an normalized_normalizers.py"""
        return normalize_activity_status(status_name)

    def _calculate_confidence_score(self, field_name: str, raw_value: str, atomic_value: str) -> float:
        """Delegiert an normalized_normalizers.py"""
        return calculate_confidence_score(field_name, raw_value, atomic_value)

    def _detect_template_value(self, field_name: str, atomic_value: str) -> bool:
        """Delegiert an normalized_normalizers.py"""
        return detect_template_value(field_name, atomic_value)

    # GET OR CREATE FUNCTIONS (delegiert an normalized_getters.py)
    def get_or_create_company(self, company_name: str, smart_extractor=None, db_session:
    """get_or_create_company - TODO: Dokumentation hinzufügen"""
Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_company(company_name, smart_extractor or self.smart_extractor,
db_session, db_manager or self)

    def get_or_create_country(self, country_name: str, db_session: Optional[Session] = None,
    """get_or_create_country - TODO: Dokumentation hinzufügen"""
db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_country(country_name, db_session, db_manager or self)

    def get_or_create_region(self, region_name: str, smart_extractor=None, country_id: Optional[int]
    """get_or_create_region - TODO: Dokumentation hinzufügen"""
= None, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_region(region_name, smart_extractor or self.smart_extractor,
country_id, db_session, db_manager or self)

    def get_or_create_mine_type(self, type_name: str, smart_extractor=None, db_session:
    """get_or_create_mine_type - TODO: Dokumentation hinzufügen"""
Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_mine_type(type_name, smart_extractor or self.smart_extractor,
db_session, db_manager or self)

    def get_or_create_commodity(self, commodity_name: str, smart_extractor=None, db_session:
    """get_or_create_commodity - TODO: Dokumentation hinzufügen"""
Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_commodity(commodity_name, smart_extractor or self.smart_extractor,
db_session, db_manager or self)

    def get_or_create_activity_status(self, status_name: str, smart_extractor=None, db_session:
    """get_or_create_activity_status - TODO: Dokumentation hinzufügen"""
Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_activity_status(status_name, smart_extractor or self.smart_extractor,
db_session, db_manager or self)

    def get_or_create_mine(self, mine_name: str, smart_extractor=None, structured_data: Dict[str,
    """get_or_create_mine - TODO: Dokumentation hinzufügen"""
Any] = None, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
        """Delegiert an normalized_getters.py"""
        return get_or_create_mine(mine_name, smart_extractor or self.smart_extractor,
structured_data, db_session, db_manager or self)

    # SAVE FUNCTIONS (delegiert an normalized_savers.py)
    def save_mine_field_data(self, mine_id: int, search_result_id: int, structured_data: Dict[str, Any],
    """save_mine_field_data - TODO: Dokumentation hinzufügen"""
                           model_used: str, sources: List[Dict[str, str]] = None,
                           session_id: str = None, db_session: Optional[Session] = None,
                           value_normalizer=None) -> None:
        """Delegiert an normalized_savers.py"""
        return save_mine_field_data(self, mine_id, search_result_id, structured_data, model_used,
sources, session_id, db_session, value_normalizer)

    def save_search_result_normalized(self, mine_name: str, structured_data: Dict[str, Any],
    """save_search_result_normalized - TODO: Dokumentation hinzufügen"""
                                    sources: List[Dict[str, str]], model_used: str,
                                    search_duration: int, session_id: str,
                                    db_session: Optional[Session] = None,
                                    value_normalizer=None) -> Optional[int]:
        """Delegiert an normalized_savers.py"""
        return save_search_result_normalized(self, mine_name, structured_data, sources, model_used,
search_duration, session_id, db_session, value_normalizer)

    def _insert_mine_data_field_3nf(self, session: Session, field_data: Dict[str, Any],
    """_insert_mine_data_field_3nf - TODO: Dokumentation hinzufügen"""
                                   actor: str = "system", reason: str = "data_import") -> None:
        """Delegiert an normalized_savers.py"""
        return insert_mine_data_field_3nf(self, session, field_data, actor, reason)

    def _get_or_create_field_definition_id(self, session: Session, field_name: str) -> int:
        """Delegiert an normalized_savers.py"""
        return get_or_create_field_definition_id(self, session, field_name)

    # UTILITY FUNCTIONS (bleiben hier da sie klein sind)
    def _determine_field_type(self, field_name: str) -> str:
        """
        Bestimme ob ein Feld als 'normalized' oder 'primitive' gespeichert werden soll
        """
        field_lower = field_name.lower()

        # NORMALIZED Felder: Werden in Referenz-Tabellen normalisiert
        normalized_patterns = [
            'rohstoffabbau', 'commodity', 'commodities',
            'eigentümer', 'owner', 'betreiber', 'operator',
            'aktivitätsstatus', 'activity', 'status',
            'minentyp', 'mine_type', 'type',
            'country', 'land', 'staat',
            'region', 'province', 'state'
        ]

        for pattern in normalized_patterns:
            if pattern in field_lower:
                return 'normalized'

        # Standard: PRIMITIVE Felder
        return 'primitive'

    def _get_or_create_ai_model_id(self, session: Session, model_name: str) -> int:
        """Hole oder erstelle AI Model ID"""
        try:
            result = session.execute(text("SELECT id FROM ai_models WHERE name = :name"), {'name': model_name})
            row = result.fetchone()
            if row:
                return row[0]

            # Erstelle neues Model
            insert_result = session.execute(text("""
                INSERT INTO ai_models (name, provider, description, created_at)
                VALUES (:name, :provider, :description, :created_at)
                RETURNING id
            """), {
                'name': model_name,
                'provider': 'unknown',
                'description': f'Auto-created for {model_name}',
                'created_at': datetime.now()
            })
            model_id = insert_result.fetchone()[0]
            session.flush()
            return model_id

        except Exception as e:
            logger.error(f"Fehler beim Erstellen/Finden der AI Model ID: {e}")
            return 1  # Fallback zu Default-Model

    def _get_source_id_by_name(self, session: Session, source_name: str) -> Optional[int]:
        """Hole Source-ID basierend auf Namen"""
        try:
            if not source_name or source_name.lower() in ['unknown', 'unbekannt']:
                return None

            result = session.execute(text("SELECT id FROM sources WHERE name = :name"), {'name': source_name})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logger.debug(f"Keine Source-ID gefunden für '{source_name}': {e}")
            return None

    def _ensure_field_definitions_initialized(self) -> None:
        """
        KRITISCHER FIX 29.08.2025: Stelle sicher, dass field_definitions Tabelle
        mit allen Standard-Feldnamen gefüllt ist
        """
        try:
            with self.get_session() as session:
                # Importiere CSV_COLUMNS aus config
                from minesearch.config import CSV_COLUMNS

                # Zusätzliche dynamische Feldnamen die bei Batch-Suchen auftreten können
                additional_fields = [
                    # Test-Felder
                    'TEST_Country', 'TEST_Region', 'TEST_Owner', 'DIRECT_TEST',
                    # Häufige Variationen
                    'Mine Name', 'Company', 'Owner', 'Operator', 'Location',
                    'Status', 'Type', 'Commodity', 'Production', 'Capacity'
                ]

                # Kombiniere alle Feldnamen
                all_field_names = list(CSV_COLUMNS) + additional_fields

                # Füge alle Feldnamen hinzu (OR IGNORE für Duplikate)
                for field_name in all_field_names:
                    session.execute(text("""
                        INSERT OR IGNORE INTO field_definitions (field_name, display_name, data_type)
                        VALUES (:field_name, :display_name, 'text')
                    """), {
                        'field_name': field_name,
                        'display_name': field_name
                    })

                session.commit()

                # Prüfe finalen Status
                count_result = session.execute(text('SELECT COUNT(*) FROM field_definitions')).fetchone()
                logger.info(f"✅ field_definitions initialisiert: {count_result[0]} Feldnamen verfügbar")

        except Exception as e:
            logger.error(f"❌ Fehler bei field_definitions Initialisierung: {e}")
            # Nicht re-raise, damit der Hauptprozess weiterläuft

    def get_mine_data_with_joins(self, mine_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Hole Minendaten mit JOINs für lesbare Ausgabe der normalisierten Felder"""
        try:
            with self.get_session() as session:
                # Base Query für alle Feldwerte
                base_conditions = "WHERE mdf.mine_id = :mine_id"
                params = {'mine_id': mine_id}

                if session_id:
                    base_conditions += " AND mdf.session_id = :session_id"
                    params['session_id'] = session_id

                # Query mit JOINs für normalisierte Felder
                query = f"""
                SELECT
                    mdf.field_name,
                    mdf.field_type,
                    mdf.primitive_value,
                    mdf.numeric_value,
                    mdf.unit,
                    c.name as commodity_name,
                    comp.name as company_name,
                    ast.status as activity_status,
                    mt.name as mine_type_name,
                    cnt.name as country_name,
                    r.name as region_name,
                    mdf.confidence_score,
                    mdf.is_template_value,
                    mdf.model_used,
                    mdf.extraction_timestamp
                FROM mine_data_fields mdf
                LEFT JOIN commodities c ON mdf.commodity_id = c.id
                LEFT JOIN companies comp ON mdf.company_id = comp.id
                LEFT JOIN activity_statuses ast ON mdf.activity_status_id = ast.id
                LEFT JOIN mine_types mt ON mdf.mine_type_id = mt.id
                LEFT JOIN countries cnt ON mdf.country_id = cnt.id
                LEFT JOIN regions r ON mdf.region_id = r.id
                {base_conditions}
                ORDER BY mdf.field_name
                """

                result = session.execute(text(query), params)
                rows = result.fetchall()

                # Konvertiere zu lesbarem Dictionary
                readable_data = {}
                for row in rows:
                    field_name = row[0]
                    field_type = row[1]

                    if field_type == 'normalized':
                        # Für normalisierte Felder: Zeige den lesbaren Namen
                        if row[5]:  # commodity_name
                            readable_data[field_name] = row[5]
                        elif row[6]:  # company_name
                            readable_data[field_name] = row[6]
                        elif row[7]:  # activity_status
                            readable_data[field_name] = row[7]
                        elif row[8]:  # mine_type_name
                            readable_data[field_name] = row[8]
                        elif row[9]:  # country_name
                            readable_data[field_name] = row[9]
                        elif row[10]:  # region_name
                            readable_data[field_name] = row[10]
                    else:
                        # Für primitive Felder: Zeige den primitiven Wert
                        value = row[2]  # primitive_value
                        if row[3] and row[4]:  # numeric_value und unit
                            value = f"{row[3]} {row[4]}"
                        readable_data[field_name] = value

                return readable_data

        except Exception as e:
            logger.error(f"[JOIN_QUERY_ERROR] Fehler beim Abrufen der Minendaten für Mine {mine_id}: {e}")
            return {}
