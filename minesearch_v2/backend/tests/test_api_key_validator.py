"""
Author: rahn
Datum: 10.07.2025
Version: 1.0
Beschreibung: Unit-Tests für APIKeyValidator
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_key_validator import APIKeyValidator


class TestAPIKeyValidator:
    """Test-Klasse für API-Key Validierung"""
    
    def test_validate_key_empty(self):
        """Test: Leerer API-Key sollte fehlschlagen"""
        is_valid, error = APIKeyValidator.validate_key('perplexity', '')
        assert not is_valid
        assert error == "API-Key ist leer"
    
    def test_validate_key_whitespace(self):
        """Test: API-Key mit nur Whitespace sollte fehlschlagen"""
        is_valid, error = APIKeyValidator.validate_key('perplexity', '   ')
        assert not is_valid
        # Nach strip() ist der Key leer, aber validate_key sieht nur den getrimmten Key
        # und gibt daher die Format-Fehlermeldung zurück
        assert "Format" in error or error == "API-Key ist leer"
    
    def test_validate_key_unknown_provider(self):
        """Test: Unbekannter Provider sollte Basis-Validierung nutzen"""
        # Zu kurzer Key
        is_valid, error = APIKeyValidator.validate_key('unknown', 'short')
        assert not is_valid
        assert "mindestens 10 Zeichen" in error
        
        # Ausreichend langer Key
        is_valid, error = APIKeyValidator.validate_key('unknown', 'thisisalongapikey123')
        assert is_valid
        assert error is None
    
    def test_validate_perplexity_key(self):
        """Test: Perplexity API-Key Format"""
        # Gültiges Format
        valid_key = 'pplx-' + 'a' * 48
        is_valid, error = APIKeyValidator.validate_key('perplexity', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format - falsches Prefix
        invalid_key = 'sk-' + 'a' * 48
        is_valid, error = APIKeyValidator.validate_key('perplexity', invalid_key)
        assert not is_valid
        assert "pplx-" in error
        
        # Ungültiges Format - zu kurz
        invalid_key = 'pplx-abc'
        is_valid, error = APIKeyValidator.validate_key('perplexity', invalid_key)
        assert not is_valid
    
    def test_validate_openrouter_key(self):
        """Test: OpenRouter API-Key Format"""
        # Gültiges Format
        valid_key = 'sk-or-v1-' + 'a' * 64
        is_valid, error = APIKeyValidator.validate_key('openrouter', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format
        invalid_key = 'sk-or-' + 'a' * 64
        is_valid, error = APIKeyValidator.validate_key('openrouter', invalid_key)
        assert not is_valid
    
    def test_validate_exa_key(self):
        """Test: Exa API-Key Format (UUID)"""
        # Gültiges UUID Format
        valid_key = '12345678-1234-5678-1234-567812345678'
        is_valid, error = APIKeyValidator.validate_key('exa', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format
        invalid_key = '12345678-1234-5678-1234'
        is_valid, error = APIKeyValidator.validate_key('exa', invalid_key)
        assert not is_valid
    
    def test_validate_openai_key(self):
        """Test: OpenAI API-Key Format (aktualisiert)"""
        # Gültiges Format - kurz
        valid_key = 'sk-' + 'a' * 20
        is_valid, error = APIKeyValidator.validate_key('openai', valid_key)
        assert is_valid
        assert error is None
        
        # Gültiges Format - lang
        valid_key = 'sk-proj-' + 'a' * 150
        is_valid, error = APIKeyValidator.validate_key('openai', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format - zu kurz
        invalid_key = 'sk-abc'
        is_valid, error = APIKeyValidator.validate_key('openai', invalid_key)
        assert not is_valid
    
    def test_validate_grok_key(self):
        """Test: Grok API-Key Format (aktualisiert)"""
        # Gültiges Format - kurz
        valid_key = 'xai-' + 'a' * 48
        is_valid, error = APIKeyValidator.validate_key('grok', valid_key)
        assert is_valid
        assert error is None
        
        # Gültiges Format - lang
        valid_key = 'xai-' + 'a' * 80
        is_valid, error = APIKeyValidator.validate_key('grok', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format - zu kurz
        invalid_key = 'xai-abc'
        is_valid, error = APIKeyValidator.validate_key('grok', invalid_key)
        assert not is_valid
    
    def test_validate_deepseek_key(self):
        """Test: DeepSeek API-Key Format"""
        # Gültiges Format
        valid_key = 'sk-' + 'a' * 32
        is_valid, error = APIKeyValidator.validate_key('deepseek', valid_key)
        assert is_valid
        assert error is None
        
        # Ungültiges Format - falsches Prefix
        invalid_key = 'ds-' + 'a' * 32
        is_valid, error = APIKeyValidator.validate_key('deepseek', invalid_key)
        assert not is_valid
    
    def test_validate_all_keys(self):
        """Test: Validierung aller Keys in einer Config"""
        test_config = {
            'perplexity': {
                'enabled': True,
                'api_key': 'pplx-' + 'a' * 48
            },
            'openrouter': {
                'enabled': True,
                'api_key': 'invalid-key'
            },
            'tavily': {
                'enabled': False,
                'api_key': ''
            }
        }
        
        results = APIKeyValidator.validate_all_keys(test_config)
        
        # Perplexity sollte gültig sein
        assert results['perplexity']['enabled']
        assert results['perplexity']['validated']
        assert results['perplexity']['message'] == 'API-Key validiert'
        
        # OpenRouter sollte ungültig sein
        assert results['openrouter']['enabled']
        assert not results['openrouter']['validated']
        assert 'sk-or-v1-' in results['openrouter']['message']
        
        # Tavily sollte deaktiviert sein
        assert not results['tavily']['enabled']
        assert not results['tavily']['validated']
        assert results['tavily']['message'] == 'Provider deaktiviert'
    
    def test_mask_key(self):
        """Test: API-Key Maskierung für sichere Anzeige"""
        # Normaler Key
        key = 'sk-1234567890abcdef'
        masked = APIKeyValidator.mask_key(key)
        assert masked == 'sk-1...cdef'
        
        # Kurzer Key
        short_key = 'abc'
        masked = APIKeyValidator.mask_key(short_key)
        assert masked == '***'
        
        # Leerer Key
        empty_key = ''
        masked = APIKeyValidator.mask_key(empty_key)
        assert masked == '***'
    
    def test_all_provider_patterns(self):
        """Test: Überprüfe dass alle Provider-Patterns definiert sind"""
        expected_providers = [
            'perplexity', 'openrouter', 'tavily', 'exa', 'scrapingbee',
            'firecrawl', 'brightdata', 'openai', 'anthropic', 'gemini',
            'grok', 'abacus', 'deepseek'
        ]
        
        for provider in expected_providers:
            assert provider in APIKeyValidator.KEY_PATTERNS
            pattern_info = APIKeyValidator.KEY_PATTERNS[provider]
            assert 'pattern' in pattern_info
            assert 'description' in pattern_info
            assert 'example' in pattern_info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])