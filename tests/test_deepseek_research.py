"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Tests für DeepSeek Research Agent Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

from src.agents.deepseek_research import (
    DeepSeekResearchAgent, DeepSeekModel, ResearchStep,
    AdaptationStrategy, ResearchProcessor
)
from src.agents.base_agent import MineQuery, SearchResult, AgentStatus


class TestDeepSeekResearchAgent:
    """Tests für DeepSeekResearchAgent"""
    
    @pytest.fixture
    def deepseek_agent(self, mock_config):
        """DeepSeekResearchAgent Instanz"""
        return DeepSeekResearchAgent("deepseek", mock_config, model_type="chat")
    
    def test_initialization(self, deepseek_agent):
        """Test Initialisierung"""
        assert deepseek_agent.name == "deepseek"
        assert deepseek_agent.model_type == "chat"
        assert deepseek_agent.use_openrouter is True
        assert deepseek_agent.processor is not None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, deepseek_agent, mock_session_class):
        """Test erfolgreiche Initialisierung"""
        deepseek_agent.validate_credentials = AsyncMock(return_value=True)
        
        result = await deepseek_agent.initialize()
        
        assert result is True
        assert deepseek_agent.status != AgentStatus.DISABLED
    
    @pytest.mark.asyncio
    async def test_initialize_no_api_key(self, deepseek_agent):
        """Test Initialisierung ohne API Key"""
        deepseek_agent.api_key = None
        
        result = await deepseek_agent.initialize()
        
        assert result is False
        assert deepseek_agent.status == AgentStatus.DISABLED
    
    @pytest.mark.asyncio
    async def test_validate_credentials(self, deepseek_agent, mock_session):
        """Test Credential-Validierung"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        deepseek_agent._session = mock_session
        
        result = await deepseek_agent.validate_credentials()
        
        assert result is True
        
        # Prüfe Headers
        call_args = mock_session.post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {deepseek_agent.api_key}"
    
    @pytest.mark.asyncio
    async def test_search_with_reasoning(self, deepseek_agent, sample_mine_query, mock_session):
        """Test Suche mit Reasoning Model"""
        deepseek_agent.model_type = "reasoner"
        deepseek_agent._session = mock_session
        deepseek_agent.status = AgentStatus.ACTIVE
        
        # Mock API Responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "objective": "Find operator",
                        "strategy": "Search databases",
                        "sources": ["government"],
                        "keywords": ["operator"],
                        "expected_data": ["betreiber"]
                    }])
                }
            }]
        })
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        results = await deepseek_agent.search(sample_mine_query)
        
        assert isinstance(results, list)
        assert deepseek_agent.status == AgentStatus.IDLE
    
    @pytest.mark.asyncio
    async def test_create_research_plan(self, deepseek_agent, sample_mine_query, mock_session):
        """Test Research-Plan Erstellung"""
        deepseek_agent._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "objective": "Test objective",
                        "strategy": "Test strategy",
                        "sources": ["test"],
                        "keywords": ["test"],
                        "expected_data": ["test"]
                    }])
                }
            }]
        })
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        plan = await deepseek_agent._create_research_plan(sample_mine_query)
        
        assert isinstance(plan, list)
        assert len(plan) > 0
        assert isinstance(plan[0], ResearchStep)
    
    @pytest.mark.asyncio
    async def test_make_api_call_success(self, deepseek_agent, mock_session):
        """Test erfolgreicher API Call"""
        deepseek_agent._session = mock_session
        deepseek_agent._rate_limiter.acquire = AsyncMock()
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {"content": "Test response"}
            }]
        })
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await deepseek_agent._make_api_call("Test prompt")
        
        assert result == "Test response"
        deepseek_agent._rate_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_api_call_error(self, deepseek_agent, mock_session):
        """Test API Call mit Fehler"""
        deepseek_agent._session = mock_session
        deepseek_agent._rate_limiter.acquire = AsyncMock()
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Server error")
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await deepseek_agent._make_api_call("Test prompt")
        
        assert result is None


class TestResearchProcessor:
    """Tests für ResearchProcessor"""
    
    @pytest.fixture
    def processor(self):
        """ResearchProcessor Instanz"""
        return ResearchProcessor()
    
    @pytest.mark.asyncio
    async def test_create_research_plan_from_json(self, processor, sample_mine_query):
        """Test Plan-Erstellung aus JSON"""
        json_response = json.dumps([{
            "objective": "Find mine data",
            "strategy": "Search databases",
            "sources": ["government", "industry"],
            "keywords": ["mine", "operator"],
            "expected_data": ["betreiber", "koordinaten"],
            "priority": "high"
        }])
        
        plan = await processor.create_research_plan(sample_mine_query, json_response)
        
        assert len(plan) == 1
        assert isinstance(plan[0], ResearchStep)
        assert plan[0].objective == "Find mine data"
        assert plan[0].priority == "high"
    
    @pytest.mark.asyncio
    async def test_create_research_plan_fallback(self, processor, sample_mine_query):
        """Test Fallback-Plan bei Fehler"""
        invalid_response = "Invalid JSON"
        
        plan = await processor.create_research_plan(sample_mine_query, invalid_response)
        
        assert len(plan) > 0
        assert isinstance(plan[0], ResearchStep)
        # Sollte Fallback-Plan sein
        assert "basic mine information" in plan[0].objective
    
    def test_extract_structured_data(self, processor, sample_mine_query):
        """Test strukturierte Datenextraktion"""
        response = """
        Found the following information:
        {"field": "betreiber", "value": "Test Mining Corp", "confidence": 0.9}
        
        Also coordinates: 45.5° N, 73.6° W
        """
        
        step = ResearchStep(
            objective="Test",
            strategy="Test",
            sources=["test"],
            keywords=["test"],
            expected_data=["betreiber", "koordinaten"]
        )
        
        results = processor.extract_structured_data(response, sample_mine_query, step)
        
        assert len(results) > 0
        # Sollte mindestens Koordinaten finden
        coord_results = [r for r in results if r.field_name == "koordinaten"]
        assert len(coord_results) > 0
    
    def test_adapt_research_plan(self, processor, sample_mine_query):
        """Test Plan-Anpassung"""
        remaining_steps = [
            ResearchStep(
                objective="Find remaining data",
                strategy="General search",
                sources=["all"],
                keywords=["mine"],
                expected_data=["produktion", "status"]
            )
        ]
        
        recent_findings = [
            SearchResult(
                field_name="betreiber",
                value="Test Corp",
                source="test",
                confidence_score=0.9,
                metadata={}
            )
        ]
        
        adapted_steps, strategy = processor.adapt_research_plan(
            remaining_steps, recent_findings, sample_mine_query
        )
        
        assert isinstance(strategy, AdaptationStrategy)
        assert "betreiber" not in strategy.missing_fields
        assert "betreiber" in strategy.found_fields
        
        # Bei vielen fehlenden Feldern sollte angepasst werden
        if len(strategy.missing_fields) > 1:
            assert strategy.adaptation_type in ["expand", "pivot", "refine"]
    
    def test_create_step_prompt(self, processor, sample_mine_query):
        """Test Prompt-Erstellung für Research-Schritt"""
        from src.agents.deepseek_research.models import ResearchContext
        
        step = ResearchStep(
            objective="Find operator information",
            strategy="Search government databases",
            sources=["government"],
            keywords=["operator", "owner"],
            expected_data=["betreiber"]
        )
        
        context = ResearchContext(
            mine_name=sample_mine_query.mine_name,
            country=sample_mine_query.country,
            region=sample_mine_query.region,
            languages=sample_mine_query.languages,
            required_fields=sample_mine_query.required_fields,
            search_domains=["gov.ca", "nrcan.gc.ca"],
            time_budget=120
        )
        
        prompt = processor.create_step_prompt(step, context)
        
        assert step.objective in prompt
        assert sample_mine_query.mine_name in prompt
        assert "government" in prompt
        assert "betreiber" in prompt
    
    def test_validate_extraction(self, processor):
        """Test Validierung extrahierter Werte"""
        # Test Koordinaten
        valid, confidence = processor.validate_extraction(
            "koordinaten", "45.5° N, 73.6° W"
        )
        assert valid is True
        assert confidence > 0.8
        
        # Test ungültige Koordinaten
        valid, confidence = processor.validate_extraction(
            "koordinaten", "invalid coords"
        )
        assert valid is False
        
        # Test Kosten
        valid, confidence = processor.validate_extraction(
            "sanierungskosten", "50 million USD"
        )
        assert valid is True
        
        # Test generisches Feld
        valid, confidence = processor.validate_extraction(
            "betreiber", "Test Corp"
        )
        assert valid is True
        assert confidence >= 0.7


class TestModels:
    """Tests für DeepSeek Datenmodelle"""
    
    def test_model_config(self):
        """Test ModelConfig"""
        from src.agents.deepseek_research.models import ModelConfig
        
        models = ModelConfig.get_models()
        
        assert "chat" in models
        assert "reasoner" in models
        assert "coder" in models
        
        chat_model = models["chat"]
        assert chat_model.id == "deepseek-chat"
        assert "multilingual" in chat_model.capabilities
        assert chat_model.cost_per_1k > 0
    
    def test_research_context(self):
        """Test ResearchContext"""
        from src.agents.deepseek_research.models import ResearchContext
        
        context = ResearchContext(
            mine_name="Test Mine",
            country="Canada",
            region="Ontario",
            languages=["en", "fr"],
            required_fields=["betreiber"],
            search_domains=["gov.ca"],
            time_budget=120
        )
        
        prompt_context = context.to_prompt_context()
        
        assert "Test Mine" in prompt_context
        assert "Canada" in prompt_context
        assert "Ontario" in prompt_context
        assert "en, fr" in prompt_context
    
    def test_extraction_result(self):
        """Test ExtractionResult"""
        from src.agents.deepseek_research.models import ExtractionResult
        
        extraction = ExtractionResult(
            field_name="betreiber",
            value="Test Corp",
            source="deepseek",
            confidence=0.85,
            metadata={"method": "ai"},
            extraction_method="pattern"
        )
        
        search_result = extraction.to_search_result()
        
        assert search_result["field_name"] == "betreiber"
        assert search_result["value"] == "Test Corp"
        assert search_result["confidence_score"] == 0.85


# Integration Tests
@pytest.mark.integration
class TestDeepSeekIntegration:
    """Integrationstests für DeepSeek Research"""
    
    @pytest.mark.asyncio
    async def test_full_research_workflow(self, mock_config, sample_mine_query):
        """Test kompletter Research-Workflow"""
        agent = DeepSeekResearchAgent("deepseek", mock_config, model_type="reasoner")
        
        # Mock Session und Responses
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock verschiedene API Calls
            responses = [
                # Credential validation
                {"status": 200},
                # Research plan
                {
                    "status": 200,
                    "json": {
                        "choices": [{
                            "message": {
                                "content": json.dumps([{
                                    "objective": "Find operator",
                                    "strategy": "Search",
                                    "sources": ["gov"],
                                    "keywords": ["operator"],
                                    "expected_data": ["betreiber"]
                                }])
                            }
                        }]
                    }
                },
                # Research execution
                {
                    "status": 200,
                    "json": {
                        "choices": [{
                            "message": {
                                "content": "Found operator: Integration Test Corp"
                            }
                        }]
                    }
                }
            ]
            
            response_iter = iter(responses)
            
            def mock_post(*args, **kwargs):
                resp_data = next(response_iter)
                mock_resp = AsyncMock()
                mock_resp.status = resp_data["status"]
                if "json" in resp_data:
                    mock_resp.json = AsyncMock(return_value=resp_data["json"])
                return mock_resp
            
            mock_session.post.return_value.__aenter__.side_effect = mock_post
            
            # Initialize
            await agent.initialize()
            
            # Execute search
            results = await agent.search(sample_mine_query)
            
            # Validate
            assert isinstance(results, list)
            # Sollte mindestens Pattern-basierte Extraktion finden
            assert any("operator" in str(r).lower() for r in results)