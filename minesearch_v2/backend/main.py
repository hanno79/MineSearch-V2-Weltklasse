"""
Author: rahn
Datum: 04.07.2025
Version: 2.1
Beschreibung: MineSearch 2.1 - Refactored Main Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager

from config import config
from api import router, setup_middleware, setup_exception_handlers
from providers.registry import provider_registry
from api_key_validator import APIKeyValidator

# Logging auf Deutsch
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ÄNDERUNG 10.07.2025: Lifespan-Funktion implementiert für Startup/Shutdown Events
# Ersetzt die vorherige on_event-Decorator-Methode für bessere Fehlerbehandlung
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""
    # Startup
    logger.info("MineSearch v2.1 startet...")
    
    # Provider-Registry initialisieren
    try:
        # Validiere API-Keys vor Provider-Initialisierung
        logger.info("Validiere API-Keys...")
        validation_results = APIKeyValidator.validate_all_keys(config.PROVIDERS)
        
        # Zeige Validierungsergebnisse
        valid_providers = []
        for provider, result in validation_results.items():
            if result['enabled'] and result['validated']:
                valid_providers.append(provider)
                logger.info(f"✓ {provider}: {result['message']}")
            elif result['enabled']:
                logger.warning(f"✗ {provider}: {result['message']}")
        
        if not valid_providers:
            raise ValueError("Keine Provider mit gültigen API-Keys gefunden. Bitte .env-Datei prüfen.")
        
        provider_registry.initialize(config.PROVIDERS)
        available_models = list(provider_registry.get_all_models().keys())
        logger.info(f"Provider-Registry initialisiert. Verfügbare Modelle: {available_models}")
        
        # Validiere dass mindestens ein Modell verfügbar ist
        if not available_models:
            raise ValueError("Keine Provider-Modelle verfügbar. Bitte API-Keys in .env prüfen.")
            
    except ImportError as e:
        logger.error(f"Import-Fehler bei Provider-Initialisierung: {e}")
        logger.error("Bitte Provider-Module überprüfen")
        raise
    except ValueError as e:
        logger.error(f"Konfigurations-Fehler: {e}")
        raise
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Provider-Initialisierung: {type(e).__name__}: {e}")
        raise
    
    # Datenbank initialisieren
    try:
        from database import db_manager
        # Datenbank wird bereits beim Import initialisiert
        logger.info("Datenbank erfolgreich initialisiert")
        
        # Datenbank-Verbindung wird beim ersten Zugriff automatisch getestet
        
    except ImportError as e:
        logger.error(f"Datenbank-Modul konnte nicht importiert werden: {e}")
        raise
    except AttributeError as e:
        logger.error(f"Datenbank-Manager nicht korrekt initialisiert: {e}")
        raise
    except Exception as e:
        logger.error(f"Datenbank-Fehler: {type(e).__name__}: {e}")
        logger.error("Bitte Datenbank-Konfiguration und -Verbindung prüfen")
        raise
    
    yield
    
    # Shutdown
    logger.info("MineSearch v2.1 wird beendet...")

# FastAPI App
app = FastAPI(
    title="MineSearch 2.1",
    description="Mining-Recherche-System mit Multi-Provider-Unterstützung",
    version="2.1.0",
    lifespan=lifespan
)

# Middleware konfigurieren
setup_middleware(app)

# Exception Handler aktivieren
setup_exception_handlers(app)

# Statische Dateien für Frontend  
app.mount("/static", StaticFiles(directory="/app/minesearch_v2/frontend"), name="static")

# Statische Dateien für CSV-Zugriff
app.mount("/csv", StaticFiles(directory="/app/minesearch_v2"), name="csv")

# API-Router einbinden
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    
    if config.DEBUG:
        uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
    else:
        uvicorn.run(app, host=config.HOST, port=config.PORT)