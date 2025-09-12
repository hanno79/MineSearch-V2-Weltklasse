"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Statische Seiten-Routes
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, Response
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

# Frontend-Verzeichnis definieren
FRONTEND_PATH = Path("/app/frontend")

@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Hauptseite mit Suchformular"""
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    logger.error(f"Index-Datei nicht gefunden: {index_path}")
    return HTMLResponse("<h1>Fehler beim Laden der Seite</h1>", status_code=500)

@router.get("/sources", response_class=HTMLResponse)
async def sources_page():
    """Quellen-Datenbank Seite"""
    try:
        with open("/app/frontend/sources.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Fehler beim Laden der Quellen-Seite: {e}")
        return "<h1>Fehler beim Laden der Seite</h1>"

@router.get("/style.css")
async def get_style_css():
    """Serve style.css from frontend directory"""
    css_path = FRONTEND_PATH / "style.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    else:
        logger.error(f"CSS-Datei nicht gefunden: {css_path}")
        return {"error": "CSS file not found"}

@router.get("/favicon.ico")
async def get_favicon():
    """Serve favicon.ico"""
    favicon_path = FRONTEND_PATH / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/x-icon")
    else:
        # Return a simple 1x1 transparent pixel as fallback
        from fastapi.responses import Response
        transparent_pixel =
b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(content=transparent_pixel, media_type="image/png")
