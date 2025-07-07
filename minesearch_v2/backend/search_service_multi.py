"""
Author: rahn
Datum: 02.07.2025  
Version: 1.0
Beschreibung: Multi-Provider Search Service für MineSearch
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from config import config, Config, SOURCE_SHARING_CONFIG
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config
from source_aggregator import SourceAggregator
from search_phases import SearchPhaseManager
from search_utils import SearchQueryBuilder, DataQualityCalculator, SourceCacheManager, ResultCombiner
from search_result_combiner import SearchResultCombiner
from search_async_utils import AsyncSearchUtils
from shared_sources_analyzer import SharedSourcesAnalyzer

logger = logging.getLogger(__name__)


class MultiProviderSearchService:
    """Service für Multi-Provider Mining-Suchen"""
    
    def __init__(self):
        # Initialisiere Provider Registry
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
        
        # Helper-Klassen initialisieren
        self.phase_manager = SearchPhaseManager()
        self.query_builder = SearchQueryBuilder()
        self.quality_calculator = DataQualityCalculator()
        self.cache_manager = SourceCacheManager()
        self.result_combiner = ResultCombiner()
        self.search_result_combiner = SearchResultCombiner()
        self.async_utils = AsyncSearchUtils()
        self.sources_analyzer = SharedSourcesAnalyzer(self.registry)
        
        # ÄNDERUNG 05.07.2025: Phase-Modelle für Two-Phase Search
        self.phase1_models = self.phase_manager.phase1_models
        self.phase2_models = self.phase_manager.phase2_models
        self.phase3_models = self.phase_manager.phase3_models
    
    async def search_with_model(self, model_id: str, mine_name: str, 
                               country: Optional[str] = None,
                               commodity: Optional[str] = None,
                               region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führe Suche mit einem spezifischen Modell durch
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Suchergebnis im Standard-Format
        """
        # Validiere Modell
        if not self.registry.is_model_available(model_id):
            return {
                "success": False,
                "error": f"Modell {model_id} nicht verfügbar",
                "data": {}
            }
        
        # Hole Provider und Modell-Config
        provider = self.registry.get_provider_for_model(model_id)
        model_config = self.registry.get_model_config(model_id)
        
        if not provider:
            return {
                "success": False,
                "error": f"Provider für {model_id} nicht gefunden",
                "data": {}
            }
        
        # Starte Source Discovery Session
        session = None
        try:
            session = self.enhanced_discovery.start_session(mine_name, country, region)
            if not session:
                logger.warning("[MULTI-SEARCH] Konnte keine Source Discovery Session starten")
        except Exception as e:
            logger.error(f"[MULTI-SEARCH] Fehler beim Start der Source Discovery Session: {e}")
        
        # ÄNDERUNG 04.07.2025: Source Discovery für ALLE Modelle durchführen
        # Auch OpenRouter-Modelle können von den Quellen-URLs profitieren
        discovered_sources = []
        if session:
            try:
                # Verwende die korrekte synchrone Methode (Session bereits gestartet)
                discovered_sources = self.enhanced_discovery.discover_sources_for_mine(
                    mine_name=mine_name, 
                    country=country, 
                    region=region,
                    commodity=commodity
                )
                logger.info(f"[MULTI-SEARCH] {len(discovered_sources)} Quellen für {mine_name} entdeckt")
            except Exception as e:
                logger.warning(f"[MULTI-SEARCH] Fehler bei Source Discovery: {str(e)}")
        
        # Erstelle Suchanfrage
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Basis-Query
        query = self.query_builder.build_search_query(
            mine_name, name_variants, multilingual_terms, 
            country, commodity, model_id, discovered_sources,
            model_config
        )
        
        # Provider-spezifische Optionen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': country_config.get('currency', 'USD'),
            'name_variants': name_variants,
            'multilingual_terms': multilingual_terms,  # ÄNDERUNG 04.07.2025: Füge multilingual terms hinzu
            'discovered_sources': discovered_sources
        }
        
        # Führe Suche durch
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            # Konvertiere Provider-Result in Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            # ÄNDERUNG 06.07.2025: Stelle sicher, dass das Ergebnis korrekt ist
            if not standard_result.get('success'):
                logger.warning(f"[MULTI-SEARCH] {model_id} gab keinen Erfolg zurück: {standard_result.get('error', 'Unbekannter Fehler')}")
            else:
                logger.info(f"[MULTI-SEARCH] {model_id} erfolgreich: {len(standard_result.get('data', {}))} Felder extrahiert")
            
            return standard_result
            
        except ValueError as e:
            logger.error(f"[MULTI-SEARCH] Model-ID Format-Fehler bei {model_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Ungültiges Model-ID Format: {model_id}",
                "data": {},
                "status": "error"
            }
        except AttributeError as e:
            logger.error(f"[MULTI-SEARCH] Provider-Methode fehlt bei {model_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Provider-Implementierungsfehler: {str(e)}",
                "data": {},
                "status": "error"
            }
        except Exception as e:
            logger.error(f"[MULTI-SEARCH] Unerwarteter Fehler bei {model_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}",
                "data": {},
                "status": "error"
            }
        finally:
            # Finalisiere Session
            if session:
                try:
                    self.enhanced_discovery.finalize_session()
                except Exception as e:
                    logger.error(f"[MULTI-SEARCH] Fehler beim Finalisieren der Session: {e}")
    
    async def search_with_multiple_models(self, model_ids: List[str], mine_name: str,
                                        country: Optional[str] = None,
                                        commodity: Optional[str] = None,
                                        region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führe Suche mit mehreren Modellen parallel durch
        
        Args:
            model_ids: Liste von Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Dict mit Ergebnissen pro Modell
        """
        # ÄNDERUNG 04.07.2025: Echte parallele Ausführung mit asyncio.gather
        # Erstelle Tasks für alle Modelle
        tasks = []
        model_ids_list = []
        for model_id in model_ids:
            task = self.search_with_model(model_id, mine_name, country, commodity, region)
            tasks.append(task)
            model_ids_list.append(model_id)
        
        # Führe alle Suchen WIRKLICH parallel aus
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verarbeite Ergebnisse
        results = {}
        for model_id, result in zip(model_ids_list, task_results):
            if isinstance(result, Exception):
                logger.error(f"[MULTI-SEARCH] Fehler bei {model_id}: {str(result)}")
                results[model_id] = {
                    "success": False,
                    "error": str(result),
                    "data": {}
                }
            else:
                results[model_id] = result
        
        return {
            "success": True,
            "mine_name": mine_name,
            "country": country,
            "models_searched": len(model_ids),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def search_two_phase(self, mine_name: str, country: Optional[str] = None,
                              commodity: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """
        ÄNDERUNG 04.07.2025: Optimierte Zwei-Phasen-Suche
        
        Phase 1: Schnelle Quellensuche mit günstigem Modell
        Phase 2: Detaillierte Datenextraktion mit Premium-Modellen
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Kombiniertes Ergebnis mit besten Daten
        """
        logger.info(f"[TWO-PHASE] Starte Zwei-Phasen-Suche für {mine_name}")
        
        # Phase 1: Schnelle Quellensuche
        logger.info("[TWO-PHASE] Phase 1: Quellensuche...")
        phase1_result = await self.search_with_model(
            self.phase_manager.phase1_models[0], 
            mine_name, 
            country, 
            commodity, 
            region
        )
        
        # Extrahiere gefundene Quellen aus Phase 1
        discovered_sources = []
        if phase1_result.get('success') and phase1_result.get('sources'):
            discovered_sources = phase1_result['sources']
            logger.info(f"[TWO-PHASE] Phase 1 abgeschlossen: {len(discovered_sources)} Quellen gefunden")
        else:
            logger.warning("[TWO-PHASE] Phase 1: Keine Quellen gefunden")
        
        # Phase 2: Detaillierte Suche mit Premium-Modellen
        logger.info("[TWO-PHASE] Phase 2: Detailsuche mit Premium-Modellen...")
        
        # Erstelle spezialisierte Query für Phase 2
        specialized_query = self.phase_manager.build_phase2_query(mine_name, country, region, commodity, discovered_sources)
        
        # Führe Phase 2 Suchen parallel aus
        phase2_tasks = []
        for model_id in self.phase_manager.phase2_models:
            if self.registry.is_model_available(model_id):
                task = self.async_utils.search_with_enhanced_query(
                    self.registry,
                    self._convert_to_standard_format,
                    model_id, 
                    mine_name, 
                    country, 
                    commodity, 
                    region,
                    specialized_query,
                    discovered_sources
                )
                phase2_tasks.append(task)
        
        phase2_results = await asyncio.gather(*phase2_tasks, return_exceptions=True)
        
        # Kombiniere Ergebnisse
        combined_data = self.result_combiner.combine_phase_results(phase1_result, phase2_results)
        
        # ÄNDERUNG 04.07.2025: Optionale Phase 3 mit Abacus AI für kritische Felder
        phase3_triggered = False
        if self.phase_manager.should_trigger_phase3(combined_data):
            logger.info("[TWO-PHASE] Phase 3: Ultra-Deep Research mit Abacus AI...")
            phase3_triggered = True
            
            # Erstelle spezielle Query für fehlende kritische Felder
            missing_fields_query = self.phase_manager.build_phase3_query(
                mine_name, country, region, commodity, 
                combined_data['best_data'], combined_data['all_sources']
            )
            
            # Phase 3 mit Abacus Deep Agent
            for model_id in self.phase_manager.phase3_models:
                if self.registry.is_model_available(model_id):
                    try:
                        phase3_result = await self.async_utils.search_with_enhanced_query(
                            self.registry,
                            self._convert_to_standard_format,
                            model_id, mine_name, country, commodity, region,
                            missing_fields_query, combined_data['all_sources']
                        )
                        
                        # Integriere Phase 3 Ergebnisse
                        if phase3_result.get('success'):
                            combined_data = self.result_combiner.integrate_phase3_results(
                                combined_data, phase3_result
                            )
                    except Exception as e:
                        logger.error(f"[TWO-PHASE] Phase 3 Fehler: {str(e)}")
        
        return {
            "success": True,
            "mine_name": mine_name,
            "country": country,
            "search_type": "two_phase" if not phase3_triggered else "three_phase",
            "phase1_sources": len(discovered_sources),
            "phase2_models": len(self.phase2_models),
            "phase3_triggered": phase3_triggered,
            "data": combined_data['best_data'],
            "confidence_scores": combined_data['confidence'],
            "sources": combined_data['all_sources'],
            "timestamp": datetime.now().isoformat()
        }
    
    
    
    
    
    
    
    
    def _convert_to_standard_format(self, provider_result: SearchResult, 
                                   model_id: str, mine_name: str,
                                   country: Optional[str]) -> Dict[str, Any]:
        """Konvertiere Provider-Result in Standard MineSearch Format"""
        
        # ÄNDERUNG 06.07.2025: Robustere Fehlerbehandlung
        if not provider_result.success:
            return {
                "success": False,
                "status": "error",
                "error": provider_result.error or "Provider gab keinen Erfolg zurück",
                "data": {},
                "sources": [],
                "model_id": model_id
            }
        
        # Stelle sicher, dass structured_data existiert
        structured_data = provider_result.structured_data or {}
        sources = provider_result.sources or []
        
        # Berechne Datenqualität
        try:
            data_quality = self.quality_calculator.calculate_data_quality(structured_data)
        except Exception as e:
            logger.warning(f"[CONVERT] Fehler bei Datenqualitäts-Berechnung: {e}")
            data_quality = {
                "score": 0,
                "filled_fields": len([v for v in structured_data.values() if v]),
                "total_fields": len(structured_data)
            }
        
        # ÄNDERUNG 06.07.2025: Einheitliche Struktur für alle Antworten
        return {
            "success": True,
            "status": "success",
            "data": structured_data,  # Direkt die strukturierten Daten
            "sources": sources,  # Quellen auf oberster Ebene
            "model_id": model_id,
            "mine_name": mine_name,
            "country": country,
            "filled_fields": len([v for v in structured_data.values() if v and str(v).strip()]),
            "metadata": {
                "content": provider_result.content[:1000] if provider_result.content else "",  # Begrenze Content-Größe
                "mine_name": mine_name,
                "structured_data_with_sources": provider_result.metadata.get('structured_data_with_sources', {}) if provider_result.metadata else {},
                "source_index": provider_result.metadata.get('source_index', {}) if provider_result.metadata else {},
                "source_summary": {
                    "urls": len([s for s in sources if s.get('type') == 'url']),
                    "documents": len([s for s in sources if s.get('type') == 'document']),
                    "organizations": len([s for s in sources if s.get('type') == 'organization']),
                    "total": len(sources)
                },
                "data_quality": data_quality,
                "search_metadata": {
                    "model_used": model_id,
                    "provider": provider_result.metadata.get('provider', model_id.split(':')[0]) if provider_result.metadata else model_id.split(':')[0],
                    "search_timestamp": datetime.now().isoformat(),
                    "search_duration": provider_result.search_duration or 0
                }
            }
        }
    
    
    async def search_with_source_sharing(self, model_ids: List[str], mine_name: str,
                                       country: Optional[str] = None,
                                       commodity: Optional[str] = None,
                                       region: Optional[str] = None) -> Dict[str, Any]:
        """
        ÄNDERUNG 05.07.2025: Cross-Provider Source Sharing Implementation
        
        Führt eine zweistufige Suche durch:
        1. Alle Provider sammeln Quellen
        2. Alle Provider analysieren ALLE gesammelten Quellen
        
        Args:
            model_ids: Liste von Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Dict mit kombinierten Ergebnissen und maximaler Abdeckung
        """
        logger.info(f"[SOURCE-SHARING] Starte Cross-Provider Suche für {mine_name} mit {len(model_ids)} Modellen")
        start_time = datetime.now()
        
        # ÄNDERUNG 05.07.2025: Performance-Optimierungen
        config = SOURCE_SHARING_CONFIG
        
        # Prüfe Cache für Quellen
        cache_key = self.cache_manager.generate_cache_key(mine_name, country, commodity, region)
        if config['cache_sources']:
            cached_sources = self.cache_manager.get_cached_sources(cache_key)
            if cached_sources:
                logger.info(f"[SOURCE-SHARING] Verwende {len(cached_sources)} gecachte Quellen")
                # Springe direkt zu Phase 2 mit gecachten Quellen
                return await self.async_utils.execute_phase2_with_sources(
                    cached_sources, model_ids, mine_name, country, commodity, region, start_time,
                    self, self.phase_manager, config
                )
        
        # Phase 1: Quellen-Sammlung
        logger.info("[SOURCE-SHARING] Phase 1: Sammle Quellen von allen Providern...")
        
        # ÄNDERUNG 05.07.2025: Batch-Processing für bessere Performance
        batch_size = config.get('batch_size', 5)
        phase1_results = []
        
        for i in range(0, len(model_ids), batch_size):
            batch = model_ids[i:i + batch_size]
            source_tasks = []
            
            for model_id in batch:
                # Verwende Timeout für Phase 1
                task = asyncio.create_task(
                    self.async_utils.search_with_timeout(
                        self.search_with_model,
                        model_id, mine_name, country, commodity, region,
                        timeout=config.get('phase1_timeout', 30)
                    )
                )
                source_tasks.append(task)
            
            # Führe Batch parallel aus
            batch_results = await asyncio.gather(*source_tasks, return_exceptions=True)
            phase1_results.extend(batch_results)
        
        # Aggregiere alle Quellen
        aggregator = SourceAggregator()
        all_sources = []
        successful_providers = []
        
        for model_id, result in zip(model_ids, phase1_results):
            if isinstance(result, Exception):
                logger.error(f"[SOURCE-SHARING] Fehler bei {model_id} in Phase 1: {str(result)}")
                continue
                
            if result.get('success') and result.get('sources'):
                sources = result['sources']
                logger.info(f"[SOURCE-SHARING] {model_id} lieferte {len(sources)} Quellen")
                all_sources.extend(sources)
                successful_providers.append(model_id)
                
                # Sammle auch bereits gefundene Daten
                aggregator.add_provider_result(model_id, result)
        
        # Dedupliziere und ranke Quellen
        unique_sources = aggregator.deduplicate_sources(all_sources)
        
        # ÄNDERUNG 05.07.2025: Limitiere Gesamtanzahl Quellen
        max_sources = config.get('max_total_sources', 30)
        if len(unique_sources) > max_sources:
            unique_sources = unique_sources[:max_sources]
            logger.info(f"[SOURCE-SHARING] Limitiere auf Top {max_sources} Quellen")
        
        logger.info(f"[SOURCE-SHARING] {len(all_sources)} Gesamt-Quellen -> {len(unique_sources)} unique Quellen")
        
        # Cache die Quellen für zukünftige Anfragen
        if config['cache_sources']:
            self.cache_manager.cache_sources(cache_key, unique_sources, config.get('source_cache_ttl', 21600))
        
        # Wenn keine Quellen gefunden, gib Phase 1 Ergebnisse zurück
        if not unique_sources:
            logger.warning("[SOURCE-SHARING] Keine Quellen gefunden, überspringe Phase 2")
            return self.search_result_combiner.combine_source_sharing_results(phase1_results, model_ids, [], start_time)
        
        # Phase 2: Cross-Provider-Analyse
        logger.info("[SOURCE-SHARING] Phase 2: Alle Provider analysieren alle Quellen...")
        
        # Erstelle erweiterte Query mit allen Quellen
        enhanced_query = self.phase_manager.build_source_sharing_query(mine_name, country, region, commodity, unique_sources)
        
        # Erstelle Tasks für Phase 2
        phase2_tasks = []
        for model_id in successful_providers:
            task = self.sources_analyzer.analyze_with_shared_sources(
                model_id, mine_name, country, commodity, region, 
                enhanced_query, unique_sources,
                self._convert_to_standard_format
            )
            phase2_tasks.append(task)
        
        # Führe Phase 2 parallel aus
        phase2_results = await asyncio.gather(*phase2_tasks, return_exceptions=True)
        
        # Kombiniere alle Ergebnisse
        combined_result = self.search_result_combiner.combine_source_sharing_results(
            phase1_results, model_ids, phase2_results, start_time, unique_sources
        )
        
        logger.info(f"[SOURCE-SHARING] Abgeschlossen. Gesamtdauer: {(datetime.now() - start_time).total_seconds():.1f}s")
        
        return combined_result
    
    async def search_direct(self, model_id: str, mine_name: str,
                          country: Optional[str] = None,
                          commodity: Optional[str] = None,
                          region: Optional[str] = None,
                          focus: str = "financial") -> Dict[str, Any]:
        """
        ÄNDERUNG 06.07.2025: Vereinfachte direkte Suche mit Fokus auf Finanzdaten
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            focus: Suchfokus ("financial", "technical", "general")
            
        Returns:
            Suchergebnis mit extrahierten Daten
        """
        provider = self.registry.get_provider_for_model(model_id)
        if not provider:
            return {
                "success": False,
                "error": f"Provider für {model_id} nicht gefunden",
                "data": {}
            }
        
        # Fokussierte Query basierend auf Suchtyp
        if focus == "financial":
            query = f"""Finde detaillierte FINANZDATEN für {mine_name} Mine in {country or 'unbekannt'}:
            
PRIORITÄT 1 - Restaurationskosten:
- Closure costs / Reclamation costs / ARO (Asset Retirement Obligation)
- Rehabilitation costs / Restoration provisions
- Suche nach Beträgen in CAD, USD mit Jahr

PRIORITÄT 2 - Finanzielle Kennzahlen:
- Marktkapitalisierung / Market cap
- Jahresumsatz / Annual revenue
- Investitionssumme / Capital expenditure
- EBITDA / Cashflow

PRIORITÄT 3 - Reserven:
- Gold/Mineral reserves (in Unzen/Tonnen)
- Ressourcen / Resources
- Mine life / Lebensdauer

Gib konkrete Zahlen mit Währung und Jahr an."""
        else:
            # Standard-Query
            query = f"Finde detaillierte Informationen über {mine_name} Mine"
            if country:
                query += f" in {country}"
            if commodity:
                query += f", die {commodity} abbaut"
        
        try:
            # Direkte Suche ohne komplexe Transformationen
            provider_name, model_key = model_id.split(':')
            
            # Minimale Optionen
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'temperature': 0.1,  # Niedrig für präzise Daten
                'focus': focus
            }
            
            # Führe Suche aus
            start_time = datetime.now()
            result = await provider.search(query, model_key, options)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Direkte Rückgabe mit minimaler Transformation
            if result.success:
                return {
                    "success": True,
                    "status": "success",
                    "data": result.structured_data,
                    "sources": result.sources,
                    "model_id": model_id,
                    "duration": duration,
                    "filled_fields": len([v for v in result.structured_data.values() if v and str(v).strip()]),
                    "focus": focus
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "error": result.error or "Suche fehlgeschlagen",
                    "data": {},
                    "model_id": model_id,
                    "duration": duration
                }
                
        except Exception as e:
            logger.error(f"[SEARCH-DIRECT] Fehler bei {model_id}: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "data": {},
                "model_id": model_id
            }
    
    async def _analyze_with_shared_sources(self, model_id: str, mine_name: str,
                                          country: str, commodity: str, region: str,
                                          enhanced_query: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        Analysiere mit geteilten Quellen aus anderen Providern
        
        Args:
            model_id: Modell-ID
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff
            region: Region
            enhanced_query: Erweiterte Query mit Quellen-Informationen
            sources: Liste von Quellen aus Phase 1
            
        Returns:
            Suchergebnis
        """
        provider = self.registry.get_provider_for_model(model_id)
        if not provider:
            return {
                "success": False,
                "error": f"Provider für {model_id} nicht gefunden",
                "data": {}
            }
        
        # Erweiterte Optionen mit geteilten Quellen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'shared_sources': sources,
            'focus': 'restoration_costs',  # Fokus auf Restaurationskosten
            'temperature': 0.1  # Niedrige Temperature für präzise Extraktion
        }
        
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(enhanced_query, model_key, options)
            
            # Konvertiere und annotiere mit Source-Sharing Info
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            standard_result['source_sharing_used'] = True
            standard_result['shared_sources_count'] = len(sources)
            
            return standard_result
            
        except Exception as e:
            logger.error(f"[SOURCE-SHARING] Fehler bei {model_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "source_sharing_used": True
            }


# Globale Service-Instanz
multi_search_service = MultiProviderSearchService()