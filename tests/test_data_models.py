"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Tests für Data Models und Database
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.data.models import Mine, SearchSession, SearchResultDB, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestDataModels:
    """Tests für SQLAlchemy Datenmodelle"""
    
    def test_mine_model(self):
        """Test Mine Model"""
        mine = Mine(
            name="Test Mine",
            region="Test Region",
            country="Canada",
            betreiber="Test Corp",
            koordinaten="45.5° N, 73.6° W",
            rohstofftyp="Gold",
            produktion="100k tons",
            aktivitaetsstatus=MineStatus.PRODUCING,
            sanierungskosten="50M USD"
        )
        
        assert mine.name == "Test Mine"
        assert mine.aktivitaetsstatus == MineStatus.PRODUCING
        assert mine.is_active is True
        
        # Test String representation
        assert "Test Mine" in str(mine)
        assert "Canada" in str(mine)
    
    def test_mine_status_enum(self):
        """Test MineStatus Enum"""
        assert MineStatus.EXPLORATION.value == "exploration"
        assert MineStatus.PRODUCING.value == "producing"
        assert MineStatus.SUSPENDED.value == "suspended"
        assert MineStatus.CLOSED.value == "closed"
        assert MineStatus.UNKNOWN.value == "unknown"
    
    def test_search_session_model(self):
        """Test SearchSession Model"""
        session = SearchSession(
            mine_name="Test Mine",
            region="Test Region",
            country="Canada",
            languages=["en", "fr"],
            mode="standard",
            total_agents=5,
            successful_agents=4,
            failed_agents=1,
            total_results=20,
            unique_fields=8,
            execution_time=45.5,
            discovered_sources=10
        )
        
        assert session.mine_name == "Test Mine"
        assert session.languages == ["en", "fr"]
        assert session.success_rate == 80.0  # 4/5 * 100
    
    def test_search_result_model(self):
        """Test SearchResult Model"""
        result = DBSearchResult(
            mine_id=1,
            session_id=1,
            field_name="betreiber",
            value="Test Corp",
            source="tavily",
            confidence_score=0.95,
            metadata={"url": "http://example.com"}
        )
        
        assert result.field_name == "betreiber"
        assert result.confidence_score == 0.95
        assert result.metadata["url"] == "http://example.com"


@pytest.mark.asyncio
class TestDatabase:
    """Tests für Database Klasse"""
    
    @pytest.fixture
    async def test_db(self, mock_config):
        """Test-Datenbank"""
        db = Database(mock_config.database_config)
        await db.initialize()
        yield db
        await db.close()
    
    @pytest.mark.asyncio
    async def test_create_mine(self, test_db):
        """Test Mine erstellen"""
        mine_data = {
            "name": "Create Test Mine",
            "region": "Ontario",
            "country": "Canada",
            "betreiber": "Test Mining Corp"
        }
        
        mine = await test_db.create_mine(**mine_data)
        
        assert mine.id is not None
        assert mine.name == "Create Test Mine"
        assert mine.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_mine_by_name(self, test_db):
        """Test Mine nach Name finden"""
        # Erstelle Mine
        mine_data = {
            "name": "Find Test Mine",
            "region": "Quebec",
            "country": "Canada"
        }
        created = await test_db.create_mine(**mine_data)
        
        # Finde Mine
        found = await test_db.get_mine_by_name("Find Test Mine")
        
        assert found is not None
        assert found.id == created.id
        assert found.region == "Quebec"
    
    @pytest.mark.asyncio
    async def test_update_mine(self, test_db):
        """Test Mine aktualisieren"""
        # Erstelle Mine
        mine = await test_db.create_mine(
            name="Update Test Mine",
            region="BC",
            country="Canada"
        )
        
        # Aktualisiere
        updated = await test_db.update_mine(
            mine.id,
            betreiber="New Operator",
            produktion="200k tons"
        )
        
        assert updated.betreiber == "New Operator"
        assert updated.produktion == "200k tons"
        assert updated.updated_at > mine.created_at
    
    @pytest.mark.asyncio
    async def test_create_search_session(self, test_db):
        """Test SearchSession erstellen"""
        # Erstelle Mine
        mine = await test_db.create_mine(
            name="Session Test Mine",
            region="Alberta",
            country="Canada"
        )
        
        # Erstelle Session
        session_data = {
            "mine_id": mine.id,
            "mine_name": mine.name,
            "region": mine.region,
            "country": mine.country,
            "languages": ["en"],
            "mode": "fast",
            "total_agents": 3,
            "successful_agents": 3,
            "failed_agents": 0,
            "total_results": 15,
            "unique_fields": 5,
            "execution_time": 12.5
        }
        
        session = await test_db.create_search_session(**session_data)
        
        assert session.id is not None
        assert session.mine_id == mine.id
        assert session.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_add_search_result(self, test_db):
        """Test SearchResult hinzufügen"""
        # Erstelle Mine und Session
        mine = await test_db.create_mine(
            name="Result Test Mine",
            region="Saskatchewan",
            country="Canada"
        )
        
        session = await test_db.create_search_session(
            mine_id=mine.id,
            mine_name=mine.name,
            region=mine.region,
            country=mine.country,
            languages=["en"],
            mode="standard"
        )
        
        # Füge Result hinzu
        result = await test_db.add_search_result(
            mine_id=mine.id,
            session_id=session.id,
            field_name="koordinaten",
            value="52.1° N, 106.6° W",
            source="tavily",
            confidence_score=0.9,
            metadata={"method": "extraction"}
        )
        
        assert result.id is not None
        assert result.mine_id == mine.id
        assert result.session_id == session.id
    
    @pytest.mark.asyncio
    async def test_get_latest_mine_data(self, test_db):
        """Test neueste Mine-Daten abrufen"""
        # Erstelle Mine mit Daten
        mine = await test_db.create_mine(
            name="Latest Data Mine",
            region="Yukon",
            country="Canada"
        )
        
        session = await test_db.create_search_session(
            mine_id=mine.id,
            mine_name=mine.name,
            region=mine.region,
            country=mine.country,
            languages=["en"],
            mode="standard"
        )
        
        # Füge mehrere Results hinzu
        await test_db.add_search_result(
            mine_id=mine.id,
            session_id=session.id,
            field_name="betreiber",
            value="Old Operator",
            source="source1",
            confidence_score=0.7
        )
        
        await test_db.add_search_result(
            mine_id=mine.id,
            session_id=session.id,
            field_name="betreiber",
            value="New Operator",
            source="source2",
            confidence_score=0.9
        )
        
        # Hole neueste Daten
        latest = await test_db.get_latest_mine_data(mine.id)
        
        assert "betreiber" in latest
        # Sollte höhere Confidence wählen
        assert latest["betreiber"]["value"] == "New Operator"
        assert latest["betreiber"]["confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_search_mines(self, test_db):
        """Test Mine-Suche"""
        # Erstelle mehrere Minen
        await test_db.create_mine(
            name="Search Test 1",
            region="Ontario",
            country="Canada",
            rohstofftyp="Gold"
        )
        
        await test_db.create_mine(
            name="Search Test 2",
            region="Quebec",
            country="Canada",
            rohstofftyp="Silver"
        )
        
        await test_db.create_mine(
            name="Different Mine",
            region="NSW",
            country="Australia",
            rohstofftyp="Coal"
        )
        
        # Suche nach Land
        canada_mines = await test_db.search_mines(country="Canada")
        assert len(canada_mines) >= 2
        
        # Suche nach Rohstoff
        gold_mines = await test_db.search_mines(commodity="Gold")
        assert len(gold_mines) >= 1
        
        # Suche nach Name
        search_mines = await test_db.search_mines(name_contains="Search Test")
        assert len(search_mines) >= 2
    
    @pytest.mark.asyncio
    async def test_get_search_statistics(self, test_db):
        """Test Such-Statistiken"""
        # Erstelle Test-Daten
        mine = await test_db.create_mine(
            name="Stats Test Mine",
            region="NWT",
            country="Canada"
        )
        
        # Mehrere Sessions
        for i in range(3):
            await test_db.create_search_session(
                mine_id=mine.id,
                mine_name=mine.name,
                region=mine.region,
                country=mine.country,
                languages=["en"],
                mode="standard",
                total_agents=5,
                successful_agents=4,
                failed_agents=1,
                total_results=20,
                unique_fields=8,
                execution_time=30.0 + i * 5
            )
        
        # Hole Statistiken
        stats = await test_db.get_search_statistics()
        
        assert stats["total_mines"] >= 1
        assert stats["total_searches"] >= 3
        assert stats["average_search_time"] > 0
        assert stats["average_success_rate"] == 80.0  # 4/5 * 100
    
    @pytest.mark.asyncio
    async def test_export_mine_data(self, test_db):
        """Test Mine-Daten Export"""
        # Erstelle Mine mit vollständigen Daten
        mine = await test_db.create_mine(
            name="Export Test Mine",
            region="Manitoba",
            country="Canada",
            betreiber="Export Mining Corp",
            koordinaten="55.0° N, 97.0° W",
            rohstofftyp="Nickel",
            produktion="500k tons",
            aktivitaetsstatus=MineStatus.PRODUCING,
            sanierungskosten="100M CAD"
        )
        
        # Exportiere
        export_data = await test_db.export_mine_data(mine.id)
        
        assert export_data["mine"]["name"] == "Export Test Mine"
        assert export_data["mine"]["betreiber"] == "Export Mining Corp"
        assert "search_history" in export_data
        assert "latest_results" in export_data
    
    @pytest.mark.asyncio
    async def test_duplicate_mine_constraint(self, test_db):
        """Test Unique Constraint für Mine Name"""
        # Erstelle erste Mine
        await test_db.create_mine(
            name="Unique Test Mine",
            region="Region 1",
            country="Country 1"
        )
        
        # Versuche Duplikat zu erstellen
        with pytest.raises(IntegrityError):
            await test_db.create_mine(
                name="Unique Test Mine",
                region="Region 2",
                country="Country 2"
            )
    
    @pytest.mark.asyncio
    async def test_cascade_delete(self, test_db):
        """Test Cascade Delete"""
        # Erstelle Mine mit Results
        mine = await test_db.create_mine(
            name="Cascade Test Mine",
            region="Region",
            country="Country"
        )
        
        session = await test_db.create_search_session(
            mine_id=mine.id,
            mine_name=mine.name,
            region=mine.region,
            country=mine.country,
            languages=["en"],
            mode="standard"
        )
        
        await test_db.add_search_result(
            mine_id=mine.id,
            session_id=session.id,
            field_name="test",
            value="test",
            source="test",
            confidence_score=0.5
        )
        
        # Lösche Mine
        await test_db.delete_mine(mine.id)
        
        # Prüfe dass alles gelöscht wurde
        found = await test_db.get_mine_by_name("Cascade Test Mine")
        assert found is None


class TestDatabaseExtensions:
    """Tests für Database Extensions"""
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_db):
        """Test Bulk-Operationen"""
        # Bulk create mines
        mines_data = [
            {"name": f"Bulk Mine {i}", "region": "Region", "country": "Country"}
            for i in range(10)
        ]
        
        created = await test_db.bulk_create_mines(mines_data)
        assert len(created) == 10
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db):
        """Test Transaktion Rollback"""
        try:
            async with test_db.session() as session:
                # Erstelle Mine in Transaktion
                mine = Mine(
                    name="Transaction Test",
                    region="Region",
                    country="Country"
                )
                session.add(mine)
                
                # Force error
                raise Exception("Test rollback")
        except:
            pass
        
        # Mine sollte nicht existieren
        found = await test_db.get_mine_by_name("Transaction Test")
        assert found is None


# Performance Tests
@pytest.mark.performance
class TestDatabasePerformance:
    """Performance Tests für Database"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_dataset_performance(self, test_db):
        """Test Performance mit großem Datensatz"""
        import time
        
        # Erstelle viele Minen
        start = time.time()
        
        for i in range(100):
            await test_db.create_mine(
                name=f"Performance Mine {i}",
                region=f"Region {i % 10}",
                country=f"Country {i % 5}",
                rohstofftyp=f"Commodity {i % 3}"
            )
        
        create_time = time.time() - start
        
        # Suche
        start = time.time()
        results = await test_db.search_mines(country="Country 0")
        search_time = time.time() - start
        
        assert len(results) == 20  # 100 / 5
        assert create_time < 10  # Sollte unter 10 Sekunden sein
        assert search_time < 1   # Suche sollte schnell sein