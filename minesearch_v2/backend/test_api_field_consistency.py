"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Test für include_field_consistency Parameter in der API
"""

import requests
import json
import sys
import logging
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_field_consistency():
    """Test die neue include_field_consistency Funktionalität"""
    
    base_url = "http://localhost:8002"
    
    try:
        # Test 1: API ohne include_field_consistency Parameter (default=False)
        logger.info("Test 1: API ohne include_field_consistency Parameter")
        response = requests.get(f"{base_url}/api/statistics/models/openrouter/anthropic/claude-3.5-sonnet/details")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API funktioniert - Status: {response.status_code}")
            
            # Prüfe dass critical_fields_consistency NICHT vorhanden ist
            if "critical_fields_consistency" not in data.get("data", {}):
                logger.info("✅ critical_fields_consistency ist wie erwartet nicht im Response (default=False)")
            else:
                logger.warning("⚠️ critical_fields_consistency ist unerwartet im Response vorhanden")
        else:
            logger.error(f"❌ API-Fehler - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
        
        # Test 2: API mit include_field_consistency=true
        logger.info("\nTest 2: API mit include_field_consistency=true")
        response = requests.get(f"{base_url}/api/statistics/models/openrouter/anthropic/claude-3.5-sonnet/details?include_field_consistency=true")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API funktioniert mit Parameter - Status: {response.status_code}")
            
            # Prüfe dass critical_fields_consistency vorhanden ist (falls Daten existieren)
            if "critical_fields_consistency" in data.get("data", {}):
                consistency_data = data["data"]["critical_fields_consistency"]
                logger.info(f"✅ critical_fields_consistency gefunden: {consistency_data}")
                logger.info(f"Datentyp: {type(consistency_data)}")
                if isinstance(consistency_data, dict):
                    logger.info(f"Anzahl Felder: {len(consistency_data)}")
                    for field, value in list(consistency_data.items())[:3]:
                        logger.info(f"  {field}: {value}")
            else:
                logger.info("ℹ️ critical_fields_consistency nicht im Response (möglicherweise keine ModelSummary-Daten verfügbar)")
        else:
            logger.error(f"❌ API-Fehler mit Parameter - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
        
        # Test 3: API mit include_field_consistency=false (explizit)
        logger.info("\nTest 3: API mit include_field_consistency=false")
        response = requests.get(f"{base_url}/api/statistics/models/openrouter/anthropic/claude-3.5-sonnet/details?include_field_consistency=false")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API funktioniert mit false Parameter - Status: {response.status_code}")
            
            # Prüfe dass critical_fields_consistency NICHT vorhanden ist
            if "critical_fields_consistency" not in data.get("data", {}):
                logger.info("✅ critical_fields_consistency ist wie erwartet nicht im Response (explizit false)")
            else:
                logger.warning("⚠️ critical_fields_consistency ist unerwartet im Response vorhanden")
        else:
            logger.error(f"❌ API-Fehler mit false Parameter - Status: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        logger.error("❌ Verbindung fehlgeschlagen - Server läuft wahrscheinlich nicht auf localhost:8002")
        logger.info("Starte den Server mit: python -m uvicorn main:app --host 0.0.0.0 --port 8002")
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    logger.info("=== API Field Consistency Test ===")
    logger.info(f"Zeit: {datetime.now()}")
    test_api_field_consistency()
    logger.info("=== Test abgeschlossen ===")