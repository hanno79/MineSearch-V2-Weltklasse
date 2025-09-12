"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Model-Information Routes
"""

from fastapi import APIRouter, Query
import logging
from minesearch.providers.registry import provider_registry

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
