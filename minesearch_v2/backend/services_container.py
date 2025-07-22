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
        self._enhanced_search_service = None
        self._multi_search_service = None
        self._benchmark_service = None
        self._web_fetch_service = None
        self._validation_service = None
        
        self._initialized = True
        logger.info("[SERVICE-CONTAINER] Initialized")
    
    @property
    def mine_search_service(self):
        """Lazy loading MineSearchService"""
        if self._mine_search_service is None:
            from search_service import MineSearchService
            self._mine_search_service = MineSearchService()
            logger.info("[SERVICE-CONTAINER] MineSearchService created")
        return self._mine_search_service
    
    @property
    def enhanced_search_service(self):
        """Lazy loading EnhancedMultiProviderSearchService"""
        if self._enhanced_search_service is None:
            from search_service_multi_enhanced import EnhancedMultiProviderSearchService
            self._enhanced_search_service = EnhancedMultiProviderSearchService()
            logger.info("[SERVICE-CONTAINER] EnhancedMultiProviderSearchService created")
        return self._enhanced_search_service
    
    @property
    def multi_search_service(self):
        """Lazy loading MultiProviderSearchService"""
        if self._multi_search_service is None:
            from search_service_multi import MultiProviderSearchService
            self._multi_search_service = MultiProviderSearchService()
            logger.info("[SERVICE-CONTAINER] MultiProviderSearchService created")
        return self._multi_search_service
    
    @property
    def benchmark_service(self):
        """Lazy loading ModelBenchmarkService"""
        if self._benchmark_service is None:
            from model_benchmark_service import ModelBenchmarkService
            self._benchmark_service = ModelBenchmarkService()
            logger.info("[SERVICE-CONTAINER] ModelBenchmarkService created")
        return self._benchmark_service
    
    @property
    def web_fetch_service(self):
        """Lazy loading WebFetchService"""
        if self._web_fetch_service is None:
            from web_fetch_service import WebFetchService
            self._web_fetch_service = WebFetchService()
            logger.info("[SERVICE-CONTAINER] WebFetchService created")
        return self._web_fetch_service
    
    @property
    def validation_service(self):
        """Lazy loading ValidationService"""
        if self._validation_service is None:
            from validation_service import ValidationService
            self._validation_service = ValidationService()
            logger.info("[SERVICE-CONTAINER] ValidationService created")
        return self._validation_service
    
    def reset(self):
        """Reset für Tests"""
        self._mine_search_service = None
        self._enhanced_search_service = None
        self._multi_search_service = None
        self._benchmark_service = None
        self._web_fetch_service = None
        self._validation_service = None
        logger.info("[SERVICE-CONTAINER] Reset")

# Singleton-Instanz
services = ServiceContainer()