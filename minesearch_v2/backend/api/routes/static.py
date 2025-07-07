"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Statische Seiten-Routes
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Hauptseite mit Suchformular"""
    try:
        with open("../frontend/index.html", "rb") as f:
            content = f.read()
            # Versuche verschiedene Encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Fallback: Ignoriere fehlerhafte Zeichen
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Fehler beim Laden der HTML-Datei: {e}")
        return "<h1>Fehler beim Laden der Seite</h1>"

@router.get("/sources", response_class=HTMLResponse)
async def sources_page():
    """Quellen-Datenbank Seite"""
    try:
        with open("../frontend/sources.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Fehler beim Laden der Quellen-Seite: {e}")
        return "<h1>Fehler beim Laden der Seite</h1>"