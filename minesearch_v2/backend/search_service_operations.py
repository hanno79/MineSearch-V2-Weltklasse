"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Such-Operationen für Multi-Provider Search Service
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from search_service_core import SearchServiceCore
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config

logger = logging.getLogger(__name__)


class SearchServiceOperations(SearchServiceCore):
    """Such-Operationen für den Multi-Provider Search Service"""
    
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
        
        # Bereite Suchkontext vor
        context = await self.prepare_search_context(mine_name, country, region, commodity)
        
        # Erstelle Suchanfrage
        query = self.query_builder.build_search_query(
            mine_name, context['name_variants'], context['multilingual_terms'], 
            country, commodity, model_id, context['discovered_sources'],
            model_config
        )
        
        # Provider-spezifische Optionen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': context['country_config'].get('currency', 'USD'),
            'name_variants': context['name_variants'],
            'multilingual_terms': context['multilingual_terms'],
            'discovered_sources': context['discovered_sources'],
            'sources': context['discovered_sources']
        }
        
        # Führe Suche durch
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            # Konvertiere Provider-Result in Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            if not standard_result.get('success'):
                logger.warning(f"[OPERATIONS] {model_id} gab keinen Erfolg zurück: {standard_result.get('error', 'Unbekannter Fehler')}")
                await self._capture_error_stats(model_id, mine_name, standard_result.get('error', 'Unbekannter Fehler'))
            else:
                # Detailliertes Logging für erfolgreiche Suchen
                data = standard_result.get('data', {})
                structured_data = data.get('structured_data', {}) if isinstance(data, dict) else {}
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
                logger.info(f"[OPERATIONS] {model_id} erfolgreich: {filled_fields} Felder extrahiert")
                
                if filled_fields > 0:
                    filled_field_names = [k for k, v in structured_data.items() if v and str(v).strip()]
                    logger.debug(f"[OPERATIONS] {model_id} gefüllte Felder: {filled_field_names[:10]}")
                
                # Erfasse Statistiken für normale Suchen
                await self._capture_stats(model_id, mine_name, filled_fields, structured_data)
                
                # Verfolge verwendete Quellen
                result_sources = data.get('sources', [])
                await self._track_used_sources(result_sources, context['discovered_sources'])
            
            return standard_result
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout bei {model_id}"
            logger.error(f"[OPERATIONS] {error_msg}")
            await self._capture_error_stats(model_id, mine_name, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
        except Exception as e:
            error_msg = f"Fehler bei {model_id}: {str(e)}"
            logger.error(f"[OPERATIONS] {error_msg}")
            await self._capture_error_stats(model_id, mine_name, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
    
    async def search_with_multiple_models(self, model_ids: List[str], mine_name: str,
                                        country: Optional[str] = None,
                                        commodity: Optional[str] = None,
                                        region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führe parallele Suche mit mehreren Modellen durch
        
        Args:
            model_ids: Liste der Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Aggregierte Suchergebnisse
        """
        logger.info(f"[OPERATIONS] Starte parallele Suche mit {len(model_ids)} Modellen für {mine_name}")
        
        # Erstelle Tasks für parallele Ausführung
        tasks = [
            self.search_with_model(model_id, mine_name, country, commodity, region)
            for model_id in model_ids
        ]
        
        # Führe alle Suchen parallel aus
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verarbeite Ergebnisse
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "model_id": model_ids[i],
                    "error": str(result)
                })
            elif result.get('success'):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        # FIXED 15.07.2025: Gebe Ergebnisse im Batch-kompatiblen Format zurück
        # Erstelle ein Dictionary mit einzelnen Modell-Ergebnissen für die Batch-Verarbeitung
        results_dict = {}
        
        # FIXED 15.07.2025: Korrigiere Feldname - verwende 'model_id' statt 'model_used'
        for result in successful_results:
            if 'model_id' in result:
                model_id = result['model_id']
                results_dict[model_id] = result
            elif 'model_used' in result:
                # Fallback für mögliche Legacy-Formate
                model_id = result['model_used']
                results_dict[model_id] = result
        
        # Füge fehlgeschlagene Ergebnisse hinzu
        for failed in failed_results:
            if 'model_id' in failed:
                model_id = failed['model_id']
                results_dict[model_id] = {
                    'success': False,
                    'error': failed.get('error', 'Unknown error'),
                    'data': {}
                }
        
        # ENHANCED 15.07.2025: Validiere results_dict vor Rückgabe
        logger.info(f"[OPERATIONS] Results dict enthält {len(results_dict)} Modell-Ergebnisse")
        for model_id, result in results_dict.items():
            success = result.get('success', False)
            has_data = bool(result.get('data', {}))
            logger.info(f"[OPERATIONS] {model_id}: success={success}, has_data={has_data}")
            
            # Detaillierte Struktur-Validierung
            if success and has_data:
                data = result.get('data', {})
                structured_data = data.get('structured_data', {})
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
                logger.info(f"[OPERATIONS] {model_id}: {filled_fields} gefüllte Felder in structured_data")
            
        # Erstelle das finale Ergebnis im erwarteten Format
        combined_result = {
            'success': len(successful_results) > 0,
            'mine_name': mine_name,
            'country': country,
            'models_searched': model_ids,
            'results': results_dict,
            'failed_models': failed_results,
            'total_models': len(model_ids),
            'successful_models': len(successful_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # Füge auch aggregierte Daten hinzu (für Rückwärtskompatibilität)
        if successful_results:
            combined_result['data'] = successful_results[0].get('data', {})
        else:
            combined_result['data'] = {}
            combined_result['error'] = 'Alle Modelle fehlgeschlagen'
        
        logger.info(f"[OPERATIONS] Parallele Suche abgeschlossen: {len(successful_results)}/{len(model_ids)} erfolgreich")
        return combined_result
    
    async def search_direct(self, model_id: str, mine_name: str,
                          country: Optional[str] = None,
                          commodity: Optional[str] = None,
                          region: Optional[str] = None) -> Dict[str, Any]:
        """
        Direkter Single-Model Search ohne Shared Sources
        
        Args:
            model_id: Modell-ID
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Suchergebnis
        """
        logger.info(f"[OPERATIONS] Starte direkte Suche mit {model_id} für {mine_name}")
        
        # Validiere Modell
        if not self.registry.is_model_available(model_id):
            return {
                "success": False,
                "error": f"Modell {model_id} nicht verfügbar",
                "data": {}
            }
        
        # Hole Provider
        provider = self.registry.get_provider_for_model(model_id)
        if not provider:
            return {
                "success": False,
                "error": f"Provider für {model_id} nicht gefunden",
                "data": {}
            }
        
        # Bereite einfachen Suchkontext vor (ohne Source Discovery)
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Erstelle direkte Suchanfrage
        query = self.query_builder.build_search_query(
            mine_name, name_variants, multilingual_terms, 
            country, commodity, model_id, [],  # Keine discovered sources
            {}  # Keine model config
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
            'discovered_sources': [],
            'sources': []
        }
        
        # Führe direkte Suche durch
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            # Konvertiere zu Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            if standard_result.get('success'):
                data = standard_result.get('data', {})
                structured_data = data.get('structured_data', {})
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
                logger.info(f"[OPERATIONS] Direkte Suche {model_id} erfolgreich: {filled_fields} Felder")
            else:
                logger.warning(f"[OPERATIONS] Direkte Suche {model_id} fehlgeschlagen: {standard_result.get('error')}")
            
            return standard_result
            
        except Exception as e:
            error_msg = f"Fehler bei direkter Suche {model_id}: {str(e)}"
            logger.error(f"[OPERATIONS] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
    
    async def _capture_stats(self, model_id: str, mine_name: str, filled_fields: int, structured_data: Dict):
        """Erfasse Statistiken für erfolgreiche Suchen (Fire-and-forget)"""
        try:
            import aiohttp
            import json
            
            stats_data = {
                'model_id': model_id,
                'mine_name': mine_name,
                'filled_fields': filled_fields,
                'timestamp': datetime.now().isoformat(),
                'search_type': 'single_model',
                'field_names': list(structured_data.keys()) if structured_data else []
            }
            
            # Fire-and-forget HTTP Request
            async def capture_stats():
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.post(
                            'http://localhost:8000/api/benchmark/capture',
                            json=stats_data,
                            headers={'Content-Type': 'application/json'}
                        ) as response:
                            if response.status == 200:
                                logger.debug(f"[OPERATIONS] Statistiken für {model_id} erfasst")
                            else:
                                logger.debug(f"[OPERATIONS] Fehler beim Erfassen der Statistiken: {response.status}")
                except Exception as e:
                    logger.debug(f"[OPERATIONS] Statistik-Erfassung fehlgeschlagen: {e}")
            
            # Fire-and-forget
            asyncio.create_task(capture_stats())
            
        except Exception as e:
            logger.debug(f"[OPERATIONS] Fehler bei Statistik-Vorbereitung: {e}")
    
    async def _capture_error_stats(self, model_id: str, mine_name: str, error_msg: str):
        """Erfasse Fehler-Statistiken (Fire-and-forget)"""
        try:
            import aiohttp
            import json
            
            error_data = {
                'model_id': model_id,
                'mine_name': mine_name,
                'error_message': error_msg,
                'timestamp': datetime.now().isoformat(),
                'search_type': 'single_model'
            }
            
            async def capture_error_stats():
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.post(
                            'http://localhost:8000/api/benchmark/capture',
                            json=error_data,
                            headers={'Content-Type': 'application/json'}
                        ) as response:
                            if response.status == 200:
                                logger.debug(f"[OPERATIONS] Fehler-Statistiken für {model_id} erfasst")
                except Exception as e:
                    logger.debug(f"[OPERATIONS] Fehler-Statistik-Erfassung fehlgeschlagen: {e}")
            
            # Fire-and-forget
            asyncio.create_task(capture_error_stats())
            
        except Exception as e:
            logger.debug(f"[OPERATIONS] Fehler bei Fehler-Statistik-Vorbereitung: {e}")