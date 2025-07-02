"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Gemeinsame Test-Fixtures und Konfiguration für pytest
"""

# ÄNDERUNG 01.07.2025: Central Test-Konfiguration erstellt

import pytest
import os
import sys
import json
from unittest.mock import Mock, patch
from datetime import datetime

# Backend-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import config


# Globale Test-Konfiguration
@pytest.fixture(scope="session")
def test_config():
    """Globale Test-Konfiguration"""
    return {
        "test_mine_name": "Test Gold Mine",
        "test_country": "Kanada",
        "test_region": "Ontario",
        "test_coordinates": "48.5,-89.3",
        "test_commodities": ["Gold", "Silber"],
        "api_timeout": 5,  # Kurzer Timeout für Tests
        "use_mock_api": True  # Mock API für Tests verwenden
    }


# Mock Perplexity Response
@pytest.fixture
def mock_perplexity_success():
    """Erfolgreiche Perplexity API Response"""
    return {
        "id": "test-response-id",
        "model": "sonar",
        "created": int(datetime.now().timestamp()),
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 250,
            "total_tokens": 400
        },
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "daten": {
                        "Minenname": "Test Gold Mine",
                        "Land": "Kanada",
                        "Region": "Ontario",
                        "Koordinaten": "48.5,-89.3",
                        "Rohstoffe": "Gold, Silber",
                        "Eigentümer": "Test Mining Corp",
                        "Betreiber": "Test Operations Ltd",
                        "Status": "Aktiv",
                        "Jahresproduktion": "250,000 oz Gold",
                        "Reserven": "5 Mio oz Gold",
                        "Ressourcen": "8 Mio oz Gold",
                        "Minenlaufzeit": "2020-2035",
                        "Mitarbeiter": "650",
                        "Website": "www.testgoldmine.com",
                        "Kontakt": "info@testgoldmine.com",
                        "Telefon": "+1-705-555-0123",
                        "Adresse": "123 Mining Road, Thunder Bay, ON",
                        "Beschreibung": "Moderne Goldmine mit nachhaltigen Praktiken",
                        "Gründungsjahr": "2018",
                        "Minentyp": "Tagebau und Untertagebau",
                        "Verarbeitungskapazität": "30,000 t/Tag",
                        "Umweltstandards": "ISO 14001, TSM",
                        "Zertifizierungen": "Responsible Gold Mining",
                        "Gewerkschaft": "United Steelworkers",
                        "Investitionsvolumen": "800 Mio CAD",
                        "Infrastruktur": "Straße, Schiene, Strom vorhanden",
                        "Wasserquelle": "Lake Superior",
                        "Energiequelle": "Wasserkraft (80%), Diesel (20%)",
                        "Umweltgenehmigungen": "Vollständig erteilt 2019",
                        "Sicherheitsleistung": "150 Mio CAD",
                        "Restaurationskosten": "200 Mio CAD",
                        "Notizen": "Expansion geplant für 2026"
                    },
                    "quellen": [
                        {
                            "titel": "Official Mining Registry Report 2024",
                            "url": "https://mining.gov.on.ca/reports/test-gold-mine-2024.pdf",
                            "domain": "mining.gov.on.ca",
                            "beschreibung": "Offizieller Regierungsbericht",
                            "datum": "2024-03-15"
                        },
                        {
                            "titel": "TSX Company Filing",
                            "url": "https://tsx.com/companies/test-mining-corp",
                            "domain": "tsx.com",
                            "beschreibung": "Börsennotierung und Finanzdaten",
                            "datum": "2024-06-01"
                        },
                        {
                            "titel": "Environmental Assessment Report",
                            "url": "https://environment.gov.ca/assessments/test-gold-mine",
                            "domain": "environment.gov.ca",
                            "beschreibung": "Umweltverträglichkeitsprüfung",
                            "datum": "2023-12-10"
                        }
                    ],
                    "datenqualität": 92,
                    "suchverlauf": []
                })
            }
        }]
    }


# Mock Perplexity Error Response
@pytest.fixture
def mock_perplexity_error():
    """Fehlerhafte Perplexity API Response"""
    return {
        "error": {
            "message": "API rate limit exceeded",
            "type": "rate_limit_error",
            "code": "rate_limit_exceeded"
        }
    }


# Mock CSV Daten
@pytest.fixture
def sample_csv_data():
    """Beispiel CSV Daten für Batch-Tests"""
    return """Minenname,Land,Region,Rohstoffe
Eagle Gold,Kanada,Yukon,Gold
Cerro Verde,Peru,Arequipa,Kupfer
Olympic Dam,Australien,South Australia,"Kupfer, Uran, Gold"
Grasberg,Indonesien,Papua,"Gold, Kupfer"
Muruntau,Usbekistan,Navoiy,Gold"""


# Mock Mine Data Dictionary
@pytest.fixture
def sample_mine_dict():
    """Beispiel Minen-Dictionary"""
    return {
        "Minenname": "Sample Mine",
        "Land": "Chile",
        "Region": "Atacama",
        "Koordinaten": "-23.65,-70.40",
        "Rohstoffe": "Kupfer, Molybdän",
        "Status": "In Betrieb",
        "Eigentümer": "Sample Mining Company",
        "Betreiber": "Sample Operations SA"
    }


# Session Mock für Batch Processing
@pytest.fixture
def mock_batch_session():
    """Mock Batch Processing Session"""
    from backend.batch_service import BatchSession
    
    session = BatchSession(
        id="test-session-123",
        total_mines=5,
        mines=[
            {"Minenname": f"Mine {i}", "Land": "Kanada"} 
            for i in range(1, 6)
        ]
    )
    session.processed = 0
    session.errors = 0
    session.results = []
    
    return session


# API Client Mock
@pytest.fixture
def mock_api_client():
    """Mock API Client mit vorkonfigurierten Responses"""
    client = Mock()
    client.post = Mock()
    client.get = Mock()
    client.timeout = 30
    return client


# Temporäre Test-Dateien
@pytest.fixture
def temp_test_file(tmp_path):
    """Erstelle temporäre Test-Datei"""
    def _create_file(filename, content):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return str(file_path)
    return _create_file


# Skip wenn kein API Key
@pytest.fixture
def skip_without_api_key():
    """Skip Test wenn kein API Key konfiguriert"""
    if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == "your_perplexity_api_key_here":
        pytest.skip("Perplexity API Key nicht konfiguriert")


# Async Event Loop für async Tests
@pytest.fixture
def event_loop():
    """Event Loop für async Tests"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Environment Variables Mock
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock Environment Variables"""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _set_env


# Cleanup nach Tests
@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup nach jedem Test"""
    yield
    # Hier können Cleanup-Aktionen durchgeführt werden
    # z.B. temporäre Dateien löschen, Connections schließen, etc.


# Markiere Tests die API Keys benötigen
def pytest_configure(config):
    """pytest Konfiguration"""
    config.addinivalue_line(
        "markers", 
        "requires_api_key: Test benötigt gültigen API Key"
    )


# Test Report Customization
def pytest_html_report_title(report):
    """Customize HTML Report Title"""
    report.title = "MineSearch v2 Test Report"