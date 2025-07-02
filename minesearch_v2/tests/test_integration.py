"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Integration Tests für API-Calls und End-to-End Funktionalität
"""

# ÄNDERUNG 01.07.2025: Integration Test-Suite erstellt

import pytest
import os
import sys
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from minesearch_v2.backend.main import app
from minesearch_v2.backend.search_service import MineSearchService
from minesearch_v2.backend.batch_service import BatchService
from minesearch_v2.backend.config import PERPLEXITY_API_KEY


class TestAPIIntegration:
    """Integration Tests für API Endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test-Client für FastAPI"""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    @pytest.fixture
    def mock_perplexity_response(self):
        """Mock Perplexity API Response"""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "daten": {
                            "Minenname": "Integration Test Mine",
                            "Land": "Kanada",
                            "Region": "Ontario",
                            "Koordinaten": "48.5,-89.3",
                            "Rohstoffe": "Gold",
                            "Status": "Aktiv",
                            "Jahresproduktion": "200,000 oz",
                            "Eigentümer": "Test Mining Corp",
                            "Betreiber": "Test Operations Inc"
                        },
                        "quellen": [
                            {
                                "url": "https://test.com/report.pdf",
                                "titel": "Test Report 2024",
                                "domain": "test.com",
                                "datum": "2024-01-15"
                            }
                        ],
                        "datenqualität": 75,
                        "suchverlauf": []
                    })
                }
            }]
        }
    
    def test_health_endpoint(self, client):
        """Test: Health Check Endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_search_endpoint_basic(self, client, mock_perplexity_response):
        """Test: Basis-Such-Endpoint"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_perplexity_response
            
            response = client.post("/search", json={
                "mine_name": "Integration Test Mine",
                "country": "Kanada"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["daten"]["Minenname"] == "Integration Test Mine"
            assert data["datenqualität"] == 75
    
    def test_search_endpoint_with_options(self, client, mock_perplexity_response):
        """Test: Such-Endpoint mit erweiterten Optionen"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_perplexity_response
            
            response = client.post("/search", json={
                "mine_name": "Test Mine",
                "country": "Kanada",
                "enhanced_search": True,
                "smart_search": True,
                "model": "deep_research"
            })
            
            assert response.status_code == 200
            assert mock_post.called
    
    def test_search_endpoint_validation(self, client):
        """Test: Eingabe-Validierung"""
        # Fehlende Pflichtfelder
        response = client.post("/search", json={})
        assert response.status_code == 422
        
        # Leerer Minenname
        response = client.post("/search", json={
            "mine_name": "",
            "country": "Kanada"
        })
        assert response.status_code == 422
    
    def test_batch_upload_endpoint(self, client):
        """Test: Batch Upload Endpoint"""
        csv_content = """Minenname,Land,Region
Test Mine 1,Kanada,Ontario
Test Mine 2,USA,Nevada"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post("/batch/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["total_mines"] == 2
    
    def test_batch_status_endpoint(self, client):
        """Test: Batch Status Endpoint"""
        # Nicht existierende Session
        response = client.get("/batch/status/non-existent-session")
        assert response.status_code == 404
    
    def test_batch_download_endpoint(self, client):
        """Test: Batch Download Endpoint"""
        # Nicht existierende Session
        response = client.get("/batch/download/non-existent-session")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_websocket_updates(self):
        """Test: WebSocket Updates"""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            with client.websocket_connect("/ws/test-session") as websocket:
                # Send test message
                websocket.send_json({"type": "ping"})
                
                # Should receive response
                data = websocket.receive_json()
                assert data is not None


class TestPerplexityAPIIntegration:
    """Integration Tests für Perplexity API"""
    
    @pytest.fixture
    def service(self):
        """MineSearchService Instanz"""
        return MineSearchService()
    
    @pytest.mark.skipif(not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == "your_perplexity_api_key_here", 
                       reason="Perplexity API Key nicht konfiguriert")
    def test_real_api_call(self, service):
        """Test: Echter API Call (nur wenn API Key vorhanden)"""
        # Sehr limitierter Test um API Limits zu schonen
        result = service.search_mine("Cerro Verde", "Peru", timeout_override=5)
        
        assert result is not None
        assert "daten" in result or "error" in result
    
    def test_api_timeout_handling(self, service):
        """Test: API Timeout Handling"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.Timeout("Connection timeout")
            
            result = service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert "error" in result
            assert "Timeout" in result["error"]
    
    def test_api_rate_limit_handling(self, service):
        """Test: API Rate Limit Handling"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 429
            mock_post.return_value.json.return_value = {"error": "Rate limit exceeded"}
            
            result = service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert "error" in result
    
    def test_api_authentication_error(self, service):
        """Test: API Authentication Error"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {"error": "Invalid API key"}
            
            result = service.search_mine("Test Mine", "Kanada")
            
            assert result is not None
            assert "error" in result


class TestBatchProcessingIntegration:
    """Integration Tests für Batch Processing"""
    
    @pytest.fixture
    def batch_service(self):
        """BatchService Instanz"""
        return BatchService()
    
    def test_batch_processing_flow(self, batch_service):
        """Test: Kompletter Batch Processing Flow"""
        # CSV Daten
        csv_data = [
            {"Minenname": "Mine 1", "Land": "Kanada", "Region": "Ontario"},
            {"Minenname": "Mine 2", "Land": "Chile", "Region": "Atacama"}
        ]
        
        with patch.object(batch_service.search_service, 'search_mine') as mock_search:
            mock_search.return_value = {
                "daten": {"Minenname": "Test", "Land": "Test"},
                "quellen": [],
                "datenqualität": 50
            }
            
            # Session erstellen
            session = batch_service.create_session(csv_data)
            assert session is not None
            assert session.total_mines == 2
            
            # Batch verarbeiten
            asyncio.run(batch_service.process_batch(session.id))
            
            # Status prüfen
            status = batch_service.get_session_status(session.id)
            assert status["processed"] == 2
            assert status["status"] == "completed"
    
    def test_batch_error_handling(self, batch_service):
        """Test: Fehlerbehandlung im Batch Processing"""
        csv_data = [{"Minenname": "Error Mine", "Land": "Unknown"}]
        
        with patch.object(batch_service.search_service, 'search_mine') as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            session = batch_service.create_session(csv_data)
            
            # Should handle error gracefully
            asyncio.run(batch_service.process_batch(session.id))
            
            status = batch_service.get_session_status(session.id)
            assert status["errors"] > 0


class TestEndToEndScenarios:
    """End-to-End Test Szenarien"""
    
    @pytest.fixture
    def client(self):
        """Test-Client für FastAPI"""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_complete_search_flow(self, client):
        """Test: Kompletter Such-Flow"""
        with patch('requests.post') as mock_post:
            # Mock verschiedene Responses für verschiedene Phasen
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "daten": {
                                "Minenname": "E2E Test Mine",
                                "Land": "Kanada",
                                "Koordinaten": "48.5,-89.3",
                                "Rohstoffe": "Gold, Silber"
                            },
                            "quellen": [
                                {"url": "https://gov.ca/mine", "domain": "gov.ca"},
                                {"url": "https://tsx.com/mine", "domain": "tsx.com"}
                            ],
                            "datenqualität": 85
                        })
                    }
                }]
            }
            
            # 1. Einfache Suche
            response = client.post("/search", json={
                "mine_name": "E2E Test Mine",
                "country": "Kanada"
            })
            assert response.status_code == 200
            
            # 2. Erweiterte Suche
            response = client.post("/search", json={
                "mine_name": "E2E Test Mine",
                "country": "Kanada",
                "enhanced_search": True
            })
            assert response.status_code == 200
            
            # 3. Smart Search
            response = client.post("/search", json={
                "mine_name": "E2E Test Mine",
                "country": "Kanada",
                "smart_search": True,
                "model": "deep_research"
            })
            assert response.status_code == 200
    
    def test_complete_batch_flow(self, client):
        """Test: Kompletter Batch-Flow"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "daten": {"Minenname": "Batch Mine"},
                            "quellen": [],
                            "datenqualität": 60
                        })
                    }
                }]
            }
            
            # 1. Upload CSV
            csv_content = "Minenname,Land\nBatch Mine 1,Kanada\nBatch Mine 2,Chile"
            files = {"file": ("batch.csv", csv_content, "text/csv")}
            
            upload_response = client.post("/batch/upload", files=files)
            assert upload_response.status_code == 200
            
            session_id = upload_response.json()["session_id"]
            
            # 2. Check Status
            status_response = client.get(f"/batch/status/{session_id}")
            assert status_response.status_code == 200
            
            # 3. Process (würde normalerweise automatisch laufen)
            # Hier nur simuliert
            
            # 4. Download Results
            # (würde nach Verarbeitung funktionieren)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-k", "not real_api_call"])