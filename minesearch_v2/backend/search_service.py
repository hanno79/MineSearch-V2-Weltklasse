"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored MineSearchService (CLAUDE.md konform)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.base import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from utils import normalize_accents, generate_name_variants, generate_multilingual_search_terms, get_country_config
from data_extraction import DataExtractor, assign_sources_to_data
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from cache_service import get_cache_service, cached_search
# BEREINIGUNG 06.08.2025: Legacy import entfernt - Datei wurde nach to_delete/ verschoben
# from search_service_legacy import LegacySearchFunctions
from cost_monitor import cost_monitor
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class MineSearchService:
    """Hauptklasse für Mining-Suchen mit Provider-Unterstützung"""
    
    def __init__(self):
        # Provider-basierte Architektur
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
        # Database Manager für Persistierung
        self.db_manager = DatabaseManager()
    
    async def search_mine(self, mine_name: str, model: str, country: Optional[str] = None, 
                         commodity: Optional[str] = None, region: Optional[str] = None, 
                         _is_auto_enhanced: bool = False) -> Dict[str, Any]:
        """
        Hauptsuchfunktion für Mining-Informationen
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Zu verwendendes Modell
            region: Region (optional)
            _is_auto_enhanced: Intern - verhindert Rekursion
            
        Returns:
            Strukturiertes Suchergebnis
        """
        logger.info(f"[SEARCH] Starte Suche für: {mine_name}, Land: {country}, Modell: {model}")
        
        # ÄNDERUNG 14.07.2025: Generische Provider-Unterstützung statt nur Perplexity
        # Prüfe ob Modell verfügbar ist (mit Provider-Präfix)
        full_model_id = model if ':' in model else f"openrouter:{model}"
        
        # Cache-Check - BUGFIX 20.07.2025: Temporär deaktiviert für Tests
        # cached_result = await self._check_cache(mine_name, country or "", full_model_id, commodity=commodity, region=region)
        # if cached_result:
        #     logger.info(f"[SEARCH] Cache-Hit für {mine_name} mit Model {full_model_id}")
        #     return cached_result
        logger.info(f"[SEARCH] Cache temporär deaktiviert - jede Suche wird frisch ausgeführt")
        if not self.registry.is_model_available(full_model_id):
            # Fallback auf Default-Modell
            logger.warning(f"Modell {full_model_id} nicht verfügbar, verwende Default: {config.DEFAULT_MODEL}")
            full_model_id = config.DEFAULT_MODEL
        
        # ÄNDERUNG 14.07.2025: Kostenüberwachung für Premium-Modelle
        if not cost_monitor.check_model_costs(full_model_id, "search"):
            logger.error(f"Verwendung von kostenpflichtigem Modell {full_model_id} blockiert")
            alternatives = cost_monitor.suggest_free_alternatives(full_model_id)
            if alternatives:
                full_model_id = alternatives[0]
                logger.info(f"Verwende kostenlose Alternative: {full_model_id}")
            else:
                full_model_id = config.DEFAULT_MODEL
        
        # Verwende Provider-basierte Suche
        try:
            result = await self._search_with_provider(mine_name, country, commodity, full_model_id, region)
            
            # Cache das Ergebnis - BUGFIX 20.07.2025: Temporär deaktiviert für Tests
            # if result.get('success'):
            #     await self._cache_result(mine_name, country or "", full_model_id, result, commodity=commodity, region=region)
            
            return result
            
        except Exception as e:
            logger.error(f"[SEARCH] Provider-Fehler für {mine_name}: {e}")
            # Fallback auf Legacy-Suche
            return await self._legacy_search(mine_name, country, commodity, model, region)
    
    async def enhanced_search(self, mine_name: str, model: str, country: Optional[str] = None,
                            commodity: Optional[str] = None, region: Optional[str] = None, 
                            _from_auto: bool = False) -> Dict[str, Any]:
        """
        Erweiterte Zwei-Phasen-Suche für umfangreichere Ergebnisse
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Zu verwendendes Modell
            region: Region (optional)
            _from_auto: Verhindert Rekursion
            
        Returns:
            Erweiterte Suchergebnisse
        """
        logger.info(f"[ENHANCED] Starte erweiterte Zwei-Phasen-Suche für: {mine_name}")
        
        # Phase 1: Initiale Suche mit Rekursionsschutz
        phase1_result = await self.search_mine(
            mine_name, country, commodity, model, region, 
            _is_auto_enhanced=_from_auto
        )
        
        if not phase1_result.get('success') or not phase1_result.get('data'):
            return phase1_result
        
        # Extrahiere Quellen für Phase 2
        sources = phase1_result['data'].get('sources', [])
        logger.info(f"[ENHANCED] Phase 1 Quellen gefunden: {len(sources)}")
        
        # Filtere valide Quellen
        valid_sources = [s for s in sources if 
            s.get('type') == 'url' or 
            (s.get('type') == 'document' and len(s.get('value', '')) > 5)]
        
        if not valid_sources:
            logger.info("[ENHANCED] Keine validen Quellen für Phase 2 gefunden")
            return phase1_result
        
        # Phase 2: Vertiefende Suche mit gefundenen Quellen
        phase2_results = []
        for i, source in enumerate(valid_sources[:5]):  # Limitiere auf 5 Quellen
            try:
                phase2_result = await self._search_phase2(source, mine_name, country, model)
                if phase2_result.get('success'):
                    phase2_results.append(phase2_result)
            except Exception as e:
                logger.warning(f"[ENHANCED] Phase 2 Quelle {i+1} fehlgeschlagen: {e}")
        
        # Kombiniere Phase 1 und Phase 2 Ergebnisse
        combined_result = self._combine_phase_results(phase1_result, phase2_results)
        
        logger.info(f"[ENHANCED] Erweiterte Suche abgeschlossen: {len(phase2_results)} zusätzliche Quellen")
        return combined_result
    
    async def _search_with_provider(self, mine_name: str, country: Optional[str],
                                  commodity: Optional[str], full_model_id: str, 
                                  region: Optional[str]) -> Dict[str, Any]:
        """
        Suche mit Provider-System
        
        Args:
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff
            full_model_id: Vollständige Modell-ID mit Provider-Präfix
            region: Region
            
        Returns:
            Provider-basiertes Suchergebnis
        """
        # ÄNDERUNG 14.07.2025: Generische Provider-Extraktion aus model_id
        provider_name = full_model_id.split(':')[0] if ':' in full_model_id else 'openrouter'
        provider = self.registry.get_provider(provider_name)
        if not provider:
            logger.warning(f"Provider {provider_name} nicht verfügbar, verwende Default-Provider")
            provider = self.registry.get_provider("openrouter")
            if not provider:
                raise Exception("Kein verfügbarer Provider gefunden")
        
        # Bereite Suchkontext vor
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Erstelle Suchanfrage
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('restoration_cost_terms', ['restoration costs'])
        
        query = self._build_search_query(
            mine_name, name_variants, country, currency, restoration_terms
        )
        
        # Provider-Optionen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': currency,
            'name_variants': name_variants,
            'multilingual_terms': multilingual_terms
        }
        
        # ÄNDERUNG 14.07.2025: Führe Suche durch mit korrektem Model-Namen
        model_name = full_model_id.split(':')[1] if ':' in full_model_id else full_model_id
        result = await provider.search(query, model_name, options)
        
        # Verarbeite Ergebnis
        return await self._process_search_result(result, mine_name, country, full_model_id)
    
    async def _legacy_search(self, mine_name: str, country: Optional[str],
                           commodity: Optional[str], model: str, 
                           region: Optional[str]) -> Dict[str, Any]:
        """
        Legacy-Suche mit direkter API-Nutzung
        
        Args:
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff
            model: Modell
            region: Region
            
        Returns:
            Legacy-Suchergebnis
        """
        logger.info(f"[LEGACY] Verwende Legacy-Suche für {mine_name}")
        
        # Bereite Suchkontext vor
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('restoration_cost_terms', ['restoration costs'])
        
        # Erstelle Suchanfrage
        query = self._build_search_query(
            mine_name, name_variants, country, currency, restoration_terms
        )
        
        # ÄNDERUNG 14.07.2025: Generischer Provider-Aufruf statt nur Perplexity
        # Berechne tatsächlich verwendetes Modell für Legacy
        legacy_full_model_id = model if ':' in model else f"openrouter:{model}"
        provider_name = legacy_full_model_id.split(':')[0]
        provider = self.registry.get_provider(provider_name)
        if not provider:
            logger.warning(f"Provider {provider_name} nicht verfügbar, verwende Default-Provider")
            provider = self.registry.get_provider("openrouter")
            legacy_full_model_id = config.DEFAULT_MODEL  # Aktualisiere auf tatsächlich verwendetes Modell
            if not provider:
                raise Exception("Kein verfügbarer Provider gefunden")
        
        model_name = legacy_full_model_id.split(':')[1] if ':' in legacy_full_model_id else legacy_full_model_id
        
        # Erstelle Options für Legacy-Suche
        legacy_options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region
        }
        
        api_result = await provider.search(query, model_name, legacy_options)
        
        if not api_result.get('success'):
            return {
                "success": False,
                "error": api_result.get('error', 'Legacy-API-Fehler'),
                "data": {}
            }
        
        # Verarbeite Legacy-Ergebnis
        content = api_result.get('content', '')
        sources = api_result.get('sources', [])
        
        # Validiere Ergebnis
        is_valid, confidence = self._validate_result(content, mine_name, name_variants)
        
        if not is_valid:
            return {
                "success": False,
                "error": "Unzureichende Suchergebnisse",
                "data": {}
            }
        
        # Extrahiere strukturierte Daten
        structured_data = self.data_extractor.extract_structured_data(
            content, mine_name, name_variants
        )
        
        # Füge Quellen zu strukturierten Daten hinzu
        structured_data = assign_sources_to_data(
            structured_data, content, sources
        )
        
        # Berechne Datenqualität
        quality_metrics = self._calculate_data_quality(structured_data)
        
        # DATABASE INTEGRATION: Speichere Legacy-Suchergebnis in Database
        # BUGFIX 20.07.2025: Verwende tatsächlich verwendetes Modell
        try:
            logger.info(f"[DB LEGACY] Speichere mit model_used: {legacy_full_model_id} (original request: {model})")
            search_result = self.db_manager.save_search_result(
                mine_name=mine_name,
                model_used=legacy_full_model_id,
                structured_data=structured_data,
                sources=[{
                    'url': s.get('url', ''),
                    'title': s.get('title', ''),
                    'type': s.get('type', 'unknown'),
                    'reliability': s.get('reliability', 0.5)
                } for s in sources],
                data_quality=quality_metrics.get('completion_percentage', 0),
                success=True,
                country=country,
                search_type="legacy"
            )
            logger.info(f"[DB] Legacy-Suchergebnis für {mine_name} gespeichert (ID: {search_result.id})")
            
            # Aktualisiere Source-Statistiken in Database  
            for source in sources:
                if source.get('url'):
                    self.db_manager.add_or_update_source(
                        url=source.get('url'),
                        domain=source.get('domain', ''),
                        country=country,
                        source_type=source.get('type', 'unknown'),
                        metadata={
                            'title': source.get('title', ''),
                            'reliability': source.get('reliability', 0.5)
                        }
                    )
                    
        except Exception as e:
            logger.error(f"[DB] Fehler beim Speichern des Legacy-Suchergebnisses: {e}")
        
        return {
            "success": True,
            "data": {
                "raw_content": content,
                "structured_data": structured_data,
                "sources": sources,
                "quality_metrics": quality_metrics,
                "model_used": legacy_full_model_id,
                "confidence": confidence,
                "search_type": "legacy"
            }
        }
    
    async def _process_search_result(self, result: SearchResult, mine_name: str, 
                                   country: Optional[str], model: str) -> Dict[str, Any]:
        """
        Verarbeitet Provider-Suchergebnis
        
        Args:
            result: Provider-Suchergebnis
            mine_name: Name der Mine
            country: Land
            model: Verwendetes Modell
            
        Returns:
            Verarbeitetes Suchergebnis
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error or "Provider-Fehler",
                "data": {}
            }
        
        # Extrahiere Daten
        content = result.content or ""
        sources = result.sources or []
        structured_data = result.structured_data or {}
        
        # Falls keine strukturierten Daten vorhanden, extrahiere sie
        if not structured_data and content:
            name_variants = generate_name_variants(mine_name)
            structured_data = self.data_extractor.extract_structured_data(
                content, mine_name, name_variants
            )
            
            # Füge Quellen hinzu
            structured_data = assign_sources_to_data(
                structured_data, content, sources
            )
        
        # Berechne Qualitäts-Metriken
        quality_metrics = self._calculate_data_quality(structured_data)
        
        # ÄNDERUNG 15.07.2025: Sources Usage Tracking implementieren
        await self._track_sources_usage(sources, success=True, model=model)
        
        # DATABASE INTEGRATION: Speichere Suchergebnis in Database
        # BUGFIX 20.07.2025: Verwende tatsächlich verwendetes Modell statt Request-Modell
        try:
            # Robuste Ermittlung der Laufzeit (Sekunden):
            # 1) Provider liefert sie direkt als result.search_duration (sek.)
            # 2) Alternativ in result.metadata als response_time_ms / response_time (ms)
            # 3) Fallback: None (nicht 0 eintragen, um falsche Durchschnitte zu vermeiden)
            search_duration = None
            if hasattr(result, 'search_duration') and result.search_duration:
                search_duration = float(result.search_duration)
            else:
                # Unterschiedliche Keys unterstützen
                meta = result.metadata or {}
                if 'response_time_ms' in meta and meta['response_time_ms']:
                    search_duration = float(meta['response_time_ms']) / 1000.0
                elif 'response_time' in meta and meta['response_time']:
                    search_duration = float(meta['response_time']) / 1000.0

            # Bestimme tatsächlich verwendetes Modell aus Result oder verwende übergebenes
            actual_model_used = result.metadata.get('model_used') or model
            logger.info(f"[DB] Speichere mit model_used: {actual_model_used} (original request: {model})")
            
            search_result = self.db_manager.save_search_result(
                mine_name=mine_name,
                model_used=actual_model_used,
                structured_data=structured_data,
                sources=[{
                    'url': s.get('url', ''),
                    'title': s.get('title', ''),
                    'type': s.get('type', 'unknown'),
                    'reliability': s.get('reliability', 0.5)
                } for s in sources],
                # Speichere nur, wenn messbar (> 0). None bleibt NULL in DB
                search_duration=search_duration if (search_duration is not None and search_duration > 0) else None,
                data_quality=quality_metrics.get('completion_percentage', 0),
                success=True,
                country=country,
                search_type="provider"
            )
            logger.info(f"[DB] Suchergebnis für {mine_name} gespeichert (ID: {search_result.id})")
            
            # Aktualisiere Source-Statistiken in Database  
            for source in sources:
                if source.get('url'):
                    self.db_manager.add_or_update_source(
                        url=source.get('url'),
                        domain=source.get('domain', ''),
                        country=country,
                        source_type=source.get('type', 'unknown'),
                        metadata={
                            'title': source.get('title', ''),
                            'reliability': source.get('reliability', 0.5)
                        }
                    )
                    
        except Exception as e:
            logger.error(f"[DB] Fehler beim Speichern des Suchergebnisses: {e}")
        
        # BUGFIX 20.07.2025: Verwende tatsächlich verwendetes Modell in Response
        actual_model_used = result.metadata.get('model_used') or model
        
        return {
            "success": True,
            "data": {
                "raw_content": content,
                "structured_data": structured_data,
                "sources": sources,
                "quality_metrics": quality_metrics,
                "model_used": actual_model_used,
                "confidence": result.metadata.get("confidence", 0.8),
                "search_type": "provider"
            }
        }
    
    async def _search_phase2(self, source: Dict, mine_name: str, 
                           country: Optional[str], model: str) -> Dict[str, Any]:
        """
        Phase 2 Suche mit spezifischer Quelle
        
        Args:
            source: Quellen-Information
            mine_name: Name der Mine
            country: Land
            model: Modell
            
        Returns:
            Phase 2 Suchergebnis
        """
        # Erstelle spezifische Query für diese Quelle
        query = self._build_phase2_query(source, mine_name, country)
        
        # ÄNDERUNG 14.07.2025: Generischer Provider-Aufruf für Phase 2
        provider_name = model.split(':')[0] if ':' in model else 'openrouter'
        provider = self.registry.get_provider(provider_name)
        if not provider:
            logger.warning(f"Provider {provider_name} nicht verfügbar, verwende Default-Provider")
            provider = self.registry.get_provider("openrouter")
            if not provider:
                raise Exception("Kein verfügbarer Provider gefunden")
        
        model_name = model.split(':')[1] if ':' in model else model
        api_result = await provider.search(query, model_name)
        
        if api_result.get('success'):
            content = api_result.get('content', '')
            name_variants = generate_name_variants(mine_name)
            
            # Extrahiere strukturierte Daten
            structured_data = self.data_extractor.extract_structured_data(
                content, mine_name, name_variants
            )
            
            return {
                "success": True,
                "data": {
                    "structured_data": structured_data,
                    "raw_content": content,
                    "source": source
                }
            }
        
        return {"success": False, "error": api_result.get('error', 'Phase 2 Fehler')}
    
    def _build_phase2_query(self, source: Dict[str, str], mine_name: str, 
                          country: Optional[str]) -> str:
        """Erstellt Phase 2 Query für spezifische Quelle"""
        location = f" in {country}" if country else ""
        
        if source.get('type') == 'url':
            return f"""
            Basierend auf der Quelle {source['value']}, finde spezifische Details über die Mine "{mine_name}"{location}:
            
            1. Exakte GPS-Koordinaten
            2. Aktueller Betreiber/Eigentümer
            3. Rohstoffproduktion (Mengen und Werte)
            4. Restaurations-/Rekultivierungskosten
            5. Mitarbeiterzahl
            6. Umweltauswirkungen
            
            Antworte nur mit verifizierten Informationen aus dieser spezifischen Quelle.
            """
        else:
            return f"""
            Analysiere folgende Information über die Mine "{mine_name}"{location}:
            
            {source['value'][:500]}...
            
            Extrahiere:
            1. GPS-Koordinaten
            2. Betreiber
            3. Produktionsdaten
            4. Kosten
            5. Status
            
            Gib nur die konkret erwähnten Fakten an.
            """
    
    def _combine_phase_results(self, phase1: Dict, phase2_results: List[Dict]) -> Dict:
        """Kombiniert Phase 1 und Phase 2 Ergebnisse"""
        combined_data = phase1['data']['structured_data'].copy()
        all_sources = phase1['data']['sources'].copy()
        
        # Integriere Phase 2 Daten
        for phase2 in phase2_results:
            if phase2.get('success') and phase2.get('data'):
                phase2_data = phase2['data'].get('structured_data', {})
                
                # Aktualisiere leere Felder mit Phase 2 Daten
                for key, value in phase2_data.items():
                    if value and not combined_data.get(key):
                        combined_data[key] = value
                
                # Füge Phase 2 Quelle hinzu
                if phase2['data'].get('source'):
                    all_sources.append(phase2['data']['source'])
        
        # Aktualisiere Qualitäts-Metriken
        quality_metrics = self._calculate_data_quality(combined_data)
        
        # Erstelle kombiniertes Ergebnis
        result = phase1.copy()
        result['data'].update({
            'structured_data': combined_data,
            'sources': all_sources,
            'quality_metrics': quality_metrics,
            'search_type': 'enhanced_two_phase',
            'phase2_sources_used': len(phase2_results)
        })
        
        return result
    
    async def _check_cache(self, mine_name: str, country: str, model: str, **kwargs) -> Optional[Dict]:
        """
        Prüft Cache auf vorhandenes Ergebnis
        BUGFIX 20.07.2025: Verwende korrekte Cache-Parameter statt String-Key
        """
        try:
            cache_service = get_cache_service()
            return cache_service.get(mine_name, country, model, **kwargs)
        except Exception as e:
            logger.debug(f"[CACHE] Cache-Check fehlgeschlagen: {e}")
            return None
    
    async def _cache_result(self, mine_name: str, country: str, model: str, result: Dict, **kwargs):
        """
        Speichert Ergebnis im Cache  
        BUGFIX 20.07.2025: Verwende korrekte Cache-Parameter statt String-Key
        """
        try:
            cache_service = get_cache_service()
            cache_service.set(mine_name, country, model, result, ttl=3600, **kwargs)  # 1 Stunde TTL
        except Exception as e:
            logger.debug(f"[CACHE] Cache-Speicherung fehlgeschlagen: {e}")
    
    async def _track_sources_usage(self, sources: List[Dict], success: bool, model: str):
        """
        ÄNDERUNG 15.07.2025: Trackt Sources-Verwendung in der Datenbank
        
        Args:
            sources: Liste der verwendeten Quellen
            success: Ob die Suche erfolgreich war
            model: Verwendetes Modell
        """
        try:
            from database import Source
            from urllib.parse import urlparse
            
            logger.info(f"[SOURCES TRACKING] Tracke {len(sources)} Sources für {model}")
            
            with self.db_manager.get_session() as session:
                for source in sources:
                    try:
                        # Extrahiere URL aus verschiedenen Source-Formaten
                        source_url = None
                        if isinstance(source, dict):
                            source_url = source.get('url') or source.get('value') or source.get('link')
                        elif isinstance(source, str):
                            source_url = source
                        
                        if not source_url or not source_url.startswith('http'):
                            continue
                        
                        # Normalisiere URL (entferne Query-Parameter)
                        try:
                            parsed = urlparse(source_url)
                            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                            domain = parsed.netloc
                        except:
                            continue
                        
                        # Finde oder erstelle Source in DB
                        db_source = session.query(Source).filter_by(url=base_url).first()
                        if not db_source:
                            # Versuche Domain-basierte Suche
                            db_source = session.query(Source).filter_by(domain=domain).first()
                        
                        if db_source:
                            # Aktualisiere Source-Statistiken
                            db_source.total_searches += 1
                            if success:
                                db_source.successful_searches += 1
                            db_source.last_attempted_access = datetime.now()
                            if success:
                                db_source.last_successful_access = datetime.now()
                            
                            logger.debug(f"[SOURCES TRACKING] Updated {domain}: {db_source.successful_searches}/{db_source.total_searches}")
                        else:
                            # Source nicht in DB gefunden - logge für Debugging
                            logger.debug(f"[SOURCES TRACKING] Source nicht in DB gefunden: {domain}")
                    
                    except Exception as e:
                        logger.warning(f"[SOURCES TRACKING] Fehler beim Tracken von Source: {e}")
                        continue
                
                session.commit()
                logger.info(f"[SOURCES TRACKING] Source-Tracking abgeschlossen für {model}")
                
        except Exception as e:
            logger.error(f"[SOURCES TRACKING] Fehler beim Sources-Tracking: {e}")


# Service-Instanz für Kompatibilität (DEPRECATED - use services_container)
from services_container import services
search_service = services.mine_search_service