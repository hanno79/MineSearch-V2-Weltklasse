#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Utility-Funktionen für einheitliche Datenbankverwendung
"""

import sqlite3
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

def get_db_connection_string() -> str:
    """
    Hole die zentrale Datenbank-URL aus der Konfiguration
    
    Returns:
        Datenbank-URL aus config.DATABASE_URL
    """
    try:
        from minesearch.config.base import config
        return config.DATABASE_URL
    except ImportError:
        # Fallback für Scripts außerhalb des Backend-Moduls - nutze absoluten Pfad
        return "sqlite:////app/backend/mines.db"

def get_sqlite_path_from_url(database_url: Optional[str] = None) -> str:
    """
    Extrahiere SQLite-Pfad aus Datenbank-URL
    
    Args:
        database_url: Optional - falls None, wird config.DATABASE_URL verwendet
        
    Returns:
        Absoluter Pfad zur SQLite-Datenbank
        
    Raises:
        ValueError: Falls URL kein SQLite-Schema hat
    """
    if database_url is None:
        database_url = get_db_connection_string()
    
    if not database_url.startswith('sqlite:///'):
        raise ValueError(f"Nur SQLite-URLs werden unterstützt. Erhalten: {database_url}")
    
    # Entferne 'sqlite:///' Präfix
    db_path = database_url.replace('sqlite:///', '')
    
    # Stelle sicher, dass der Pfad absolut ist
    path = Path(db_path)
    if not path.is_absolute():
        # Falls relativer Pfad, mache ihn absolut von der Projekt-Root aus
        project_root = Path(__file__).resolve().parents[4]  # 4 Ebenen hoch zu /app
        path = (project_root / db_path).resolve()
    
    return str(path)

def get_sqlite_connection(database_url: Optional[str] = None) -> sqlite3.Connection:
    """
    Erstelle SQLite-Verbindung mit korrekten Einstellungen
    
    Args:
        database_url: Optional - falls None, wird config.DATABASE_URL verwendet
        
    Returns:
        SQLite-Connection mit Foreign Keys aktiviert
    """
    db_path = get_sqlite_path_from_url(database_url)
    conn = sqlite3.connect(db_path)
    
    # Aktiviere Foreign Key Constraints
    conn.execute("PRAGMA foreign_keys=ON")
    
    # Row Factory für dict-ähnlichen Zugriff
    conn.row_factory = sqlite3.Row
    
    return conn

def get_normalized_db_path() -> str:
    """
    NORMALISIERTE DATENBANK-PFAD
    
    Returns:
        Absoluter Pfad zur normalisierten Hauptdatenbank
    """
    return get_sqlite_path_from_url()

# Für Kompatibilität - Legacy-Funktionen die deprecated sind
def get_legacy_db_path() -> str:
    """
    DEPRECATED: Nutze get_normalized_db_path()
    
    Returns:
        Pfad zur normalisierten Datenbank
    """
    import warnings
    warnings.warn(
        "get_legacy_db_path() ist deprecated. Nutze get_normalized_db_path()",
        DeprecationWarning,
        stacklevel=2
    )
    return get_normalized_db_path()