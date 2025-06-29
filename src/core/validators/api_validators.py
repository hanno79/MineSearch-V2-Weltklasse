"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: API-Datenvalidierung
"""

from typing import Any, Dict
from .base import BaseValidator
from ..logger import get_logger

logger = get_logger(__name__)


class APIValidator(BaseValidator):
    """Validierung für API-Responses und Suchergebnisse"""
    
    def validate_search_result(self, result: Dict[str, Any]) -> bool:
        """Validiert einzelnes Suchergebnis"""
        required_fields = ['field_name', 'value', 'source', 'agent_name']
        
        for field in required_fields:
            if field not in result:
                logger.error(f"Suchergebnis fehlt Pflichtfeld: {field}")
                return False
        
        # Wert darf nicht leer sein
        if result['value'] is None or result['value'] == '':
            logger.warning(f"Leerer Wert für Feld: {result['field_name']}")
            return False
        
        return True
    
    def validate_api_response(self, response: Dict[str, Any]) -> bool:
        """Validiert API Response"""
        # Prüfe auf Erfolg
        if 'status' in response and response['status'] != 'success':
            logger.error(f"API Response mit Fehlerstatus: {response.get('status')}")
            return False
        
        # Prüfe auf Daten
        if 'data' not in response:
            logger.error("API Response ohne Daten-Feld")
            return False
        
        return True
    
    def validate_batch_results(self, results: list) -> int:
        """Validiert Batch-Ergebnisse und gibt Anzahl valider Ergebnisse zurück"""
        valid_count = 0
        
        for result in results:
            if self.validate_search_result(result):
                valid_count += 1
        
        return valid_count