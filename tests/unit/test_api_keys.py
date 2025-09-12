"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Unit Tests für API Keys Konfiguration
"""

import pytest
import sys
import os
from unittest.mock import patch

# Füge Backend-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from minesearch.config.api_keys import APIKeysConfig


class TestAPIKeysConfig:
    """Test-Klasse für APIKeysConfig"""
    
    def test_api_keys_config_creation(self):
        """Test APIKeysConfig-Erstellung"""
        config = APIKeysConfig()
        
        # Prüfe dass alle API-Keys als Attribute existieren
        assert hasattr(config, 'PERPLEXITY_API_KEY')
        assert hasattr(config, 'OPENROUTER_API_KEY')
        assert hasattr(config, 'TAVILY_API_KEY')
        assert hasattr(config, 'EXA_API_KEY')
        assert hasattr(config, 'SCRAPINGBEE_API_KEY')
        assert hasattr(config, 'FIRECRAWL_API_KEY')
        assert hasattr(config, 'BRIGHTDATA_API_KEY')
    
    @patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-perplexity-key'})
    def test_perplexity_api_key_from_env(self):
        """Test Perplexity API Key aus Umgebungsvariable"""
        config = APIKeysConfig()
        assert config.PERPLEXITY_API_KEY == 'test-perplexity-key'
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-openrouter-key'})
    def test_openrouter_api_key_from_env(self):
        """Test OpenRouter API Key aus Umgebungsvariable"""
        config = APIKeysConfig()
        assert config.OPENROUTER_API_KEY == 'test-openrouter-key'
    
    def test_validate_key_valid(self):
        """Test Validierung gültiger API-Keys"""
        valid_keys = [
            ('PERPLEXITY_API_KEY', 'pplx-valid-key-123'),
            ('OPENROUTER_API_KEY', 'sk-or-valid-key-456'),
            ('TAVILY_API_KEY', 'tvly-valid-key-789')
        ]
        
        for key_name, key_value in valid_keys:
            result = APIKeysConfig.validate_key(key_name, key_value)
            assert result == True, f"Key {key_name} sollte gültig sein"
    
    def test_validate_key_invalid(self):
        """Test Validierung ungültiger API-Keys"""
        invalid_keys = [
            ('PERPLEXITY_API_KEY', ''),
            ('OPENROUTER_API_KEY', 'invalid-key'),
            ('TAVILY_API_KEY', None),
            ('UNKNOWN_KEY', 'some-value')
        ]
        
        for key_name, key_value in invalid_keys:
            result = APIKeysConfig.validate_key(key_name, key_value)
            assert result == False, f"Key {key_name} sollte ungültig sein"
    
    def test_get_missing_keys(self):
        """Test Identifikation fehlender API-Keys"""
        with patch.dict(os.environ, {}, clear=True):
            missing_keys = APIKeysConfig.get_missing_keys()
            
            # Alle Keys sollten fehlen
            assert len(missing_keys) > 0
            assert 'PERPLEXITY_API_KEY' in missing_keys
            assert 'OPENROUTER_API_KEY' in missing_keys
    
    def test_get_missing_keys_partial(self):
        """Test Identifikation teilweise fehlender API-Keys"""
        with patch.dict(os.environ, {
            'PERPLEXITY_API_KEY': 'pplx-test-key',
            'OPENROUTER_API_KEY': 'sk-or-test-key'
        }):
            missing_keys = APIKeysConfig.get_missing_keys()
            
            # Einige Keys sollten fehlen
            assert len(missing_keys) > 0
            assert 'PERPLEXITY_API_KEY' not in missing_keys
            assert 'OPENROUTER_API_KEY' not in missing_keys
    
    def test_validate_all_keys(self):
        """Test Validierung aller API-Keys"""
        with patch.dict(os.environ, {
            'PERPLEXITY_API_KEY': 'pplx-test-key',
            'OPENROUTER_API_KEY': 'sk-or-test-key',
            'TAVILY_API_KEY': 'tvly-test-key'
        }):
            result = APIKeysConfig.validate_all_keys()
            
            assert isinstance(result, dict)
            assert 'valid_keys' in result
            assert 'invalid_keys' in result
            assert 'missing_keys' in result
    
    def test_api_key_format_validation(self):
        """Test Format-Validierung für verschiedene API-Keys"""
        # Perplexity Keys sollten mit 'pplx-' beginnen
        assert APIKeysConfig.validate_key('PERPLEXITY_API_KEY', 'pplx-valid-key')
        assert not APIKeysConfig.validate_key('PERPLEXITY_API_KEY', 'invalid-key')
        
        # OpenRouter Keys sollten mit 'sk-or-' beginnen
        assert APIKeysConfig.validate_key('OPENROUTER_API_KEY', 'sk-or-valid-key')
        assert not APIKeysConfig.validate_key('OPENROUTER_API_KEY', 'invalid-key')
        
        # Tavily Keys sollten mit 'tvly-' beginnen
        assert APIKeysConfig.validate_key('TAVILY_API_KEY', 'tvly-valid-key')
        assert not APIKeysConfig.validate_key('TAVILY_API_KEY', 'invalid-key')
    
    def test_empty_key_validation(self):
        """Test Validierung leerer API-Keys"""
        empty_values = ['', None, '   ', '\t', '\n']
        
        for empty_value in empty_values:
            result = APIKeysConfig.validate_key('PERPLEXITY_API_KEY', empty_value)
            assert result == False, f"Leerer Wert '{empty_value}' sollte ungültig sein"
    
    def test_unknown_key_validation(self):
        """Test Validierung unbekannter API-Keys"""
        result = APIKeysConfig.validate_key('UNKNOWN_API_KEY', 'some-value')
        assert result == False, "Unbekannte API-Keys sollten ungültig sein"


if __name__ == "__main__":
    pytest.main([__file__])
