"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: API Routes Module
"""

from fastapi import APIRouter
from .search import router as search_router
from .batch import router as batch_router
from .sources import router as sources_router
from .results import router as results_router
from .models_info import router as models_router
from .static import router as static_router
from .cache import router as cache_router
from .benchmark import router as benchmark_router

# Haupt-Router erstellen
router = APIRouter()

# Health-Check Endpoint
@router.get("/health")
async def health_check():
    """Health-Check Endpoint für Service-Management"""
    return {
        "status": "healthy",
        "service": "MineSearch v2.1", 
        "timestamp": "2025-07-12"
    }

# Sub-Router einbinden
router.include_router(static_router)
router.include_router(search_router, prefix="/api", tags=["search"])
router.include_router(batch_router, prefix="/api", tags=["batch"])
router.include_router(sources_router, prefix="/api", tags=["sources"])
router.include_router(results_router, prefix="/api", tags=["results"])
router.include_router(models_router, prefix="/api", tags=["models"])
router.include_router(cache_router, prefix="/api", tags=["cache"])
router.include_router(benchmark_router)