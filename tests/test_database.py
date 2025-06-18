import pytest
import tempfile
from pathlib import Path
from src.core.database import DatabaseManager, Mine, Search, Result


@pytest.fixture
def temp_db():
    """Fixture für temporäre Test-Datenbank"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Mock config
    class MockConfig:
        class DatabaseConfig:
            path = db_path
        database = DatabaseConfig()
        debug_mode = False
    
    db_manager = DatabaseManager()
    db_manager.config = MockConfig()
    
    # Override engine to use temp database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    db_manager.engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create tables
    from src.core.database import Base
    Base.metadata.create_all(bind=db_manager.engine)
    
    # Session Factory
    db_manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_manager.engine)
    
    yield db_manager
    
    # Cleanup
    Path(db_path).unlink()


def test_create_mine(temp_db):
    """Test Mine erstellen"""
    mine = temp_db.create_mine(
        name="Create Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en", "fr"]
    )
    
    assert mine.id is not None
    assert mine.name == "Create Test Mine"
    assert mine.languages == ["en", "fr"]


def test_get_or_create_mine(temp_db):
    """Test get_or_create Mine"""
    # Erste Erstellung
    mine1 = temp_db.get_or_create_mine(
        name="GetOrCreate Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en"]
    )
    
    # Zweiter Aufruf sollte gleiche Mine zurückgeben
    mine2 = temp_db.get_or_create_mine(
        name="GetOrCreate Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en"]
    )
    
    assert mine1.id == mine2.id


def test_search_workflow(temp_db):
    """Test kompletter Such-Workflow"""
    # Mine erstellen
    mine = temp_db.create_mine(
        name="Workflow Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en"]
    )
    
    # Suchlauf starten
    search = temp_db.create_search(
        mine_id=mine.id,
        agents=["claude", "scraper"]
    )
    
    assert search.status == "running"
    
    # Ergebnis hinzufügen
    temp_db.add_result(
        search_id=search.id,
        mine_id=mine.id,
        result_data={
            "field_name": "betreiber",
            "value": "Test Corp",
            "source": "Test Source",
            "confidence_score": 0.95,
            "agent_name": "claude"
        }
    )
    
    # Suchlauf abschließen
    temp_db.complete_search(search.id)
    
    # Prüfe Ergebnisse
    results = temp_db.get_mine_results(mine.id)
    assert len(results) == 1
    assert results[0].value == "Test Corp"