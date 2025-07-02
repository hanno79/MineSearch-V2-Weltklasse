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
from models import SourceRecord, SearchSession, source_registry
from source_discovery import SourceDiscovery

logger = logging.getLogger(__name__)


class EnhancedSourceDiscovery(SourceDiscovery):
    """Erweiterte Quellensuche mit Active Discovery"""
    
    def __init__(self):
        super().__init__()
        self.session: Optional[SearchSession] = None
    
    def start_session(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> SearchSession:
        """Starte neue Such-Session"""
        self.session = source_registry.create_session(mine_name, country, region)
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
        
        # 5. Bekannte erfolgreiche Quellen aus Registry
        registry_sources = self._get_registry_recommendations(country, region, commodity)
        discovered_sources.extend(registry_sources)
        logger.info(f"[ACTIVE DISCOVERY] {len(registry_sources)} Quellen aus Registry")
        
        # 6. ÄNDERUNG 02.07.2025: Zusätzliche Quellen aus Datenbank
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
        
        # Basis-Suchbegriffe für technische Dokumente
        doc_patterns = [
            f'"{mine_name}" NI 43-101 technical report filetype:pdf',
            f'"{mine_name}" feasibility study filetype:pdf',
            f'"{mine_name}" closure plan filetype:pdf',
            f'"{mine_name}" environmental assessment filetype:pdf',
            f'"{mine_name}" annual report filetype:pdf'
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
    
    def _get_registry_recommendations(self, country: Optional[str], region: Optional[str], 
                                    commodity: Optional[str]) -> List[Dict[str, Any]]:
        """Hole Empfehlungen aus der Source Registry"""
        sources = []
        
        # Hole erfolgreiche Quellen aus Registry
        if country and region:
            registry_sources = source_registry.get_sources_for_region(country, region, min_reliability=70.0)
        elif country:
            registry_sources = source_registry.get_sources_for_country(country, min_reliability=70.0)
        else:
            registry_sources = source_registry.get_top_sources(limit=5)
        
        for source in registry_sources:
            sources.append({
                'url': source.url,
                'domain': source.domain,
                'type': source.source_type,
                'priority': 1 if source.reliability_score > 80 else 2,
                'description': f"Bewährte Quelle (Score: {source.reliability_score:.0f}%)",
                'reliability_score': source.reliability_score
            })
        
        return sources
    
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
        db_sources = db_manager.get_sources_for_search(
            country=country,
            region=region,
            min_reliability=40.0,  # Mindestens 40% Zuverlässigkeit
            limit=30  # Max 30 zusätzliche Quellen
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
        
        # Update Registry
        source = source_registry.get_source(url)
        if not source:
            # Neue Quelle erstellen
            domain = urllib.parse.urlparse(url).netloc
            source = SourceRecord(
                url=url,
                domain=domain,
                country=self.session.country,
                region=self.session.region,
                source_type=self._classify_domain(domain)
            )
            source_registry.add_source(source)
        
        # Update Zugriffstatistiken
        source_registry.db.update_source_statistics(url, success, content_type)
        
        logger.info(f"[SOURCE TRACKING] {url}: {'Erfolg' if success else 'Fehlschlag'} (Score: {source.reliability_score:.0f}%)")
    
    def finalize_session(self) -> Optional[Dict[str, Any]]:
        """Beende Session und erstelle Zusammenfassung"""
        if not self.session:
            return None
        
        self.session.finalize()
        summary = self.session.get_summary()
        
        # Speichere Registry
        import os
        registry_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'source_registry.json')
        os.makedirs(os.path.dirname(registry_file), exist_ok=True)
        source_registry.save_to_file(registry_file)
        
        logger.info(f"[SOURCE DISCOVERY] Session {self.session.session_id} beendet: "
                   f"{summary['statistics']['searched']} Quellen durchsucht, "
                   f"{summary['statistics']['successful']} erfolgreich")
        
        return summary
    
    def build_enhanced_prompt(self, mine_name: str, discovered_sources: List[Dict[str, Any]], 
                            max_sources: int = 15) -> str:
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