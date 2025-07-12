#!/usr/bin/env python3
"""
Author: rahn
Datum: 08.07.2025
Version: 1.0
Beschreibung: Bereinigung der Quellen-Datenbank - Entfernt Duplikate und korrigiert Inkonsistenzen
"""

import logging
from sqlalchemy import func, and_
from database import db_manager, Source
from urllib.parse import urlparse
import re

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ÄNDERUNG 08.07.2025: Domain-zu-Land Mapping
DOMAIN_COUNTRY_MAP = {
    # Kanada
    '.ca': 'Canada',
    '.gc.ca': 'Canada',
    '.qc.ca': 'Canada',
    '.gouv.qc.ca': 'Canada',
    'canadianmalartic.com': 'Canada',
    'agnicoeagle.com': 'Canada',
    'searchminerals.ca': 'Canada',
    'glencore.ca': 'Canada',
    
    # USA
    '.gov': 'USA',
    'blm.gov': 'USA',
    'usgs.gov': 'USA',
    
    # Australien
    '.gov.au': 'Australia',
    '.com.au': 'Australia',
    
    # Südafrika
    '.gov.za': 'South Africa',
    '.co.za': 'South Africa',
}

# ÄNDERUNG 08.07.2025: Erweiterte Source-Type Patterns
SOURCE_TYPE_PATTERNS = {
    'government': [
        r'\.gov(\.|$)',
        r'\.gouv\.',
        r'mern\.gouv',
        r'mrnf\.gouv',
        r'mines\.gouv',
        r'bape\.gouv',
        r'gestim.*gouv',
        r'nrcan\.gc\.ca',
        r'blm\.gov',
        r'usgs\.gov'
    ],
    'database': [
        r'mindat\.org',
        r'miningdataonline\.com',
        r'minfind\.com',
        r'gestim.*mines',  # GESTIM ist eine Datenbank
        r'geonames\.nrcan'
    ],
    'exchange': [
        r'sedar\.com',
        r'tsx\.com',
        r'asx\.com\.au',
        r'jse\.co\.za'
    ],
    'industry': [
        r'mining\.com$',
        r'miningweekly\.com',
        r'mining-technology\.com',
        r'miningwatch\.ca',
        r'northernminer\.com',
        r'miningfrontier\.com',
        r'resourceworld\.com'
    ],
    'document': [
        r'\.pdf$',
        r'/GM\d+/',  # Quebec mining documents
        r'/DV\d+/',  # Quebec mining documents
        r'q4cdn\.com',
        r'kaisersearch\.com'
    ],
    'media': [
        r'youtube\.com',
        r'vimeo\.com',
        r'accessnewswire\.com'
    ],
    'wikipedia': [
        r'wikipedia\.org'
    ]
}

def classify_source_type_enhanced(url: str) -> str:
    """Verbesserte Source-Type Klassifizierung"""
    url_lower = url.lower()
    
    # Prüfe alle Patterns
    for source_type, patterns in SOURCE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return source_type
    
    # Default
    return 'unknown'

def get_country_from_domain(url: str) -> str:
    """Ermittle Land basierend auf Domain"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Prüfe spezifische Domains zuerst
        for domain_pattern, country in DOMAIN_COUNTRY_MAP.items():
            if domain_pattern in domain:
                return country
        
        # Prüfe TLD
        if domain.endswith('.ca'):
            return 'Canada'
        elif domain.endswith('.us'):
            return 'USA'
        elif domain.endswith('.au'):
            return 'Australia'
        elif domain.endswith('.za'):
            return 'South Africa'
        elif domain.endswith('.cl'):
            return 'Chile'
        elif domain.endswith('.pe'):
            return 'Peru'
        elif domain.endswith('.mx'):
            return 'Mexico'
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Could not parse domain from URL {url}: {e}")
        pass
    
    return None

def cleanup_sources():
    """Hauptfunktion für Datenbank-Bereinigung"""
    
    with db_manager.get_session() as session:
        # 1. Statistiken vor Bereinigung
        total_before = session.query(Source).count()
        logger.info(f"Quellen vor Bereinigung: {total_before}")
        
        # 2. Standardisiere Ländernamen
        logger.info("\n=== Standardisiere Ländernamen ===")
        
        # Kanada → Canada
        updated = session.query(Source).filter(Source.country == 'Kanada').update({'country': 'Canada'})
        logger.info(f"Kanada → Canada: {updated} Einträge aktualisiert")
        
        # Weitere Standardisierungen
        country_mappings = {
            'United States': 'USA',
            'Vereinigte Staaten': 'USA',
            'Australien': 'Australia',
            'Südafrika': 'South Africa',
            'Süd-Afrika': 'South Africa',
            'Brasilien': 'Brazil',
            'Chile': 'Chile',
            'Mexiko': 'Mexico'
        }
        
        for old_name, new_name in country_mappings.items():
            updated = session.query(Source).filter(Source.country == old_name).update({'country': new_name})
            if updated > 0:
                logger.info(f"{old_name} → {new_name}: {updated} Einträge aktualisiert")
        
        session.commit()
        
        # 3. Korrigiere source_type
        logger.info("\n=== Korrigiere Source Types ===")
        
        sources_to_fix = session.query(Source).filter(Source.source_type == 'url').all()
        logger.info(f"Zu korrigierende 'url' Einträge: {len(sources_to_fix)}")
        
        type_updates = {}
        for source in sources_to_fix:
            new_type = classify_source_type_enhanced(source.url)
            if new_type != 'unknown':
                source.source_type = new_type
                if new_type not in type_updates:
                    type_updates[new_type] = 0
                type_updates[new_type] += 1
        
        session.commit()
        
        for source_type, count in type_updates.items():
            logger.info(f"url → {source_type}: {count} Einträge")
        
        # 4. Füge fehlende Länder hinzu
        logger.info("\n=== Füge fehlende Länder hinzu ===")
        
        sources_without_country = session.query(Source).filter(
            (Source.country == None) | (Source.country == '')
        ).all()
        logger.info(f"Quellen ohne Land: {len(sources_without_country)}")
        
        country_additions = {}
        for source in sources_without_country:
            country = get_country_from_domain(source.url)
            if country:
                source.country = country
                if country not in country_additions:
                    country_additions[country] = 0
                country_additions[country] += 1
        
        session.commit()
        
        for country, count in country_additions.items():
            logger.info(f"Land hinzugefügt - {country}: {count} Einträge")
        
        # 5. Entferne echte Duplikate (exakt gleiche URL)
        logger.info("\n=== Entferne echte Duplikate ===")
        
        # ÄNDERUNG 09.07.2025: Nutze die neue cleanup_duplicate_sources Methode
        session.commit()  # Commit bisherige Änderungen
        
        # Nutze die verbesserte Methode aus db_manager
        removed_count = db_manager.cleanup_duplicate_sources()
        logger.info(f"Duplikate entfernt: {removed_count}")
        
        # 6. Finale Statistiken
        logger.info("\n=== Finale Statistiken ===")
        
        total_after = session.query(Source).count()
        logger.info(f"Quellen nach Bereinigung: {total_after}")
        logger.info(f"Differenz: {total_before - total_after} entfernt")
        
        # Type-Verteilung
        type_stats = session.query(
            Source.source_type,
            func.count(Source.id)
        ).group_by(Source.source_type).all()
        
        logger.info("\nSource-Type Verteilung:")
        for source_type, count in sorted(type_stats, key=lambda x: x[1], reverse=True):
            percentage = (count / total_after) * 100
            logger.info(f"  {source_type}: {count} ({percentage:.1f}%)")
        
        # Länder-Verteilung
        country_stats = session.query(
            Source.country,
            func.count(Source.id)
        ).group_by(Source.country).all()
        
        logger.info("\nLänder-Verteilung:")
        for country, count in sorted(country_stats, key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / total_after) * 100
            country_name = country if country else "Kein Land"
            logger.info(f"  {country_name}: {count} ({percentage:.1f}%)")

def show_domain_statistics():
    """Zeige Statistiken gruppiert nach Domain"""
    logger.info("\n=== Domain-Statistiken ===")
    
    with db_manager.get_session() as session:
        sources = session.query(Source).all()
        
        domain_stats = {}
        for source in sources:
            try:
                parsed = urlparse(source.url)
                domain = parsed.netloc
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        'count': 0,
                        'types': set(),
                        'countries': set()
                    }
                domain_stats[domain]['count'] += 1
                domain_stats[domain]['types'].add(source.source_type)
                if source.country:
                    domain_stats[domain]['countries'].add(source.country)
            except:
                continue
        
        # Top 20 Domains
        sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
        
        logger.info("\nTop 20 Domains:")
        for domain, stats in sorted_domains:
            types = ', '.join(stats['types'])
            countries = ', '.join(stats['countries']) if stats['countries'] else 'Kein Land'
            logger.info(f"  {domain}: {stats['count']} URLs | Types: {types} | Länder: {countries}")

if __name__ == "__main__":
    logger.info("=== Starte Quellen-Bereinigung ===")
    
    # Backup-Hinweis
    logger.info("\n⚠️  WICHTIG: Stelle sicher, dass ein Backup der Datenbank existiert!")
    
    try:
        cleanup_sources()
        show_domain_statistics()
        logger.info("\n✅ Bereinigung erfolgreich abgeschlossen!")
    except Exception as e:
        logger.error(f"❌ Fehler bei Bereinigung: {str(e)}")
        raise