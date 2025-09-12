"""
Author: rahn
Datum: 06.08.2025
Version: 2.0
Beschreibung: Statistics API Router Orchestrator - Koordiniert alle Statistik-Endpunkte
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Orchestrator-Pattern implementiert
"""

import logging
from fastapi import APIRouter

# Refactored Module imports
from minesearch.api.routes.statistics_core import statistics_core_router, STATISTICS_FIELD_ORDER
from minesearch.api.routes.statistics_advanced import statistics_advanced_router
from minesearch.api.routes.statistics_utils import statistics_calculator, statistics_analyzer, statistics_time_analyzer

logger = logging.getLogger(__name__)

# Hauptrouter der alle Sub-Router koordiniert
router = APIRouter()

# Include aller Sub-Router
router.include_router(statistics_core_router)
router.include_router(statistics_advanced_router)

# Export wichtiger Konstanten und Utilities für Backward Compatibility
__all__ = [
    'router',
    'STATISTICS_FIELD_ORDER',
    'statistics_calculator',
    'statistics_analyzer',
    'statistics_time_analyzer'
]

@router.get("/health")
async def statistics_health_check():
    """
    Health Check für Statistics API Orchestrator
    """
    try:
        return {
            'status': 'healthy',
            'modules': {
                'core_statistics': 'active',
                'advanced_statistics': 'active',
                'utilities': 'active'
            },
            'version': '2.0',
            'refactored': True
        }
    except Exception as e:
        logger.error(f"[STATS-ORCHESTRATOR] Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

# Compatibility Layer für Legacy-Code
def calculate_field_coverage(field_data: dict) -> float:
    """Backward compatibility function"""
    return statistics_calculator.calculate_avg_field_coverage([])

def calculate_reliability_trend(queries: list) -> list:
    """Backward compatibility function"""
    return statistics_calculator.calculate_reliability_trend(queries)

def calculate_field_breakdown(queries: list) -> dict:
    """Backward compatibility function"""
    return statistics_calculator.calculate_field_breakdown(queries)

async def analyze_field_sources(session, field_name: str) -> dict:
    """Backward compatibility function"""
    return await statistics_analyzer.analyze_specific_field_coverage(session, field_name, [])

async def analyze_system_bottlenecks(session, search_results: list) -> dict:
    """Backward compatibility function"""
    return await statistics_analyzer.analyze_system_bottlenecks(session, search_results)

def create_time_buckets(start_date, granularity: str, days_back: int) -> dict:
    """Backward compatibility function"""
    return statistics_time_analyzer.create_time_buckets(start_date, granularity, days_back)

logger.info("[STATS-ORCHESTRATOR] Statistics API Orchestrator initialisiert - 3 Module koordiniert")
