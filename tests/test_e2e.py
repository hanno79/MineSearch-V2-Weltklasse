"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: End-to-End Tests für das Mining Research System
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import json

from src.core.config import Config, APIConfig, DatabaseConfig
from src.core.database import Database
from src.core.orchestrator import Orchestrator, SearchMode
from src.agents.base_agent import SearchResult, AgentStatus
from src.data.models import MineStatus


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-End Tests für das komplette System"""
    
    @pytest.fixture
    async def e2e_system(self, temp_dir):
        """Komplettes System für E2E Tests"""
        # Konfiguration
        api_config = APIConfig(
            claude_key="test_key",
            openai_key="test_key",
            tavily_key="test_key",
            perplexity_key="test_key"
        )
        
        db_config = DatabaseConfig(
            path=str(temp_dir / "e2e_test.db"),
            echo=False
        )
        
        config = Config(
            api_config=api_config,
            database_config=db_config
        )
        
        # Datenbank
        db = Database(db_config)
        await db.initialize()
        
        # Orchestrator
        orchestrator = Orchestrator(config, db)
        
        # Mock Agents
        mock_agents = self._create_mock_agents()
        
        with patch('src.core.orchestrator.AgentFactory') as mock_factory:
            mock_factory.return_value.get_available_agents.return_value = mock_agents
            mock_factory.return_value.create_agent.side_effect = lambda name, config: mock_agents.get(name)
            
            await orchestrator.initialize()
        
        yield orchestrator
        
        await orchestrator.cleanup()
        await db.close()
    
    def _create_mock_agents(self):
        """Erstellt realistische Mock Agents"""
        agents = {}
        
        # Tavily - Web Search
        tavily = AsyncMock()
        tavily.name = "tavily"
        tavily.status = AgentStatus.ACTIVE
        tavily.initialize = AsyncMock(return_value=True)
        tavily.search = AsyncMock(side_effect=self._tavily_search)
        agents["tavily"] = tavily
        
        # Perplexity - AI Search
        perplexity = AsyncMock()
        perplexity.name = "perplexity"
        perplexity.status = AgentStatus.ACTIVE
        perplexity.initialize = AsyncMock(return_value=True)
        perplexity.search = AsyncMock(side_effect=self._perplexity_search)
        agents["perplexity"] = perplexity
        
        # Claude - Deep Analysis
        claude = AsyncMock()
        claude.name = "claude"
        claude.status = AgentStatus.ACTIVE
        claude.initialize = AsyncMock(return_value=True)
        claude.search = AsyncMock(side_effect=self._claude_search)
        agents["claude"] = claude
        
        # Scraper - Direct Extraction
        scraper = AsyncMock()
        scraper.name = "scraper"
        scraper.status = AgentStatus.ACTIVE
        scraper.initialize = AsyncMock(return_value=True)
        scraper.search = AsyncMock(side_effect=self._scraper_search)
        agents["scraper"] = scraper
        
        return agents
    
    async def _tavily_search(self, query):
        """Simuliert Tavily Suchergebnisse"""
        await asyncio.sleep(0.1)  # Simuliere Netzwerk-Latenz
        
        results = []
        
        if "Cerro Vanguardia" in query.mine_name:
            results.extend([
                SearchResult(
                    field_name="betreiber",
                    value="AngloGold Ashanti",
                    source="tavily: mining.com",
                    confidence_score=0.85,
                    metadata={"url": "https://mining.com/cerro-vanguardia"}
                ),
                SearchResult(
                    field_name="koordinaten",
                    value="48°20'S 69°42'W",
                    source="tavily: mindat.org",
                    confidence_score=0.92,
                    metadata={"url": "https://mindat.org/loc-123"}
                )
            ])
        
        return results
    
    async def _perplexity_search(self, query):
        """Simuliert Perplexity Suchergebnisse"""
        await asyncio.sleep(0.15)
        
        results = []
        
        if "Cerro Vanguardia" in query.mine_name:
            results.append(
                SearchResult(
                    field_name="rohstofftyp",
                    value="Gold, Silver",
                    source="perplexity: AI synthesis",
                    confidence_score=0.88,
                    metadata={"sources": ["mining journals", "company reports"]}
                )
            )
        
        return results
    
    async def _claude_search(self, query):
        """Simuliert Claude Analyse-Ergebnisse"""
        await asyncio.sleep(0.2)
        
        results = []
        
        if "sanierungskosten" in query.required_fields:
            results.append(
                SearchResult(
                    field_name="sanierungskosten",
                    value="85 million USD",
                    source="claude: analysis of environmental reports",
                    confidence_score=0.91,
                    metadata={
                        "analysis": "Based on similar mine sizes and environmental requirements",
                        "year": "2023 estimate"
                    }
                )
            )
        
        return results
    
    async def _scraper_search(self, query):
        """Simuliert Scraper Ergebnisse"""
        await asyncio.sleep(0.25)
        
        results = []
        
        if query.country == "Argentina":
            results.extend([
                SearchResult(
                    field_name="produktion",
                    value="250,000 oz gold/year",
                    source="scraper: government database",
                    confidence_score=0.95,
                    metadata={"official": True, "year": 2023}
                ),
                SearchResult(
                    field_name="aktivitaetsstatus",
                    value="producing",
                    source="scraper: mining ministry",
                    confidence_score=0.93,
                    metadata={"last_updated": "2024-01"}
                )
            ])
        
        return results
    
    @pytest.mark.asyncio
    async def test_complete_mine_search(self, e2e_system):
        """Test komplette Mine-Suche von Anfang bis Ende"""
        # Suche nach echter Mine
        results = await e2e_system.search_mine(
            mine_name="Cerro Vanguardia",
            region="Santa Cruz",
            country="Argentina",
            languages=["es", "en"],
            required_fields=[
                "betreiber", "koordinaten", "rohstofftyp",
                "produktion", "aktivitaetsstatus", "sanierungskosten"
            ],
            mode=SearchMode.DEEP,
            save_to_db=True
        )
        
        # Validiere Ergebnisse
        assert results["found_fields"]["betreiber"] == "AngloGold Ashanti"
        assert "48°20'S" in results["found_fields"]["koordinaten"]
        assert "Gold" in results["found_fields"]["rohstofftyp"]
        assert "250,000" in results["found_fields"]["produktion"]
        assert results["found_fields"]["aktivitaetsstatus"] == "producing"
        assert "85 million" in results["found_fields"]["sanierungskosten"]
        
        # Prüfe Metadaten
        metadata = results["search_metadata"]
        assert metadata["total_agents_used"] == 4
        assert metadata["total_results"] == 6
        assert metadata["execution_time"] > 0
        assert metadata["saved_to_db"] is True
        
        # Keine fehlenden Felder
        assert len(results["missing_fields"]) == 0
    
    @pytest.mark.asyncio
    async def test_progressive_search_modes(self, e2e_system):
        """Test verschiedene Such-Modi progressiv"""
        mine_params = {
            "mine_name": "Test Progressive Mine",
            "region": "Test Region",
            "country": "Canada",
            "required_fields": ["betreiber", "koordinaten", "produktion"]
        }
        
        # Fast Mode
        fast_results = await e2e_system.search_mine(**mine_params, mode=SearchMode.FAST)
        fast_time = fast_results["search_metadata"]["execution_time"]
        
        # Standard Mode
        standard_results = await e2e_system.search_mine(**mine_params, mode=SearchMode.STANDARD)
        standard_time = standard_results["search_metadata"]["execution_time"]
        
        # Deep Mode
        deep_results = await e2e_system.search_mine(**mine_params, mode=SearchMode.DEEP)
        deep_time = deep_results["search_metadata"]["execution_time"]
        
        # Zeiten sollten progressiv steigen
        assert fast_time < standard_time < deep_time
        
        # Mehr Agents in tieferen Modi
        assert (fast_results["search_metadata"]["total_agents_used"] <= 
                standard_results["search_metadata"]["total_agents_used"] <= 
                deep_results["search_metadata"]["total_agents_used"])
    
    @pytest.mark.asyncio
    async def test_multi_language_search(self, e2e_system):
        """Test Mehrsprachige Suche"""
        # Modifiziere Mock für spanische Ergebnisse
        e2e_system.agents["tavily"].search = AsyncMock(return_value=[
            SearchResult(
                field_name="betreiber",
                value="Minera Ejemplo S.A.",
                source="tavily: gobierno.ar",
                confidence_score=0.9,
                metadata={"language": "es"}
            )
        ])
        
        results = await e2e_system.search_mine(
            mine_name="Mina Ejemplo",
            region="Mendoza",
            country="Argentina",
            languages=["es", "en"],
            required_fields=["betreiber"]
        )
        
        assert results["found_fields"]["betreiber"] == "Minera Ejemplo S.A."
        
        # Prüfe dass Sprachen verwendet wurden
        for agent in e2e_system.agents.values():
            if agent.search.called:
                query = agent.search.call_args[0][0]
                assert query.languages == ["es", "en"]
    
    @pytest.mark.asyncio
    async def test_search_with_cancellation(self, e2e_system):
        """Test Suche mit Abbruch"""
        from src.core.cancellation import CancellationToken
        
        # Verlängere Agent-Antwortzeiten
        for agent in e2e_system.agents.values():
            original_search = agent.search
            async def slow_search(query):
                await asyncio.sleep(1)  # 1 Sekunde Verzögerung
                return await original_search(query)
            agent.search = AsyncMock(side_effect=slow_search)
        
        token = CancellationToken()
        
        # Starte Suche
        search_task = asyncio.create_task(
            e2e_system.search_mine(
                mine_name="Cancellation Test Mine",
                region="Region",
                country="Country",
                cancellation_token=token
            )
        )
        
        # Warte kurz und breche ab
        await asyncio.sleep(0.1)
        token.cancel()
        
        # Warte auf Ergebnis
        results = await search_task
        
        assert results["search_metadata"]["cancelled"] is True
        assert results["search_metadata"]["execution_time"] < 0.5
    
    @pytest.mark.asyncio
    async def test_database_persistence(self, e2e_system):
        """Test Datenbank-Persistenz"""
        # Erste Suche mit Speichern
        first_results = await e2e_system.search_mine(
            mine_name="Persistence Test Mine",
            region="Test Region",
            country="Test Country",
            required_fields=["betreiber", "koordinaten"],
            save_to_db=True
        )
        
        # Hole aus Datenbank
        mine = await e2e_system.database.get_mine_by_name("Persistence Test Mine")
        assert mine is not None
        
        # Zweite Suche sollte Cache nutzen
        second_results = await e2e_system.search_mine(
            mine_name="Persistence Test Mine",
            region="Test Region",
            country="Test Country"
        )
        
        # Sollte Mine ID haben
        assert second_results["search_metadata"].get("mine_id") == mine.id
    
    @pytest.mark.asyncio
    async def test_bulk_search_e2e(self, e2e_system):
        """Test Bulk-Suche End-to-End"""
        mines = [
            {
                "name": f"Bulk Test Mine {i}",
                "region": f"Region {i}",
                "country": "Canada"
            }
            for i in range(3)
        ]
        
        results = await e2e_system.bulk_search(mines, max_concurrent=2)
        
        assert len(results) == 3
        
        for mine_name, result in results.items():
            assert "found_fields" in result
            assert result["search_metadata"]["total_agents_used"] > 0
    
    @pytest.mark.asyncio
    async def test_export_workflow(self, e2e_system, temp_dir):
        """Test Export-Workflow"""
        # Suche und speichere
        await e2e_system.search_mine(
            mine_name="Export Test Mine",
            region="Export Region",
            country="Export Country",
            required_fields=["betreiber", "koordinaten", "produktion"],
            save_to_db=True
        )
        
        # Exportiere als CSV
        csv_file = temp_dir / "export_test.csv"
        export_result = await e2e_system.export_results(
            mine_name="Export Test Mine",
            format="csv",
            filename=str(csv_file)
        )
        
        assert export_result["success"] is True
        assert csv_file.exists()
        
        # Prüfe CSV Inhalt
        content = csv_file.read_text()
        assert "Export Test Mine" in content
        assert "betreiber" in content
        
        # Exportiere als JSON
        json_file = temp_dir / "export_test.json"
        export_result = await e2e_system.export_results(
            mine_name="Export Test Mine",
            format="json",
            filename=str(json_file)
        )
        
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert data["mine_name"] == "Export Test Mine"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, e2e_system):
        """Test Fehler-Recovery"""
        # Lass einige Agents fehlschlagen
        e2e_system.agents["tavily"].search = AsyncMock(
            side_effect=Exception("Network error")
        )
        e2e_system.agents["perplexity"].search = AsyncMock(
            side_effect=Exception("API error")
        )
        
        # Suche sollte trotzdem funktionieren
        results = await e2e_system.search_mine(
            mine_name="Error Recovery Mine",
            region="Region",
            country="Country",
            required_fields=["betreiber", "koordinaten"]
        )
        
        # Sollte Ergebnisse von funktionierenden Agents haben
        assert len(results["found_fields"]) > 0
        assert results["search_metadata"]["errors"] == 2
        assert results["search_metadata"]["total_agents_used"] >= 2
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_searches_e2e(self, e2e_system):
        """Test gleichzeitige Suchen End-to-End"""
        # Starte 5 Suchen gleichzeitig
        searches = []
        for i in range(5):
            search = e2e_system.search_mine(
                mine_name=f"Concurrent Mine {i}",
                region="Concurrent Region",
                country="Concurrent Country",
                mode=SearchMode.FAST
            )
            searches.append(search)
        
        # Warte auf alle
        results = await asyncio.gather(*searches)
        
        # Alle sollten erfolgreich sein
        assert len(results) == 5
        for result in results:
            assert result["search_metadata"]["total_agents_used"] > 0
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, e2e_system):
        """Test Statistik-Tracking"""
        # Führe mehrere Suchen durch
        for i in range(3):
            await e2e_system.search_mine(
                mine_name=f"Stats Mine {i}",
                region="Stats Region",
                country="Stats Country",
                mode=SearchMode.FAST
            )
        
        # Hole Statistiken
        stats = await e2e_system.get_search_statistics()
        
        assert stats["total_searches"] >= 3
        assert stats["average_search_time"] > 0
        assert stats["total_agents_used"] > 0
        assert 0 <= stats["success_rate"] <= 100


@pytest.mark.performance
class TestE2EPerformance:
    """Performance Tests für End-to-End Szenarien"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_scale_search(self, e2e_system):
        """Test große Anzahl von Suchen"""
        import time
        
        start = time.time()
        
        # 20 Minen parallel suchen
        mines = [
            {"name": f"Scale Test Mine {i}", "region": f"Region {i%5}", "country": "TestCountry"}
            for i in range(20)
        ]
        
        results = await e2e_system.bulk_search(mines, max_concurrent=5)
        
        duration = time.time() - start
        
        assert len(results) == 20
        assert duration < 30  # Sollte unter 30 Sekunden sein
        
        # Durchschnittliche Zeit pro Mine
        avg_time = duration / 20
        assert avg_time < 1.5  # Unter 1.5 Sekunden pro Mine