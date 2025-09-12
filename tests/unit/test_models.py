"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Unit Tests für Datenbank-Modelle
"""

import pytest
import sys
import os
from datetime import datetime

# Füge Backend-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from minesearch.database.models import (
    Source, SearchSession, SearchResult, ModelPerformance,
    NormalizedMine, NormalizedFieldValue, Base
)


class TestSourceModel:
    """Test-Klasse für Source-Modell"""
    
    def test_source_creation(self):
        """Test Source-Erstellung"""
        source = Source(
            url="https://example.com",
            domain="example.com",
            country="Canada",
            source_type="government"
        )
        
        assert source.url == "https://example.com"
        assert source.domain == "example.com"
        assert source.country == "Canada"
        assert source.source_type == "government"
        assert source.reliability_score == 50.0  # Default
    
    def test_source_to_dict(self):
        """Test Source zu Dictionary Konvertierung"""
        source = Source(
            url="https://example.com",
            domain="example.com",
            country="Canada"
        )
        
        source_dict = source.to_dict()
        
        assert isinstance(source_dict, dict)
        assert source_dict['url'] == "https://example.com"
        assert source_dict['domain'] == "example.com"
        assert source_dict['country'] == "Canada"
    
    def test_source_repr(self):
        """Test Source String-Repräsentation"""
        source = Source(
            url="https://example.com",
            domain="example.com"
        )
        
        repr_str = repr(source)
        assert "Source" in repr_str
        assert "example.com" in repr_str


class TestSearchSessionModel:
    """Test-Klasse für SearchSession-Modell"""
    
    def test_search_session_creation(self):
        """Test SearchSession-Erstellung"""
        session = SearchSession(
            session_id="test-session-123",
            mine_name="Test Mine",
            model_id="test-model",
            provider="test-provider"
        )
        
        assert session.session_id == "test-session-123"
        assert session.mine_name == "Test Mine"
        assert session.model_id == "test-model"
        assert session.provider == "test-provider"
        assert session.status == "pending"  # Default
    
    def test_search_session_to_dict(self):
        """Test SearchSession zu Dictionary Konvertierung"""
        session = SearchSession(
            session_id="test-session-123",
            mine_name="Test Mine",
            model_id="test-model",
            provider="test-provider"
        )
        
        session_dict = session.to_dict()
        
        assert isinstance(session_dict, dict)
        assert session_dict['session_id'] == "test-session-123"
        assert session_dict['mine_name'] == "Test Mine"
        assert session_dict['model_id'] == "test-model"
        assert session_dict['provider'] == "test-provider"


class TestSearchResultModel:
    """Test-Klasse für SearchResult-Modell"""
    
    def test_search_result_creation(self):
        """Test SearchResult-Erstellung"""
        result = SearchResult(
            session_id="test-session-123",
            mine_name="Test Mine",
            model_id="test-model",
            provider="test-provider",
            field_name="mine_name",
            extracted_value="Test Mine Value"
        )
        
        assert result.session_id == "test-session-123"
        assert result.mine_name == "Test Mine"
        assert result.field_name == "mine_name"
        assert result.extracted_value == "Test Mine Value"
        assert result.is_placeholder == False  # Default
        assert result.is_fallback == False  # Default
    
    def test_search_result_to_dict(self):
        """Test SearchResult zu Dictionary Konvertierung"""
        result = SearchResult(
            session_id="test-session-123",
            mine_name="Test Mine",
            model_id="test-model",
            provider="test-provider",
            field_name="mine_name",
            extracted_value="Test Mine Value"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['session_id'] == "test-session-123"
        assert result_dict['mine_name'] == "Test Mine"
        assert result_dict['field_name'] == "mine_name"
        assert result_dict['extracted_value'] == "Test Mine Value"


class TestNormalizedMineModel:
    """Test-Klasse für NormalizedMine-Modell"""
    
    def test_normalized_mine_creation(self):
        """Test NormalizedMine-Erstellung"""
        mine = NormalizedMine(
            mine_name="Test Mine",
            country="Canada",
            region="Quebec",
            mineral_type="Iron Ore",
            production_status="active"
        )
        
        assert mine.mine_name == "Test Mine"
        assert mine.country == "Canada"
        assert mine.region == "Quebec"
        assert mine.mineral_type == "Iron Ore"
        assert mine.production_status == "active"
        assert mine.data_quality_score == 0.0  # Default
    
    def test_normalized_mine_to_dict(self):
        """Test NormalizedMine zu Dictionary Konvertierung"""
        mine = NormalizedMine(
            mine_name="Test Mine",
            country="Canada",
            mineral_type="Iron Ore"
        )
        
        mine_dict = mine.to_dict()
        
        assert isinstance(mine_dict, dict)
        assert mine_dict['mine_name'] == "Test Mine"
        assert mine_dict['country'] == "Canada"
        assert mine_dict['mineral_type'] == "Iron Ore"


class TestNormalizedFieldValueModel:
    """Test-Klasse für NormalizedFieldValue-Modell"""
    
    def test_normalized_field_value_creation(self):
        """Test NormalizedFieldValue-Erstellung"""
        field_value = NormalizedFieldValue(
            mine_id=1,
            field_name="annual_production",
            normalized_value="1,500,000 tons",
            confidence_score=0.9
        )
        
        assert field_value.mine_id == 1
        assert field_value.field_name == "annual_production"
        assert field_value.normalized_value == "1,500,000 tons"
        assert field_value.confidence_score == 0.9
        assert field_value.is_placeholder == False  # Default
    
    def test_normalized_field_value_to_dict(self):
        """Test NormalizedFieldValue zu Dictionary Konvertierung"""
        field_value = NormalizedFieldValue(
            mine_id=1,
            field_name="annual_production",
            normalized_value="1,500,000 tons"
        )
        
        field_dict = field_value.to_dict()
        
        assert isinstance(field_dict, dict)
        assert field_dict['mine_id'] == 1
        assert field_dict['field_name'] == "annual_production"
        assert field_dict['normalized_value'] == "1,500,000 tons"


class TestModelPerformanceModel:
    """Test-Klasse für ModelPerformance-Modell"""
    
    def test_model_performance_creation(self):
        """Test ModelPerformance-Erstellung"""
        performance = ModelPerformance(
            model_id="test-model",
            provider="test-provider",
            field_name="mine_name",
            total_searches=100,
            successful_extractions=80
        )
        
        assert performance.model_id == "test-model"
        assert performance.provider == "test-provider"
        assert performance.field_name == "mine_name"
        assert performance.total_searches == 100
        assert performance.successful_extractions == 80
        assert performance.success_rate == 0.0  # Default
    
    def test_model_performance_to_dict(self):
        """Test ModelPerformance zu Dictionary Konvertierung"""
        performance = ModelPerformance(
            model_id="test-model",
            provider="test-provider",
            field_name="mine_name"
        )
        
        perf_dict = performance.to_dict()
        
        assert isinstance(perf_dict, dict)
        assert perf_dict['model_id'] == "test-model"
        assert perf_dict['provider'] == "test-provider"
        assert perf_dict['field_name'] == "mine_name"


if __name__ == "__main__":
    pytest.main([__file__])
