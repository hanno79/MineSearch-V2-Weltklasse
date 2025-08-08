"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Provider-Registry für dynamische Verwaltung aller Search-Provider
"""

import logging
from typing import Dict, List, Optional, Type, Any
from importlib import import_module

from .base_provider import AbstractProvider, ModelConfig
from minesearch.config.base import config as Config

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Zentrale Registry für alle Search-Provider"""
    
    def __init__(self):
        self._providers: Dict[str, AbstractProvider] = {}
        self._available_models: Dict[str, ModelConfig] = {}
        self._provider_classes: Dict[str, Type[AbstractProvider]] = {
            'perplexity': 'PerplexityProvider',
            'openrouter': 'OpenRouterProvider',
            'abacus': 'AbacusProvider',
            'tavily': 'TavilyProvider',
            'exa': 'ExaProvider',
            'scrapingbee': 'ScrapingBeeProvider',
            'firecrawl': 'FirecrawlProvider',
            'brightdata': 'BrightdataProvider',
            'openai': 'OpenAIProvider',
            'anthropic': 'AnthropicProvider',
            'gemini': 'GeminiProvider',
            'grok': 'GrokProvider',
            'deepseek': 'DeepSeekProvider'
        }
        
    def initialize(self, config: Dict[str, Any]):
        """
        Initialisiere alle konfigurierten Provider
        
        Args:
            config: Provider-Konfiguration aus config.py
        """
        logger.info(f"[REGISTRY] 🚀 Starte Provider-Initialisierung für {len(config)} Provider")
        
        # Zähle erwartete Modelle pro Provider
        expected_models = {}
        for provider_name, provider_config in config.items():
            if provider_config.get('enabled', False):
                models = provider_config.get('models', {})
                expected_models[provider_name] = len(models)
                logger.info(f"[REGISTRY] 📋 Provider {provider_name}: {len(models)} Modelle erwartet")
        
        for provider_name, provider_config in config.items():
            if not provider_config.get('enabled', False):
                logger.info(f"[REGISTRY] ⏭️  Provider {provider_name} ist deaktiviert")
                continue
                
            logger.info(f"[REGISTRY] 🔧 Initialisiere Provider: {provider_name}")
            
            try:
                # Lade Provider-Klasse dynamisch
                provider_class = self._load_provider_class(provider_name)
                if not provider_class:
                    logger.error(f"[REGISTRY] ❌ Provider-Klasse für {provider_name} konnte nicht geladen werden")
                    continue
                
                logger.info(f"[REGISTRY] ✅ Provider-Klasse {provider_class.__name__} geladen")
                
                # Initialisiere Provider
                api_key = provider_config.get('api_key', '')
                api_key_status = "✅ Verfügbar" if api_key else "❌ Fehlt"
                logger.info(f"[REGISTRY] 🔑 API-Key Status für {provider_name}: {api_key_status}")
                
                provider = provider_class(api_key, provider_config)
                
                # Validiere Provider
                if not provider.validate_config():
                    logger.error(f"[REGISTRY] ❌ Provider {provider_name} Validierung fehlgeschlagen")
                    continue
                
                logger.info(f"[REGISTRY] ✅ Provider {provider_name} Validierung erfolgreich")
                
                # Registriere Provider und seine Modelle
                self._providers[provider_name] = provider
                
                # Hole verfügbare Modelle vom Provider
                provider_models = provider.get_models()
                logger.info(f"[REGISTRY] 📊 Provider {provider_name} stellt {len(provider_models)} Modelle bereit")
                
                # Registriere Modelle mit Provider-Präfix
                registered_count = 0
                for model_key, model_config in provider_models.items():
                    full_model_id = f"{provider_name}:{model_key}"
                    self._available_models[full_model_id] = model_config
                    logger.info(f"[REGISTRY] ✅ Modell registriert: {full_model_id}")
                    registered_count += 1
                
                expected_count = expected_models.get(provider_name, 0)
                if registered_count == expected_count:
                    logger.info(f"[REGISTRY] ✅ Provider {provider_name} erfolgreich initialisiert: {registered_count}/{expected_count} Modelle")
                else:
                    logger.warning(f"[REGISTRY] ⚠️  Provider {provider_name}: Nur {registered_count}/{expected_count} Modelle registriert")
                
            except Exception as e:
                logger.error(f"[REGISTRY] ❌ Fehler beim Initialisieren von {provider_name}: {str(e)}")
                import traceback
                logger.error(f"[REGISTRY] 🔍 Traceback: {traceback.format_exc()}")
        
        # Final Summary
        total_models = len(self._available_models)
        total_providers = len(self._providers)
        logger.info(f"[REGISTRY] 🏁 INITIALIZATION COMPLETE: {total_providers} Provider, {total_models} Modelle registriert")
        
        if total_models == 0:
            logger.error(f"[REGISTRY] 🚨 CRITICAL: Keine Modelle registriert! Alle Provider fehlgeschlagen.")
        else:
            logger.info(f"[REGISTRY] 📋 Registrierte Modelle:")
            for model_id in sorted(self._available_models.keys()):
                logger.info(f"[REGISTRY]   ✅ {model_id}")
    
    def _load_provider_class(self, provider_name: str) -> Optional[Type[AbstractProvider]]:
        """
        Lade Provider-Klasse dynamisch
        
        Args:
            provider_name: Name des Providers
            
        Returns:
            Provider-Klasse oder None
        """
        class_name = self._provider_classes.get(provider_name)
        if not class_name:
            logger.error(f"[REGISTRY] Unbekannter Provider: {provider_name}")
            return None
        
        try:
            # Dynamischer Import mit absolutem Pfad im `minesearch`-Namespace
            module = import_module(f'minesearch.providers.{provider_name}_provider')
            provider_class = getattr(module, class_name)
            return provider_class
        except Exception as e:
            logger.error(f"[REGISTRY] Fehler beim Laden von {class_name}: {str(e)}")
            return None
    
    def get_provider(self, provider_name: str) -> Optional[AbstractProvider]:
        """
        Hole einen spezifischen Provider
        
        Args:
            provider_name: Name des Providers
            
        Returns:
            Provider-Instanz oder None
        """
        return self._providers.get(provider_name)
    
    def get_provider_for_model(self, model_id: str) -> Optional[AbstractProvider]:
        """
        Hole Provider für ein bestimmtes Modell
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            
        Returns:
            Provider-Instanz oder None
        """
        if ':' not in model_id:
            logger.error(f"[REGISTRY] Ungültiges Modell-ID Format: {model_id}")
            return None
        
        provider_name = model_id.split(':')[0]
        return self.get_provider(provider_name)
    
    def get_all_models(self) -> Dict[str, ModelConfig]:
        """
        Hole alle verfügbaren Modelle
        
        Returns:
            Dict mit allen Modellen (model_id -> ModelConfig)
        """
        return self._available_models.copy()
    
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Alias für get_all_models für Backward-Compatibility"""
        return self.get_all_models()
    
    def get_models_by_provider(self, provider_name: str) -> Dict[str, ModelConfig]:
        """
        Hole alle Modelle eines bestimmten Providers
        
        Args:
            provider_name: Name des Providers
            
        Returns:
            Dict mit Modellen des Providers
        """
        return {
            model_id: config 
            for model_id, config in self._available_models.items()
            if model_id.startswith(f"{provider_name}:")
        }
    
    def get_free_models(self) -> Dict[str, ModelConfig]:
        """
        Hole alle kostenlosen Modelle
        
        Returns:
            Dict mit kostenlosen Modellen
        """
        return {
            model_id: config
            for model_id, config in self._available_models.items()
            if config.is_free
        }
    
    def get_web_search_models(self) -> Dict[str, ModelConfig]:
        """
        Hole alle Modelle mit Web-Suche
        
        Returns:
            Dict mit Web-Such-fähigen Modellen
        """
        return {
            model_id: config
            for model_id, config in self._available_models.items()
            if config.supports_web_search
        }
    
    def is_model_available(self, model_id: str) -> bool:
        """
        Prüfe ob ein Modell verfügbar ist
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            
        Returns:
            True wenn verfügbar, False sonst
        """
        return model_id in self._available_models
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """
        Hole Konfiguration für ein bestimmtes Modell
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            
        Returns:
            ModelConfig oder None
        """
        return self._available_models.get(model_id)
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Führe Health-Check für alle Provider durch
        
        Returns:
            Dict mit Provider-Name -> Status
        """
        results = {}
        
        for provider_name, provider in self._providers.items():
            try:
                results[provider_name] = await provider.health_check()
            except Exception as e:
                logger.error(f"[REGISTRY] Health-Check für {provider_name} fehlgeschlagen: {str(e)}")
                results[provider_name] = False
        
        return results
    
    def get_default_models(self) -> List[str]:
        """
        Hole empfohlene Standard-Modelle
        
        Returns:
            Liste von Modell-IDs
        """
        defaults = []
        
        # ÄNDERUNG 14.07.2025: Kimi K2 als primäre Option für beste Performance
        if 'openrouter:kimi-k2' in self._available_models:
            defaults.append('openrouter:kimi-k2')
        
        # Weitere kostenlose OpenRouter Modelle als Fallback
        if 'openrouter:deepseek-free' in self._available_models:
            defaults.append('openrouter:deepseek-free')
        
        if 'openrouter:deepseek-chat' in self._available_models:
            defaults.append('openrouter:deepseek-chat')
        
        if 'openrouter:mistral-small-free' in self._available_models:
            defaults.append('openrouter:mistral-small-free')
        
        return defaults


# Globale Registry-Instanz
provider_registry = ProviderRegistry()