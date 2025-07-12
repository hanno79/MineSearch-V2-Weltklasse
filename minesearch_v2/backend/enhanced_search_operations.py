"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Such-Operationen für Enhanced Multi-Provider Search Service
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from enhanced_search_core import EnhancedSearchCore

logger = logging.getLogger(__name__)


class EnhancedSearchOperations(EnhancedSearchCore):
    """Such-Operationen für Enhanced Multi-Provider Search Service"""
    
    async def search_single_model(self, model_id: str, mine_name: str, 
                                country: Optional[str] = None,
                                commodity: Optional[str] = None,
                                region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führt erweiterte Suche mit einem spezifischen Modell durch
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Erweiterte Suchergebnisse
        """
        start_time = datetime.now()
        
        try:
            # Validiere Modell
            if not self.registry.is_model_available(model_id):
                return {
                    "success": False,
                    "error": f"Modell {model_id} nicht verfügbar",
                    "data": {}
                }
            
            # Bereite Suchkontext vor
            context = await self.prepare_search_context(mine_name, country, region, commodity)
            
            # Hole Provider
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {
                    "success": False,
                    "error": f"Provider für {model_id} nicht gefunden",
                    "data": {}
                }
            
            # Erstelle erweiterte Suchanfrage
            query = self.query_builder.build_search_query(
                mine_name, context['name_variants'], context['multilingual_terms'],
                country, commodity, model_id, context['discovered_sources'],
                {}  # Model config wird vom Provider gehandhabt
            )
            
            # Provider-Optionen
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'currency': context['country_config'].get('currency', 'USD'),
                'name_variants': context['name_variants'],
                'multilingual_terms': context['multilingual_terms'],
                'discovered_sources': context['discovered_sources'],
                'sources': context['discovered_sources'],
                'context': context
            }
            
            # Führe Suche durch
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            # Konvertiere zu Standard-Format
            standard_result = self._convert_to_standard_format(result, model_id, mine_name, country)
            
            # Berechne Performance-Metriken
            response_time = (datetime.now() - start_time).total_seconds()
            filled_fields = 0
            
            if standard_result.get('success'):
                structured_data = standard_result.get('data', {}).get('structured_data', {})
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
                
                logger.info(f"[ENHANCED-OPS] {model_id} erfolgreich: {filled_fields} Felder, {response_time:.2f}s")
            else:
                logger.warning(f"[ENHANCED-OPS] {model_id} fehlgeschlagen: {standard_result.get('error')}")
            
            # Aktualisiere Performance-Tracking
            self.update_model_performance(model_id, standard_result.get('success', False), filled_fields, response_time)
            
            return standard_result
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Fehler bei erweiterte Suche {model_id}: {str(e)}"
            logger.error(f"[ENHANCED-OPS] {error_msg}")
            
            # Aktualisiere Performance bei Fehler
            self.update_model_performance(model_id, False, 0, response_time)
            
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
    
    async def collect_sources_all_models(self, mine_name: str, country: Optional[str] = None,
                                       commodity: Optional[str] = None, region: Optional[str] = None,
                                       max_models: int = 10) -> List[Dict]:
        """
        Sammelt Quellen von allen verfügbaren Modellen
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            max_models: Maximale Anzahl Modelle
            
        Returns:
            Liste aller gesammelten Quellen
        """
        logger.info(f"[ENHANCED-OPS] Sammle Quellen mit {max_models} Modellen für {mine_name}")
        
        # Bereite Kontext vor
        context = await self.prepare_search_context(mine_name, country, region, commodity)
        
        # Hole die besten verfügbaren Modelle
        available_models = self.registry.get_available_models()
        top_models = context.get('top_models', [])
        
        # Kombiniere bekannte Top-Modelle mit verfügbaren Modellen
        model_selection = []
        
        # Zuerst Top-Performer (falls verfügbar)
        for model_info in top_models[:max_models//2]:
            if model_info['model_id'] in available_models:
                model_selection.append(model_info['model_id'])
        
        # Dann weitere verfügbare Modelle
        remaining_slots = max_models - len(model_selection)
        for model_id in available_models:
            if len(model_selection) >= max_models:
                break
            if model_id not in model_selection:
                model_selection.append(model_id)
        
        logger.info(f"[ENHANCED-OPS] Verwende {len(model_selection)} Modelle für Quellensammlung")
        
        # Erstelle Tasks für parallele Quellensuche
        source_tasks = []
        for model_id in model_selection:
            task = self._collect_sources_from_model(model_id, context)
            source_tasks.append(task)
        
        # Führe alle Suchen parallel aus
        source_results = await asyncio.gather(*source_tasks, return_exceptions=True)
        
        # Sammle alle Quellen
        all_sources = []
        successful_models = 0
        
        for i, result in enumerate(source_results):
            model_id = model_selection[i]
            
            if isinstance(result, Exception):
                logger.warning(f"[ENHANCED-OPS] Quellensammlung {model_id} Exception: {result}")
                continue
            
            if isinstance(result, list):
                all_sources.extend(result)
                successful_models += 1
                logger.debug(f"[ENHANCED-OPS] {model_id} sammelte {len(result)} Quellen")
        
        # Dedupliziere und ranke Quellen
        unique_sources = self._deduplicate_and_rank_sources(all_sources)
        
        logger.info(f"[ENHANCED-OPS] Quellensammlung abgeschlossen: {len(unique_sources)} einzigartige Quellen "
                   f"von {successful_models}/{len(model_selection)} Modellen")
        
        return unique_sources
    
    async def extract_data_from_sources(self, sources: List[Dict], mine_name: str,
                                      country: Optional[str] = None, commodity: Optional[str] = None,
                                      max_models: int = 8) -> Dict[str, Dict]:
        """
        Extrahiert Daten aus gegebenen Quellen mit mehreren Modellen
        
        Args:
            sources: Liste der Quellen
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            max_models: Maximale Anzahl Modelle für Extraktion
            
        Returns:
            Extrahierte Daten von verschiedenen Modellen
        """
        logger.info(f"[ENHANCED-OPS] Extrahiere Daten aus {len(sources)} Quellen mit {max_models} Modellen")
        
        if not sources:
            return {}
        
        # Bereite Kontext vor
        context = await self.prepare_search_context(mine_name, country, None, commodity)
        
        # Wähle beste Modelle für Extraktion
        available_models = self.registry.get_available_models()
        top_models = context.get('top_models', [])
        
        extraction_models = []
        for model_info in top_models[:max_models]:
            if model_info['model_id'] in available_models:
                extraction_models.append(model_info['model_id'])
        
        # Fülle mit weiteren Modellen auf wenn nötig
        for model_id in available_models:
            if len(extraction_models) >= max_models:
                break
            if model_id not in extraction_models:
                extraction_models.append(model_id)
        
        # Generiere spezialisierte Prompts
        specialized_prompts = self._generate_specialized_prompts(mine_name, country or '', sources)
        
        logger.info(f"[ENHANCED-OPS] Verwende {len(extraction_models)} Modelle mit {len(specialized_prompts)} spezialisierten Prompts")
        
        # Erstelle Tasks für parallele Extraktion
        extraction_tasks = []
        
        for model_id in extraction_models:
            for prompt_type, prompt in specialized_prompts.items():
                task = self._extract_with_model_and_prompt(
                    model_id, prompt_type, prompt, sources, context
                )
                extraction_tasks.append((model_id, prompt_type, task))
        
        # Führe alle Extraktionen parallel aus (mit Batch-Verarbeitung)
        batch_size = 15  # Limitiere parallele Requests
        extraction_results = {}
        
        for i in range(0, len(extraction_tasks), batch_size):
            batch = extraction_tasks[i:i + batch_size]
            batch_tasks = [task for _, _, task in batch]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Verarbeite Batch-Ergebnisse
            for j, result in enumerate(batch_results):
                model_id, prompt_type, _ = batch[j]
                
                if model_id not in extraction_results:
                    extraction_results[model_id] = {}
                
                if isinstance(result, Exception):
                    logger.warning(f"[ENHANCED-OPS] Extraktion {model_id}:{prompt_type} Exception: {result}")
                    extraction_results[model_id][prompt_type] = {"success": False, "error": str(result)}
                else:
                    extraction_results[model_id][prompt_type] = result
        
        logger.info(f"[ENHANCED-OPS] Datenextraktion abgeschlossen: {len(extraction_results)} Modell-Ergebnisse")
        return extraction_results
    
    async def _collect_sources_from_model(self, model_id: str, context: Dict) -> List[Dict]:
        """
        Sammelt Quellen von einem spezifischen Modell
        
        Args:
            model_id: Modell-ID
            context: Suchkontext
            
        Returns:
            Liste der gefundenen Quellen
        """
        try:
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return []
            
            # Erstelle Source-Discovery-Query
            query = f"""Finde relevante Online-Quellen für die Mine "{context['mine_name']}" in {context.get('country', 'unbekanntem Land')}:

Suche nach:
- Offizielle Unternehmenswebsites
- Regierungsberichte und -dokumente
- Bergbau-Nachrichtenseiten
- Fachpublikationen
- Umweltberichte

Gib URLs und Beschreibungen zurück."""
            
            # Options für Source Discovery
            options = {
                'search_focus': 'sources',
                'mine_name': context['mine_name'],
                'country': context.get('country'),
                'name_variants': context.get('name_variants', [])
            }
            
            # Führe Suche durch
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            if result.success and result.data.get('sources'):
                return result.data['sources']
                
            return []
            
        except Exception as e:
            logger.debug(f"[ENHANCED-OPS] Quellensammlung {model_id} Fehler: {e}")
            return []
    
    async def _extract_with_model_and_prompt(self, model_id: str, prompt_type: str,
                                           prompt: str, sources: List[Dict], 
                                           context: Dict) -> Dict[str, Any]:
        """
        Extrahiert Daten mit spezifischem Modell und Prompt
        
        Args:
            model_id: Modell-ID
            prompt_type: Typ des Prompts
            prompt: Prompt-Text
            sources: Verfügbare Quellen
            context: Suchkontext
            
        Returns:
            Extraktionsergebnis
        """
        start_time = datetime.now()
        
        try:
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {"success": False, "error": "Provider nicht verfügbar"}
            
            # Options für Extraktion
            options = {
                'mine_name': context['mine_name'],
                'country': context.get('country'),
                'commodity': context.get('commodity'),
                'sources': sources,
                'discovered_sources': sources,
                'prompt_type': prompt_type,
                'extraction_focus': prompt_type
            }
            
            # Führe Extraktion durch
            provider_name, model_key = model_id.split(':')
            result = await provider.search(prompt, model_key, options)
            
            # Konvertiere Ergebnis
            standard_result = self._convert_to_standard_format(result, model_id, context['mine_name'], context.get('country'))
            
            # Performance-Tracking
            response_time = (datetime.now() - start_time).total_seconds()
            filled_fields = 0
            
            if standard_result.get('success'):
                structured_data = standard_result.get('data', {}).get('structured_data', {})
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
            
            self.update_model_performance(model_id, standard_result.get('success', False), filled_fields, response_time)
            
            return standard_result
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self.update_model_performance(model_id, False, 0, response_time)
            
            return {
                "success": False,
                "error": f"Extraktion Fehler: {str(e)}",
                "data": {}
            }
    
    def _generate_specialized_prompts(self, mine_name: str, country: str, 
                                    sources: List[Dict]) -> Dict[str, str]:
        """
        Generiert spezialisierte Prompts für verschiedene Datentypen
        
        Args:
            mine_name: Name der Mine
            country: Land
            sources: Verfügbare Quellen
            
        Returns:
            Dictionary mit spezialisierten Prompts
        """
        sources_text = self._format_sources_for_prompt(sources)
        location = f" in {country}" if country else ""
        
        prompts = {
            'financial': f"""Analysiere finanzielle Daten der Mine "{mine_name}"{location}:

Quellen:
{sources_text}

Finde:
- Restaurationskosten/Rekultivierungskosten
- Investitionen und Betriebskosten
- Umsätze und Gewinne
- Finanzierungsquellen

Gib konkrete Zahlen mit Währung und Jahr an.""",

            'technical': f"""Analysiere technische Daten der Mine "{mine_name}"{location}:

Quellen:
{sources_text}

Finde:
- Exakte GPS-Koordinaten
- Fläche in Hektar
- Abbaumethoden
- Produktionskapazität
- Technische Spezifikationen

Gib präzise Zahlen an.""",

            'operational': f"""Analysiere Betriebsdaten der Mine "{mine_name}"{location}:

Quellen:
{sources_text}

Finde:
- Aktueller Betreiber/Eigentümer
- Aktivitätsstatus (aktiv/stillgelegt/geplant)
- Mitarbeiterzahl
- Betriebszeiten
- Managementstruktur

Gib aktuelle Informationen an.""",

            'production': f"""Analysiere Produktionsdaten der Mine "{mine_name}"{location}:

Quellen:
{sources_text}

Finde:
- Rohstofftyp (Gold, Kupfer, Kohle, etc.)
- Jährliche Produktionsmenge
- Qualität/Grade des Rohstoffs
- Produktionshistorie
- Reserven und Ressourcen

Gib Mengen und Qualitätsangaben an.""",

            'comprehensive': f"""Sammle ALLE verfügbaren Informationen über die Mine "{mine_name}"{location}:

Quellen:
{sources_text}

Strukturiere die Antwort nach:
1. Betreiber und Eigentümer
2. Standort und Koordinaten
3. Rohstofftyp und Produktion
4. Finanzen und Kosten
5. Status und Aktivität
6. Umwelt und Sicherheit

Verwende nur verifizierte Informationen aus den Quellen."""
        }
        
        return prompts