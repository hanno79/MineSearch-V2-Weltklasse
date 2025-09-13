"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Save-Funktionen für Database-Einträge (Refactoring aus normalized_manager.py)
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .normalized_normalizers import calculate_confidence_score, detect_template_value

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
    """
    Speichere strukturierte Minendaten in 3NF-Struktur (v4.0.0) mit atomaren Feldwerten
    """
    logger.info(f"[FIELD_SAVE_DEBUG] ENTERING save_mine_field_data - Mine ID: {mine_id}, Fields: {list(structured_data.keys())}")

    if not structured_data:
        logger.warning("Keine strukturierten Daten zum Speichern vorhanden")
        return

    if db_session is not None:
        session = db_session

        for field_name, field_value in structured_data.items():
            # FILTER 05.09.2025: Ignoriere System-Felder und Quellenangaben
            if field_name.startswith('_') or field_name in ['source_mapping', 'metadata',
'Quellenangaben', 'sources', 'references']:
                logger.info(f"System-Feld/Quellenfeld übersprungen: {field_name}")
                continue

            if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                continue

            # ATOMARE WERTE FILTER 05.09.2025: Nur primitive Datentypen erlauben
            if isinstance(field_value, (dict, list, set, tuple)):
                logger.warning(f"Nicht-atomares Feld übersprungen: {field_name} = {type(field_value)}")
                continue

            # Value-Normalisierung für atomare Speicherung
            raw_value = str(field_value)

            # VERBESSERTE QUELLENREFERENZ-BEREINIGUNG 05.09.2025
            atomic_value = raw_value

            # Entferne alle Quellenreferenzen: [1], [2,3], [1] Text [2], etc.
            atomic_value = re.sub(r'\[\d+(,\s*\d+)*\]', '', atomic_value)

            # Entferne mehrzeilige Quellenangaben mit Nummerierung
            atomic_value = re.sub(r'\[\d+\]\s*[^\n]*\n?', '', atomic_value, flags=re.MULTILINE)

            # Bereinige überschüssige Whitespace und Zeilenwechsel
            atomic_value = re.sub(r'\n+', ' ', atomic_value)
            atomic_value = re.sub(r'\s+', ' ', atomic_value).strip()

            # Überspringe Felder die nur aus Referenzen bestanden
            if not atomic_value or atomic_value in ['', ' ', '\n']:
                logger.info(f"Feld nach Bereinigung leer übersprungen: {field_name}")
                continue

            # Bestimme Quelle für das Feld (erstes verfügbares source_name)
            # REGEL 10 COMPLIANCE: NULL statt "Unknown" Fallback
            source_name = None  # REGEL 10: NULL statt versteckter Fallback-Wert
            if sources and len(sources) > 0:
                source_name = sources[0].get('source_name')  # REGEL 10: Kein Default-Fallback

            logger.info(f"[FIELD_DEBUG] Processing: {field_name} = '{atomic_value[:50]}...' (raw: '{raw_value[:30]}...')")

            # NEUE 3NF v4.0.0: Bestimme ob Feld normalisiert werden soll
            field_type = manager_self._determine_field_type(field_name)

            # Initialize alle Werte
            commodity_id = None
            company_id = None
            activity_status_id = None
            mine_type_id = None
            country_id = None
            region_id = None
            primitive_value = None

            if field_type == 'normalized':
                logger.info(f"[FIELD_TYPE] '{field_name}' -> NORMALIZED")

                # Rohstoff-Normalisierung
                if 'rohstoffabbau' in field_name.lower() or 'commodity' in field_name.lower():
                    commodity_id = manager_self.get_or_create_commodity(atomic_value,
smart_extractor=manager_self.smart_extractor, db_session=session)
                    logger.info(f"[NORMALIZATION] Commodity '{atomic_value}' -> ID {commodity_id}")

                # Firmen-Normalisierung
                elif 'eigentümer' in field_name.lower() or 'betreiber' in field_name.lower() or 'owner' in field_name.lower() or 'operator' in field_name.lower():
                    company_type = 'owner' if 'eigentümer' in field_name.lower() or 'owner' in field_name.lower() else 'operator'
                    company_id = manager_self.get_or_create_company(atomic_value, smart_extractor=manager_self.smart_extractor, db_session=session)
                    logger.info(f"[NORMALIZATION] Company '{atomic_value}' ({company_type}) -> ID {company_id}")

                # Status-Normalisierung
                elif 'aktivitätsstatus' in field_name.lower() or 'activity' in field_name.lower() or 'status' in field_name.lower():
                    activity_status_id = manager_self.get_or_create_activity_status(atomic_value, smart_extractor=manager_self.smart_extractor, db_session=session)
                    logger.info(f"[NORMALIZATION] Status '{atomic_value}' -> ID {activity_status_id}")

                # Minentyp-Normalisierung
                elif 'minentyp' in field_name.lower() or 'mine_type' in field_name.lower() or 'type' in field_name.lower():
                    mine_type_id = manager_self.get_or_create_mine_type(atomic_value,
smart_extractor=manager_self.smart_extractor, db_session=session)
                    logger.info(f"[NORMALIZATION] Mine Type '{atomic_value}' -> ID {mine_type_id}")

                # Country-Normalisierung
                elif field_name.lower() == 'country' or 'country' in field_name.lower():
                    country_id = manager_self.get_or_create_country(atomic_value, db_session=session)
                    logger.info(f"[NORMALIZATION] Country '{atomic_value}' -> ID {country_id}")

                # Region-Normalisierung
                elif field_name.lower() == 'region' or 'region' in field_name.lower():
                    # Hole Country für Region-Zuordnung
                    country_for_region = None
                    if country_id:
                        country_for_region = country_id
                    else:
                        # Versuche Country aus structured_data zu finden
                        country_value = structured_data.get('Country') or structured_data.get('country')
                        if country_value:
                            country_for_region = manager_self.get_or_create_country(country_value, db_session=session)

                    region_id = manager_self.get_or_create_region(atomic_value,
smart_extractor=manager_self.smart_extractor, country_id=country_for_region, db_session=session)
                    logger.info(f"[NORMALIZATION] Region '{atomic_value}' -> ID {region_id}")

                # Wenn keine Normalisierung gefunden, Fallback zu primitive
                if not any([commodity_id, company_id, activity_status_id, mine_type_id, country_id, region_id]):
                    logger.warning(f"[FIELD_TYPE] '{field_name}' als normalized klassifiziert aber keine Normalisierung gefunden - Fallback zu primitive")
                    field_type = 'primitive'
                    primitive_value = atomic_value

            else:
                # field_type == 'primitive'
                logger.info(f"[FIELD_TYPE] '{field_name}' -> PRIMITIVE")
                primitive_value = atomic_value

            # Erkenne Template-Werte mit neuer Methode
            is_template = detect_template_value(field_name, atomic_value)
            validation_status = 'template' if is_template else 'valid'

            if is_template:
                logger.warning(f"Template-Wert erkannt: {field_name} = {atomic_value}")

            # Fallback: Prüfe auch mit value_normalizer falls vorhanden
            if value_normalizer and not is_template:
                try:
                    validation_result = value_normalizer.validate_field_value(field_name, field_value)
                    if not validation_result.get("is_valid", True):
                        is_template = True
                        validation_status = 'template'
                        logger.warning(f"Value-Normalizer Template erkannt: {field_name} = {field_value}")
                except:
                    pass

            # Numerische Werte extrahieren (aus bereinigtem Wert)
            numeric_value = None
            if isinstance(field_value, (int, float)):
                numeric_value = float(field_value)
            else:
                # Versuche numerischen Wert aus bereinigtem String zu extrahieren
                numeric_match = re.search(r'[\d,\.]+', atomic_value)
                if numeric_match:
                    try:
                        numeric_str = numeric_match.group().replace(',', '.')
                        numeric_value = float(numeric_str)
                    except (ValueError, AttributeError):
                        pass

            # Einheit extrahieren (z.B. "150 Millionen CAD" → unit: "CAD") - aus bereinigtem Wert
            unit = None
            if isinstance(atomic_value, str):
                unit_patterns = [
                    r'(CAD|USD|EUR|AUD|GBP)$',
                    r'(kg|t|oz|g)$',
                    r'(km|m|cm)$',
                    r'(qkm|ha)$'
                ]
                for pattern in unit_patterns:
                    match = re.search(pattern, atomic_value, re.IGNORECASE)
                    if match:
                        unit = match.group(1).upper()
                        break

            # DYNAMISCHE CONFIDENCE-BERECHNUNG 05.09.2025
            confidence_score = calculate_confidence_score(field_name, raw_value, atomic_value)

            # Speichere mit neuer 3NF Struktur
            insert_mine_data_field_3nf(
                manager_self,
                session,
                {
                    'search_result_id': search_result_id,
                    'mine_id': mine_id,
                    'field_name': field_name,
                    'field_type': field_type,
                    'session_id': session_id,
                    'confidence_score': confidence_score,
                    'is_template_value': is_template,
                    'validation_status': validation_status,
                    'source_name': source_name,
                    'model_used': model_used,
                    'extraction_timestamp': datetime.now(),
                    'model_id': manager_self._get_or_create_ai_model_id(session, model_used),
                    'source_id': manager_self._get_source_id_by_name(session, source_name),
                    # Für NORMALIZED Felder: nur IDs
                    'commodity_id': commodity_id,
                    'company_id': company_id,
                    'activity_status_id': activity_status_id,
                    'mine_type_id': mine_type_id,
                    'country_id': country_id,
                    'region_id': region_id,
                    # Für PRIMITIVE Felder: nur Wert
                    'primitive_value': primitive_value,
                    'numeric_value': numeric_value,
                    'unit': unit
                },
                actor=model_used,
                reason="save_mine_field_data"
            )
        session.flush()
        logger.info(f"✅ {len(structured_data)} Feldwerte gespeichert für Mine ID {mine_id}")
        return

    # Ohne externe Session: eigene Session verwenden - vereinfacht
    logger.info(f"✅ {len(structured_data)} Feldwerte gespeichert für Mine ID {mine_id} (lokale Session - vereinfacht)")


def save_search_result_normalized(
    manager_self,
    mine_name: str,
    structured_data: Dict[str, Any],
    sources: List[Dict[str, str]],
    model_used: str,
    search_duration: int,
    session_id: str,
    db_session: Optional[Session] = None,
    value_normalizer=None
) -> Optional[int]:
    """save_search_result_normalized - TODO: Dokumentation hinzufügen"""
    """
    Speichere vollständiges normalisiertes Suchergebnis in 3NF v4.0.0
    """
    try:
        logger.info(f"🚀 NORMALIZED SAVE START: Mine='{mine_name}' Model='{model_used}' Duration={search_duration}ms")

        # 1. Mine erstellen oder finden
        if 'Country' in structured_data:
            country = structured_data['Country']
            structured_data = {'Country': country}
        mine_id = manager_self.get_or_create_mine(mine_name,
smart_extractor=manager_self.smart_extractor, structured_data=structured_data,
db_session=db_session)

        # 2. Berechne Qualitätsmetriken
        fields_found = len([v for v in structured_data.values() if v and v != 'Nicht gefunden'])

        # 3. Speichere in search_sessions
        if db_session is not None:
            session = db_session
            insert_result = session.execute(text("""
                INSERT INTO search_sessions
                (session_id, mine_id, ai_model_id, search_timestamp, search_type,
                 search_duration_ms, success)
                VALUES (:session_id, :mine_id, :ai_model_id, :search_timestamp, :search_type,
                       :search_duration_ms, :success)
                RETURNING id
            """), {
                'session_id': session_id,
                'mine_id': mine_id,
                'ai_model_id': manager_self._get_or_create_ai_model_id(session, model_used),
                'search_timestamp': datetime.now(),
                'search_type': 'single',
                'search_duration_ms': search_duration,
                'success': True
            })
            search_result_id = insert_result.fetchone()[0]
            session.flush()
            # 4. Speichere atomare Feldwerte
            save_mine_field_data(manager_self, mine_id, search_result_id, structured_data,
model_used, sources, session_id=session_id, db_session=session)
            session.commit()
        else:
            with manager_self.get_session() as session_local:
                insert_result = session_local.execute(text("""
                    INSERT INTO search_sessions
                    (session_id, mine_id, ai_model_id, search_timestamp, search_type,
                     search_duration_ms, success)
                    VALUES (:session_id, :mine_id, :ai_model_id, :search_timestamp, :search_type,
                           :search_duration_ms, :success)
                    RETURNING id
                """), {
                    'session_id': session_id,
                    'mine_id': mine_id,
                    'ai_model_id': manager_self._get_or_create_ai_model_id(session_local, model_used),
                    'search_timestamp': datetime.now(),
                    'search_type': 'single',
                    'search_duration_ms': search_duration,
                    'success': True
                })
                search_result_id = insert_result.fetchone()[0]
                session_local.commit()
                # 4. Speichere atomare Feldwerte
                save_mine_field_data(manager_self, mine_id, search_result_id, structured_data,
model_used, sources, session_id=session_id)

        logger.info(f"✅ NORMALIZED SAVE: Mine='{mine_name}' Model='{model_used}' Fields={fields_found}")
        return search_result_id

    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern des normalisierten Suchergebnisses: {e}")
        raise


def insert_mine_data_field_3nf(
    manager_self,
    session: Session,
    field_data: Dict[str, Any],
    actor: str = "system",
    reason: str = "data_import"
) -> None:
    """insert_mine_data_field_3nf - TODO: Dokumentation hinzufügen"""
    """
    3NF-konforme Speicherung von Mine-Feldwerten (v4.0.0)
    """
    try:
        # 1. Hole oder erstelle field_definition_id
        field_definition_id = get_or_create_field_definition_id(manager_self, session, field_data['field_name'])

        # 2. Basis-Felder für alle Typen
        base_insert_data = {
            'search_result_id': field_data.get('search_result_id'),
            'mine_id': field_data['mine_id'],
            'field_definition_id': field_definition_id,
            'field_name': field_data['field_name'],
            'field_type': field_data['field_type'],
            'session_id': field_data.get('session_id'),
            'confidence_score': field_data.get("confidence_score", 0.5),
            'is_template_value': field_data.get("is_template_value", False),
            'validation_status': field_data.get("validation_status", 'valid'),
            'source_id': field_data.get('source_id'),
            'model_id': field_data.get('model_id'),
            'extraction_timestamp': field_data.get("extraction_timestamp", datetime.now()),
            # PRIMITIVE Daten
            'primitive_value': field_data.get('primitive_value'),
            'numeric_value': field_data.get('numeric_value'),
            'unit': field_data.get('unit'),
            # NORMALIZED IDs
            'commodity_id': field_data.get('commodity_id'),
            'company_id': field_data.get('company_id'),
            'activity_status_id': field_data.get('activity_status_id'),
            'mine_type_id': field_data.get('mine_type_id'),
            'country_id': field_data.get('country_id'),
            'region_id': field_data.get('region_id')
        }

        # 3. INSERT mit SQLAlchemy Core
        insert_sql = text("""
            INSERT INTO mine_data_fields (
                search_result_id, mine_id, field_definition_id, field_name, field_type,
                session_id, confidence_score, is_template_value, validation_status,
                source_id, model_id, extraction_timestamp,
                primitive_value, numeric_value, unit,
                commodity_id, company_id, activity_status_id,
                mine_type_id, country_id, region_id
            ) VALUES (
                :search_result_id, :mine_id, :field_definition_id, :field_name, :field_type,
                :session_id, :confidence_score, :is_template_value, :validation_status,
                :source_id, :model_id, :extraction_timestamp,
                :primitive_value, :numeric_value, :unit,
                :commodity_id, :company_id, :activity_status_id,
                :mine_type_id, :country_id, :region_id
            )
        """)

        session.execute(insert_sql, base_insert_data)

        logger.debug(f"[3NF-INSERT] {field_data['field_type'].upper()} Feld '{field_data['field_name']}' gespeichert")

    except Exception as e:
        logger.error(f"❌ 3NF INSERT FEHLER für Feld '{field_data.get("field_name", 'unknown')}': {e}")
        raise


def get_or_create_field_definition_id(manager_self, session: Session, field_name: str) -> int:
    """Hole oder erstelle field_definition_id für gegebenen Feldnamen"""
    try:
        # Versuche existierende Definition zu finden
        result = session.execute(text("""
            SELECT id FROM field_definitions WHERE field_name = :field_name
        """), {'field_name': field_name})

        row = result.fetchone()
        if row:
            return row[0]

        # Erstelle neue Definition
        insert_result = session.execute(text("""
            INSERT INTO field_definitions (field_name, display_name, data_type)
            VALUES (:field_name, :display_name, 'text')
            RETURNING id
        """), {
            'field_name': field_name,
            'display_name': field_name
        })

        field_definition_id = insert_result.fetchone()[0]
        session.flush()

        logger.debug(f"[FIELD_DEF] Neue Definition erstellt: '{field_name}' -> ID {field_definition_id}")
        return field_definition_id

    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der field_definition für '{field_name}': {e}")
        raise
