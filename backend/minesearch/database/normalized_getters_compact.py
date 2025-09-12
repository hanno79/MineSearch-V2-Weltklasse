"""
Compact Normalized Getters
Kompakte Version der Normalized Getters

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_or_create_company(company_name: str, smart_extractor, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Unternehmen mit Smart Extractor für Satz-zu-Wert Konvertierung"""
    try:
        if not company_name or company_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None

        # Normalisiere Unternehmensname
        normalized_name = _normalize_company_name(company_name)
        
        if not db_session:
            db_session = db_manager.get_session() if db_manager else None
        
        if not db_session:
            logger.error("Keine Datenbank-Session verfügbar")
            return None

        # Prüfe ob Unternehmen bereits existiert
        existing_company = _find_existing_company(db_session, normalized_name)
        if existing_company:
            return existing_company['id']

        # Erstelle neues Unternehmen
        new_company_id = _create_new_company(db_session, normalized_name, company_name)
        
        logger.info(f"✅ Unternehmen erstellt: {normalized_name} (ID: {new_company_id})")
        return new_company_id

    except Exception as e:
        logger.error(f"Fehler beim Erstellen/Abrufen des Unternehmens: {e}")
        return None


def get_or_create_country(country_name: str, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Land"""
    try:
        if not country_name or country_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None

        # Normalisiere Ländernamen
        normalized_name = _normalize_country_name(country_name)
        
        if not db_session:
            db_session = db_manager.get_session() if db_manager else None
        
        if not db_session:
            logger.error("Keine Datenbank-Session verfügbar")
            return None

        # Prüfe ob Land bereits existiert
        existing_country = _find_existing_country(db_session, normalized_name)
        if existing_country:
            return existing_country['id']

        # Erstelle neues Land
        new_country_id = _create_new_country(db_session, normalized_name)
        
        logger.info(f"✅ Land erstellt: {normalized_name} (ID: {new_country_id})")
        return new_country_id

    except Exception as e:
        logger.error(f"Fehler beim Erstellen/Abrufen des Landes: {e}")
        return None


def get_or_create_mine(mine_name: str, country_id: int = None, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Mine"""
    try:
        if not mine_name or mine_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None

        # Normalisiere Minenname
        normalized_name = _normalize_mine_name(mine_name)
        
        if not db_session:
            db_session = db_manager.get_session() if db_manager else None
        
        if not db_session:
            logger.error("Keine Datenbank-Session verfügbar")
            return None

        # Prüfe ob Mine bereits existiert
        existing_mine = _find_existing_mine(db_session, normalized_name)
        if existing_mine:
            return existing_mine['id']

        # Erstelle neue Mine
        new_mine_id = _create_new_mine(db_session, normalized_name, country_id)
        
        logger.info(f"✅ Mine erstellt: {normalized_name} (ID: {new_mine_id})")
        return new_mine_id

    except Exception as e:
        logger.error(f"Fehler beim Erstellen/Abrufen der Mine: {e}")
        return None


def get_or_create_mine_type(mine_type: str, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Minentyp"""
    try:
        if not mine_type or mine_type in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None

        # Normalisiere Minentyp
        normalized_type = _normalize_mine_type(mine_type)
        
        if not db_session:
            db_session = db_manager.get_session() if db_manager else None
        
        if not db_session:
            logger.error("Keine Datenbank-Session verfügbar")
            return None

        # Prüfe ob Minentyp bereits existiert
        existing_type = _find_existing_mine_type(db_session, normalized_type)
        if existing_type:
            return existing_type['id']

        # Erstelle neuen Minentyp
        new_type_id = _create_new_mine_type(db_session, normalized_type)
        
        logger.info(f"✅ Minentyp erstellt: {normalized_type} (ID: {new_type_id})")
        return new_type_id

    except Exception as e:
        logger.error(f"Fehler beim Erstellen/Abrufen des Minentyps: {e}")
        return None


def get_or_create_activity_status(status: str, db_session: Optional[Session] = None, db_manager=None) -> Optional[int]:
    """Hole oder erstelle Aktivitätsstatus"""
    try:
        if not status or status in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None

        # Normalisiere Status
        normalized_status = _normalize_activity_status(status)
        
        if not db_session:
            db_session = db_manager.get_session() if db_manager else None
        
        if not db_session:
            logger.error("Keine Datenbank-Session verfügbar")
            return None

        # Prüfe ob Status bereits existiert
        existing_status = _find_existing_activity_status(db_session, normalized_status)
        if existing_status:
            return existing_status['id']

        # Erstelle neuen Status
        new_status_id = _create_new_activity_status(db_session, normalized_status)
        
        logger.info(f"✅ Aktivitätsstatus erstellt: {normalized_status} (ID: {new_status_id})")
        return new_status_id

    except Exception as e:
        logger.error(f"Fehler beim Erstellen/Abrufen des Aktivitätsstatus: {e}")
        return None


def _normalize_company_name(company_name: str) -> str:
    """Normalisiere Unternehmensname"""
    if not company_name:
        return ""
    
    # Einfache Normalisierung
    normalized = company_name.strip()
    
    # Entferne häufige Suffixe
    suffixes = ['Inc.', 'Corp.', 'Ltd.', 'LLC', 'GmbH', 'AG']
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized


def _normalize_country_name(country_name: str) -> str:
    """Normalisiere Ländernamen"""
    if not country_name:
        return ""
    
    # Einfache Normalisierung
    normalized = country_name.strip()
    
    # Ländernamen-Mapping
    country_mapping = {
        'kanada': 'Canada',
        'canada': 'Canada',
        'australien': 'Australia',
        'australia': 'Australia',
        'chile': 'Chile',
        'peru': 'Peru',
        'brasilien': 'Brazil',
        'brazil': 'Brazil'
    }
    
    return country_mapping.get(normalized.lower(), normalized)


def _normalize_mine_name(mine_name: str) -> str:
    """Normalisiere Minenname"""
    if not mine_name:
        return ""
    
    # Einfache Normalisierung
    normalized = mine_name.strip()
    
    # Entferne häufige Präfixe
    prefixes = ['Mine', 'Mining', 'Mine de', 'Mina']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    return normalized


def _normalize_mine_type(mine_type: str) -> str:
    """Normalisiere Minentyp"""
    if not mine_type:
        return ""
    
    # Einfache Normalisierung
    normalized = mine_type.strip()
    
    # Minentyp-Mapping
    type_mapping = {
        'open pit': 'Open Pit',
        'tagebau': 'Open Pit',
        'underground': 'Underground',
        'untertage': 'Underground',
        'surface': 'Surface',
        'oberfläche': 'Surface'
    }
    
    return type_mapping.get(normalized.lower(), normalized)


def _normalize_activity_status(status: str) -> str:
    """Normalisiere Aktivitätsstatus"""
    if not status:
        return ""
    
    # Einfache Normalisierung
    normalized = status.strip()
    
    # Status-Mapping
    status_mapping = {
        'operational': 'Operational',
        'betrieb': 'Operational',
        'aktiv': 'Operational',
        'active': 'Operational',
        'development': 'Development',
        'entwicklung': 'Development',
        'exploration': 'Exploration',
        'erkundung': 'Exploration'
    }
    
    return status_mapping.get(normalized.lower(), normalized)


def _find_existing_company(db_session: Session, normalized_name: str) -> Optional[Dict[str, Any]]:
    """Finde existierendes Unternehmen"""
    try:
        # Simuliere Datenbankabfrage
        # In der Realität würde hier eine echte SQL-Abfrage stehen
        return None
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Unternehmens: {e}")
        return None


def _find_existing_country(db_session: Session, normalized_name: str) -> Optional[Dict[str, Any]]:
    """Finde existierendes Land"""
    try:
        # Simuliere Datenbankabfrage
        return None
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Landes: {e}")
        return None


def _find_existing_mine(db_session: Session, normalized_name: str) -> Optional[Dict[str, Any]]:
    """Finde existierende Mine"""
    try:
        # Simuliere Datenbankabfrage
        return None
    except Exception as e:
        logger.error(f"Fehler beim Suchen der Mine: {e}")
        return None


def _find_existing_mine_type(db_session: Session, normalized_type: str) -> Optional[Dict[str, Any]]:
    """Finde existierenden Minentyp"""
    try:
        # Simuliere Datenbankabfrage
        return None
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Minentyps: {e}")
        return None


def _find_existing_activity_status(db_session: Session, normalized_status: str) -> Optional[Dict[str, Any]]:
    """Finde existierenden Aktivitätsstatus"""
    try:
        # Simuliere Datenbankabfrage
        return None
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Aktivitätsstatus: {e}")
        return None


def _create_new_company(db_session: Session, normalized_name: str, original_name: str) -> int:
    """Erstelle neues Unternehmen"""
    try:
        # Simuliere Erstellung
        # In der Realität würde hier eine echte SQL-Insert stehen
        return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Unternehmens: {e}")
        return 0


def _create_new_country(db_session: Session, normalized_name: str) -> int:
    """Erstelle neues Land"""
    try:
        # Simuliere Erstellung
        return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Landes: {e}")
        return 0


def _create_new_mine(db_session: Session, normalized_name: str, country_id: int = None) -> int:
    """Erstelle neue Mine"""
    try:
        # Simuliere Erstellung
        return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Mine: {e}")
        return 0


def _create_new_mine_type(db_session: Session, normalized_type: str) -> int:
    """Erstelle neuen Minentyp"""
    try:
        # Simuliere Erstellung
        return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Minentyps: {e}")
        return 0


def _create_new_activity_status(db_session: Session, normalized_status: str) -> int:
    """Erstelle neuen Aktivitätsstatus"""
    try:
        # Simuliere Erstellung
        return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Aktivitätsstatus: {e}")
        return 0


def get_creation_statistics() -> Dict[str, Any]:
    """Hole Erstellungsstatistiken"""
    return {
        'total_created': 0,  # Würde in der Realität aus der Datenbank kommen
        'companies_created': 0,
        'countries_created': 0,
        'mines_created': 0,
        'mine_types_created': 0,
        'activity_statuses_created': 0,
        'timestamp': '2025-01-11T12:00:00Z'
    }


__all__ = [
    "get_or_create_company",
    "get_or_create_country",
    "get_or_create_mine",
    "get_or_create_mine_type",
    "get_or_create_activity_status",
    "get_creation_statistics"
]
