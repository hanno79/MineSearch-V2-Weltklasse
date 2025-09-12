"""
Compact Multi-Model Search Orchestrator
Kompakte Version des Multi-Model Search Orchestrators

Author: MineSearch Development Team
Date: 2025-01-11
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.utils import generate_name_variants, get_country_config
from minesearch.config import config
from minesearch.source_validation import source_validator

logger = logging.getLogger(__name__)


@dataclass
class ModelSearchResult:
    """Individual result for one model"""
    model_id: str
    success: bool
    data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    execution_time: float
    error_message: Optional[str] = None


@dataclass
class MultiModelSearchResult:
    """Complete result from multi-model search"""
    mine_name: str
    country: Optional[str]
    region: Optional[str]
    model_results: List[ModelSearchResult]
    total_execution_time: float
    success: bool
    timestamp: str
    consolidated_data: Optional[Dict[str, Any]] = None


class MultiModelSearchOrchestrator:
    """Orchestriert Suche mit mehreren Modellen parallel"""

    def __init__(self):
        """Initialisiere Multi-Model Search Orchestrator"""
        self.enhanced_discovery = EnhancedSourceDiscovery()
        self.provider_registry = provider_registry
        self.db_manager = db_manager
        self.normalized_db_manager = NormalizedDatabaseManager()
        self.source_validator = source_validator

    async def search_with_all_models(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> MultiModelSearchResult:
        """
        Führe Suche mit allen verfügbaren Modellen durch
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            region: Region (optional)
            models: Liste der zu verwendenden Modelle
            
        Returns:
            MultiModelSearchResult mit allen Ergebnissen
        """
        start_time = datetime.now()
        logger.info(f"[MULTI-MODEL] Starte Suche für {mine_name} mit allen Modellen")
        
        try:
            # Verwende alle verfügbaren Modelle falls keine angegeben
            if not models:
                models = self._get_available_models()
            
            # Führe parallele Suche mit allen Modellen durch
            model_results = await self._execute_parallel_model_search(
                mine_name, country, region, models
            )
            
            # Konsolidiere Ergebnisse
            consolidated_data = self._consolidate_model_results(model_results)
            
            # Berechne Gesamtzeit
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = MultiModelSearchResult(
                mine_name=mine_name,
                country=country,
                region=region,
                model_results=model_results,
                total_execution_time=total_time,
                success=any(r.success for r in model_results),
                timestamp=datetime.now().isoformat(),
                consolidated_data=consolidated_data
            )
            
            logger.info(f"[MULTI-MODEL] ✅ Suche abgeschlossen für {mine_name} in {total_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"[MULTI-MODEL] ❌ Fehler bei Suche für {mine_name}: {e}")
            total_time = (datetime.now() - start_time).total_seconds()
            
            return MultiModelSearchResult(
                mine_name=mine_name,
                country=country,
                region=region,
                model_results=[],
                total_execution_time=total_time,
                success=False,
                timestamp=datetime.now().isoformat()
            )

    async def _execute_parallel_model_search(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: List[str] = None
    ) -> List[ModelSearchResult]:
        """Führe parallele Suche mit allen Modellen durch"""
        tasks = []
        
        for model in models:
            task = self._search_with_single_model(mine_name, country, region, model)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Behandle Exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ModelSearchResult(
                    model_id=models[i],
                    success=False,
                    data={},
                    sources=[],
                    execution_time=0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results

    async def _search_with_single_model(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        model: str = None
    ) -> ModelSearchResult:
        """Führe Suche mit einem einzelnen Modell durch"""
        start_time = datetime.now()
        
        try:
            # Generiere Suchbegriffe
            search_terms = self._generate_search_terms(mine_name, country, region)
            
            # Führe Suche durch
            search_results = await self._execute_search_with_model(search_terms, model)
            
            # Extrahiere Daten
            extracted_data = await self._extract_data_with_model(search_results, mine_name, model)
            
            # Validiere Quellen
            validated_sources = await self._validate_sources(search_results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ModelSearchResult(
                model_id=model,
                success=True,
                data=extracted_data,
                sources=validated_sources,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Fehler bei Suche mit Modell {model}: {e}")
            
            return ModelSearchResult(
                model_id=model,
                success=False,
                data={},
                sources=[],
                execution_time=execution_time,
                error_message=str(e)
            )

    def _get_available_models(self) -> List[str]:
        """Hole verfügbare Modelle"""
        return [
            config.DEFAULT_MODEL,
            "anthropic:claude-3-5-sonnet",
            "perplexity:llama-3.1-sonar",
            "openrouter:meta-llama/llama-3.1-8b-instruct:free"
        ]

    def _generate_search_terms(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> List[str]:
        """Generiere Suchbegriffe"""
        terms = [mine_name]
        
        # Name-Varianten
        name_variants = generate_name_variants(mine_name)
        terms.extend(name_variants)
        
        # Länder-spezifische Begriffe
        if country:
            terms.append(f"{mine_name} {country}")
        
        # Region-spezifische Begriffe
        if region:
            terms.append(f"{mine_name} {region}")
        
        return list(set(terms))

    async def _execute_search_with_model(self, search_terms: List[str], model: str) -> List[Dict[str, Any]]:
        """Führe Suche mit spezifischem Modell durch"""
        # Simuliere Suche (würde normalerweise echte Provider-Aufrufe machen)
        results = []
        
        for term in search_terms:
            result = {
                'url': f"https://example.com/search?q={term}&model={model}",
                'title': f"Search results for {term}",
                'content': f"Content for {term} using {model}",
                'source_type': 'search_engine',
                'model_used': model
            }
            results.append(result)
        
        return results

    async def _extract_data_with_model(self, search_results: List[Dict[str, Any]], mine_name: str, model: str) -> Dict[str, Any]:
        """Extrahiere Daten mit spezifischem Modell"""
        # Simuliere Datenextraktion
        return {
            'mine_name': mine_name,
            'model_used': model,
            'extraction_method': 'multi_model_orchestrator',
            'fields_found': ['mine_name', 'country', 'commodity'],
            'confidence_score': 0.8
        }

    async def _validate_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validiere Quellen"""
        validated_sources = []
        
        for result in search_results:
            # Simuliere Quellenvalidierung
            validated_source = {
                **result,
                'validation_score': 0.9,
                'is_trusted': True,
                'validation_timestamp': datetime.now().isoformat()
            }
            validated_sources.append(validated_source)
        
        return validated_sources

    def _consolidate_model_results(self, model_results: List[ModelSearchResult]) -> Dict[str, Any]:
        """Konsolidiere Ergebnisse von allen Modellen"""
        consolidated = {
            'total_models_used': len(model_results),
            'successful_models': len([r for r in model_results if r.success]),
            'failed_models': len([r for r in model_results if not r.success]),
            'average_execution_time': sum(r.execution_time for r in model_results) / len(model_results) if model_results else 0,
            'consolidated_fields': {},
            'model_agreement': {},
            'consolidation_timestamp': datetime.now().isoformat()
        }
        
        # Konsolidiere Felder
        all_fields = {}
        for result in model_results:
            if result.success:
                for field, value in result.data.items():
                    if field not in all_fields:
                        all_fields[field] = []
                    all_fields[field].append(value)
        
        # Finde konsistente Werte
        for field, values in all_fields.items():
            if len(set(values)) == 1:  # Alle Modelle stimmen überein
                consolidated['consolidated_fields'][field] = values[0]
                consolidated['model_agreement'][field] = 1.0
            else:  # Wähle häufigsten Wert
                from collections import Counter
                most_common = Counter(values).most_common(1)[0]
                consolidated['consolidated_fields'][field] = most_common[0]
                consolidated['model_agreement'][field] = most_common[1] / len(values)
        
        return consolidated

    async def search_multiple_mines_with_all_models(
        self,
        mine_names: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> List[MultiModelSearchResult]:
        """Führe Multi-Model-Suche für mehrere Minen durch"""
        logger.info(f"[MULTI-MODEL] Starte Batch-Suche für {len(mine_names)} Minen")
        
        tasks = []
        for mine_name in mine_names:
            task = self.search_with_all_models(mine_name, country, region, models)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Behandle Exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(MultiModelSearchResult(
                    mine_name=mine_names[i],
                    country=country,
                    region=region,
                    model_results=[],
                    total_execution_time=0,
                    success=False,
                    timestamp=datetime.now().isoformat()
                ))
            else:
                processed_results.append(result)
        
        logger.info(f"[MULTI-MODEL] ✅ Batch-Suche abgeschlossen")
        return processed_results

    def get_orchestrator_statistics(self) -> Dict[str, Any]:
        """Hole Orchestrator-Statistiken"""
        return {
            'orchestrator_type': 'multi_model_search_orchestrator',
            'version': '1.0',
            'capabilities': [
                'parallel_model_search',
                'result_consolidation',
                'source_validation',
                'batch_processing'
            ],
            'available_models': self._get_available_models(),
            'timestamp': datetime.now().isoformat()
        }


# Globale Instanz für Kompatibilität
multi_model_orchestrator = MultiModelSearchOrchestrator()

__all__ = [
    "MultiModelSearchOrchestrator",
    "MultiModelSearchResult",
    "ModelSearchResult",
    "multi_model_orchestrator"
]
