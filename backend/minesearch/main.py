"""
Author: rahn
Datum: 04.07.2025
Version: 2.1
Beschreibung: MineSearch 2.1 - Refactored Main Application
"""

# ABACUS-FIX 18.07.2025: Force correct .env loading before any imports
from dotenv import load_dotenv
from pathlib import Path
# Lade Root-.env (Projektwurzel)
root_env = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(root_env, override=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
import logging
import os
from contextlib import asynccontextmanager

from minesearch.config.base import config
from .api.middleware import setup_middleware
from .api.handlers import setup_exception_handlers

SAFE_MODE = os.getenv('SAFE_MODE', '0') == '1'

if not SAFE_MODE:
    from minesearch.providers.registry import provider_registry
    from minesearch.config.api_keys import APIKeysConfig

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
    logger.info("MineSearch v2.1 startet...")

    if SAFE_MODE:
        logger.warning("SAFE_MODE aktiv – Provider/DB-Initialisierung wird übersprungen")
        yield
        logger.info("MineSearch v2.1 wird beendet (SAFE_MODE)...")
        return

    # Provider-Registry initialisieren
    try:
        logger.info("Validiere API-Keys...")
        api_keys_valid = APIKeysConfig.validate_all_keys()
        if not api_keys_valid:
            missing_keys = APIKeysConfig.get_missing_keys()
            logger.warning(f"⚠️  Fehlende API-Keys: {', '.join(missing_keys)}")
            logger.warning("Einige Provider sind möglicherweise nicht verfügbar.")
        provider_registry.initialize(config.PROVIDERS)
        available_models = list(provider_registry.get_all_models().keys())
        logger.info(f"Provider-Registry initialisiert. Verfügbare Modelle: {available_models}")
        if not available_models:
            raise ValueError("Keine Provider-Modelle verfügbar. Bitte API-Keys in .env prüfen.")
    except Exception as e:
        logger.error(f"Fehler bei Provider-Initialisierung: {type(e).__name__}: {e}")
        raise

    # Datenbank initialisieren
    try:
        from .database import db_manager
        logger.info("Datenbank erfolgreich initialisiert")
    except Exception as e:
        logger.error(f"Datenbank-Fehler: {type(e).__name__}: {e}")
        raise

    yield
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
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")

# Statische Dateien für CSV-Zugriff
app.mount("/csv", StaticFiles(directory="/app"), name="csv")

# API-Router einbinden
if SAFE_MODE:
    # Nur leichte Router laden (keine schweren Such-/Provider-Imports)
    try:
        from .api.routes.static import router as static_router
        app.include_router(static_router)
        # Root auf /static/index.html umleiten
        @app.get("/")
        async def root_redirect():
            return RedirectResponse(url="/static/index.html")
    except Exception as e:
        logger.error(f"SAFE_MODE Router-Initialisierung fehlgeschlagen: {e}")
else:
    from .api.routes import router as api_router
    app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    
    if config.DEBUG:
        uvicorn.run("backend.minesearch.main:app", host=config.HOST, port=config.PORT, reload=True)
    else:
        uvicorn.run(app, host=config.HOST, port=config.PORT)