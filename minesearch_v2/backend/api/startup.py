"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Startup-Events für MineSearch API
"""

from fastapi import FastAPI
import logging
from providers.registry import provider_registry
from database import db_manager

logger = logging.getLogger(__name__)

def setup_startup_events(app: FastAPI):
    """Konfiguriert Startup-Events für die FastAPI App"""
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("MineSearch v2.1 startet...")
        
        # Provider-Registry initialisieren
        try:
            provider_registry.initialize()
            logger.info(f"Provider-Registry initialisiert. Verfügbare Modelle: {list(provider_registry.get_all_models().keys())}")
        except Exception as e:
            logger.error(f"Fehler bei Provider-Initialisierung: {e}")
        
        # Datenbank initialisieren
        try:
            db_manager.init_db()
            logger.info("Datenbank erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("MineSearch v2.1 wird beendet...")