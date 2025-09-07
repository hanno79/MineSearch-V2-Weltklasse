"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored MineSearchService (CLAUDE.md konform)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .fallback_detector import validate_data, clean_fallback_values

from minesearch.config.base import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.utils import (
    normalize_accents,
    generate_name_variants,
    generate_multilingual_search_terms,
    get_country_config,
)
from minesearch.data_extraction import DataExtractor, assign_sources_to_data
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.providers.base_provider import SearchResult
from minesearch.cache_service import get_cache_service, cached_search
# BEREINIGUNG 06.08.2025: Legacy import entfernt - Datei wurde nach to_delete/ verschoben
# from search_service_legacy import LegacySearchFunctions
from minesearch.cost_monitor import cost_monitor
from minesearch.database.manager import DatabaseManager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.field_value_parser import (
    extract_atomic_value_and_sources, 
    normalize_atomic_value, 
    find_or_create_source_by_url
)

logger = logging.getLogger(__name__)


class MineSearchService:
    """Hauptklasse für Mining-Suchen mit Provider-Unterstützung"""
    
    def __init__(self):
        # Provider-basierte Architektur
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
        # Database Manager für Persistierung (beide Versionen)
        self.db_manager = DatabaseManager()
        self.normalized_db_manager = NormalizedDatabaseManager()
        # Data Extractor für strukturierte Datenextraktion
        self.data_extractor = DataExtractor()
    
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
        
        # Cache-Check - WICHTIG: Cache bleibt deaktiviert für akkurate Testergebnisse
        # Jede Suche muss neu ausgeführt werden um verfälschte Ergebnisse zu vermeiden
        # cached_result = await self._check_cache(mine_name, country or "", full_model_id, commodity=commodity, region=region)
        # if cached_result:
        #     logger.info(f"[SEARCH] Cache-Hit für {mine_name} mit Model {full_model_id}")
        #     return cached_result
        logger.info(f"[SEARCH] Cache deaktiviert - jede Suche wird frisch ausgeführt für akkurate Ergebnisse")
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
            
            # Cache das Ergebnis - WICHTIG: Cache bleibt deaktiviert für akkurate Testergebnisse
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
            error_msg = f"Provider '{provider_name}' für Modell '{full_model_id}' ist nicht verfügbar oder nicht korrekt konfiguriert"
            logger.error(f"[PROVIDER ERROR] {error_msg}")
            
            # Prüfe spezifische Ursachen
            available_providers = list(self.registry._providers.keys())
            if provider_name not in available_providers:
                error_msg += f". Verfügbare Provider: {available_providers}"
            else:
                error_msg += ". Provider ist registriert, aber Initialisierung fehlgeschlagen (möglicherweise fehlerhafte API-Keys)"
            
            raise Exception(error_msg)
        
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
        
        # FIX 07.09.2025: Enhanced Source Discovery für ALLE Provider
        # Damit alle Provider dieselben umfangreichen Quellen nutzen (wie OpenRouter)
        logger.info(f"[SOURCE-DISCOVERY] Starte einheitliche Source Discovery für {mine_name}")
        try:
            discovered_sources = self.enhanced_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region
            )
            logger.info(f"[SOURCE-DISCOVERY] {len(discovered_sources)} Quellen für alle Provider bereitgestellt")
        except Exception as e:
            logger.warning(f"[SOURCE-DISCOVERY] Fehler bei Discovery: {e}")
            discovered_sources = []
        
        # Provider-Optionen (erweitert mit discovered_sources)
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': currency,
            'name_variants': name_variants,
            'multilingual_terms': multilingual_terms,
            'discovered_sources': discovered_sources,  # FIX: Alle Provider bekommen dieselben Quellen
            'use_all_sources': True  # Nutze alle verfügbaren Quellen
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
            error_msg = f"Provider '{provider_name}' für Modell '{legacy_full_model_id}' ist nicht verfügbar oder nicht korrekt konfiguriert"
            logger.error(f"[PROVIDER ERROR] {error_msg}")
            
            # Prüfe spezifische Ursachen
            available_providers = list(self.registry._providers.keys())
            if provider_name not in available_providers:
                error_msg += f". Verfügbare Provider: {available_providers}"
            else:
                error_msg += ". Provider ist registriert, aber Initialisierung fehlgeschlagen (möglicherweise fehlerhafte API-Keys)"
            
            raise Exception(error_msg)
        
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
        
        # ENHANCED VALIDATION 25.08.2025: Wende Quality Gate auch auf Legacy-Suche an
        clean_structured_data = self._apply_database_quality_gate(structured_data, mine_name)
        
        # Berechne Datenqualität
        quality_metrics = self._calculate_data_quality(clean_structured_data)
        
        # LEGACY DATABASE REMOVED 03.09.2025: Alle Legacy-DB-Operationen entfernt
        # Nur noch normalisierte DB wird in _process_search_result verwendet
        
        # Legacy async tasks removed with database removal
        logger.info(f"[LEGACY-CLEANUP] Legacy database operations removed - using only normalized DB")
        
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
        
        # CLEAN DATA AT SOURCE FIX 20.08.2025: QUALITY GATE VOR DATABASE-SPEICHERUNG
        # Letzte Verteidigungslinie gegen Template/Dummy-Werte in der Datenbank
        clean_structured_data = self._apply_database_quality_gate(structured_data, mine_name)
        
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
            
            # LEGACY DATABASE REMOVED 03.09.2025: Alle Legacy-DB-Operationen entfernt
            # Nur noch normalisierte DB wird verwendet
            
            # 🆕 NORMALISIERTES SYSTEM: Einzige Speicherung
            # Debug-Datei Logging
            # with open('./normalized_debug.log', 'a') as f:
                    #                 f.write(f"DEBUG: Normalized save attempt for {mine_name} with model {actual_model_used}\n")
            
            print(f"🔥🔥🔥 DEBUG: Normalized save attempt for {mine_name} with model {actual_model_used}")
            try:
                # with open('./normalized_debug.log', 'a') as f:
                    #                     f.write(f"DEBUG: Inside try block, calling save_search_result_normalized\n")
                logger.info(f"[DB NORMALIZED] Speichere normalisiert: {mine_name} → {actual_model_used}")
                print(f"🔥🔥🔥 DEBUG: Inside try block, calling save_search_result_normalized")
                normalized_result_id = self.normalized_db_manager.save_search_result_normalized(
                    mine_name=mine_name,
                    model_used=actual_model_used,
                    structured_data=clean_structured_data,
                    sources=sources,
                    session_id=None,
                    country=country,
                    search_duration=search_duration
                )
                # with open('./normalized_debug.log', 'a') as f:
                    #                     f.write(f"DEBUG: Normalized save SUCCESS! ID = {normalized_result_id}\n")
                print(f"🔥🔥🔥 DEBUG: Normalized save SUCCESS! ID = {normalized_result_id}")
                logger.info(f"✅ NORMALIZED SAVE SUCCESS: ID={normalized_result_id}")
            except Exception as norm_error:
                # with open('./normalized_debug.log', 'a') as f:
                #     f.write(f"DEBUG: Normalized save FAILED! Error = {norm_error}\n")
                import traceback
                #     f.write(f"DEBUG: Traceback = {traceback.format_exc()}\n")
                print(f"🔥🔥🔥 DEBUG: Normalized save FAILED! Error = {norm_error}")
                logger.error(f"❌ Normalized save failed: {norm_error}")
                logger.error(f"❌ Normalized save traceback:\n{traceback.format_exc()}")
                # Continue with legacy system if normalized fails
            
            # 🆕 SCHEMA-NORMALISIERUNG 28.08.2025: Atomische Feldwerte speichern (Legacy backup)
            try:
                await self._save_atomic_field_values(
                    search_result.id, 
                    clean_structured_data, 
                    sources,
                    result.metadata.get('structured_data_with_sources', {})
                )
                logger.info(f"✅ Atomische Feldwerte gespeichert für SearchResult ID={search_result.id}")
            except Exception as atomic_error:
                logger.error(f"❌ Atomic values save failed: {atomic_error}")
                # Continue with legacy system if atomic save fails
            
            # 🚀 PERFORMANCE FIX 02.09.2025: Async Model Statistics Update für bessere Performance
            try:
                from minesearch.async_db_tasks import async_db_tasks
                # Schedule async - blockiert nicht die Suche
                asyncio.create_task(async_db_tasks.schedule_stats_update(actual_model_used))
                logger.info(f"[ASYNC-STATS] Model statistics update scheduled for {actual_model_used}")
            except Exception as stats_error:
                logger.error(f"[ASYNC-STATS] Failed to schedule model statistics for {actual_model_used}: {stats_error}")
                # Don't fail the search if statistics update fails
            
            # 🚀 PERFORMANCE FIX 02.09.2025: Async Source Updates für bessere Performance
            try:
                from minesearch.async_db_tasks import async_db_tasks
                # Schedule async source updates - blockiert nicht die Suche
                asyncio.create_task(async_db_tasks.schedule_source_updates(sources, country))
                logger.info(f"[ASYNC-SOURCES] Source updates scheduled for {len(sources)} sources")
            except Exception as source_error:
                logger.error(f"[ASYNC-SOURCES] Failed to schedule source updates: {source_error}")
                    
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
            error_msg = f"Provider '{provider_name}' für Modell '{model}' ist nicht verfügbar oder nicht korrekt konfiguriert"
            logger.error(f"[PROVIDER ERROR] {error_msg}")
            
            # Prüfe spezifische Ursachen
            available_providers = list(self.registry._providers.keys())
            if provider_name not in available_providers:
                error_msg += f". Verfügbare Provider: {available_providers}"
            else:
                error_msg += ". Provider ist registriert, aber Initialisierung fehlgeschlagen (möglicherweise fehlerhafte API-Keys)"
            
            raise Exception(error_msg)
        
        model_name = model.split(':')[1] if ':' in model else model
        api_result = await provider.search(query, model_name, {})
        
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
    
    def _apply_database_quality_gate(self, structured_data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """
        ENHANCED DATA QUALITY GATE 25.08.2025: Umfassende Validierung vor Database-Speicherung
        
        Letzte Verteidigungslinie gegen Template/Dummy-Werte und Feldkontamination in der Datenbank.
        Verwendet sowohl Template-Detection als auch Feldnamen-Blacklist.
        
        Args:
            structured_data: Extrahierte strukturierte Daten
            mine_name: Mine-Name für Logging
            
        Returns:
            Bereinigte strukturierte Daten ohne Template/Dummy-Werte und Feldkontaminationen
        """
        if not structured_data:
            return structured_data
            
        logger.info(f"[ENHANCED DB QUALITY GATE] Starte umfassende Validierung für {mine_name}")
        
        # Importiere Validierungs-Module
        from minesearch.extraction_processors import is_template_or_dummy_value
        from minesearch.field_name_blacklist import is_field_name_value, validate_extracted_fields
        
        clean_data = {}
        rejected_fields = []
        accepted_fields = []
        field_contaminations = []
        
        for field, value in structured_data.items():
            # Skip meta fields
            if field.startswith('_') or field in ['sources']:
                clean_data[field] = value
                continue
            
            # Check if value is valid data
            if value and str(value).strip():
                value_str = str(value).strip()
                
                # PHASE 1: Template/Dummy-Wert-Detection (bestehende Logik)
                if is_template_or_dummy_value(value_str, field):
                    clean_data[field] = ""
                    rejected_fields.append((field, value_str[:50]))
                    logger.warning(f"[ENHANCED DB QUALITY GATE] Template/Dummy-Wert abgelehnt: {field} = '{value_str[:50]}...'")
                
                # PHASE 2: KRITISCHE FELDNAMEN-KONTAMINATION-DETECTION (25.08.2025)
                elif is_field_name_value(value_str, field):
                    clean_data[field] = ""  # NULL in DB
                    field_contaminations.append((field, value_str[:50]))
                    logger.error(f"[CRITICAL FIELD CONTAMINATION] Feldname als Wert blockiert: {field} = '{value_str[:50]}...'")
                
                else:
                    # Echter Datenwert → behalten
                    clean_data[field] = value
                    accepted_fields.append((field, value_str[:50]))
                    logger.debug(f"[ENHANCED DB QUALITY GATE] Echter Wert akzeptiert: {field} = '{value_str[:50]}...'")
            else:
                # Bereits leerer Wert → behalten
                clean_data[field] = value
        
        # PHASE 3: GESAMTVALIDIERUNG MIT FELDNAMEN-BLACKLIST (zusätzliche Sicherheitsebene)
        final_clean_data = validate_extracted_fields(clean_data)
        
        # Erweiterte Logging Summary
        logger.info(f"[ENHANCED DB QUALITY GATE] {mine_name} Validierungsresultat:")
        logger.info(f"  ✅ {len(accepted_fields)} echte Datenwerte akzeptiert")
        logger.info(f"  ⚠️ {len(rejected_fields)} Template/Dummy-Werte abgelehnt")
        logger.info(f"  🚨 {len(field_contaminations)} Feldkontaminationen blockiert")
        
        if field_contaminations:
            logger.error(f"[CRITICAL] Feldkontamination verhindert für {mine_name}:")
            for field, value in field_contaminations:
                logger.error(f"  🚨 {field}: '{value}...'")
        
        return final_clean_data
    
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
            from minesearch.database import Source
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
                        except ValueError as e:
                            logger.warning(f"[SOURCES TRACKING] Ungültige URL-Syntax: {source_url} - {e}")
                            continue
                        except AttributeError as e:
                            logger.warning(f"[SOURCES TRACKING] URL-Parsing-Fehler: {source_url} - {e}")
                            continue
                        except Exception as e:
                            logger.error(f"[SOURCES TRACKING] Unerwarteter URL-Fehler: {source_url} - {e}")
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


    def _build_search_query(self, mine_name: str, name_variants: List[str], 
                           country: Optional[str], currency: str, 
                           restoration_terms: List[str]) -> str:
        """
        Erstellt die Such-Query für Provider
        
        Args:
            mine_name: Name der Mine
            name_variants: Namensvarianten
            country: Land
            currency: Währung
            restoration_terms: Restaurationskostenbegriffe
            
        Returns:
            Such-Query String
        """
        location = f" in {country}" if country else ""
        variants_text = ", ".join(name_variants[:3])  # Limit auf 3 Varianten
        
        return f"""
        Find detailed mining information about "{mine_name}"{location}.
        Also search for variants: {variants_text}
        
        Required information:
        1. Mine location (GPS coordinates, region)
        2. Operating company/owner
        3. Commodity/mineral type
        4. Production data (annual output, reserves)
        5. Mine type (open-pit, underground, etc.)
        6. Activity status (active, planned, closed)
        7. Restoration/closure costs in {currency}
        8. Environmental data
        9. Employment numbers
        10. Technical specifications
        
        Provide specific, factual data only. Include sources and dates.
        """
    
    def _validate_result(self, content: str, mine_name: str, 
                        name_variants: List[str]) -> tuple:
        """
        Validiert Suchergebnis auf Relevanz
        
        Args:
            content: Suchinhalt
            mine_name: Mine-Name
            name_variants: Namensvarianten
            
        Returns:
            (is_valid, confidence_score)
        """
        if not content or len(content.strip()) < 50:
            return False, 0.0
        
        # Prüfe ob Mine-Name oder Varianten im Content vorkommen
        content_lower = content.lower()
        mine_name_lower = mine_name.lower()
        
        name_match = mine_name_lower in content_lower
        variant_matches = sum(1 for variant in name_variants 
                            if variant.lower() in content_lower)
        
        # Prüfe auf Mining-relevante Begriffe
        mining_terms = ['mine', 'mining', 'extraction', 'ore', 'mineral', 
                       'production', 'reserves', 'deposit']
        mining_matches = sum(1 for term in mining_terms 
                           if term in content_lower)
        
        # Berechne Confidence Score
        confidence = 0.0
        if name_match:
            confidence += 0.4
        confidence += min(variant_matches * 0.2, 0.3)
        confidence += min(mining_matches * 0.05, 0.3)
        
        is_valid = confidence >= 0.3  # Mindestens 30% Confidence
        
        return is_valid, confidence
    
    def _calculate_data_quality(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Berechnet Datenqualitäts-Metriken
        
        Args:
            structured_data: Strukturierte Daten
            
        Returns:
            Qualitäts-Metriken
        """
        if not structured_data:
            return {
                'completion_percentage': 0,
                'filled_fields': 0,
                'total_fields': len(CSV_COLUMNS),
                'quality_score': 0.0
            }
        
        # Zähle gefüllte Felder (nicht leer, nicht "k.A.", nicht None)
        filled_fields = 0
        for key, value in structured_data.items():
            if value and str(value).strip() and str(value).strip().lower() != 'k.a.':
                filled_fields += 1
        
        total_fields = len(CSV_COLUMNS)
        completion_percentage = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Qualitäts-Score basierend auf wichtigen Feldern
        important_fields = ['Mine Name', 'Country', 'Commodity', 'Betreiber', 'Aktivitätsstatus']
        important_filled = sum(1 for field in important_fields 
                             if structured_data.get(field) and 
                             str(structured_data[field]).strip() and 
                             str(structured_data[field]).strip().lower() != 'k.a.')
        
        quality_score = (important_filled / len(important_fields)) * 0.7 + \
                       (completion_percentage / 100) * 0.3
        
        return {
            'completion_percentage': completion_percentage,
            'filled_fields': filled_fields,
            'total_fields': total_fields,
            'quality_score': quality_score,
            'important_fields_filled': important_filled,
            'important_fields_total': len(important_fields)
        }
    
    async def _save_atomic_field_values(
        self, 
        search_result_id: int, 
        structured_data: Dict[str, Any], 
        sources: List[Dict],
        structured_data_with_sources: Dict[str, Any] = None
    ) -> None:
        """
        SCHEMA-NORMALISIERUNG 28.08.2025: Speichert atomische Feldwerte in neuen Tabellen
        
        Args:
            search_result_id: ID des SearchResult
            structured_data: Bereinigte strukturierte Daten  
            sources: Liste der Quellen
            structured_data_with_sources: Originaldaten mit [1,2,3] Referenzen
        """
        from minesearch.database.models import FieldValue, FieldValueSource
        
        # Verwende structured_data_with_sources wenn verfügbar, sonst structured_data
        data_to_parse = structured_data_with_sources or structured_data
        
        if not data_to_parse:
            logger.info(f"[ATOMIC] Keine Daten zu speichern für SearchResult {search_result_id}")
            return
        
        saved_count = 0
        skipped_count = 0
        
        with self.db_manager.get_session() as session:
            try:
                # Erstelle Mapping von Source-URLs zu Source-IDs
                source_url_to_id = {}
                for source_dict in sources:
                    source_url = source_dict.get('url')
                    if source_url:
                        source_obj = find_or_create_source_by_url(session, source_url)
                        if source_obj:
                            source_url_to_id[source_url] = source_obj.id
                
                # Verarbeite jedes Feld
                for field_name, field_value in data_to_parse.items():
                    if not field_value:
                        continue
                    
                    # Handle different data formats
                    if isinstance(field_value, dict):
                        # Newer format: {'value': 'Kanada', 'sources': [...]}
                        raw_value = field_value.get('value', '')
                        if isinstance(raw_value, str) and '[' in raw_value:
                            # Even dict format might have "Gold [1,2]" in value
                            atomic_value, source_refs = extract_atomic_value_and_sources(raw_value)
                        else:
                            atomic_value = raw_value
                            source_refs = field_value.get('sources', [])
                    elif isinstance(field_value, str):
                        # Legacy format: "Kanada [1,2,3]"
                        atomic_value, source_refs = extract_atomic_value_and_sources(field_value)
                    else:
                        # Direct value
                        atomic_value = str(field_value) if field_value else ''
                        source_refs = []
                    
                    # Normalisiere atomischen Wert
                    normalized_value = normalize_atomic_value(atomic_value)
                    
                    # Nur speichern wenn wir einen validen normalisierten Wert haben
                    if not normalized_value:
                        skipped_count += 1
                        continue
                    
                    # Erstelle FieldValue-Eintrag
                    field_value_obj = FieldValue(
                        search_result_id=search_result_id,
                        field_name=field_name,
                        atomic_value=normalized_value,
                        confidence_score=75.0  # Standard-Confidence für neue Werte
                    )
                    session.add(field_value_obj)
                    session.flush()  # Für ID-Generierung
                    
                    # Verknüpfe Quellen basierend auf Referenzen
                    if source_refs:
                        for ref_num in source_refs:
                            # Mappe Referenznummer zu Source-URL (vereinfacht)
                            # In der Realität könnte das komplexer sein
                            if ref_num <= len(sources):
                                source_url = sources[ref_num - 1].get('url')  # Array ist 0-basiert
                                source_id = source_url_to_id.get(source_url)
                                
                                if source_id:
                                    field_source = FieldValueSource(
                                        field_value_id=field_value_obj.id,
                                        source_id=source_id,
                                        extraction_confidence=75.0
                                    )
                                    session.add(field_source)
                    else:
                        # Keine spezifischen Quellenreferenzen - verknüpfe mit allen Quellen
                        for source_id in source_url_to_id.values():
                            field_source = FieldValueSource(
                                field_value_id=field_value_obj.id,
                                source_id=source_id,
                                extraction_confidence=50.0  # Niedrigere Confidence bei unspezifischen Zuordnungen
                            )
                            session.add(field_source)
                    
                    saved_count += 1
                
                session.commit()
                logger.info(f"[ATOMIC] ✅ {saved_count} atomische Feldwerte gespeichert, {skipped_count} übersprungen")
                
            except Exception as e:
                session.rollback()
                logger.error(f"[ATOMIC] ❌ Fehler beim Speichern atomischer Werte: {e}")
                raise


# Service-Instanz für Kompatibilität (DEPRECATED - use services_container)
from minesearch.services_container import services
search_service = services.mine_search_service