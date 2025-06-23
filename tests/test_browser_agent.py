"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Tests für Browser Agent Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.browser_agent import (
    BrowserAgent, PageAnalyzer, BrowserConfig,
    ScrapeResult, PortalConfig
)
from src.agents.base_agent import MineQuery, SearchResult, AgentStatus


class TestBrowserAgent:
    """Tests für BrowserAgent"""
    
    @pytest.fixture
    def browser_agent(self, mock_config):
        """BrowserAgent Instanz"""
        return BrowserAgent("browser", mock_config)
    
    def test_initialization(self, browser_agent):
        """Test Initialisierung"""
        assert browser_agent.name == "browser"
        assert isinstance(browser_agent.browser_config, BrowserConfig)
        assert browser_agent.analyzer is not None
        assert len(browser_agent.government_portals) > 0
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, browser_agent):
        """Test erfolgreiche Browser-Initialisierung"""
        # Mock Playwright
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        
        with patch('src.agents.browser_agent.browser_agent.async_playwright') as mock_pw:
            mock_pw.return_value.start.return_value = mock_playwright
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            
            result = await browser_agent.initialize()
            
            assert result is True
            assert browser_agent.status == AgentStatus.ACTIVE
            assert browser_agent.browser is not None
            assert browser_agent.context is not None
    
    @pytest.mark.asyncio
    async def test_initialize_no_playwright(self, browser_agent):
        """Test Initialisierung ohne Playwright"""
        with patch('src.agents.browser_agent.browser_agent.async_playwright', side_effect=ImportError):
            result = await browser_agent.initialize()
            
            assert result is False
            assert browser_agent.status == AgentStatus.DISABLED
    
    @pytest.mark.asyncio
    async def test_search_mine(self, browser_agent, sample_mine_query):
        """Test Mine-Suche"""
        # Mock discovered sources
        mock_source = MagicMock()
        mock_source.url = "http://test.arcgis.com/map"
        mock_source.source_type = "map"
        sample_mine_query.discovered_sources = [mock_source]
        
        # Mock scrape methods
        browser_agent._scrape_dynamic_site = AsyncMock(return_value=[
            SearchResult(
                field_name="koordinaten",
                value="45.5° N, 73.6° W",
                source="browser: http://test.arcgis.com/map",
                confidence_score=0.85,
                metadata={"method": "browser"}
            )
        ])
        
        browser_agent._search_government_portals = AsyncMock(return_value=[])
        
        results = await browser_agent.search_mine(sample_mine_query)
        
        assert len(results) > 0
        assert results[0].field_name == "koordinaten"
        browser_agent._scrape_dynamic_site.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_dynamic_site(self, browser_agent, sample_mine_query):
        """Test dynamisches Website-Scraping"""
        # Mock page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="""
            <html>
            <body>
                <h1>Test Mine</h1>
                <div>Coordinates: 45.5° N, 73.6° W</div>
            </body>
            </html>
        """)
        mock_page.close = AsyncMock()
        
        browser_agent.context = AsyncMock()
        browser_agent.context.new_page = AsyncMock(return_value=mock_page)
        
        browser_agent._wait_for_content = AsyncMock()
        browser_agent._search_on_page = AsyncMock(return_value=True)
        browser_agent._take_screenshot = AsyncMock(return_value="screenshot.png")
        
        results = await browser_agent._scrape_dynamic_site(
            "http://test.com", sample_mine_query, "web"
        )
        
        assert len(results) > 0
        mock_page.goto.assert_called_once()
        mock_page.content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_government_portals(self, browser_agent, sample_mine_query):
        """Test Government Portal Suche"""
        sample_mine_query.country = "Canada"
        
        # Mock search_portal
        browser_agent._search_portal = AsyncMock(return_value=[
            SearchResult(
                field_name="betreiber",
                value="Test Mining Corp",
                source="government: Natural Resources Canada",
                confidence_score=0.95,
                metadata={"portal": "Natural Resources Canada", "official_source": True}
            )
        ])
        
        results = await browser_agent._search_government_portals(sample_mine_query)
        
        assert len(results) > 0
        assert results[0].metadata["official_source"] is True
    
    @pytest.mark.asyncio
    async def test_wait_for_content(self, browser_agent):
        """Test Warten auf dynamische Inhalte"""
        mock_page = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=[True, False, False])  # React detected
        mock_page.wait_for_selector = AsyncMock()
        
        await browser_agent._wait_for_content(mock_page)
        
        mock_page.wait_for_load_state.assert_called_with("networkidle")
        # Sollte auf React warten
        assert mock_page.evaluate.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_search_on_page(self, browser_agent):
        """Test Suche auf Seite"""
        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=AsyncMock())
        mock_page.keyboard.press = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="Test Mine found")
        
        result = await browser_agent._search_on_page(mock_page, "Test Mine")
        
        assert result is True
    
    def test_load_government_portals(self, browser_agent):
        """Test Government Portal Konfiguration"""
        portals = browser_agent._load_government_portals()
        
        assert len(portals) > 0
        
        # Prüfe Canada Portal
        canada_portal = next((p for p in portals if p.country == "Canada"), None)
        assert canada_portal is not None
        assert canada_portal.name == "Natural Resources Canada"
        assert "search_input" in canada_portal.selectors


class TestPageAnalyzer:
    """Tests für PageAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """PageAnalyzer Instanz"""
        return PageAnalyzer()
    
    def test_needs_browser_rendering(self, analyzer):
        """Test Browser-Rendering Erkennung"""
        # Positive Fälle
        assert analyzer.needs_browser_rendering("http://test.arcgis.com/map") is True
        assert analyzer.needs_browser_rendering("http://app.powerbi.com/dashboard") is True
        assert analyzer.needs_browser_rendering("http://test.com/viewer?search=mine") is True
        
        # Negative Fälle
        assert analyzer.needs_browser_rendering("http://test.com/static.html") is False
        assert analyzer.needs_browser_rendering("http://pdf.com/document.pdf") is False
    
    @pytest.mark.asyncio
    async def test_analyze_page_structure(self, analyzer):
        """Test Seitenstruktur-Analyse"""
        html_content = """
        <html>
        <body>
            <table><tr><td>Data</td></tr></table>
            <form action="/search"></form>
            <div class="mapbox-container"></div>
        </body>
        </html>
        """
        
        analysis = await analyzer.analyze_page_structure(html_content, "http://test.com")
        
        assert analysis["has_tables"] is True
        assert analysis["has_forms"] is True
        assert analysis["has_maps"] is True
        assert analysis["language"] in ["en", "es", "fr", "pt", "de"]
    
    def test_extract_from_page(self, analyzer, sample_mine_query):
        """Test Datenextraktion aus Seite"""
        html_content = """
        <html>
        <body>
            <table>
                <tr>
                    <td>Operator:</td>
                    <td>Test Mining Corp</td>
                </tr>
                <tr>
                    <td>Coordinates:</td>
                    <td>45.5° N, 73.6° W</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        results = analyzer.extract_from_page(
            html_content, sample_mine_query, "http://test.com", "web"
        )
        
        assert len(results) > 0
        
        # Sollte Operator finden
        operator_results = [r for r in results if r.field_name in ["betreiber", "operator"]]
        assert len(operator_results) > 0
        
        # Sollte Koordinaten finden
        coord_results = [r for r in results if r.field_name in ["koordinaten", "coordinates"]]
        assert len(coord_results) > 0
    
    def test_create_extraction_rules(self, analyzer):
        """Test Erstellung von Extraktionsregeln"""
        fields = ["betreiber", "koordinaten", "produktion"]
        
        rules = analyzer.create_extraction_rules(fields, "en")
        
        assert len(rules) > 0
        
        # Prüfe Regel-Eigenschaften
        for rule in rules:
            assert rule.field_name in fields
            assert rule.selector is not None
            assert rule.strategy is not None
    
    def test_validate_extraction(self, analyzer):
        """Test Validierung extrahierter Werte"""
        # Test Koordinaten
        valid, confidence = analyzer.validate_extraction(
            "koordinaten", "45.5° N, 73.6° W"
        )
        assert valid is True
        assert confidence > 0.8
        
        # Test ungültige Koordinaten
        valid, confidence = analyzer.validate_extraction(
            "koordinaten", "not coordinates"
        )
        assert valid is False
        
        # Test Kosten
        valid, confidence = analyzer.validate_extraction(
            "sanierungskosten", "50 million USD"
        )
        assert valid is True
        
        # Test Produktion
        valid, confidence = analyzer.validate_extraction(
            "produktion", "100,000 tons/year"
        )
        assert valid is True
        
        # Test generisches Feld
        valid, confidence = analyzer.validate_extraction(
            "betreiber", "Test Corp"
        )
        assert valid is True
        assert confidence >= 0.7
    
    def test_detect_language(self, analyzer):
        """Test Spracherkennung"""
        # Englisch
        en_text = "The mine operator is conducting mining operations in the region"
        assert analyzer._detect_language(en_text) == "en"
        
        # Spanisch
        es_text = "La mina está operada por la empresa minera en la región"
        assert analyzer._detect_language(es_text) == "es"
        
        # Französisch
        fr_text = "La mine est exploitée par la société minière dans la région"
        assert analyzer._detect_language(fr_text) == "fr"
    
    def test_extract_from_tables(self, analyzer, sample_mine_query):
        """Test Tabellen-Extraktion"""
        html_with_table = """
        <table>
            <tr>
                <td>Operator</td>
                <td>Mining Company XYZ</td>
            </tr>
            <tr>
                <td>Location</td>
                <td>45.5° N, 73.6° W</td>
            </tr>
        </table>
        """
        
        results = analyzer._extract_from_tables(
            html_with_table, sample_mine_query, "en"
        )
        
        assert len(results) > 0
        assert any(r["field"] in ["betreiber", "operator"] for r in results)
    
    def test_extract_with_patterns(self, analyzer, sample_mine_query):
        """Test Pattern-basierte Extraktion"""
        text = """
        The mine is located at coordinates 45.5° N, 73.6° W.
        Annual production capacity is 100,000 tons.
        Estimated remediation costs are 50 million USD.
        """
        
        results = analyzer._extract_with_patterns(text, sample_mine_query, "en")
        
        assert len(results) > 0
        
        # Sollte alle Muster finden
        fields_found = {r["field"] for r in results}
        assert "koordinaten" in fields_found or "coordinates" in fields_found
        assert "produktion" in fields_found or "production" in fields_found
        assert "sanierungskosten" in fields_found or "remediation_costs" in fields_found


class TestModels:
    """Tests für Browser Agent Modelle"""
    
    def test_browser_config(self):
        """Test BrowserConfig"""
        config = BrowserConfig(headless=False, timeout=60000)
        
        assert config.headless is False
        assert config.timeout == 60000
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert len(config.args) > 0
    
    def test_portal_config(self):
        """Test PortalConfig"""
        portal = PortalConfig(
            country="Canada",
            name="Test Portal",
            base_url="http://test.ca",
            search_path="/search",
            selectors={"search": "input#search"}
        )
        
        assert portal.country == "Canada"
        assert portal.requires_js is True
        assert isinstance(portal.wait_conditions, list)
    
    def test_extraction_rule(self):
        """Test ExtractionRule"""
        from src.agents.browser_agent.models import ExtractionRule, ExtractionStrategy
        
        rule = ExtractionRule(
            field_name="betreiber",
            selector="td:contains('Operator') + td",
            strategy=ExtractionStrategy.TABLE,
            transform="trim"
        )
        
        # Test Transformation
        assert rule.apply_transform("  Test Corp  ") == "Test Corp"
        assert rule.apply_transform("") == ""
        
        # Test andere Transformationen
        rule.transform = "lowercase"
        assert rule.apply_transform("TEST") == "test"
        
        rule.transform = "uppercase"
        assert rule.apply_transform("test") == "TEST"
        
        rule.transform = "replace:a:b"
        assert rule.apply_transform("banana") == "bbnbnb"


# Integration Tests
@pytest.mark.integration
class TestBrowserAgentIntegration:
    """Integrationstests für Browser Agent"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_scraping_workflow(self, mock_config, sample_mine_query):
        """Test kompletter Scraping-Workflow"""
        browser = BrowserAgent("browser", mock_config)
        
        # Mock Playwright und Browser
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        with patch('src.agents.browser_agent.browser_agent.async_playwright') as mock_pw:
            mock_pw.return_value.start.return_value = mock_playwright
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # Mock page methods
            mock_page.goto = AsyncMock()
            mock_page.content = AsyncMock(return_value="""
                <html>
                <body>
                    <h1>Integration Test Mine</h1>
                    <table>
                        <tr>
                            <td>Operator:</td>
                            <td>Integration Mining Corp</td>
                        </tr>
                        <tr>
                            <td>GPS Coordinates:</td>
                            <td>45.5017° N, 73.5673° W</td>
                        </tr>
                    </table>
                </body>
                </html>
            """)
            mock_page.close = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            
            # Initialize
            await browser.initialize()
            
            # Add discovered source
            mock_source = MagicMock()
            mock_source.url = "http://test.com/mine-data"
            mock_source.source_type = "web"
            sample_mine_query.discovered_sources = [mock_source]
            
            # Mock analyzer to return dynamic content detection
            browser.analyzer.needs_browser_rendering = MagicMock(return_value=True)
            
            # Execute search
            results = await browser.search(sample_mine_query)
            
            # Validate
            assert len(results) > 0
            
            # Cleanup
            await browser.cleanup()