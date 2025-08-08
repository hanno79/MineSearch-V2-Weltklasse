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
from .consolidated_results import router as consolidated_results_router
from .mines import router as mines_router
from .models_info import router as models_router
from .static import router as static_router
from .cache import router as cache_router
from .benchmark import router as benchmark_router
from .health import router as health_router
from .test_search import router as test_search_router
from .statistics import router as statistics_router
from .statistics_advanced import router as statistics_advanced_router
from .statistics_core import router as statistics_core_router
# statistics_utils hat keinen router - ist nur eine Utility-Klasse

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

# Sub-Router einbinden - WICHTIG: Spezifischere Routen ZUERST!
router.include_router(static_router)
router.include_router(search_router, prefix="/api", tags=["search"])
router.include_router(batch_router, prefix="/api", tags=["batch"])
router.include_router(sources_router, prefix="/api", tags=["sources"])
router.include_router(consolidated_results_router, prefix="/api", tags=["consolidated"])  # ZUERST: spezifische /results/consolidated
router.include_router(results_router, prefix="/api", tags=["results"])  # DANACH: allgemeine /results/{id}
router.include_router(mines_router, prefix="/api", tags=["mines"])
router.include_router(models_router, prefix="/api", tags=["models"])
router.include_router(cache_router, prefix="/api", tags=["cache"])
router.include_router(benchmark_router)
router.include_router(health_router, prefix="/api", tags=["health"])
router.include_router(test_search_router, prefix="/api", tags=["test"])

# PHASE 1 FIX: Statistics-Router einbinden
router.include_router(statistics_router, prefix="/api", tags=["statistics"])
router.include_router(statistics_advanced_router, prefix="/api", tags=["statistics-advanced"])  
router.include_router(statistics_core_router, prefix="/api", tags=["statistics-core"])
# statistics_utils_router entfernt - ist nur eine Utility-Klasse