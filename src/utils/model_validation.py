"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Model Validation für API-Modelle
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from src.core.logger import get_logger

class ModelValidator:
    """Validiert und verwaltet API Model IDs"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._valid_models = self._initialize_valid_models()
        self._model_mappings = self._initialize_model_mappings()
    
    def _initialize_valid_models(self) -> Dict[str, List[str]]:
        """Definiert gültige Model IDs für jede API (Stand: Juni 2025)"""
        return {
            "openrouter": [
                # Anthropic Models
                "anthropic/claude-3.5-sonnet-20241022",
                "anthropic/claude-3-opus",
                "anthropic/claude-3-sonnet",
                "anthropic/claude-3-haiku",
                
                # Google Models
                # ÄNDERUNG 24.06.2025: Diese Models werden von OpenRouter API nicht mehr unterstützt
                # "google/gemini-2.0-flash-exp",  # 404 - No endpoints found
                # "google/gemini-2.0-flash-thinking-exp",  # 400 - not a valid model ID
                # "google/gemini-2.0-flash-thinking-exp:free",  # 400 - not a valid model ID
                "google/gemini-pro-1.5",
                "google/gemini-pro",
                "google/gemma-2-27b-it",
                
                # Meta Llama Models  
                "meta-llama/llama-3.2-90b-vision-instruct",  # Vision Model
                "meta-llama/llama-3.2-90b-vision-instruct:free",
                "meta-llama/llama-3.1-405b-instruct",
                "meta-llama/llama-3.1-70b-instruct",
                "meta-llama/llama-3.1-8b-instruct",
                
                # OpenAI Models
                "openai/gpt-4o",
                "openai/gpt-4o-2024-11-20",
                "openai/o1",
                "openai/o1-preview",
                "openai/gpt-4-turbo",
                "openai/gpt-3.5-turbo",
                
                # Other Models
                "deepseek/deepseek-chat",
                "qwen/qwen-2.5-72b-instruct",
                "mistralai/mistral-7b-instruct",
                "x-ai/grok-2-1212",
                "nousresearch/hermes-3-llama-3.1-70b"
            ],
            
            "perplexity": [
                # Aktuelle Perplexity Models (Juni 2025)
                "sonar",  # Basic model
                "sonar-pro",  # Advanced search
                "sonar-deep-research",  # Deep research mode
                "sonar-reasoning-pro",  # Enhanced reasoning
                
                # Llama-basierte Models
                "llama-3.1-sonar-small-128k-online",
                "llama-3.1-sonar-large-128k-online",
                "llama-3.1-sonar-small-128k-chat",
                "llama-3.1-sonar-large-128k-chat",
                
                # Andere verfügbare Models
                "llama-3.1-70b-instruct",
                "llama-3.1-8b-instruct",
                "mistral-7b",
                "codellama-34b"
            ],
            
            "claude": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022"
            ],
            
            "openai": [
                "gpt-4o",
                "gpt-4o-2024-11-20", 
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "gpt-4",
                "o1",
                "o1-preview"
            ]
        }
    
    def _initialize_model_mappings(self) -> Dict[str, Dict[str, str]]:
        """Mappings für veraltete/ungültige Model IDs zu gültigen Alternativen"""
        return {
            "openrouter": {
                # Falsche Model IDs -> Korrekte Model IDs
                "meta-llama/llama-3.2-90b-instruct": "meta-llama/llama-3.2-90b-vision-instruct",
                "google/gemini-2.0-flash-thinking-exp-1219:free": "google/gemini-2.0-flash-thinking-exp:free",
                "google/gemini-2-flash-exp": "google/gemini-2.0-flash-exp",
                "meta-llama/llama-3-70b-instruct": "meta-llama/llama-3.1-70b-instruct",
                "meta-llama/llama-3-8b-instruct": "meta-llama/llama-3.1-8b-instruct"
            },
            
            "perplexity": {
                # Veraltete Model IDs -> Neue Model IDs
                "sonar-medium-online": "sonar",
                "sonar-small-online": "sonar",
                "sonar-large-online": "sonar-pro",
                "llama-3-sonar-small-32k-online": "llama-3.1-sonar-small-128k-online",
                "llama-3-sonar-large-32k-online": "llama-3.1-sonar-large-128k-online",
                "llama-3-sonar-small-32k-chat": "llama-3.1-sonar-small-128k-chat",
                "llama-3-sonar-large-32k-chat": "llama-3.1-sonar-large-128k-chat",
                "mixtral-8x7b-instruct": "mistral-7b"
            }
        }
    
    def validate_model(self, api: str, model_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validiert ein Model ID für eine bestimmte API
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, suggested_alternative)
        """
        api = api.lower()
        
        # Prüfe ob API bekannt ist
        if api not in self._valid_models:
            self.logger.warning(f"Unbekannte API: {api}")
            return False, None
        
        # Prüfe ob Model ID gültig ist
        if model_id in self._valid_models[api]:
            return True, None
        
        # Prüfe ob es ein Mapping gibt
        if api in self._model_mappings and model_id in self._model_mappings[api]:
            suggested = self._model_mappings[api][model_id]
            self.logger.info(
                f"Model '{model_id}' ist veraltet/ungültig für {api}. "
                f"Empfehlung: '{suggested}'"
            )
            return False, suggested
        
        # Kein gültiges Model und kein Mapping
        self.logger.error(f"Ungültiges Model '{model_id}' für {api}")
        return False, None
    
    def get_valid_models(self, api: str) -> List[str]:
        """Gibt Liste aller gültigen Models für eine API zurück"""
        return self._valid_models.get(api.lower(), [])
    
    def auto_fix_model(self, api: str, model_id: str) -> str:
        """
        Versucht automatisch ein ungültiges Model ID zu korrigieren
        
        Returns:
            str: Korrigiertes Model ID oder Original wenn keine Korrektur möglich
        """
        is_valid, suggested = self.validate_model(api, model_id)
        
        if is_valid:
            return model_id
        
        if suggested:
            self.logger.info(f"Auto-Fix: '{model_id}' -> '{suggested}' für {api}")
            return suggested
        
        # Fallback auf Default-Model der API
        defaults = {
            "openrouter": "deepseek/deepseek-chat",  # Free tier default
            "perplexity": "sonar",
            "claude": "claude-3-haiku-20240307",
            "openai": "gpt-3.5-turbo"
        }
        
        default = defaults.get(api.lower())
        if default:
            self.logger.warning(
                f"Kein Mapping für '{model_id}' gefunden. "
                f"Verwende Default: '{default}'"
            )
            return default
        
        return model_id
    
    def validate_api_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validiert alle Model IDs in einer API-Konfiguration
        
        Returns:
            Dict mit Validierungsfehlern pro API
        """
        errors = {}
        
        # OpenRouter Models
        if "openrouter_models" in config:
            openrouter_errors = []
            for model in config["openrouter_models"]:
                is_valid, suggested = self.validate_model("openrouter", model)
                if not is_valid:
                    error_msg = f"Ungültiges Model: {model}"
                    if suggested:
                        error_msg += f" (Empfehlung: {suggested})"
                    openrouter_errors.append(error_msg)
            
            if openrouter_errors:
                errors["openrouter"] = openrouter_errors
        
        # Perplexity Models
        if "perplexity_model" in config:
            is_valid, suggested = self.validate_model("perplexity", config["perplexity_model"])
            if not is_valid:
                error_msg = f"Ungültiges Model: {config['perplexity_model']}"
                if suggested:
                    error_msg += f" (Empfehlung: {suggested})"
                errors["perplexity"] = [error_msg]
        
        return errors


# Singleton Instance
_validator_instance = None

def get_model_validator() -> ModelValidator:
    """Gibt Singleton-Instanz des Model Validators zurück"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ModelValidator()
    return _validator_instance