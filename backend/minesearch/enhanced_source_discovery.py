"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Erweiterte Source Discovery mit Active Discovery für MineSearch v2
"""

# ÄNDERUNG 01.07.2025: Neue Datei für erweiterte Quellensuche

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import urllib.parse
import asyncio
import time
from collections.abc import Iterable

from minesearch.config import config, Config, COUNTRY_CONFIG
from minesearch.source_discovery import SourceDiscovery
from minesearch.models import SearchSession
import uuid
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class EnhancedSourceDiscovery(SourceDiscovery):
    """Erweiterte Quellensuche mit Active Discovery"""
    
    def __init__(self):
        super().__init__()
        self.session: Optional[SearchSession] = None
    
    def start_session(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> 'SearchSession':
        """Starte neue Such-Session"""
        # ÄNDERUNG 04.07.2025: Verwende SearchSession aus models.py mit korrekter Initialisierung
        import uuid
        self.session = SearchSession(
            session_id=str(uuid.uuid4()),
            mine_name=mine_name,
            country=country,
            region=region
        )
        logger.info(f"[SOURCE DISCOVERY] Session {self.session.session_id} gestartet für {mine_name}")
        return self.session
    
    def discover_sources_for_mine(self, mine_name: str, country: Optional[str] = None, 
                                 region: Optional[str] = None, commodity: Optional[str] = None,
                                 priority_focus: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aktive Quellensuche für eine Mine
        
        Returns:
            Liste von potentiellen Quellen mit Metadaten
        """
        logger.info(f"[ACTIVE DISCOVERY] Starte für {mine_name} in {country}/{region}")
        
        discovered_sources = []
        
        # 1. Länderspezifische Priority Domains
        if country:
            country_sources = self._get_country_specific_sources(mine_name, country, region)
            discovered_sources.extend(country_sources)
            logger.info(f"[ACTIVE DISCOVERY] {len(country_sources)} länderspezifische Quellen gefunden")
        
        # 2. Globale Mining-Datenbanken (Tier 1)
        global_sources = self._get_global_mining_sources(mine_name)
        discovered_sources.extend(global_sources)
        logger.info(f"[ACTIVE DISCOVERY] {len(global_sources)} globale Quellen gefunden")
        
        # 3. Börsen und Finanzdokumente (Tier 2)
        if country:
            exchange_sources = self._get_exchange_sources(mine_name, country)
            discovered_sources.extend(exchange_sources)
            logger.info(f"[ACTIVE DISCOVERY] {len(exchange_sources)} Börsenquellen gefunden")
        
        # 4. Technische Dokumente (PDFs)
        pdf_sources = self._search_technical_documents(mine_name, country)
        discovered_sources.extend(pdf_sources)
        logger.info(f"[ACTIVE DISCOVERY] {len(pdf_sources)} technische Dokumente gefunden")
        
        # 5. ÄNDERUNG 02.07.2025: Bekannte erfolgreiche Quellen aus Datenbank
        db_sources = self._get_database_sources(mine_name, country, region)
        discovered_sources.extend(db_sources)
        logger.info(f"[ACTIVE DISCOVERY] {len(db_sources)} Quellen aus Datenbank")
        
        # Deduplizierung
        unique_sources = self._deduplicate_sources(discovered_sources)
        
        # Tracking in Session
        if self.session:
            for source in unique_sources:
                self.session.add_discovered_source(source['url'])
        
        # ÄNDERUNG 25.08.2025: Persistiere neue Quellen in Datenbank
        # Fehlerbehandlung mit begrenztem Retry, damit Aufrufer bei Persistenzfehlern informiert werden
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                self._persist_discovered_sources(unique_sources, mine_name, country, region)
                break
            except Exception as e:
                logger.error(
                    f"[ACTIVE DISCOVERY][PERSIST-ERROR] Versuch {attempt}/{max_attempts} fehlgeschlagen "
                    f"für Mine='{mine_name}', Country='{country}', Region='{region}': {e}"
                )
                if attempt == max_attempts:
                    # Letzter Versuch fehlgeschlagen → nach oben propagieren, damit Caller es erkennt
                    raise
                # kurzer Backoff vor erneutem Versuch
                time.sleep(1 * attempt)
        
        logger.info(f"[ACTIVE DISCOVERY] Gesamt: {len(unique_sources)} unique Quellen entdeckt")
        
        return unique_sources
    
    def _persist_discovered_sources(self, sources: List[Dict[str, Any]], mine_name: str, 
                                   country: Optional[str], region: Optional[str]) -> None:
        """
        Persistiere neu entdeckte Quellen in der Datenbank
        
        ÄNDERUNG 25.08.2025: Automatische Persistierung für bessere Quellenabdeckung
        """
        from minesearch.database import db_manager
        from sqlalchemy import text
        
        persisted_count = 0
        
        for source in sources:
            try:
                # Prüfe ob Quelle bereits existiert
                with db_manager.get_session() as session:
                    existing = session.execute(
                        text("SELECT id FROM sources WHERE url = :url"),
                        {"url": source['url']}
                    ).fetchone()
                    
                    if not existing:
                        # Neue Quelle hinzufügen
                        db_manager.add_or_update_source(
                            url=source['url'],
                            domain=source['domain'],
                            country=country,
                            region=region,
                            source_type=source['type'],
                            metadata={
                                'discovered_for': mine_name,
                                'discovery_method': 'enhanced_source_discovery',
                                'priority': source.get('priority', 3),
                                'description': source.get('description', ''),
                                'auto_discovered': True
                            }
                        )
                        persisted_count += 1
                        
            except Exception as e:
                logger.warning(f"[SOURCE PERSIST] Fehler beim Speichern von {source['url']}: {e}")
        
        if persisted_count > 0:
            logger.info(f"[SOURCE PERSIST] {persisted_count} neue Quellen in Datenbank gespeichert")
        else:
            logger.debug(f"[SOURCE PERSIST] Keine neuen Quellen zu speichern")
    
    def _get_country_specific_sources(self, mine_name: str, country: str, region: Optional[str]) -> List[Dict[str, Any]]:
        """Hole länderspezifische Quellen"""
        sources = []
        
        # Hole Länderkonfiguration
        country_config = COUNTRY_CONFIG.get(country.lower(), {})
        priority_domains = country_config.get('priority_domains', [])
        
        # ÄNDERUNG 06.07.2025: Erweiterte GESTIM-Integration für Restaurationskosten
        # Spezialbehandlung für Quebec/GESTIM
        if country.lower() in ['kanada', 'canada'] and region and 'quebec' in region.lower():
            sources.append({
                'url': f"https://gestim.mines.gouv.qc.ca/MRN_GestimP_Presentation/ODM02201_menu_base.aspx",
                'domain': 'gestim.mines.gouv.qc.ca',
                'type': 'database',
                'priority': 1,
                'description': 'GESTIM - Quebec Mining Registry (Konzessionen & Umweltauflagen)',
                'search_hint': f"Suche nach: {mine_name} - Fokus auf Umweltgarantien",
                'api_available': True,  # Markiere dass API verfügbar ist
                'restoration_focus': True  # Markierung für Restaurationskosten-Fokus
            })
            
            # Zusätzliche GESTIM-spezifische Suche für Restaurationskosten
            sources.append({
                'url': f"search:'{mine_name}' GESTIM environmental guarantee filetype:pdf",
                'domain': 'gestim.mines.gouv.qc.ca',
                'type': 'document',
                'priority': 1,
                'description': 'GESTIM Umweltgarantien und Sicherheitsleistungen',
                'search_pattern': f"'{mine_name}' GESTIM environmental guarantee filetype:pdf"
            })
        
        # Andere Priority Domains - GENERIERE SPEZIFISCHE URLS statt generische /search URLs
        for domain in priority_domains:
            if 'gestim' not in domain:  # GESTIM bereits hinzugefügt
                # Generiere verschiedene spezifische URLs für bessere Datenqualität
                specific_searches = self._generate_specific_search_urls(mine_name, domain)
                if specific_searches is None:
                    logger.debug(f"[ACTIVE DISCOVERY] _generate_specific_search_urls gab None zurück für Domain {domain}; überspringe Erweiterung")
                    continue
                if isinstance(specific_searches, Iterable) and not isinstance(specific_searches, (str, bytes, dict)):
                    specific_list = list(specific_searches)
                    if len(specific_list) == 0:
                        logger.debug(f"[ACTIVE DISCOVERY] _generate_specific_search_urls gab eine leere Liste/Iterable zurück für Domain {domain}; nichts zu erweitern")
                        continue
                    sources.extend(specific_list)
                else:
                    logger.warning(
                        f"[ACTIVE DISCOVERY] Ungültiger Rückgabewert von _generate_specific_search_urls für Domain {domain}: Typ {type(specific_searches).__name__}; erwarte Liste/Iterable"
                    )
        
        return sources
    
    def _generate_specific_search_urls(self, mine_name: str, domain: str) -> List[Dict[str, Any]]:
        """
        Generiere spezifische URLs für bessere Suchergebnisse statt generischer /search URLs
        """
        sources = []
        mine_quoted = urllib.parse.quote(mine_name)
        
        # Domain-spezifische URL-Generierung
        if 'mern.gouv.qc.ca' in domain:
            # Quebec Mining Ministry - spezifische Bereiche
            sources.extend([
                {
                    'url': f"https://mern.gouv.qc.ca/mines/publications-mines-hydrocarbures/{mine_quoted}",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"Quebec Mining Publications: {mine_name}"
                },
                {
                    'url': f"https://mern.gouv.qc.ca/mines/environnement/{mine_quoted}-restoration",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"Quebec Environmental Restoration Data: {mine_name}"
                }
            ])
        elif 'nrcan.gc.ca' in domain:
            # Natural Resources Canada - spezifische Sektionen
            sources.extend([
                {
                    'url': f"https://nrcan.gc.ca/mining-materials/publications/{mine_quoted}",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"NRCan Mining Publications: {mine_name}"
                },
                {
                    'url': f"https://nrcan.gc.ca/mining-materials/markets/{mine_quoted}-data",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"NRCan Mining Market Data: {mine_name}"
                }
            ])
        elif 'usgs.gov' in domain:
            # USGS - Mining Resource Data System
            sources.extend([
                {
                    'url': f"https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id={mine_quoted}",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"USGS MRDS Database: {mine_name}"
                },
                {
                    'url': f"https://pubs.usgs.gov/search?q={mine_quoted}+mining+report",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"USGS Mining Reports: {mine_name}"
                }
            ])
        elif 'sedar.com' in domain:
            # SEDAR - spezifische Dokumenttypen
            sources.extend([
                {
                    'url': f"https://sedar.com/search/search_form_pc.htm?search={mine_quoted}",
                    'domain': domain,
                    'type': 'exchange',
                    'priority': 2,
                    'description': f"SEDAR Financial Documents: {mine_name}"
                }
            ])
        else:
            # Fallback für andere Domains - aber immer noch spezifischer als nur /search
            sources.append({
                'url': f"https://{domain}/{mine_quoted}-mining-data",
                'domain': domain,
                'type': self._classify_domain(domain),
                'priority': 2,
                'description': f"Specialized search: {domain} - {mine_name}"
            })
        
        return sources
    
    async def search_with_apis(self, mine_name: str, country: Optional[str], 
                              region: Optional[str]) -> Dict[str, Any]:
        """
        Durchsucht verfügbare APIs für Mining-Daten
        
        Returns:
            Dict mit API-Suchergebnissen
        """
        api_results = {}
        
        # GESTIM für Quebec
        if country and country.lower() in ['kanada', 'canada'] and region and 'quebec' in region.lower():
            from gestim_connector import gestim_connector
            logger.info(f"[API SEARCH] Suche in GESTIM für {mine_name}")
            
            gestim_result = await gestim_connector.search_mine(mine_name)
            if gestim_result['success']:
                api_results['gestim'] = gestim_result['data']
                
                # Hole zusätzliche Restaurationsdaten wenn Mining Titles vorhanden
                if 'mining_titles' in gestim_result['data']:
                    restoration_data = await gestim_connector.get_restoration_obligations(
                        gestim_result['data']['mining_titles']
                    )
                    api_results['gestim']['restoration_obligations'] = restoration_data
        
        # Weitere APIs können hier hinzugefügt werden
        # z.B. BLM für USA, SARIG für Australien, etc.
        
        return api_results
    
    def _get_global_mining_sources(self, mine_name: str) -> List[Dict[str, Any]]:
        """Hole globale Mining-Quellen"""
        sources = []
        
        # Tier 1 Domains - SPEZIFISCHE URLs statt generische /search
        for domain in Config.PRIORITY_MINING_DOMAINS.get('tier1', []):
            specific_sources = self._generate_specific_search_urls(mine_name, domain)
            if specific_sources:
                sources.extend(specific_sources)
            else:
                # Fallback nur wenn keine spezifischen URLs generiert werden konnten
                sources.append({
                    'url': f"https://{domain}/mining-database/{urllib.parse.quote(mine_name)}",
                    'domain': domain,
                    'type': 'government',
                    'priority': 1,
                    'description': f"Government Mining Database: {domain}"
                })
        
        return sources
    
    def _get_exchange_sources(self, mine_name: str, country: str) -> List[Dict[str, Any]]:
        """Hole Börsenquellen"""
        sources = []
        
        # Land-zu-Börse Mapping
        country_exchanges = {
            'kanada': ['sedar.com', 'tsx.com'],
            'canada': ['sedar.com', 'tsx.com'],
            'usa': ['sec.gov'],
            'australien': ['asx.com.au'],
            'australia': ['asx.com.au'],
            'südafrika': ['jse.co.za'],
            'south africa': ['jse.co.za'],
            'chile': ['bolsadesantiago.com'],
            'peru': ['bvl.com.pe'],
            'indonesien': ['idx.co.id'],
            'indonesia': ['idx.co.id']
        }
        
        exchanges = country_exchanges.get(country.lower(), [])
        
        for exchange in exchanges:
            # ÄNDERUNG 25.08.2025: Spezifische URLs statt generic search
            specific_sources = self._generate_specific_exchange_urls(mine_name, exchange)
            sources.extend(specific_sources)
        
        return sources
    
    def _generate_specific_exchange_urls(self, mine_name: str, exchange: str) -> List[Dict[str, Any]]:
        """Generiere spezifische Exchange-URLs für verschiedene Dokumenttypen"""
        sources = []
        mine_encoded = urllib.parse.quote(mine_name)
        
        # Börsenspezifische URL-Pattern
        exchange_patterns = {
            'sedar.com': [
                f"https://sedar.com/companies/{mine_encoded.replace('%20', '-').lower()}-reports",
                f"https://sedar.com/filings/ni-43-101/{mine_encoded.replace('%20', '-').lower()}",
                f"https://sedar.com/annual-reports/{mine_encoded.replace('%20', '-').lower()}",
                f"https://sedar.com/financial-statements/{mine_encoded.replace('%20', '-').lower()}"
            ],
            'tsx.com': [
                f"https://tsx.com/listings/current-listings?symbol={mine_name.replace(' ', '')}",
                f"https://tsx.com/company-directory?search={urllib.parse.quote(mine_name)}"
            ],
            'sec.gov': [
                f"https://sec.gov/edgar/search/?q={urllib.parse.quote(mine_name)}+10-K",
                f"https://sec.gov/edgar/search/?q={urllib.parse.quote(mine_name)}+10-Q",
                f"https://sec.gov/edgar/search/?q={urllib.parse.quote(mine_name)}+8-K"
            ],
            'asx.com.au': [
                f"https://asx.com.au/markets/company/{mine_name.replace(' ', '').lower()}",
                f"https://asx.com.au/asxpdf/announcements/{mine_name.replace(' ', '')}"
            ]
        }
        
        urls = exchange_patterns.get(exchange, [
            f"https://{exchange}/search?q={urllib.parse.quote(mine_name)}+annual+report",
            f"https://{exchange}/search?q={urllib.parse.quote(mine_name)}+financial+statements"
        ])
        
        for url in urls:
            sources.append({
                'url': url,
                'domain': exchange,
                'type': 'exchange',
                'priority': 2,
                'description': f"Börsendokumente: {exchange} - {url.split('/')[-1]}"
            })
        
        return sources
    
    def _search_technical_documents(self, mine_name: str, country: Optional[str]) -> List[Dict[str, Any]]:
        """Suche nach technischen Dokumenten"""
        sources = []
        
        # ÄNDERUNG 25.08.2025: Spezifische URLs für technische Dokumente statt generic search
        specific_sources = self._generate_specific_document_urls(mine_name, country)
        sources.extend(specific_sources)
        
        return sources
    
    def _generate_specific_document_urls(self, mine_name: str, country: Optional[str]) -> List[Dict[str, Any]]:
        """Generiere spezifische URLs für verschiedene Dokumenttypen"""
        sources = []
        mine_encoded = urllib.parse.quote(mine_name)
        
        # Land-spezifische Dokumentquellen
        if country and country.lower() in ['kanada', 'canada']:
            # SEDAR - Kanadische Börsenregulierung
            sources.extend([
                {
                    'url': f"https://sedar.com/documents/ni-43-101/{mine_encoded.replace('%20', '-').lower()}-technical-report.pdf",
                    'domain': 'sedar.com',
                    'type': 'document',
                    'priority': 1,
                    'description': f"SEDAR NI 43-101 Technical Report: {mine_name}"
                },
                {
                    'url': f"https://sedar.com/documents/annual-info/{mine_encoded.replace('%20', '-').lower()}-aif.pdf",
                    'domain': 'sedar.com', 
                    'type': 'document',
                    'priority': 1,
                    'description': f"SEDAR Annual Information Form: {mine_name}"
                }
            ])
            
            # Natural Resources Canada
            sources.append({
                'url': f"https://nrcan.gc.ca/mining-materials/mining/{mine_encoded.replace('%20', '-').lower()}",
                'domain': 'nrcan.gc.ca',
                'type': 'document',
                'priority': 1,
                'description': f"Natural Resources Canada: {mine_name}"
            })
        
        elif country and country.lower() in ['usa', 'united states']:
            # SEC Edgar Database
            sources.extend([
                {
                    'url': f"https://sec.gov/edgar/search/?q={mine_encoded}+10-K+mining",
                    'domain': 'sec.gov',
                    'type': 'document',
                    'priority': 1,
                    'description': f"SEC 10-K Filing: {mine_name}"
                },
                {
                    'url': f"https://sec.gov/edgar/search/?q={mine_encoded}+environmental+compliance",
                    'domain': 'sec.gov',
                    'type': 'document', 
                    'priority': 1,
                    'description': f"SEC Environmental Reports: {mine_name}"
                }
            ])
        
        elif country and country.lower() in ['australien', 'australia']:
            # ASX Australian Securities Exchange
            sources.append({
                'url': f"https://asx.com.au/markets/research/announcements?q={mine_encoded}+mining+report",
                'domain': 'asx.com.au',
                'type': 'document',
                'priority': 1,
                'description': f"ASX Mining Reports: {mine_name}"
            })
        
        # Allgemeine akademische und industrielle Quellen
        sources.extend([
            {
                'url': f"https://pubmed.ncbi.nlm.nih.gov/?term={mine_encoded}+mining+environmental+impact",
                'domain': 'pubmed.ncbi.nlm.nih.gov',
                'type': 'document',
                'priority': 2,
                'description': f"PubMed Environmental Studies: {mine_name}"
            },
            {
                'url': f"https://scholar.google.com/scholar?q={mine_encoded}+mining+closure+rehabilitation",
                'domain': 'scholar.google.com',
                'type': 'document',
                'priority': 2,
                'description': f"Google Scholar Research: {mine_name}"
            },
            {
                'url': f"https://infomine.com/minesite/{mine_encoded.replace('%20', '-').lower()}",
                'domain': 'infomine.com',
                'type': 'document',
                'priority': 2,
                'description': f"InfoMine Database: {mine_name}"
            }
        ])
        
        return sources
    
    # ÄNDERUNG 02.07.2025: _get_registry_recommendations entfernt - verwende _get_database_sources
    
    def _get_database_sources(self, mine_name: str, country: Optional[str], 
                             region: Optional[str]) -> List[Dict[str, Any]]:
        """
        Hole zusätzliche Quellen aus der Datenbank
        
        ÄNDERUNG 02.07.2025: Nutze DB für bewährte Quellen
        """
        sources = []
        
        # Import hier um zirkuläre Imports zu vermeiden
        from minesearch.database import db_manager
        
        # Hole relevante Quellen aus DB
        # ÄNDERUNG 08.07.2025: Erweiterte Datenbank-Quellennutzung
        # Hole ALLE relevanten Quellen, nicht nur die mit hoher Zuverlässigkeit
        db_sources = db_manager.get_sources_for_search(
            country=country,
            region=region,
            min_reliability=10.0,  # Noch weiter gesenkt für maximale Abdeckung
            limit=100  # Erhöht auf 100 für umfassende Quellennutzung
        )
        
        logger.info(f"[SOURCE DISCOVERY] {len(db_sources)} existierende Quellen aus Datenbank geladen")
        
        for db_source in db_sources:
            sources.append({
                'url': db_source.url,
                'domain': db_source.domain,
                'type': db_source.source_type or 'unknown',
                'priority': 1 if db_source.reliability_score > 70 else 2,
                'description': f"DB-Quelle (Score: {db_source.reliability_score:.0f}%, Suchen: {db_source.total_searches})",
                'reliability_score': db_source.reliability_score,
                'from_database': True  # Markierung für Tracking
            })
        
        return sources
    
    def _classify_domain(self, domain: str) -> str:
        """Klassifiziere Domain-Typ"""
        if any(gov in domain for gov in ['.gov', '.gouv', '.gob', '.go.']):
            return 'government'
        elif any(exchange in domain for exchange in ['sedar', 'sec', 'asx', 'tsx', 'jse', 'bolsa', 'bvl', 'idx']):
            return 'exchange'
        elif any(mining in domain for mining in ['mining', 'mine', 'mineral', 'infomine']):
            return 'industry'
        else:
            return 'general'
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Entferne doppelte Quellen"""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        # Sortiere nach Priorität
        unique_sources.sort(key=lambda x: (x.get('priority', 3), -x.get('reliability_score', 0)))
        
        return unique_sources
    
    def track_source_result(self, url: str, success: bool, content_type: Optional[str] = None, 
                          found_data: Optional[Dict[str, Any]] = None):
        """Tracke Ergebnis einer Quellensuche"""
        if not self.session:
            return
        
        # Update Session
        self.session.add_searched_source(url, success, found_data)
        
        # ÄNDERUNG 02.07.2025: Verwende direkt die Datenbank
        from minesearch.database import db_manager
        
        # Parse Domain
        domain = urllib.parse.urlparse(url).netloc
        
        # Erstelle oder aktualisiere Quelle in DB
        source = db_manager.add_or_update_source(
            url=url,
            domain=domain,
            country=self.session.country,
            region=self.session.region,
            source_type='unknown',  # Wird automatisch klassifiziert in add_or_update_source
            metadata={
                'discovered_for': self.session.mine_name,
                'found_fields': found_data.get('fields', []) if found_data else []
            }
        )
        
        # Update Zugriffstatistiken
        db_manager.update_source_statistics(url, success, content_type)
        
        # Hole aktualisierte Quelle für Score-Anzeige
        with db_manager.get_session() as session:
            updated_source = session.query(db_manager.Source).filter_by(url=url).first()
            if updated_source:
                logger.info(f"[SOURCE TRACKING] {url}: {'Erfolg' if success else 'Fehlschlag'} (Score: {updated_source.reliability_score:.0f}%, Typ: {updated_source.source_type})")
    
    def finalize_session(self) -> Optional[Dict[str, Any]]:
        """Beende Session und erstelle Zusammenfassung"""
        if not self.session:
            return None
        
        self.session.finalize()
        summary = self.session.get_summary()
        
        # ÄNDERUNG 02.07.2025: Registry-Speicherung entfernt - alles in DB
        logger.info(f"[SOURCE DISCOVERY] Session {self.session.session_id} beendet: "
                   f"{summary['statistics']['searched']} Quellen durchsucht, "
                   f"{summary['statistics']['successful']} erfolgreich")
        
        return summary
    
    def build_enhanced_prompt(self, mine_name: str, discovered_sources: List[Dict[str, Any]], 
                            max_sources: int = 25) -> str:
        """Erstelle erweiterten Prompt mit Quellenhinweisen"""
        
        # Basis-Prompt mit expliziter Anweisung zur Quellennutzung
        prompt = f"Suche detaillierte Informationen über die Mine: {mine_name}\n\n"
        prompt += "WICHTIG: Nutze ZUERST die unten aufgeführten bewährten Quellen aus unserer Datenbank, "\
                 "bevor du neue Quellen suchst. Diese Quellen haben sich in der Vergangenheit als zuverlässig erwiesen.\n\n"
        
        # Füge Top-Quellen hinzu
        if discovered_sources:
            prompt += "Prüfe speziell diese relevanten Quellen:\n\n"
            
            # Gruppiere nach Typ
            by_type = {}
            for source in discovered_sources[:max_sources]:
                source_type = source.get('type', 'general')
                if source_type not in by_type:
                    by_type[source_type] = []
                by_type[source_type].append(source)
            
            # Füge Quellen nach Typ hinzu
            type_descriptions = {
                'database': 'Offizielle Datenbanken:',
                'government': 'Regierungsquellen:',
                'exchange': 'Börsendokumente:',
                'document': 'Technische Berichte:',
                'industry': 'Industrie-Portale:',
                'general': 'Weitere Quellen:'
            }
            
            for source_type, type_sources in by_type.items():
                if type_sources:
                    prompt += f"\n{type_descriptions.get(source_type, 'Quellen:')}\n"
                    for source in type_sources[:3]:  # Max 3 pro Typ
                        if source['url'].startswith('search:'):
                            # Dokumentsuche
                            prompt += f"- Suche nach: {source['search_pattern']}\n"
                        else:
                            prompt += f"- {source['url']} ({source.get('description', '')})\n"
            
            prompt += "\n"
        
        return prompt
    
    def build_deep_search_prompts(self, mine_name: str, discovered_sources: List[Dict[str, Any]], 
                                 country: Optional[str] = None) -> List[str]:
        """
        Erstellt mehrere spezialisierte Prompts für tiefere Perplexity-Suchen
        
        Args:
            mine_name: Name der Mine
            discovered_sources: Liste der entdeckten Quellen
            country: Land der Mine
            
        Returns:
            Liste von spezialisierten Suchprompts
        """
        prompts = []
        
        # Gruppiere Quellen nach Typ
        by_type = {}
        for source in discovered_sources:
            source_type = source.get('type', 'general')
            if source_type not in by_type:
                by_type[source_type] = []
            by_type[source_type].append(source)
        
        # 1. PDF-Dokument Suche
        pdf_prompt = f"""
        Suche nach PDF-Dokumenten für die Mine "{mine_name}":
        - NI 43-101 Technical Reports
        - Feasibility Studies
        - Environmental Impact Assessments
        - Closure Plans
        - Annual Reports mit Asset Retirement Obligations (ARO)
        
        Suche speziell auf:
        """
        if 'government' in by_type:
            for source in by_type['government'][:3]:
                pdf_prompt += f"\n- {source['domain']}"
        pdf_prompt += "\n\nGib für jedes gefundene PDF den direkten Download-Link an."
        prompts.append(pdf_prompt)
        
        # 2. Datenbank-spezifische Suche
        if 'database' in by_type:
            db_prompt = f"""
            Durchsuche Mining-Datenbanken nach "{mine_name}":
            """
            for source in by_type['database'][:5]:
                db_prompt += f"\n- {source['url']} ({source.get('description', '')})"
            db_prompt += """
            
            Extrahiere speziell:
            - Closure Costs / Restaurationskosten
            - Environmental Bonds
            - Koordinaten
            - Produktionsdaten
            """
            prompts.append(db_prompt)
        
        # 3. Finanzinformationen
        if 'exchange' in by_type:
            finance_prompt = f"""
            Suche Finanzinformationen für Mine "{mine_name}" auf:
            """
            for source in by_type['exchange']:
                finance_prompt += f"\n- {source['domain']}"
            finance_prompt += """
            
            Finde speziell:
            - Asset Retirement Obligations (ARO)
            - Closure Cost Estimates
            - Environmental Liabilities
            - Restoration Provisions
            """
            prompts.append(finance_prompt)
        
        # 4. Regionale Behörden
        if country and 'government' in by_type:
            gov_prompt = f"""
            Prüfe regionale Bergbaubehörden in {country} für "{mine_name}":
            """
            for source in by_type['government'][:5]:
                gov_prompt += f"\n- {source['url']}"
            gov_prompt += """
            
            Suche nach:
            - Genehmigungen und Lizenzen
            - Umweltauflagen
            - Sicherheitsleistungen
            - Monitoring-Berichte
            """
            prompts.append(gov_prompt)
        
        # ÄNDERUNG 02.07.2025: Spezialisierter Finanz-Prompt
        # 5. Dedizierter Restaurationskosten-Prompt
        restoration_prompt = f"""
        SPEZIALISIERTE SUCHE NUR FÜR RESTAURATIONSKOSTEN für Mine "{mine_name}":
        
        Suche gezielt nach folgenden Finanzbegriffen und deren Werten:
        - Asset Retirement Obligation (ARO)
        - Closure Costs / Mine Closure Costs
        - Environmental Liability / Environmental Obligations
        - Restoration Provision / Rehabilitation Provision
        - Decommissioning Costs / Abandonment Costs
        - Financial Assurance / Closure Bond / Environmental Bond
        - Post-closure monitoring costs
        - Progressive rehabilitation costs
        - Exploration closure costs (für kleine Minen)
        - Initial restoration costs
        
        Prüfe speziell diese Dokumenttypen:
        - Annual Reports: Notes to Financial Statements (Note über ARO/Environmental Liabilities)
        - Sustainability Reports: Environmental Provisions Section
        - Technical Reports: Section über Closure Costs
        - MD&A: Diskussion über zukünftige Verpflichtungen
        - KONZESSIONSDOKUMENTE: Umweltauflagen und Sicherheitsleistungen
        - MANAGEMENTPLÄNE: Restaurationsverpflichtungen
        - GESTIM DATENBANK (für Quebec): Mining titles und Umweltgarantien
        - UMWELTGENEHMIGUNGEN: Finanzielle Sicherheiten
        
        WICHTIG: 
        - Gib ALLE gefundenen Beträge an, auch kleine Beträge ab $1,000!
        - Explorationsminen können Kosten von nur $5,000 - $50,000 haben
        - Format: "$5,000 CAD (2023)" oder "$25k USD exploration closure"
        - Achte auf Bezeichnungen wie "thousand", "k", "tausend"
        
        Wenn verschiedene Währungen gefunden werden, gib alle an und rechne ggf. um.
        """
        prompts.append(restoration_prompt)
        
        return prompts
    
    async def track_discovered_sources(self, discovered_sources: List[Dict[str, Any]]) -> None:
        """
        Trackt alle entdeckten Quellen als durchsucht
        
        Dies ist wichtig für korrekte Statistiken, auch wenn Perplexity
        die eigentliche Suche durchführt
        """
        for source in discovered_sources:
            url = source.get('url', '')
            if url and self.session:
                # Markiere als durchsucht (Perplexity wird sie verwenden)
                self.session.add_searched_source(url, True)  # Als erfolgreich markieren da Perplexity sie nutzt
                
                # Später wird track_source_result aufgerufen wenn Perplexity
                # die Quelle in seiner Antwort erwähnt


# ÄNDERUNG 04.07.2025: SearchSession aus models.py verwenden statt lokale Definition


class IncrementalSourceDiscovery(EnhancedSourceDiscovery):
    """
    ÄNDERUNG 27.08.2025: Erweiterung für Sequential Field Orchestrator
    Implementiert inkrementelle/additive Quellensammlung für optimalen Workflow

    REFAKTOR 29.08.2025:
    - Dünne Fassade: Orchestrierung, Persistenz und Statistik ausgelagert
    - Abhängigkeiten via Konstruktor injiziert (kein harter DB-Import)
    """
    
    def __init__(
        self,
        orchestrator: Optional['IncrementalDiscoveryOrchestrator'] = None,
        accumulator: Optional['SourceAccumulator'] = None,
        persistence_manager: Optional['SourcePersistenceManager'] = None,
        statistics_calculator: Optional['SourceStatisticsCalculator'] = None,
        db_manager: Optional[object] = None
    ):
        super().__init__()
        self.source_accumulator = accumulator or SourceAccumulator()
        self.persistence_manager = persistence_manager or SourcePersistenceManager(db_manager=db_manager)
        self.statistics_calculator = statistics_calculator or SourceStatisticsCalculator()
        # Orchestrator zuletzt erzeugen, nachdem Abhängigkeiten stehen
        self.orchestrator = orchestrator or IncrementalDiscoveryOrchestrator(
            discovery_service=self,
            accumulator=self.source_accumulator,
            persistence_manager=self.persistence_manager,
            statistics_calculator=self.statistics_calculator
        )
    
    async def discover_incremental_sources(
        self,
        mine_name: str,
        model_id: str,
        existing_sources: List[Dict[str, Any]],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        priority_focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Entdeckt neue Quellen inkrementell - fügt nur neue Quellen zu bestehenden hinzu
        
        Args:
            mine_name: Name der Mine
            model_id: ID des Modells das die Suche durchführt
            existing_sources: Bereits bekannte Quellen
            country: Land
            region: Region
            commodity: Rohstoff
            priority_focus: Schwerpunkt für diese Runde (z.B. "model_1_discovery")
            
        Returns:
            Liste neuer Quellen (nur die, die noch nicht in existing_sources sind)
        """
        logger.info(f"[INCREMENTAL-DISCOVERY] {model_id} sucht neue Quellen für {mine_name}")
        
        # Delegiere an Orchestrator
        new_sources = self.orchestrator.run_incremental_discovery(
            mine_name=mine_name,
            model_id=model_id,
            existing_sources=existing_sources,
            country=country,
            region=region,
            commodity=commodity,
            priority_focus=priority_focus
        )
        # Persistiere neue Quellen
        await self._persist_incremental_sources(new_sources, mine_name, model_id)
        return new_sources
    
    def _filter_new_sources(
        self,
        discovered_sources: List[Dict[str, Any]],
        existing_sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Adapter: delegiert an Orchestrator-Utility
        return IncrementalDiscoveryOrchestrator.filter_new_sources_static(discovered_sources, existing_sources)
    
    def _are_urls_similar(self, url1: str, url2: str, similarity_threshold: float = 0.8) -> bool:
        # Adapter: delegiert an Orchestrator-Utility
        return IncrementalDiscoveryOrchestrator.are_urls_similar_static(url1, url2, similarity_threshold)
    
    async def _persist_incremental_sources(
        self,
        sources: List[Dict[str, Any]],
        mine_name: str,
        model_id: str
    ) -> None:
        """
        Persistiert neue Quellen in die Datenbank
        """
        try:
            self.persistence_manager.save_sources(sources=sources, mine_name=mine_name, model_id=model_id)
            logger.info(f"[INCREMENTAL-PERSIST] {len(sources)} neue Quellen für {model_id} persistiert")
        except Exception as e:
            logger.error(f"[INCREMENTAL-PERSIST] Kritischer Fehler beim Persistieren: {str(e)}")
    
    def get_accumulated_sources_for_mine(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Holt alle akkumulierten Quellen für eine Mine aus der Datenbank
        
        Returns:
            Liste aller bereits entdeckten und persistierten Quellen
        """
        try:
            from minesearch.database import db_manager
            
            # Hole alle gespeicherten Quellen für diese Mine
            with db_manager.get_session() as session:
                # Implementierung hängt von der DB-Struktur ab
                # Für jetzt verwenden wir die bestehende source discovery
                all_sources = self.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region
                )
                
                logger.info(f"[ACCUMULATED-SOURCES] {len(all_sources)} akkumulierte Quellen für {mine_name} abgerufen")
                return all_sources
                
        except Exception as e:
            logger.error(f"[ACCUMULATED-SOURCES] Fehler beim Abrufen akkumulierter Quellen: {str(e)}")
            return []


class SourceAccumulator:
    """
    Hilfklasse für die Akkumulation von Quellen über mehrere Modell-Durchläufe
    """
    
    def __init__(self):
        self.accumulated_sources = []
        self.source_quality_scores = {}
        self.model_contributions = defaultdict(int)
    
    def add_sources(self, sources: List[Dict[str, Any]], model_id: str) -> int:
        """
        Fügt neue Quellen zur Akkumulation hinzu
        
        Returns:
            Anzahl der tatsächlich hinzugefügten neuen Quellen
        """
        existing_urls = {s.get('url') for s in self.accumulated_sources}
        new_sources_count = 0
        
        for source in sources:
            url = source.get('url')
            if url and url not in existing_urls:
                source['contributed_by'] = model_id
                self.accumulated_sources.append(source)
                existing_urls.add(url)
                new_sources_count += 1
        
        self.model_contributions[model_id] += new_sources_count
        
        logger.debug(f"[SOURCE-ACCUMULATOR] {model_id} trug {new_sources_count} neue Quellen bei")
        
        return new_sources_count
    
    def get_accumulated_sources(self) -> List[Dict[str, Any]]:
        """Gibt alle akkumulierten Quellen zurück"""
        return self.accumulated_sources.copy()
    
    def get_model_contributions(self) -> Dict[str, int]:
        """Gibt Beiträge pro Modell zurück"""
        return dict(self.model_contributions)
    
    def rank_sources_by_quality(self) -> List[Dict[str, Any]]:
        """Delegiert Ranking an SourceStatisticsCalculator."""
        calculator = SourceStatisticsCalculator()
        return calculator.rank_sources_by_quality(self.accumulated_sources)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Delegiert Statistiken an SourceStatisticsCalculator."""
        calculator = SourceStatisticsCalculator()
        return calculator.get_statistics(self.accumulated_sources, self.model_contributions)


# =========================
# Neue fokussierte Komponenten
# =========================

class SourcePersistenceManager:
    """
    Verantwortlich für die Persistenz von Quellen mit injizierbarem db_manager.
    """

    def __init__(self, db_manager: Optional[object] = None):
        self.db_manager = db_manager

    def save_sources(self, sources: List[Dict[str, Any]], mine_name: str, model_id: str) -> int:
        if not sources:
            return 0
        if self.db_manager is None:
            try:
                from minesearch.database import db_manager as default_db
                self.db_manager = default_db
            except Exception as e:
                logger.warning(f"[PERSISTENCE] Kein db_manager injiziert: {e}")
                return 0

        persisted = 0
        for source in sources:
            try:
                self.db_manager.add_or_update_source(
                    url=source.get('url'),
                    domain=source.get('domain'),
                    country=source.get('country'),
                    region=source.get('region'),
                    source_type=source.get('type'),
                    metadata={
                        'discovered_for': mine_name,
                        'discovered_by_model': model_id,
                        'discovered_at': source.get('discovered_at') or datetime.now().isoformat(),
                        'discovery_round': source.get('discovery_round'),
                        'priority': source.get('priority', 2),
                        'description': source.get('description', ''),
                        'incremental_discovery': True,
                    }
                )
                persisted += 1
            except Exception as e:
                logger.warning(f"[PERSISTENCE] Fehler beim Speichern von {source.get('url')}: {e}")

        return persisted


class SourceStatisticsCalculator:
    """Berechnet Rankings und Statistiken für Quellen."""

    def rank_sources_by_quality(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def source_quality_score(source: Dict[str, Any]) -> float:
            type_scores = {
                'government': 0.9,
                'database': 0.8,
                'exchange': 0.7,
                'industry': 0.6,
                'document': 0.5,
                'general': 0.3
            }
            base_score = type_scores.get(source.get('type', 'general'), 0.3)
            priority = source.get('priority', 2)
            priority_bonus = (4 - priority) * 0.1 if isinstance(priority, int) and priority <= 3 else 0
            reliability = source.get('reliability_score', 0) or 0
            reliability_bonus = float(reliability) * 0.1 if reliability else 0.0
            return float(base_score) + float(priority_bonus) + float(reliability_bonus)

        return sorted(list(sources or []), key=source_quality_score, reverse=True)

    def get_statistics(
        self,
        sources: List[Dict[str, Any]],
        model_contributions: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        type_distribution = defaultdict(int)
        priority_distribution = defaultdict(int)

        for source in sources or []:
            type_distribution[source.get('type', 'unknown')] += 1
            priority_distribution[source.get('priority', 'unknown')] += 1

        return {
            'total_sources': len(sources or []),
            'model_contributions': dict(model_contributions or {}),
            'type_distribution': dict(type_distribution),
            'priority_distribution': dict(priority_distribution),
            'unique_domains': len(set(s.get('domain') for s in (sources or []) if s.get('domain')))
        }


class IncrementalDiscoveryOrchestrator:
    """
    Koordiniert den inkrementellen Discovery-Flow und entkoppelt die Verantwortlichkeiten.
    """

    def __init__(
        self,
        discovery_service: EnhancedSourceDiscovery,
        accumulator: SourceAccumulator,
        persistence_manager: SourcePersistenceManager,
        statistics_calculator: SourceStatisticsCalculator
    ):
        self.discovery_service = discovery_service
        self.accumulator = accumulator
        self.persistence_manager = persistence_manager
        self.statistics_calculator = statistics_calculator

    def run_incremental_discovery(
        self,
        mine_name: str,
        model_id: str,
        existing_sources: List[Dict[str, Any]],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        priority_focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        all_discovered = self.discovery_service.discover_sources_for_mine(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            priority_focus=priority_focus
        )
        new_sources = self.filter_new_sources_static(all_discovered, existing_sources)
        annotated = self._annotate_sources(new_sources, model_id, priority_focus)
        self.accumulator.add_sources(annotated, model_id)
        return annotated

    def _annotate_sources(
        self,
        sources: List[Dict[str, Any]],
        model_id: str,
        priority_focus: Optional[str]
    ) -> List[Dict[str, Any]]:
        for source in sources:
            source['discovered_by_model'] = model_id
            source['discovered_at'] = datetime.now().isoformat()
            source['discovery_round'] = priority_focus or 'sequential_discovery'
            source['incremental_discovery'] = True
        return sources

    @staticmethod
    def filter_new_sources_static(
        discovered_sources: List[Dict[str, Any]],
        existing_sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        existing_urls = set()
        existing_domains = set()
        for source in existing_sources:
            url = (source.get('url') or '').strip().lower()
            domain = (source.get('domain') or '').strip().lower()
            if url:
                existing_urls.add(url)
            if domain:
                existing_domains.add(domain)
        new_sources: List[Dict[str, Any]] = []
        for source in discovered_sources or []:
            source_url = (source.get('url') or '').strip().lower()
            source_domain = (source.get('domain') or '').strip().lower()
            if source_url and source_url not in existing_urls:
                is_duplicate = False
                if source_domain in existing_domains:
                    for existing_source in existing_sources:
                        existing_url = (existing_source.get('url') or '').strip().lower()
                        if existing_url and source_domain in existing_url:
                            if IncrementalDiscoveryOrchestrator.are_urls_similar_static(source_url, existing_url):
                                is_duplicate = True
                                break
                if not is_duplicate:
                    new_sources.append(source)
        return new_sources

    @staticmethod
    def are_urls_similar_static(url1: str, url2: str, similarity_threshold: float = 0.8) -> bool:
        try:
            from urllib.parse import urlparse
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            if parsed1.netloc != parsed2.netloc:
                return False
            path1_parts = set(filter(None, parsed1.path.split('/')))
            path2_parts = set(filter(None, parsed2.path.split('/')))
            if path1_parts and path2_parts:
                intersection = len(path1_parts.intersection(path2_parts))
                union = len(path1_parts.union(path2_parts))
                similarity = (intersection / union) if union > 0 else 0.0
                return similarity >= similarity_threshold
            return False
        except Exception as e:
            logger.debug(f"[URL-SIMILARITY] Fehler beim Vergleichen von URLs: {str(e)}")
            return False

# Global instances für einfache Verwendung (nach Definition der neuen Klassen)
incremental_source_discovery = IncrementalSourceDiscovery()