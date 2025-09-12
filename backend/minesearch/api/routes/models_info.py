"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Model-Information Routes
"""

from fastapi import APIRouter, Query
import logging

try:
    from minesearch.providers.registry import provider_registry
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Provider registry import failed: {e}")
    provider_registry = None

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/models")
async def get_available_models():
    """Hole alle verfügbaren Modelle"""
    try:
        models = provider_registry.get_all_models()
        return {
            "success": True,
            "models": {
                model_id: {
                    "name": config.name,
                    "description": config.description,
                    "timeout": config.timeout,
                    "max_tokens": config.max_tokens,
                    "supports_web_search": config.supports_web_search,
                    "supports_deep_research": getattr(config, 'supports_deep_research', False),
                    "is_free": config.is_free,
                    "provider": config.provider
                }
                for model_id, config in models.items()
            }
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Modelle: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/available-models")
async def get_available_models_fallback():
    """Fallback-Endpoint im selben Schema wie provider_status:/available-models.

    Nutzt die Provider-Registry, um verfügbare Modelle zu liefern, falls der
    provider_status Router nicht geladen wurde. Markiert alle Modelle als
    'healthy' ohne externe Health-Checks.
    """
    try:
        if provider_registry is None:
            logger.warning("Provider registry nicht verfügbar - gebe leere Modelliste zurück")
            return {
                "success": True,
                "data": {
                    "available_models": {},
                    "unavailable_models": {},
                    "summary": {
                        "total_available": 0,
                        "total_unavailable": 0,
                        "healthy_providers": 0,
                        "total_providers": 0
                    }
                },
                "error": "Provider registry nicht initialisiert"
            }
        
        models = provider_registry.get_all_models()

        available_models = {}
        for model_id, config in models.items():
            # model_id Format: provider:key
            provider = model_id.split(":")[0] if ":" in model_id else getattr(config, 'provider', 'unknown')
            available_models[model_id] = {
                "name": getattr(config, 'name', model_id),
                "description": getattr(config, 'description', ''),
                "provider": provider,
                "provider_status": "healthy",
                "provider_category": getattr(config, 'provider_category', None)
            }

        response = {
            "success": True,
            "data": {
                "available_models": available_models,
                "unavailable_models": {},
                "summary": {
                    "total_available": len(available_models),
                    "total_unavailable": 0,
                    "healthy_providers": None,
                    "total_providers": None
                }
            }
        }
        return response
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der verfügbaren Modelle (Fallback): {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/models/{model_id}")
async def get_model_info(model_id: str):
    """Hole Informationen zu einem spezifischen Modell"""
    try:
        model_config = provider_registry.get_model_config(model_id)
        if not model_config:
            return {
                "success": False,
                "error": f"Modell {model_id} nicht gefunden"
            }

        return {
            "success": True,
            "model": {
                "id": model_id,
                "name": model_config.name,
                "description": model_config.description,
                "timeout": model_config.timeout,
                "max_tokens": model_config.max_tokens,
                "supports_web_search": model_config.supports_web_search,
                "supports_deep_research": getattr(model_config, 'supports_deep_research', False),
                "is_free": model_config.is_free,
                "provider": model_config.provider
            }
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Modells {model_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
