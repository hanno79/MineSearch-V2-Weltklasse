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

from config import config, Config
from source_discovery import SourceDiscovery
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnhancedSourceDiscovery(SourceDiscovery):
    """Erweiterte Quellensuche mit Active Discovery"""
    
    def __init__(self):
        super().__init__()
        self.session: Optional[SearchSession] = None
    
    def start_session(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> 'SearchSession':
        """Starte neue Such-Session"""
        # ÄNDERUNG 02.07.2025: Einfache Session-Implementierung ohne Registry
        self.session = SearchSession(mine_name, country, region)
        logger.info(f"[SOURCE DISCOVERY] Session {self.session.session_id} gestartet für {mine_name}")
        return self.session
    
    def discover_sources_for_mine(self, mine_name: str, country: Optional[str] = None, 
                                 region: Optional[str] = None, commodity: Optional[str] = None) -> List[Dict[str, Any]]:
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
        
        logger.info(f"[ACTIVE DISCOVERY] Gesamt: {len(unique_sources)} unique Quellen entdeckt")
        
        return unique_sources
    
    def _get_country_specific_sources(self, mine_name: str, country: str, region: Optional[str]) -> List[Dict[str, Any]]:
        """Hole länderspezifische Quellen"""
        sources = []
        
        # Hole Länderkonfiguration
        country_config = Config.COUNTRY_CONFIGS.get(country.lower(), {})
        priority_domains = country_config.get('priority_domains', [])
        
        # Spezialbehandlung für Quebec/GESTIM
        if country.lower() in ['kanada', 'canada'] and region and 'quebec' in region.lower():
            sources.append({
                'url': f"https://gestim.mines.gouv.qc.ca/MRN_GestimP_Presentation/ODM02201_menu_base.aspx",
                'domain': 'gestim.mines.gouv.qc.ca',
                'type': 'database',
                'priority': 1,
                'description': 'GESTIM - Quebec Mining Registry',
                'search_hint': f"Suche nach: {mine_name}",
                'api_available': True  # Markiere dass API verfügbar ist
            })
        
        # Andere Priority Domains
        for domain in priority_domains:
            if 'gestim' not in domain:  # GESTIM bereits hinzugefügt
                sources.append({
                    'url': f"https://{domain}/search?q={urllib.parse.quote(mine_name)}",
                    'domain': domain,
                    'type': self._classify_domain(domain),
                    'priority': 1,
                    'description': f"Länderspezifische Quelle: {domain}"
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
        
        # Tier 1 Domains
        for domain in Config.PRIORITY_MINING_DOMAINS.get('tier1', []):
            sources.append({
                'url': f"https://{domain}/search?q={urllib.parse.quote(mine_name)}",
                'domain': domain,
                'type': 'government',
                'priority': 1,
                'description': f"Regierungsdatenbank: {domain}"
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
            sources.append({
                'url': f"https://{exchange}/search?q={urllib.parse.quote(mine_name)}",
                'domain': exchange,
                'type': 'exchange',
                'priority': 2,
                'description': f"Börsendokumente: {exchange}"
            })
        
        return sources
    
    def _search_technical_documents(self, mine_name: str, country: Optional[str]) -> List[Dict[str, Any]]:
        """Suche nach technischen Dokumenten"""
        sources = []
        
        # ÄNDERUNG 02.07.2025: Erweiterte PDF-Suchpatterns
        # Basis-Suchbegriffe für technische Dokumente
        doc_patterns = [
            f'"{mine_name}" NI 43-101 technical report filetype:pdf',
            f'"{mine_name}" feasibility study filetype:pdf',
            f'"{mine_name}" closure plan filetype:pdf',
            f'"{mine_name}" environmental assessment filetype:pdf',
            f'"{mine_name}" annual report filetype:pdf',
            # Neue Patterns für bessere Abdeckung
            f'"{mine_name}" sustainability report filetype:pdf',
            f'"{mine_name}" ESG report filetype:pdf',
            f'"{mine_name}" environmental impact assessment filetype:pdf',
            f'"{mine_name}" MD&A management discussion analysis filetype:pdf',
            f'"{mine_name}" financial statements notes filetype:pdf',
            f'"{mine_name}" asset retirement obligation filetype:pdf',
            f'"{mine_name}" reclamation plan filetype:pdf',
            f'"{mine_name}" rehabilitation plan filetype:pdf',
            f'"{mine_name}" decommissioning plan filetype:pdf'
        ]
        
        # Erstelle Google-ähnliche Suchanfragen
        for pattern in doc_patterns:
            sources.append({
                'url': f"search:{pattern}",  # Spezieller Marker für Dokumentsuche
                'domain': 'document_search',
                'type': 'document',
                'priority': 2,
                'description': f"Dokumentsuche: {pattern}",
                'search_pattern': pattern
            })
        
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
        from database import db_manager
        
        # Hole relevante Quellen aus DB
        # ÄNDERUNG 02.07.2025: Erhöhte Limits für bessere Abdeckung
        db_sources = db_manager.get_sources_for_search(
            country=country,
            region=region,
            min_reliability=25.0,  # Gesenkt von 40% auf 25% für mehr Quellen
            limit=50  # Erhöht von 30 auf 50 zusätzliche Quellen
        )
        
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
        from database import db_manager
        
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
        
        # Basis-Prompt
        prompt = f"Suche detaillierte Informationen über die Mine: {mine_name}\n\n"
        
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
        
        Prüfe speziell diese Dokumenttypen:
        - Annual Reports: Notes to Financial Statements (Note über ARO/Environmental Liabilities)
        - Sustainability Reports: Environmental Provisions Section
        - Technical Reports: Section über Closure Costs
        - MD&A: Diskussion über zukünftige Verpflichtungen
        
        WICHTIG: Gib ALLE gefundenen Beträge mit Währung und Jahr an!
        Beispiel: "$45.3 million CAD (2023)" oder "USD 123 million as of December 2022"
        
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


# ÄNDERUNG 02.07.2025: Einfache SearchSession-Klasse ohne Registry
class SearchSession:
    """Einfache Session-Klasse für Source Discovery"""
    
    def __init__(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None):
        self.session_id = str(uuid.uuid4())
        self.mine_name = mine_name
        self.country = country
        self.region = region
        self.start_time = datetime.now()
        self.end_time = None
        self.discovered_sources = []
        self.searched_sources = []
        self.successful_sources = []
        self.failed_sources = []
    
    def add_discovered_source(self, url: str):
        """Füge entdeckte Quelle hinzu"""
        if url not in self.discovered_sources:
            self.discovered_sources.append(url)
    
    def add_searched_source(self, url: str, success: bool, data: Optional[Dict[str, Any]] = None):
        """Füge durchsuchte Quelle hinzu"""
        source_info = {
            'url': url,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': data
        }
        
        self.searched_sources.append(source_info)
        
        if success:
            self.successful_sources.append(source_info)
        else:
            self.failed_sources.append(source_info)
    
    def finalize(self):
        """Beende Session"""
        self.end_time = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Erstelle Session-Zusammenfassung"""
        duration = (self.end_time or datetime.now()) - self.start_time
        
        return {
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration.total_seconds(),
            'statistics': {
                'discovered': len(self.discovered_sources),
                'searched': len(self.searched_sources),
                'successful': len(self.successful_sources),
                'failed': len(self.failed_sources),
                'success_rate': (len(self.successful_sources) / len(self.searched_sources) * 100) if self.searched_sources else 0
            },
            'sources': {
                'discovered': self.discovered_sources[:10],  # Top 10
                'successful': self.successful_sources[:10],  # Top 10
                'failed': self.failed_sources[:10]  # Top 10
            }
        }