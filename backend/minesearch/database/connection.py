"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Datenbank-Verbindung und Initialisierung für MineSearch v2
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging
from typing import Generator

from minesearch.config.base import config as Config
from minesearch.database.models import Base

logger = logging.getLogger(__name__)

# Globale Engine und Session Factory
engine = None
SessionLocal = None


def init_db():
    """Initialisiere Datenbank-Verbindung"""
    global engine, SessionLocal

    config = Config()
    database_url = config.get("DATABASE_URL", 'sqlite:///./mines.db')

    # PERFORMANCE FIX 02.09.2025: Connection Pooling konfiguriert für bessere Performance
    engine_args = {
        "pool_size": 10,  # Basis-Pool-Größe
        "max_overflow": 20,  # Zusätzliche Connections bei Bedarf
        "pool_timeout": 30,  # Timeout für Pool-Acquisition
        "pool_pre_ping": True,  # Connection-Validierung
        "pool_recycle": 3600,  # Connections recyceln nach 1h
    }

    if database_url.startswith('sqlite'):
        # SQLite-spezifische Optimierungen
        engine_args.update({
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,  # Connection timeout
            },
            "pool_size": 5,  # SQLite braucht weniger Connections
            "max_overflow": 10,
        })

    engine = create_engine(database_url, **engine_args)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Erstelle Tabellen
    Base.metadata.create_all(bind=engine)

    logger.info(f"Datenbank initialisiert: {database_url}")


def get_db() -> Generator[Session, None, None]:
    """Dependency für FastAPI/andere Frameworks"""
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """Hole neue Datenbank-Session"""
    if SessionLocal is None:
        init_db()

    return SessionLocal()
