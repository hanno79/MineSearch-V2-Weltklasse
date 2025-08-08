"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test Search Endpoint für Debugging und Stabilität
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/test_search")
async def test_search(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test-Endpoint für stabile Suche
    """
    try:
        logger.info(f"[TEST SEARCH] Request: {request}")
        
        mine_name = request.get("mine_name", "Unbekannt")
        country = request.get("country", "Canada")
        model = request.get("model", "test-model")
        
        # Erstelle Test-Daten mit den neuen Datenkonsistenz-Features
        test_structured_data = {
            "Name": mine_name,
            "Country": country,
            "Region": "Quebec",
            "Eigentümer": "Test Company [1]",
            "Betreiber": "Test Operator [1,2]",
            "x-Koordinate": "45.123456",
            "y-Koordinate": "-73.987654",
            "Aktivitätsstatus": "Aktiv [1]",
            "Restaurationskosten": "X",
            "Jahr der Aufnahme der Kosten": "X",
            "Jahr der Erstellung des Dokumentes": "X",
            "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold, Kupfer [1,2]",
            "Minentyp (Untertage/ Open-Pit/ usw.)": "Open-Pit [2]",
            "Produktionsstart": "2010",
            "Produktionsende": "noch aktiv",
            "Fördermenge/Jahr": "50000 oz/Jahr [1]",
            "Fläche der Mine in qkm": "2.5",
            "Quellenangaben": "[1] Test Source 1: https://test1.com\\n[2] Test Source 2: https://test2.com"
        }
        
        # Source Mapping mit neuen Features
        source_mapping = {
            "sources": {
                "1": {
                    "url": "https://test1.com",
                    "title": "Test Source 1",
                    "type": "government",
                    "reliability": 0.9
                },
                "2": {
                    "url": "https://test2.com", 
                    "title": "Test Source 2",
                    "type": "industry",
                    "reliability": 0.7
                }
            },
            "field_sources": {
                "Eigentümer": [1],
                "Betreiber": [1, 2],
                "Aktivitätsstatus": [1],
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": [1, 2],
                "Minentyp (Untertage/ Open-Pit/ usw.)": [2],
                "Fördermenge/Jahr": [1]
            }
        }
        
        return {
            "success": True,
            "data": {
                "structured_data": test_structured_data,
                "source_mapping": source_mapping,
                "mine_name": mine_name,
                "country": country,
                "model_used": model,
                "search_timestamp": datetime.now().isoformat(),
                "search_duration": 1.5,
                "test_mode": True,
                "features_demonstrated": [
                    "LEER-Normalisierung zu X",
                    "Minentyp ohne Präfix",
                    "Quellen-Nummerierung [1,2]",
                    "Feld-spezifische Quellenreferenzen",
                    "Strukturierte Quellenangaben"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"[TEST SEARCH] Fehler: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }