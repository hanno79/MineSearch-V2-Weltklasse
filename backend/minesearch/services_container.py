"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Service Container für shared Service-Instanzen
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ServiceContainer:
    """Singleton Container für alle Services"""
    
    _instance: Optional['ServiceContainer'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Service Instanzen (lazy loading)
        self._mine_search_service = None
        self._benchmark_service = None
        # CONSOLIDATION 09.08.2025: Entfernte obsolete Services:
        # - enhanced_search_service (search_service_multi_enhanced)  
        # - multi_search_service (search_service_multi)
        # - validation_service (validation_service)
        # - web_fetch_service (nicht mehr verwendet)
        
        self._initialized = True
        logger.info("[SERVICE-CONTAINER] Initialized")
    
    @property
    def mine_search_service(self):
        """Lazy loading MineSearchService"""
        if self._mine_search_service is None:
            from minesearch.search_service import MineSearchService
            self._mine_search_service = MineSearchService()
            logger.info("[SERVICE-CONTAINER] MineSearchService created")
        return self._mine_search_service
    
    # CONSOLIDATION 09.08.2025: enhanced_search_service und multi_search_service entfernt
    # Alle Multi-Provider-Funktionalität ist jetzt in MineSearchService integriert
    
    @property
    def benchmark_service(self):
        """Lazy loading ModelBenchmarkService"""
        if self._benchmark_service is None:
            from minesearch.model_benchmark_service import ModelBenchmarkService
            self._benchmark_service = ModelBenchmarkService()
            logger.info("[SERVICE-CONTAINER] ModelBenchmarkService created")
        return self._benchmark_service
    
    # CONSOLIDATION 09.08.2025: web_fetch_service und validation_service entfernt
    # - web_fetch_service: Nicht mehr verwendet
    # - validation_service: War defekter Adapter zu gelöschtem minesearch_v2
    
    def reset(self):
        """Reset für Tests"""
        self._mine_search_service = None
        self._benchmark_service = None
        # CONSOLIDATION 09.08.2025: Obsolete Service-Referenzen entfernt
        logger.info("[SERVICE-CONTAINER] Reset")

# Singleton-Instanz
services = ServiceContainer()