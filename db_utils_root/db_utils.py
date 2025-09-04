#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: ROOT-LEVEL Database Utils für Scripts außerhalb des Backend-Moduls
"""

import sqlite3
import sys
import os
from pathlib import Path
from typing import Optional

def get_normalized_db_path() -> str:
    """
    Hole den normalisierten DB-Pfad für Root-Level-Scripts
    
    Returns:
        Absoluter Pfad zur normalisierten Hauptdatenbank
    """
    # EINZIGE normalisierte Datenbank
    return "/app/backend/mines.db"

def get_sqlite_connection(database_url: Optional[str] = None) -> sqlite3.Connection:
    """
    Erstelle SQLite-Verbindung mit korrekten Einstellungen für Root-Level-Scripts
    
    Returns:
        SQLite-Connection mit Foreign Keys aktiviert
    """
    db_path = get_normalized_db_path()
    conn = sqlite3.connect(db_path)
    
    # Aktiviere Foreign Key Constraints
    conn.execute("PRAGMA foreign_keys=ON")
    
    # Row Factory für dict-ähnlichen Zugriff
    conn.row_factory = sqlite3.Row
    
    return conn

# Legacy-Kompatibilität
def get_db_connection_string() -> str:
    """DEPRECATED: Nutze get_normalized_db_path()"""
    return f"sqlite:///{get_normalized_db_path()}"