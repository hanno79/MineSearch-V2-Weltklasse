"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Middleware-Konfiguration für MineSearch API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI):
    """Konfiguriert alle Middleware für die FastAPI App"""

    # CORS konfigurieren - Frontend-Ports hinzufügen
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",  # Frontend-Port hinzugefügt
            "http://127.0.0.1:8080",  # Frontend-Port hinzugefügt
            "http://localhost:8000",  # Backend selbst für direkte Tests
            "http://127.0.0.1:8000"   # Backend selbst für direkte Tests
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Middleware erfolgreich konfiguriert")
