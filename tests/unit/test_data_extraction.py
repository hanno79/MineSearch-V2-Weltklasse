"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Unit Tests für DataExtractionService
"""

import pytest
import sys
import os

# Füge Backend-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from minesearch.data_extraction import DataExtractionService


class TestDataExtractionService:
    """Test-Klasse für DataExtractionService"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.service = DataExtractionService()
    
    def test_extract_field_value_basic(self):
        """Test grundlegende Feldextraktion"""
        content = "Mine Name: Test Mine\nCountry: Canada\nProduction: 1000 tons"
        
        result = self.service.extract_field_value('mine_name', content, 'Test Mine')
        
        assert result is not None
        assert 'value' in result
        assert result['field'] == 'mine_name'
    
    def test_extract_coordinates(self):
        """Test Koordinaten-Extraktion"""
        content = "Location: 45.5017° N, 73.5673° W"
        
        result = self.service.extract_field_value('coordinates', content, 'Test Mine')
        
        assert result is not None
        if result.get('value'):
            assert ',' in result['value']
    
    def test_extract_production_data(self):
        """Test Produktionsdaten-Extraktion"""
        content = "Annual Production: 1,500,000 tons of iron ore"
        
        result = self.service.extract_field_value('annual_production', content, 'Test Mine')
        
        assert result is not None
        if result.get('value'):
            assert '1500000' in result['value'] or '1,500,000' in result['value']
    
    def test_extract_all_fields(self):
        """Test Extraktion aller Felder"""
        content = """
        Mine Name: Test Mine
        Country: Canada
        Region: Quebec
        Coordinates: 45.5017° N, 73.5673° W
        Mineral Type: Iron Ore
        Annual Production: 1,500,000 tons
        Owner: Test Company
        """
        
        result = self.service.extract_all_fields(content, 'Test Mine')
        
        assert result is not None
        assert 'extracted_data' in result
        assert 'extraction_stats' in result
        assert result['mine_name'] == 'Test Mine'
        assert result['extraction_stats']['total_fields'] > 0
    
    def test_extract_specific_fields(self):
        """Test Extraktion spezifischer Felder"""
        content = "Mine Name: Test Mine\nCountry: Canada\nProduction: 1000 tons"
        fields = ['mine_name', 'country', 'annual_production']
        
        result = self.service.extract_specific_fields(fields, content, 'Test Mine')
        
        assert result is not None
        assert result['requested_fields'] == fields
        assert 'extracted_data' in result
        assert result['extraction_stats']['requested_fields'] == len(fields)
    
    def test_validate_extraction_results(self):
        """Test Validierung von Extraktions-Ergebnissen"""
        extraction_results = {
            'mine_name': 'Test Mine',
            'extracted_data': {
                'mine_name': {'value': 'Test Mine', 'confidence': 0.9},
                'coordinates': {'value': '45.5017, -73.5673', 'confidence': 0.8}
            }
        }
        
        result = self.service.validate_extraction_results(extraction_results)
        
        assert result is not None
        assert 'validation_stats' in result
        assert 'validation_success_rate' in result
    
    def test_empty_content(self):
        """Test mit leerem Inhalt"""
        result = self.service.extract_all_fields("", "Test Mine")
        
        assert result is not None
        assert result['extraction_stats']['successful_extractions'] == 0
    
    def test_invalid_field(self):
        """Test mit ungültigem Feld"""
        content = "Some content here"
        
        result = self.service.extract_field_value('invalid_field', content, 'Test Mine')
        
        assert result is not None
        # Sollte entweder None oder leeren Wert zurückgeben
        assert result.get('value') is None or result.get('value') == ''
    
    def test_confidence_calculation(self):
        """Test Konfidenz-Berechnung"""
        content = "Mine Name: Test Mine\nProduction: 1000 tons"
        
        result = self.service.extract_field_value('mine_name', content, 'Test Mine')
        
        assert result is not None
        if result.get('value'):
            assert 'confidence' in result
            assert 0.0 <= result['confidence'] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])
