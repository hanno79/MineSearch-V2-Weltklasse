"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Konsolidiert doppelte Quellen in der Datenbank
"""

import logging
from database import db_manager, Source
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_url(url: str) -> tuple[str, str]:
    """
    Normalisiert eine URL für Vergleiche
    Returns: (base_url_without_query, domain)
    """
    if url.startswith('search:'):
        # Spezialbehandlung für Document-Search Muster
        return ('document_search', 'document_search')
    
    try:
        parsed = urlparse(url)
        # Basis-URL ohne Query-Parameter
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
        domain = parsed.netloc
        return (base_url, domain)
    except:
        return (url, '')

def consolidate_sources():
    """
    Konsolidiert doppelte Quellen basierend auf Domain
    """
    logger.info("=== Starte Quellen-Konsolidierung ===")
    
    with db_manager.get_session() as session:
        # Hole alle Quellen
        all_sources = session.query(Source).all()
        logger.info(f"Gefunden: {len(all_sources)} Quellen gesamt")
        
        # Gruppiere nach Domain
        domain_groups = defaultdict(list)
        for source in all_sources:
            _, domain = normalize_url(source.url)
            if domain:  # Ignoriere leere Domains
                domain_groups[domain].append(source)
        
        logger.info(f"Gefunden: {len(domain_groups)} unique Domains")
        
        # Statistiken
        consolidated_count = 0
        deleted_count = 0
        
        # Konsolidiere jede Domain-Gruppe
        for domain, sources in domain_groups.items():
            if len(sources) <= 1:
                continue  # Keine Duplikate
            
            logger.info(f"\nKonsolidiere {domain} ({len(sources)} Einträge):")
            
            # Sortiere nach ID (älteste zuerst)
            sources.sort(key=lambda x: x.id)
            
            # Behalte den ersten Eintrag als Master
            master = sources[0]
            
            # Kombiniere Statistiken von allen Duplikaten
            total_searches = master.total_searches
            successful_searches = master.successful_searches
            
            # Sammle beste Metadaten
            best_country = master.country
            best_region = master.region
            best_type = master.source_type
            latest_success = master.last_successful_access
            latest_attempt = master.last_attempted_access
            all_content_types = set(master.typical_content_types or [])
            
            for duplicate in sources[1:]:
                # Addiere Statistiken
                total_searches += duplicate.total_searches
                successful_searches += duplicate.successful_searches
                
                # Behalte beste Metadaten
                if duplicate.country and not best_country:
                    best_country = duplicate.country
                if duplicate.region and not best_region:
                    best_region = duplicate.region
                if duplicate.source_type != 'unknown' and best_type == 'unknown':
                    best_type = duplicate.source_type
                
                # Aktualisiere Zeitstempel
                if duplicate.last_successful_access:
                    if not latest_success or duplicate.last_successful_access > latest_success:
                        latest_success = duplicate.last_successful_access
                if duplicate.last_attempted_access:
                    if not latest_attempt or duplicate.last_attempted_access > latest_attempt:
                        latest_attempt = duplicate.last_attempted_access
                
                # Sammle Content-Types
                if duplicate.typical_content_types:
                    all_content_types.update(duplicate.typical_content_types)
                
                logger.info(f"  - Lösche ID {duplicate.id}: {duplicate.total_searches} Suchen")
                session.delete(duplicate)
                deleted_count += 1
            
            # Aktualisiere Master mit kombinierten Daten
            master.total_searches = total_searches
            master.successful_searches = successful_searches
            master.country = best_country
            master.region = best_region
            master.source_type = best_type
            master.last_successful_access = latest_success
            master.last_attempted_access = latest_attempt
            master.typical_content_types = list(all_content_types) if all_content_types else []
            
            # Normalisiere URL (entferne Query-Parameter)
            base_url, _ = normalize_url(master.url)
            if not base_url.startswith('search:'):
                master.url = base_url
            
            # Neuberechnung des Scores
            master.reliability_score = master.calculate_reliability_score()
            
            logger.info(f"  → Master ID {master.id}: {master.total_searches} Suchen total, Score: {master.reliability_score:.0f}%")
            consolidated_count += 1
        
        # Commit aller Änderungen
        session.commit()
        
        # Finale Statistiken
        remaining_sources = session.query(Source).count()
        logger.info(f"\n=== Konsolidierung abgeschlossen ===")
        logger.info(f"Konsolidiert: {consolidated_count} Domain-Gruppen")
        logger.info(f"Gelöscht: {deleted_count} Duplikate")
        logger.info(f"Verbleibende Quellen: {remaining_sources}")
        
        # Zeige Top 10 nach Konsolidierung
        top_sources = session.query(Source).order_by(Source.reliability_score.desc()).limit(10).all()
        logger.info("\nTop 10 Quellen nach Konsolidierung:")
        for i, source in enumerate(top_sources, 1):
            logger.info(f"  {i}. {source.domain} - Score: {source.reliability_score:.0f}%, "
                      f"Erfolg: {source.successful_searches}/{source.total_searches}")

if __name__ == "__main__":
    consolidate_sources()