"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Unit Tests für Perplexity API Integration
"""

# ÄNDERUNG 01.07.2025: Komplette Test-Suite für Perplexity Integration erstellt

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Füge Backend-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from minesearch_v2.backend.search_service import MineSearchService
from minesearch_v2.backend.config import PERPLEXITY_API_KEY, MODEL_CONFIG


class TestPerplexityIntegration:
    """Test-Klasse für Perplexity API Integration"""
    
    @pytest.fixture
    def search_service(self):
        """Erstelle MineSearchService Instanz für Tests"""
        return MineSearchService()
    
    @pytest.fixture
    def mock_response(self):
        """Mock Perplexity API Response"""
        return {
            "id": "test-123",
            "model": "sonar",
            "created": 1234567890,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            },
            "choices": [{
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "daten": {
                            "Minenname": "Test Mine",
                            "Land": "Kanada",
                            "Region": "Ontario",
                            "Koordinaten": "48.123,-89.456",
                            "Rohstoffe": "Gold, Silber",
                            "Eigentümer": "Test Corp",
                            "Betreiber": "Test Operations Ltd",
                            "Status": "Aktiv",
                            "Jahresproduktion": "100.000 oz Gold",
                            "Reserven": "2 Mio oz Gold",
                            "Ressourcen": "5 Mio oz Gold",
                            "Minenlaufzeit": "2025-2035",
                            "Mitarbeiter": "500",
                            "Website": "www.testmine.com",
                            "Kontakt": "info@testmine.com",
                            "Telefon": "+1-555-0123",
                            "Adresse": "123 Mining St, Ontario",
                            "Beschreibung": "Große Goldmine in Ontario",
                            "Gründungsjahr": "2020",
                            "Minentyp": "Tagebau",
                            "Verarbeitungskapazität": "10.000 t/Tag",
                            "Umweltstandards": "ISO 14001",
                            "Zertifizierungen": "Responsible Mining",
                            "Gewerkschaft": "United Miners",
                            "Investitionsvolumen": "500 Mio USD",
                            "Infrastruktur": "Straße, Strom vorhanden",
                            "Wasserquelle": "Lake Superior",
                            "Energiequelle": "Netzstrom",
                            "Notizen": "Expansion geplant 2026"
                        },
                        "quellen": [
                            {
                                "titel": "Test Mine Official Report",
                                "url": "https://testmine.com/report.pdf",
                                "domain": "testmine.com",
                                "beschreibung": "Offizieller Jahresbericht 2024",
                                "datum": "2024-03-15"
                            }
                        ],
                        "datenqualität": 85,
                        "suchverlauf": []
                    })
                }
            }]
        }
    
    def test_api_key_exists(self):
        """Test: API Key ist konfiguriert"""
        assert PERPLEXITY_API_KEY is not None
        assert PERPLEXITY_API_KEY != ""
        assert PERPLEXITY_API_KEY != "your_perplexity_api_key_here"
    
    def test_search_mine_basic(self, search_service, mock_response):
        """Test: Basis-Minensuche"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = search_service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert result["daten"]["Minenname"] == "Test Mine"
            assert result["daten"]["Land"] == "Kanada"
            assert result["datenqualität"] == 85
    
    def test_search_mine_with_timeout(self, search_service):
        """Test: Timeout-Handling"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Timeout")
            
            result = search_service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert "error" in result
    
    def test_enhanced_search(self, search_service, mock_response):
        """Test: 2-Phasen erweiterte Suche"""
        with patch('requests.post') as mock_post:
            # Phase 1 Response
            phase1_response = mock_response.copy()
            phase1_response["choices"][0]["message"]["content"] = json.dumps({
                "daten": {"Minenname": "Test Mine"},
                "quellen": [
                    {"url": "https://mining.gov/test", "domain": "mining.gov"},
                    {"url": "https://testmine.com", "domain": "testmine.com"},
                    {"url": "https://news.com/test", "domain": "news.com"}
                ],
                "datenqualität": 60
            })
            
            # Phase 2 Response
            phase2_response = mock_response.copy()
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = [phase1_response, phase2_response]
            
            result = search_service.enhanced_search("Test Mine", "Kanada")
            
            assert result is not None
            assert mock_post.call_count == 2  # 2 Phasen
    
    def test_model_config(self):
        """Test: Model-Konfiguration"""
        assert "standard" in MODEL_CONFIG
        assert "deep_research" in MODEL_CONFIG
        assert MODEL_CONFIG["standard"]["timeout"] == 30
        assert MODEL_CONFIG["deep_research"]["timeout"] == 120
    
    def test_smart_search_upgrade(self, search_service):
        """Test: Smart Search Upgrade bei niedriger Qualität"""
        with patch('requests.post') as mock_post:
            # Erste Response mit niedriger Qualität
            low_quality_response = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "daten": {"Minenname": "Test Mine"},
                            "quellen": [],
                            "datenqualität": 30  # Niedrige Qualität
                        })
                    }
                }]
            }
            
            # Zweite Response mit besserer Qualität
            high_quality_response = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "daten": {"Minenname": "Test Mine"},
                            "quellen": [{"url": "test.com"}],
                            "datenqualität": 80
                        })
                    }
                }]
            }
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = [low_quality_response, high_quality_response]
            
            result = search_service.search_mine("Test Mine", "Kanada", smart_search=True)
            
            assert result["datenqualität"] == 80
            assert len(result["suchverlauf"]) > 0
    
    def test_batch_search(self, search_service, mock_response):
        """Test: Batch-Suche mehrerer Minen"""
        mines = [
            {"name": "Mine 1", "country": "Kanada"},
            {"name": "Mine 2", "country": "USA"},
            {"name": "Mine 3", "country": "Chile"}
        ]
        
        with patch.object(search_service, 'search_mine') as mock_search:
            mock_search.return_value = mock_response["choices"][0]["message"]["content"]
            
            results = []
            for mine in mines:
                result = search_service.search_mine(mine["name"], mine["country"])
                results.append(result)
            
            assert len(results) == 3
            assert mock_search.call_count == 3
    
    def test_error_handling_invalid_json(self, search_service):
        """Test: Fehlerbehandlung bei ungültigem JSON"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "Ungültiges JSON"  # Kein JSON
                    }
                }]
            }
            
            result = search_service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert "error" in result or result.get("datenqualität", 0) == 0
    
    def test_api_error_handling(self, search_service):
        """Test: API Fehler-Handling"""
        with patch('requests.post') as mock_post:
            # Test verschiedene HTTP Status Codes
            error_codes = [400, 401, 403, 404, 429, 500, 503]
            
            for code in error_codes:
                mock_post.return_value.status_code = code
                mock_post.return_value.json.return_value = {"error": f"HTTP {code}"}
                
                result = search_service.search_mine("Test Mine", "Kanada")
                
                assert result is not None
                assert "error" in result or result.get("datenqualität", 0) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])