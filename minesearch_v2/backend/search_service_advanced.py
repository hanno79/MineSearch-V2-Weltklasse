"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Erweiterte Such-Funktionen für Multi-Provider Search Service
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from search_service_operations import SearchServiceOperations
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config

logger = logging.getLogger(__name__)


class SearchServiceAdvanced(SearchServiceOperations):
    """Erweiterte Such-Funktionen für den Multi-Provider Search Service"""
    
    async def search_two_phase(self, mine_name: str, country: Optional[str] = None,
                              commodity: Optional[str] = None, 
                              region: Optional[str] = None) -> Dict[str, Any]:
        """
        Zwei-Phasen Suche: Erst Quellensammlung, dann Datenextraktion
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Kombiniertes Suchergebnis aus beiden Phasen
        """
        logger.info(f"[ADVANCED] Starte Two-Phase Search für {mine_name}")
        
        # PHASE 1: Source Discovery mit allen verfügbaren Modellen
        logger.info(f"[ADVANCED] Phase 1: Quellensammlung mit {len(self.phase1_models)} Modellen")
        
        phase1_tasks = [
            self._search_for_sources(model_id, mine_name, country, commodity, region)
            for model_id in self.phase1_models
        ]
        
        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)
        
        # Sammle alle Quellen aus Phase 1
        all_sources = []
        successful_phase1 = 0
        
        for i, result in enumerate(phase1_results):
            if isinstance(result, Exception):
                logger.warning(f"[ADVANCED] Phase 1 Modell {self.phase1_models[i]} fehlgeschlagen: {result}")
                continue
                
            if result.get('success') and result.get('data', {}).get('sources'):
                sources = result['data']['sources']
                all_sources.extend(sources)
                successful_phase1 += 1
                logger.debug(f"[ADVANCED] {self.phase1_models[i]} fand {len(sources)} Quellen")
        
        # Dedupliziere Quellen
        unique_sources = self._deduplicate_sources(all_sources)
        logger.info(f"[ADVANCED] Phase 1 abgeschlossen: {len(unique_sources)} einzigartige Quellen aus {len(all_sources)} gefunden")
        
        if not unique_sources:
            logger.warning(f"[ADVANCED] Keine Quellen in Phase 1 gefunden - verwende Standard-Suche")
            return await self.search_with_multiple_models(self.phase2_models[:5], mine_name, country, commodity, region)
        
        # PHASE 2: Datenextraktion mit den besten Modellen
        logger.info(f"[ADVANCED] Phase 2: Datenextraktion mit {len(self.phase2_models)} Modellen und {len(unique_sources)} Quellen")
        
        phase2_tasks = [
            self._analyze_with_shared_sources(model_id, mine_name, unique_sources, country, commodity, region)
            for model_id in self.phase2_models
        ]
        
        phase2_results = await asyncio.gather(*phase2_tasks, return_exceptions=True)
        
        # Verarbeite Phase 2 Ergebnisse
        successful_results = []
        failed_models = []
        
        for i, result in enumerate(phase2_results):
            if isinstance(result, Exception):
                failed_models.append({
                    "model_id": self.phase2_models[i],
                    "error": str(result)
                })
                continue
                
            if result.get('success'):
                successful_results.append(result)
            else:
                failed_models.append(result)
        
        # Kombiniere Ergebnisse
        if successful_results:
            combined_result = self.search_result_combiner.combine_results(successful_results)
            combined_result.update({
                'search_strategy': 'two_phase',
                'phase1_models': len(self.phase1_models),
                'phase1_successful': successful_phase1,
                'phase2_models': len(self.phase2_models),
                'phase2_successful': len(successful_results),
                'total_sources_found': len(unique_sources),
                'failed_models': failed_models
            })
            
            logger.info(f"[ADVANCED] Two-Phase Search erfolgreich: {len(successful_results)} Modelle")
        else:
            combined_result = {
                'success': False,
                'error': 'Alle Phase 2 Modelle fehlgeschlagen',
                'search_strategy': 'two_phase',
                'phase1_successful': successful_phase1,
                'phase2_successful': 0,
                'failed_models': failed_models,
                'data': {}
            }
            
            logger.warning(f"[ADVANCED] Two-Phase Search fehlgeschlagen: Alle Phase 2 Modelle versagten")
        
        return combined_result
    
    async def search_with_source_sharing(self, model_ids: List[str], mine_name: str,
                                       country: Optional[str] = None,
                                       commodity: Optional[str] = None,
                                       region: Optional[str] = None) -> Dict[str, Any]:
        """
        Suche mit Source-Sharing zwischen Modellen
        
        Args:
            model_ids: Liste der Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Kombiniertes Suchergebnis mit geteilten Quellen
        """
        logger.info(f"[ADVANCED] Starte Source-Sharing Search mit {len(model_ids)} Modellen für {mine_name}")
        
        # Erste Phase: Quellensammlung mit wenigen Modellen
        source_discovery_models = model_ids[:3]  # Nur erste 3 für Source Discovery
        
        logger.info(f"[ADVANCED] Quellensammlung mit {len(source_discovery_models)} Modellen")
        source_tasks = [
            self._search_for_sources(model_id, mine_name, country, commodity, region)
            for model_id in source_discovery_models
        ]
        
        source_results = await asyncio.gather(*source_tasks, return_exceptions=True)
        
        # Sammle und dedupliziere Quellen
        shared_sources = []
        for result in source_results:
            if isinstance(result, dict) and result.get('success') and result.get('data', {}).get('sources'):
                shared_sources.extend(result['data']['sources'])
        
        unique_shared_sources = self._deduplicate_sources(shared_sources)
        logger.info(f"[ADVANCED] {len(unique_shared_sources)} einzigartige Quellen für Sharing gesammelt")
        
        # Zweite Phase: Alle Modelle mit geteilten Quellen
        logger.info(f"[ADVANCED] Datenextraktion mit allen {len(model_ids)} Modellen")
        extraction_tasks = [
            self._analyze_with_shared_sources(model_id, mine_name, unique_shared_sources, country, commodity, region)
            for model_id in model_ids
        ]
        
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        # Verarbeite Ergebnisse
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(extraction_results):
            if isinstance(result, Exception):
                failed_results.append({
                    "model_id": model_ids[i],
                    "error": str(result)
                })
            elif result.get('success'):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        # Kombiniere Ergebnisse
        if successful_results:
            combined_result = self.search_result_combiner.combine_results(successful_results)
            combined_result.update({
                'search_strategy': 'source_sharing',
                'shared_sources_count': len(unique_shared_sources),
                'successful_models': len(successful_results),
                'total_models': len(model_ids),
                'failed_models': failed_results
            })
        else:
            combined_result = {
                'success': False,
                'error': 'Alle Modelle mit Source-Sharing fehlgeschlagen',
                'search_strategy': 'source_sharing',
                'failed_models': failed_results,
                'data': {}
            }
        
        logger.info(f"[ADVANCED] Source-Sharing Search abgeschlossen: {len(successful_results)}/{len(model_ids)} erfolgreich")
        return combined_result
    
    async def _search_for_sources(self, model_id: str, mine_name: str,
                                country: Optional[str] = None,
                                commodity: Optional[str] = None,
                                region: Optional[str] = None) -> Dict[str, Any]:
        """
        Suche spezifisch nach Quellen mit einem Modell
        
        Args:
            model_id: Modell-ID
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Suchergebnis mit Fokus auf Quellen
        """
        try:
            # Validiere Modell
            if not self.registry.is_model_available(model_id):
                return {
                    "success": False,
                    "error": f"Modell {model_id} nicht verfügbar",
                    "data": {}
                }
            
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {
                    "success": False,
                    "error": f"Provider für {model_id} nicht gefunden",
                    "data": {}
                }
            
            # Bereite Suchkontext vor
            context = await self.prepare_search_context(mine_name, country, region, commodity)
            
            # Erstelle Source-Discovery-Query
            from specialized_prompts import get_source_discovery_prompt
            source_query = get_source_discovery_prompt(
                mine_name, context['name_variants'], country, commodity
            )
            
            # Provider-spezifische Optionen für Source Discovery
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'search_focus': 'sources',
                'name_variants': context['name_variants'],
                'multilingual_terms': context['multilingual_terms']
            }
            
            # Führe Source-Discovery durch
            provider_name, model_key = model_id.split(':')
            result = await provider.search(source_query, model_key, options)
            
            # Konvertiere zu Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            if standard_result.get('success'):
                logger.debug(f"[ADVANCED] Source Discovery {model_id} erfolgreich")
            else:
                logger.debug(f"[ADVANCED] Source Discovery {model_id} fehlgeschlagen: {standard_result.get('error')}")
            
            return standard_result
            
        except Exception as e:
            logger.error(f"[ADVANCED] Fehler bei Source Discovery {model_id}: {e}")
            return {
                "success": False,
                "error": f"Source Discovery Fehler: {str(e)}",
                "data": {}
            }
    
    async def _analyze_with_shared_sources(self, model_id: str, mine_name: str, shared_sources: List[Dict],
                                         country: Optional[str] = None,
                                         commodity: Optional[str] = None,
                                         region: Optional[str] = None) -> Dict[str, Any]:
        """
        Analysiere mit geteilten Quellen
        
        Args:
            model_id: Modell-ID
            mine_name: Name der Mine
            shared_sources: Liste geteilter Quellen
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Analyseergebnis
        """
        try:
            # Validiere Modell
            if not self.registry.is_model_available(model_id):
                return {
                    "success": False,
                    "error": f"Modell {model_id} nicht verfügbar",
                    "data": {}
                }
            
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {
                    "success": False,
                    "error": f"Provider für {model_id} nicht gefunden",
                    "data": {}
                }
            
            # Bereite Basis-Kontext vor
            name_variants = generate_name_variants(mine_name)
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)
            
            # Erstelle Comprehensive Extraction Query
            from specialized_prompts import get_comprehensive_extraction_prompt
            extraction_query = get_comprehensive_extraction_prompt(
                mine_name, name_variants, country, commodity, shared_sources
            )
            
            # Provider-spezifische Optionen
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'currency': country_config.get('currency', 'USD'),
                'name_variants': name_variants,
                'multilingual_terms': multilingual_terms,
                'discovered_sources': shared_sources,
                'sources': shared_sources,
                'search_focus': 'comprehensive_extraction'
            }
            
            # Führe Analyse durch
            provider_name, model_key = model_id.split(':')
            result = await provider.search(extraction_query, model_key, options)
            
            # Konvertiere zu Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            if standard_result.get('success'):
                data = standard_result.get('data', {})
                structured_data = data.get('structured_data', {})
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
                logger.debug(f"[ADVANCED] Shared Sources Analyse {model_id}: {filled_fields} Felder")
                
                # Verfolge verwendete Quellen
                result_sources = data.get('sources', [])
                await self._track_used_sources(result_sources, shared_sources)
            else:
                logger.debug(f"[ADVANCED] Shared Sources Analyse {model_id} fehlgeschlagen: {standard_result.get('error')}")
            
            return standard_result
            
        except Exception as e:
            logger.error(f"[ADVANCED] Fehler bei Shared Sources Analyse {model_id}: {e}")
            return {
                "success": False,
                "error": f"Shared Sources Analyse Fehler: {str(e)}",
                "data": {}
            }
    
    def _deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Entferne Duplikate aus Quellenliste
        
        Args:
            sources: Liste der Quellen
            
        Returns:
            Deduplizierte Quellenliste
        """
        try:
            if not sources:
                return []
            
            seen_urls = set()
            unique_sources = []
            
            for source in sources:
                if not isinstance(source, dict):
                    continue
                
                url = source.get('url', '').strip()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(source)
            
            return unique_sources
            
        except Exception as e:
            logger.error(f"[ADVANCED] Fehler bei Source-Deduplizierung: {e}")
            return sources  # Gebe Original-Liste zurück bei Fehler