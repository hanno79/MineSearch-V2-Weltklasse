"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Migration von JSON Source Registry zu SQLite Datenbank
"""

import json
import os
import logging
from datetime import datetime
from database import db_manager, Source
from models import SourceRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_json_to_db():
    """Migriere bestehende Source Registry von JSON zu SQLite"""
    
    # Pfad zur JSON-Datei
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'source_registry.json')
    
    if not os.path.exists(json_path):
        logger.info("Keine bestehende source_registry.json gefunden - nichts zu migrieren")
        return
    
    # Lade JSON-Daten
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sources_data = data.get('sources', {})
    sessions_data = data.get('sessions', {})
    
    # Zähler für Statistik
    migrated_count = 0
    skipped_count = 0
    
    # Migriere Quellen
    for url, source_data in sources_data.items():
        try:
            # Konvertiere Timestamps
            last_successful = None
            if source_data.get('last_successful_access'):
                last_successful = datetime.fromisoformat(source_data['last_successful_access'])
            
            last_attempted = None
            if source_data.get('last_attempted_access'):
                last_attempted = datetime.fromisoformat(source_data['last_attempted_access'])
            
            # Erstelle oder aktualisiere Quelle
            source = db_manager.add_or_update_source(
                url=url,
                domain=source_data.get('domain', ''),
                country=source_data.get('country'),
                region=source_data.get('region'),
                source_type=source_data.get('source_type', 'unknown'),
                metadata=source_data.get('metadata', {})
            )
            
            # Aktualisiere Statistiken
            with db_manager.get_session() as session:
                db_source = session.query(Source).filter_by(url=url).first()
                if db_source:
                    db_source.reliability_score = source_data.get('reliability_score', 50.0)
                    db_source.last_successful_access = last_successful
                    db_source.last_attempted_access = last_attempted
                    db_source.total_searches = source_data.get('total_searches', 0)
                    db_source.successful_searches = source_data.get('successful_searches', 0)
                    db_source.typical_content_types = source_data.get('typical_content_types', [])
                    session.commit()
            
            migrated_count += 1
            logger.info(f"Migriert: {url}")
            
        except Exception as e:
            logger.error(f"Fehler beim Migrieren von {url}: {str(e)}")
            skipped_count += 1
    
    # Extrahiere Quellen aus Sessions
    session_sources_count = 0
    for session_id, session_data in sessions_data.items():
        sources = session_data.get('sources', {})
        successful_sources = sources.get('successful', [])
        
        for source_info in successful_sources:
            url = source_info.get('url')
            if url:
                try:
                    # Extrahiere Domain aus URL
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    
                    # Füge Quelle hinzu wenn noch nicht vorhanden
                    source = db_manager.add_or_update_source(
                        url=url,
                        domain=domain,
                        country=session_data.get('country'),
                        region=session_data.get('region'),
                        source_type='unknown'  # Typ kann später bestimmt werden
                    )
                    session_sources_count += 1
                    
                except Exception as e:
                    logger.error(f"Fehler beim Extrahieren von Session-Quelle {url}: {str(e)}")
    
    logger.info(f"""
    Migration abgeschlossen:
    - {migrated_count} Quellen aus Registry migriert
    - {session_sources_count} Quellen aus Sessions extrahiert
    - {skipped_count} Quellen übersprungen (Fehler)
    """)
    
    # Erstelle Backup der JSON-Datei
    backup_path = json_path + '.backup'
    os.rename(json_path, backup_path)
    logger.info(f"JSON-Datei gesichert als: {backup_path}")
    
    # Zeige Statistiken
    stats = db_manager.get_statistics()
    logger.info(f"Datenbank-Statistiken: {stats['total_sources']} Quellen gesamt")


if __name__ == "__main__":
    migrate_json_to_db()