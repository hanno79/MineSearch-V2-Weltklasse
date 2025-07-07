"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Exception Handler für MineSearch API
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    """Konfiguriert Exception Handler für die FastAPI App"""
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.error(f"ValueError: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unerwarteter Fehler: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Interner Serverfehler"}
        )