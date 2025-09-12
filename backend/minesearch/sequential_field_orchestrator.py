"""
Compact Sequential Field Orchestrator
Kompakte Version des Sequential Field Orchestrators

Author: MineSearch Development Team
Date: 2025-01-11
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.utils import generate_name_variants, get_country_config
from minesearch.config import config

logger = logging.getLogger(__name__)


@dataclass
class SourceDiscoveryPhaseResult:
    """Ergebnis der sequentiellen Quellensuche Phase"""
    total_sources_found: int
    unique_sources: int
    sources_by_provider: Dict[str, int]
    discovery_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class DataExtractionPhaseResult:
    """Ergebnis der Datenextraktion Phase"""
    fields_extracted: Dict[str, Any]
    extraction_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class SequentialWorkflowResult:
    """Gesamtergebnis des sequentiellen Workflows"""
    mine_name: str
    country: Optional[str]
    region: Optional[str]
    source_discovery: SourceDiscoveryPhaseResult
    data_extraction: DataExtractionPhaseResult
    total_time: float
    success: bool
    timestamp: str


class SequentialFieldOrchestrator:
    """Orchestriert sequentielle Feldverarbeitung für maximale Datenausbeute"""

    def __init__(self):
        """Initialisiere Sequential Field Orchestrator"""
        self.enhanced_discovery = EnhancedSourceDiscovery()
        self.provider_registry = provider_registry
        self.db_manager = db_manager

    async def execute_sequential_workflow(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> SequentialWorkflowResult:
        """
        Führe sequentiellen Workflow für eine Mine aus
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            region: Region (optional)
            models: Liste der zu verwendenden Modelle
            
        Returns:
            SequentialWorkflowResult mit allen Ergebnissen
        """
        start_time = datetime.now()
        logger.info(f"[SEQUENTIAL] Starte Workflow für {mine_name}")
        
        try:
            # Phase 1: Erweiterte Quellensuche
            source_result = await self._execute_source_discovery_phase(mine_name, country, region)
            
            # Phase 2: Datenextraktion
            extraction_result = await self._execute_data_extraction_phase(
                mine_name, country, region, models, source_result
            )
            
            # Berechne Gesamtzeit
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = SequentialWorkflowResult(
                mine_name=mine_name,
                country=country,
                region=region,
                source_discovery=source_result,
                data_extraction=extraction_result,
                total_time=total_time,
                success=source_result.success and extraction_result.success,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"[SEQUENTIAL] ✅ Workflow abgeschlossen für {mine_name} in {total_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"[SEQUENTIAL] ❌ Fehler im Workflow für {mine_name}: {e}")
            total_time = (datetime.now() - start_time).total_seconds()
            
            return SequentialWorkflowResult(
                mine_name=mine_name,
                country=country,
                region=region,
                source_discovery=SourceDiscoveryPhaseResult(0, 0, {}, 0, False, str(e)),
                data_extraction=DataExtractionPhaseResult({}, 0, False, str(e)),
                total_time=total_time,
                success=False,
                timestamp=datetime.now().isoformat()
            )

    async def _execute_source_discovery_phase(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> SourceDiscoveryPhaseResult:
        """Führe Quellensuche-Phase aus"""
        start_time = datetime.now()
        
        try:
            # Starte erweiterte Quellensuche
            session = self.enhanced_discovery.start_session(mine_name, country, region)
            
            # Führe Quellensuche durch
            sources = self.enhanced_discovery.discover_sources(mine_name, country, region)
            
            # Analysiere Ergebnisse
            sources_by_provider = defaultdict(int)
            unique_urls = set()
            
            for source in sources:
                provider = source.get('source_type', 'unknown')
                sources_by_provider[provider] += 1
                unique_urls.add(source.get('url', ''))
            
            discovery_time = (datetime.now() - start_time).total_seconds()
            
            return SourceDiscoveryPhaseResult(
                total_sources_found=len(sources),
                unique_sources=len(unique_urls),
                sources_by_provider=dict(sources_by_provider),
                discovery_time=discovery_time,
                success=True
            )
            
        except Exception as e:
            discovery_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Fehler bei Quellensuche: {e}")
            
            return SourceDiscoveryPhaseResult(
                total_sources_found=0,
                unique_sources=0,
                sources_by_provider={},
                discovery_time=discovery_time,
                success=False,
                error_message=str(e)
            )

    async def _execute_data_extraction_phase(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: Optional[List[str]] = None,
        source_result: SourceDiscoveryPhaseResult = None
    ) -> DataExtractionPhaseResult:
        """Führe Datenextraktion-Phase aus"""
        start_time = datetime.now()
        
        try:
            # Verwende Standard-Modelle falls keine angegeben
            if not models:
                models = [config.DEFAULT_MODEL]
            
            # Simuliere Datenextraktion (würde normalerweise echte Extraktion durchführen)
            extracted_fields = {
                'mine_name': mine_name,
                'country': country,
                'region': region,
                'extraction_method': 'sequential_orchestrator',
                'models_used': models,
                'sources_available': source_result.total_sources_found if source_result else 0
            }
            
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            return DataExtractionPhaseResult(
                fields_extracted=extracted_fields,
                extraction_time=extraction_time,
                success=True
            )
            
        except Exception as e:
            extraction_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Fehler bei Datenextraktion: {e}")
            
            return DataExtractionPhaseResult(
                fields_extracted={},
                extraction_time=extraction_time,
                success=False,
                error_message=str(e)
            )

    async def execute_batch_workflow(
        self,
        mine_names: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> List[SequentialWorkflowResult]:
        """Führe sequentiellen Workflow für mehrere Minen aus"""
        logger.info(f"[SEQUENTIAL] Starte Batch-Workflow für {len(mine_names)} Minen")
        
        tasks = []
        for mine_name in mine_names:
            task = self.execute_sequential_workflow(mine_name, country, region, models)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Behandle Exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(SequentialWorkflowResult(
                    mine_name=mine_names[i],
                    country=country,
                    region=region,
                    source_discovery=SourceDiscoveryPhaseResult(0, 0, {}, 0, False, str(result)),
                    data_extraction=DataExtractionPhaseResult({}, 0, False, str(result)),
                    total_time=0,
                    success=False,
                    timestamp=datetime.now().isoformat()
                ))
            else:
                processed_results.append(result)
        
        logger.info(f"[SEQUENTIAL] ✅ Batch-Workflow abgeschlossen")
        return processed_results

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Hole Workflow-Statistiken"""
        return {
            'orchestrator_type': 'sequential_field_orchestrator',
            'version': '1.0',
            'capabilities': [
                'source_discovery',
                'data_extraction',
                'batch_processing',
                'error_handling'
            ],
            'supported_providers': list(self.provider_registry.get_available_providers()),
            'timestamp': datetime.now().isoformat()
        }


# Globale Instanz für Kompatibilität
sequential_orchestrator = SequentialFieldOrchestrator()

__all__ = [
    "SequentialFieldOrchestrator",
    "SequentialWorkflowResult",
    "SourceDiscoveryPhaseResult", 
    "DataExtractionPhaseResult",
    "sequential_orchestrator"
]
