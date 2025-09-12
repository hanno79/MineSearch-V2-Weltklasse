"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Get-or-Create Funktionen für Referenzdaten (Refactoring aus normalized_manager.py)
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .normalized_normalizers import (
    normalize_company_name,
    normalize_country_name,
    normalize_mine_name, 
    normalize_mine_type,
    normalize_activity_status
)

logger = logging.getLogger(__name__)


def get_or_create_company(company_name: str, smart_extractor, db_session: Optional[Session] = None, 
                          db_manager=None) -> Optional[int]:
    """Hole oder erstelle Unternehmen mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    if not company_name or company_name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None
    
    # NEUE LOGIK: Smart Extractor für Sätze
    if smart_extractor.is_sentence_like(company_name) or smart_extractor.should_reject_value(company_name):
        logger.warning(f"[SMART_COMPANY] Satz erkannt, verwende Smart Extractor: '{company_name[:60]}...'")
        extracted_company = smart_extractor.extract_company_from_text(company_name)
        if not extracted_company:
            logger.warning(f"[SMART_COMPANY] Kein Firmenname extrahierbar aus: '{company_name[:60]}...' → ABGELEHNT")
            return None
        company_name = extracted_company
        logger.info(f"[SMART_COMPANY] Erfolgreich extrahiert: '{extracted_company}'")
    
    normalized_name = normalize_company_name(company_name)
    if not normalized_name:
        return None
    
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        # Suche existierende Firma mit normalisiertem Namen
        result = db_session.execute(text("""
            SELECT id FROM companies 
            WHERE LOWER(name) = :normalized_name
            LIMIT 1
        """), {'normalized_name': normalized_name})
        existing = result.fetchone()
        if existing:
            return existing[0]
        # KORREKTUR: Speichere normalisierten Namen für Konsistenz
        insert_result = db_session.execute(text("""
            INSERT INTO companies (name) 
            VALUES (:name)
        """), {
            'name': normalized_name.title()  # Normalisiert + Title Case
        })
        db_session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            # Suche existierende Firma mit normalisiertem Namen
            result = session.execute(text("""
                SELECT id FROM companies 
                WHERE LOWER(name) = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # KORREKTUR: Speichere normalisierten Namen für Konsistenz
            insert_result = session.execute(text("""
                INSERT INTO companies (name) 
                VALUES (:name)
            """), {
                'name': normalized_name.title()  # Normalisiert + Title Case
            })
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_country(country_name: str, db_session: Optional[Session] = None, 
                          db_manager=None) -> Optional[int]:
    """Hole oder erstelle Land mit Normalisierung zu deutschen Namen"""
    if not country_name or country_name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None
    
    # KORREKTUR: Normalisierung hinzugefügt 
    normalized_country = normalize_country_name(country_name)
    if not normalized_country:
        return None
        
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        session = db_session
        # Suche mit normalisiertem Namen
        result = session.execute(text("""
            SELECT id FROM countries WHERE name = :country_name LIMIT 1
        """), {'country_name': normalized_country})
        existing = result.fetchone()
        if existing:
            return existing[0]
        # KORREKTUR: Speichere normalisierten Namen
        insert_result = session.execute(text("""
            INSERT INTO countries (name) VALUES (:country_name)
        """), {'country_name': normalized_country})
        session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            # Suche mit normalisiertem Namen
            result = session.execute(text("""
                SELECT id FROM countries WHERE name = :country_name LIMIT 1
            """), {'country_name': normalized_country})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # KORREKTUR: Speichere normalisierten Namen
            insert_result = session.execute(text("""
                INSERT INTO countries (name) VALUES (:country_name)
            """), {'country_name': normalized_country})
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_region(region_name: str, smart_extractor, country_id: Optional[int] = None, 
                         db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Region mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    if not region_name or region_name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None
        
    # NEUE LOGIK: Smart Extractor für Sätze
    if smart_extractor.is_sentence_like(region_name) or smart_extractor.should_reject_value(region_name):
        logger.warning(f"[SMART_REGION] Satz erkannt, verwende Smart Extractor: '{region_name[:60]}...'")
        extracted_region = smart_extractor.extract_region_from_text(region_name)
        if not extracted_region:
            logger.warning(f"[SMART_REGION] Keine Region extrahierbar aus: '{region_name[:60]}...' → ABGELEHNT")
            return None
        region_name = extracted_region
        logger.info(f"[SMART_REGION] Erfolgreich extrahiert: '{extracted_region}'")
        
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        session = db_session
        result = session.execute(text("""
            SELECT id FROM regions WHERE name = :region_name LIMIT 1
        """), {'region_name': region_name})
        existing = result.fetchone()
        if existing:
            return existing[0]
        insert_result = session.execute(text("""
            INSERT INTO regions (name, country_id) VALUES (:region_name, :country_id)
        """), {'region_name': region_name, 'country_id': country_id})
        session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM regions WHERE name = :region_name LIMIT 1
            """), {'region_name': region_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO regions (name, country_id) VALUES (:region_name, :country_id)
            """), {'region_name': region_name, 'country_id': country_id})
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_mine_type(type_name: str, smart_extractor, db_session: Optional[Session] = None, 
                            db_manager=None) -> Optional[int]:
    """Hole oder erstelle Minentyp mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    if not type_name:
        return None
    
    # NEUE LOGIK: Smart Extractor für Sätze
    if smart_extractor.is_sentence_like(type_name) or smart_extractor.should_reject_value(type_name):
        logger.warning(f"[SMART_MINE_TYPE] Satz erkannt, verwende Smart Extractor: '{type_name[:60]}...'")
        extracted_type = smart_extractor.extract_mine_type_from_text(type_name)
        if not extracted_type:
            logger.warning(f"[SMART_MINE_TYPE] Kein Minentyp extrahierbar aus: '{type_name[:60]}...' → ABGELEHNT")
            return None
        type_name = extracted_type
        logger.info(f"[SMART_MINE_TYPE] Erfolgreich extrahiert: '{extracted_type}'")
    
    # INTELLIGENTE NORMALISIERUNG: Synonyme erkennen
    normalized_type = normalize_mine_type(type_name)
    if not normalized_type:
        return None
        
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        session = db_session
        # Suche nach dem normalisierten Namen
        result = session.execute(text("""
            SELECT id FROM mine_types WHERE name = :type_name LIMIT 1
        """), {'type_name': normalized_type})
        existing = result.fetchone()
        if existing:
            return existing[0]
        # Falls nicht gefunden, erstelle mit normalisiertem Namen
        insert_result = session.execute(text("""
            INSERT INTO mine_types (name) VALUES (:type_name)
        """), {'type_name': normalized_type})
        session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            # Suche nach dem normalisierten Namen
            result = session.execute(text("""
                SELECT id FROM mine_types WHERE name = :type_name LIMIT 1
            """), {'type_name': normalized_type})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Falls nicht gefunden, erstelle mit normalisiertem Namen
            insert_result = session.execute(text("""
                INSERT INTO mine_types (name) VALUES (:type_name)
            """), {'type_name': normalized_type})
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_commodity(commodity_name: str, smart_extractor, db_session: Optional[Session] = None, 
                            db_manager=None) -> Optional[int]:
    """Hole oder erstelle Rohstoff mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    if not commodity_name or commodity_name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None
    
    # NEUE LOGIK: Smart Extractor für Sätze
    if smart_extractor.is_sentence_like(commodity_name) or smart_extractor.should_reject_value(commodity_name):
        logger.warning(f"[SMART_COMMODITY] Satz erkannt, verwende Smart Extractor: '{commodity_name[:60]}...'")
        extracted_commodity = smart_extractor.extract_commodity_from_text(commodity_name)
        if not extracted_commodity:
            logger.warning(f"[SMART_COMMODITY] Kein Rohstoff extrahierbar aus: '{commodity_name[:60]}...' → ABGELEHNT")
            return None
        commodity_name = extracted_commodity
        logger.info(f"[SMART_COMMODITY] Erfolgreich extrahiert: '{extracted_commodity}'")
    
    # Synonyme für Rohstoffe
    commodity_synonyms = {
        'gold': 'Gold',
        'kupfer': 'Kupfer', 
        'copper': 'Kupfer',
        'silber': 'Silber',
        'silver': 'Silber',
        'eisenerz': 'Eisenerz',
        'iron ore': 'Eisenerz',
        'kohle': 'Kohle',
        'coal': 'Kohle',
        'nickel': 'Nickel',
        'zink': 'Zink',
        'zinc': 'Zink',
        'blei': 'Blei',
        'lead': 'Blei',
        'platin': 'Platin',
        'platinum': 'Platin',
        'palladium': 'Palladium',
        'uran': 'Uran',
        'uranium': 'Uran',
        'lithium': 'Lithium',
        'diamanten': 'Diamanten',
        'diamonds': 'Diamanten'
    }
    
    # Normalisiere Input
    normalized = commodity_name.lower().strip()
    
    # Prüfe Synonyme
    if normalized in commodity_synonyms:
        commodity_name = commodity_synonyms[normalized]
    else:
        # Zusätzliche Validierung für unbekannte Werte
        if len(commodity_name) > 50:
            logger.warning(f"[SMART_COMMODITY] Unbekannter Rohstoff zu lang → ABGELEHNT: '{commodity_name[:60]}...'")
            return None
        # Fallback: Title Case
        commodity_name = commodity_name.title()
        
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        session = db_session
        result = session.execute(text("""
            SELECT id FROM commodities WHERE name = :commodity_name LIMIT 1
        """), {'commodity_name': commodity_name})
        existing = result.fetchone()
        if existing:
            return existing[0]
        # Falls nicht gefunden, erstelle neuen Rohstoff
        insert_result = session.execute(text("""
            INSERT INTO commodities (name) VALUES (:commodity_name)
        """), {'commodity_name': commodity_name})
        session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM commodities WHERE name = :commodity_name LIMIT 1
            """), {'commodity_name': commodity_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO commodities (name) VALUES (:commodity_name)
            """), {'commodity_name': commodity_name})
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_activity_status(status_name: str, smart_extractor, db_session: Optional[Session] = None, 
                                   db_manager=None) -> Optional[int]:
    """Hole oder erstelle Aktivitätsstatus mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    if not status_name:
        return None
    
    # NEUE LOGIK: Smart Extractor für Sätze
    if smart_extractor.is_sentence_like(status_name) or smart_extractor.should_reject_value(status_name):
        logger.warning(f"[SMART_ACTIVITY] Satz erkannt, verwende Smart Extractor: '{status_name[:60]}...'")
        extracted_status = smart_extractor.extract_activity_status_from_text(status_name)
        if not extracted_status:
            logger.warning(f"[SMART_ACTIVITY] Kein Status extrahierbar aus: '{status_name[:60]}...' → ABGELEHNT")
            return None
        status_name = extracted_status
        logger.info(f"[SMART_ACTIVITY] Erfolgreich extrahiert: '{extracted_status}'")
    
    # INTELLIGENTE NORMALISIERUNG: Synonyme erkennen
    normalized_status = normalize_activity_status(status_name)
    if not normalized_status:
        return None
        
    # Externe Transaktion verwenden, falls bereitgestellt
    if db_session is not None:
        session = db_session
        # Suche nach dem normalisierten Namen
        result = session.execute(text("""
            SELECT id FROM activity_statuses WHERE status = :status_name LIMIT 1
        """), {'status_name': normalized_status})
        existing = result.fetchone()
        if existing:
            return existing[0]
        # Falls nicht gefunden, erstelle mit normalisiertem Namen
        insert_result = session.execute(text("""
            INSERT INTO activity_statuses (status) VALUES (:status_name)
        """), {'status_name': normalized_status})
        session.flush()
        return insert_result.lastrowid
    
    # Eigene Session verwalten
    if db_manager:
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM activity_statuses WHERE status = :status_name LIMIT 1
            """), {'status_name': normalized_status})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO activity_statuses (status) VALUES (:status_name)
            """), {'status_name': normalized_status})
            session.commit()
            return insert_result.lastrowid
    
    return None


def get_or_create_mine(mine_name: str, smart_extractor, structured_data: Dict[str, Any] = None, 
                       db_session: Optional[Session] = None, db_manager=None,
                       get_or_create_country_func=None, get_or_create_region_func=None) -> Optional[int]:
    """
    Erstellt oder findet eine Mine basierend auf dem Namen.
    
    NEUES SCHEMA (04.09.2025): 
    - Mines Tabelle enthält nur noch: ID, Name, Country, Region
    - Alle anderen Daten (Koordinaten, Fläche, etc.) werden in mine_data_fields gespeichert
    
    Args:
        mine_name: Name der Mine
        structured_data: Optional - zusätzliche Daten für Region/Land
        db_session: Optional - vorhandene DB-Session verwenden
        
    Returns:
        Mine-ID
    """
    normalized_name = normalize_mine_name(mine_name)
    structured_data = structured_data or {}
    
    # Wenn eine Session übergeben wurde, verwende sie
    if db_session:
        session = db_session
        
        # Suche existierende Mine
        result = session.execute(text("""
            SELECT id FROM mines 
            WHERE name = :mine_name
            LIMIT 1
        """), {'mine_name': mine_name})
        
        existing = result.fetchone()
        if existing:
            return existing[0]
        
        # Extrahiere nur Region für das neue vereinfachte Schema
        region = structured_data.get('Region') or structured_data.get('region')
        
        # Hole IDs für Country und Region
        country = structured_data.get('Country') or structured_data.get('country')
        country_id = None
        region_id = None
        
        if country and get_or_create_country_func:
            country_id = get_or_create_country_func(country, db_session=session)
            if region and country_id and get_or_create_region_func:
                region_id = get_or_create_region_func(region, smart_extractor, country_id, db_session=session)
        
        # Erstelle Mine nur mit Name, Country, Region
        insert_result = session.execute(text("""
            INSERT INTO mines 
            (name, country_id, region_id)
            VALUES (:name, :country_id, :region_id)
        """), {
            'name': mine_name,
            'country_id': country_id,
            'region_id': region_id
        })
        session.flush()
        logger.info(f"✅ Neue Mine erstellt: {mine_name} (ID: {insert_result.lastrowid})")
        return insert_result.lastrowid
    
    # Ohne externe Session: eigene Session öffnen und committen
    if db_manager:
        with db_manager.get_session() as session_local:
            # Suche existierende Mine
            result = session_local.execute(text("""
                SELECT id FROM mines 
                WHERE name = :mine_name
                LIMIT 1
            """), {'mine_name': mine_name})
            
            existing = result.fetchone()
            if existing:
                return existing[0]
            
            # Extrahiere nur Region für das neue vereinfachte Schema
            region = structured_data.get('Region') or structured_data.get('region')
            
            # Hole IDs für Country und Region
            country = structured_data.get('Country') or structured_data.get('country')
            country_id = None
            region_id = None
            
            if country and get_or_create_country_func:
                country_id = get_or_create_country_func(country, db_session=session_local, db_manager=db_manager)
                if region and country_id and get_or_create_region_func:
                    region_id = get_or_create_region_func(region, smart_extractor, country_id, 
                                                          db_session=session_local, db_manager=db_manager)
            
            # Erstelle Mine nur mit Name, Country, Region  
            insert_result = session_local.execute(text("""
                INSERT INTO mines 
                (name, country_id, region_id)
                VALUES (:name, :country_id, :region_id)
            """), {
                'name': mine_name,
                'country_id': country_id,
                'region_id': region_id
            })
            session_local.commit()
            logger.info(f"✅ Neue Mine erstellt: {mine_name} (ID: {insert_result.lastrowid})")
            return insert_result.lastrowid
    
    return None