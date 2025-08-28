"""
Author: rahn
Datum: 09.08.2025  
Version: 2.1
Beschreibung: API Routes Registry
"""

from fastapi import APIRouter
from starlette.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)


def get_api_router() -> APIRouter:
    """Erstellt und konfiguriert den Haupt-API-Router"""
    router = APIRouter()
    
    # Root-Route für Frontend
    @router.get("/")
    async def root_redirect():
        return RedirectResponse(url="/static/index.html")
    
    try:
        # Lade Core Routes einzeln mit detailliertem Logging
        try:
            from .models_info import router as models_router
            router.include_router(models_router, prefix="/api", tags=["models"])
            logger.info("✅ models_info Route erfolgreich geladen")
        except Exception as models_err:
            logger.error(f"❌ models_info Route Fehler: {models_err}")
            raise
            
        try:
            from .sources import router as sources_router 
            router.include_router(sources_router, prefix="/api", tags=["sources"])
            logger.info("✅ sources Route erfolgreich geladen")
        except Exception as sources_err:
            logger.error(f"❌ sources Route Fehler: {sources_err}")
            
        try:
            from .search import router as search_router
            router.include_router(search_router, prefix="/api", tags=["search"])
            logger.info("✅ search Route erfolgreich geladen")
        except Exception as search_err:
            logger.error(f"❌ search Route Fehler: {search_err}")
            
        # NOTFALL 23.08.2025: Aktiviere ursprüngliche Batch-Route
        try:
            from .batch import router as batch_router
            router.include_router(batch_router, prefix="/api", tags=["batch"])
            logger.info("✅ batch Route erfolgreich geladen")
        except Exception as batch_err:
            logger.error(f"❌ batch Route Fehler: {batch_err}")
        logger.info("✅ Ursprüngliche batch Route aktiviert für CSV-Upload")
            
        # DEAKTIVIERT 23.08.2025: Fixed batch route hat Syntaxfehler
        # try:
        #     import sys
        #     import os
        #     sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
        #     from batch_route_fixed import create_fixed_batch_route
        #     from minesearch.database import db_manager
        #     from .batch import batch_results_cache  # Import cache from original batch module
        #     
        #     fixed_batch_router = create_fixed_batch_route(db_manager, batch_results_cache)
        #     router.include_router(fixed_batch_router, prefix="/api", tags=["batch-fixed"])
        #     logger.info("✅ FIXED batch Route erfolgreich geladen (DB-First)")
        # except Exception as fixed_batch_err:
        #     logger.error(f"❌ FIXED batch Route Fehler: {fixed_batch_err}")
        logger.info("⚠️ Fixed batch Route temporär deaktiviert wegen Syntaxfehler")
            
        try:
            from .statistics import router as statistics_router
            router.include_router(statistics_router, prefix="/api", tags=["statistics"])
            logger.info("✅ statistics Route erfolgreich geladen")
        except Exception as stats_err:
            logger.error(f"❌ statistics Route Fehler: {stats_err}")
            
        try:
            from .results import router as results_router
            router.include_router(results_router, prefix="/api", tags=["results"])
            logger.info("✅ results Route erfolgreich geladen")
        except Exception as results_err:
            logger.error(f"❌ results Route Fehler: {results_err}")
            
        # PHASE 4: Registrierung fehlender wichtiger Module
        try:
            from .consolidated_results import router as consolidated_results_router
            router.include_router(consolidated_results_router, prefix="/api/consolidated", tags=["consolidated-results"])
            logger.info("✅ consolidated_results Route erfolgreich geladen")
        except Exception as consolidated_err:
            logger.error(f"❌ consolidated_results Route Fehler: {consolidated_err}")
            
        # TEMPORÄR DEAKTIVIERT: Benchmark Route wegen Import-Problemen
        # try:
        #     from .benchmark import router as benchmark_router
        #     router.include_router(benchmark_router, prefix="/api", tags=["benchmark"])
        #     logger.info("✅ benchmark Route erfolgreich geladen")
        # except Exception as benchmark_err:
        #     logger.error(f"❌ benchmark Route Fehler: {benchmark_err}")
        #     # Continue without benchmark route
        logger.info("⚠️ benchmark Route temporär deaktiviert")
            
        # Registriere weitere wichtige Module
        try:
            from .static import router as static_router
            router.include_router(static_router, prefix="/static", tags=["static"])
            logger.info("✅ static Route erfolgreich geladen")
        except Exception as static_err:
            logger.error(f"❌ static Route Fehler: {static_err}")
            
        try:
            from .progress import router as progress_router
            router.include_router(progress_router, prefix="/api", tags=["progress"])
            logger.info("✅ progress Route erfolgreich geladen")
        except Exception as progress_err:
            logger.error(f"❌ progress Route Fehler: {progress_err}")
            
        # PROVIDER-STATUS 24.08.2025: API Key Validation und Provider Health Checks
        try:
            from .provider_status import router as provider_status_router
            router.include_router(provider_status_router, prefix="/api", tags=["provider-status"])
            logger.info("✅ provider_status Route erfolgreich geladen")
        except Exception as provider_status_err:
            logger.error(f"❌ provider_status Route Fehler: {provider_status_err}")
        
        # TEMPLATE-MONITORING 26.08.2025: REGEL 10 Compliance Monitoring
        try:
            from .template_monitor import router as template_monitor_router
            router.include_router(template_monitor_router, tags=["template-monitor"])
            logger.info("✅ template_monitor Route erfolgreich geladen")
        except Exception as template_monitor_err:
            logger.error(f"❌ template_monitor Route Fehler: {template_monitor_err}")
        
        # DATABASE-VIEWER 27.08.2025: Read-Only Zugriff auf alle DB-Tabellen
        try:
            from .database import router as database_router
            router.include_router(database_router, prefix="/api/database", tags=["database"])
            logger.info("✅ database Route erfolgreich geladen")
        except Exception as database_err:
            logger.error(f"❌ database Route Fehler: {database_err}")
        
    except ImportError as e:
        logger.error(f"❌ CRITICAL: Route Import komplett fehlgeschlagen: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Fallback mit minimalen Routes
        @router.get("/api/health")
        async def health():
            return {"status": "ok", "mode": "fallback", "error": str(e)}
            
        @router.get("/api/models")
        async def models():
            return {"models": [], "error": "Import error in routes"}
    
    return router