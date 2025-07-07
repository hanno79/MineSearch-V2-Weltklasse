"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: Datenbank-Initialisierung für MineSearch v2
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import text
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialisiere die Datenbank mit dem benötigten Schema"""
    
    # Datenbank-URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./mines.db')
    
    print(f"Initialisiere Datenbank: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    metadata = MetaData()
    
    # Define mines table
    mines_table = Table('mines', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String, nullable=False),
        Column('country', String),
        Column('region', String),
        Column('commodity', String),
        Column('owner', String),
        Column('operator', String),
        Column('status', String),
        Column('type', String),
        Column('latitude', Float),
        Column('longitude', Float),
        Column('production_start', Integer),
        Column('production_end', Integer),
        Column('production_volume', String),
        Column('area_km2', Float),
        Column('restoration_costs', String),
        Column('currency', String),
        Column('languages', String),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Define search_results table
    search_results_table = Table('search_results', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('session_id', String, nullable=False),
        Column('mine_name', String, nullable=False),
        Column('country', String),
        Column('commodity', String),
        Column('model_id', String),
        Column('provider', String),
        Column('success', Boolean),
        Column('search_duration', Float),
        Column('structured_data', Text),  # JSON
        Column('sources', Text),  # JSON
        Column('metadata', Text),  # JSON
        Column('error', Text),
        Column('created_at', DateTime, default=datetime.utcnow)
    )
    
    # Define sources table
    sources_table = Table('sources', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('url', String, unique=True),
        Column('domain', String),
        Column('type', String),
        Column('title', String),
        Column('description', Text),
        Column('quality_score', Float),
        Column('last_accessed', DateTime),
        Column('metadata', Text),  # JSON
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Create all tables
    metadata.create_all(engine)
    
    # Verify tables exist
    with engine.connect() as conn:
        # Check mines table
        result = conn.execute(text("SELECT COUNT(*) FROM mines"))
        count = result.scalar()
        print(f"✅ Tabelle 'mines' erstellt/vorhanden - {count} Einträge")
        
        # Check search_results table
        result = conn.execute(text("SELECT COUNT(*) FROM search_results"))
        count = result.scalar()
        print(f"✅ Tabelle 'search_results' erstellt/vorhanden - {count} Einträge")
        
        # Check sources table
        result = conn.execute(text("SELECT COUNT(*) FROM sources"))
        count = result.scalar()
        print(f"✅ Tabelle 'sources' erstellt/vorhanden - {count} Einträge")
    
    print("\n✅ Datenbank-Initialisierung abgeschlossen!")
    
    return True

if __name__ == "__main__":
    init_database()