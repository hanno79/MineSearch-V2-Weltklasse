"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: API-Key Validierung für alle Provider
"""

import re
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Validiert API-Keys für verschiedene Provider"""
    
    # API-Key Format-Patterns
    KEY_PATTERNS = {
        'perplexity': {
            'pattern': r'^pplx-[a-fA-F0-9]{48}$',
            'description': 'Format: pplx-[48 hexadezimale Zeichen]',
            'example': 'pplx-1234567890abcdef...'
        },
        'openrouter': {
            'pattern': r'^sk-or-v1-[a-fA-F0-9]{64}$',
            'description': 'Format: sk-or-v1-[64 hexadezimale Zeichen]',
            'example': 'sk-or-v1-1234567890abcdef...'
        },
        'tavily': {
            'pattern': r'^tvly-[a-zA-Z0-9]{32}$',
            'description': 'Format: tvly-[32 alphanumerische Zeichen]',
            'example': 'tvly-abc123def456...'
        },
        'exa': {
            'pattern': r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
            'description': 'Format: UUID (8-4-4-4-12 hexadezimale Zeichen)',
            'example': '12345678-1234-5678-1234-567812345678'
        },
        'scrapingbee': {
            'pattern': r'^[A-Z0-9]{80,100}$',
            'description': 'Format: 80-100 Großbuchstaben und Zahlen',
            'example': 'ABCDEF123456...'
        },
        'firecrawl': {
            'pattern': r'^fc-[a-zA-Z0-9]{32,48}$',
            'description': 'Format: fc-[32-48 alphanumerische Zeichen]',
            'example': 'fc-abc123def456...'
        },
        'brightdata': {
            'pattern': r'^[a-zA-Z0-9_-]{20,}$',
            'description': 'Format: Mindestens 20 alphanumerische Zeichen, _ oder -',
            'example': 'user123-zone456_key789'
        },
        'openai': {
            'pattern': r'^sk-[a-zA-Z0-9]{48}$',
            'description': 'Format: sk-[48 alphanumerische Zeichen]',
            'example': 'sk-abc123def456...'
        },
        'anthropic': {
            'pattern': r'^sk-ant-api03-[a-zA-Z0-9-_]{95}$',
            'description': 'Format: sk-ant-api03-[95 Zeichen]',
            'example': 'sk-ant-api03-abc123...'
        },
        'gemini': {
            'pattern': r'^[a-zA-Z0-9_-]{39}$',
            'description': 'Format: 39 alphanumerische Zeichen, _ oder -',
            'example': 'AIzaSyAbc123def456...'
        },
        'grok': {
            'pattern': r'^xai-[a-zA-Z0-9]{48,64}$',
            'description': 'Format: xai-[48-64 alphanumerische Zeichen]',
            'example': 'xai-abc123def456...'
        },
        'abacus': {
            'pattern': r'^[a-zA-Z0-9]{32,}$',
            'description': 'Format: Mindestens 32 alphanumerische Zeichen',
            'example': 'abc123def456ghi789...'
        }
    }
    
    @classmethod
    def validate_key(cls, provider: str, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validiert einen API-Key für einen bestimmten Provider
        
        Args:
            provider: Provider-Name
            api_key: Zu validierender API-Key
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not api_key:
            return False, "API-Key ist leer"
        
        # Entferne Whitespace
        api_key = api_key.strip()
        
        # Provider bekannt?
        if provider not in cls.KEY_PATTERNS:
            logger.warning(f"Keine Validierung für Provider {provider} definiert")
            # Basis-Validierung: Mindestens 10 Zeichen
            if len(api_key) < 10:
                return False, "API-Key zu kurz (mindestens 10 Zeichen erforderlich)"
            return True, None
        
        # Hole Pattern für Provider
        pattern_info = cls.KEY_PATTERNS[provider]
        pattern = pattern_info['pattern']
        
        # Validiere gegen Pattern
        if not re.match(pattern, api_key):
            error_msg = (
                f"API-Key entspricht nicht dem erwarteten Format für {provider}. "
                f"{pattern_info['description']}. "
                f"Beispiel: {pattern_info['example']}"
            )
            return False, error_msg
        
        return True, None
    
    @classmethod
    def validate_all_keys(cls, config: Dict[str, Dict]) -> Dict[str, Dict[str, any]]:
        """
        Validiert alle API-Keys in der Konfiguration
        
        Args:
            config: Provider-Konfiguration
            
        Returns:
            Dict mit Validierungsergebnissen pro Provider
        """
        results = {}
        
        for provider, provider_config in config.items():
            if not provider_config.get('enabled', False):
                results[provider] = {
                    'enabled': False,
                    'validated': False,
                    'message': 'Provider deaktiviert'
                }
                continue
            
            api_key = provider_config.get('api_key', '')
            is_valid, error_msg = cls.validate_key(provider, api_key)
            
            results[provider] = {
                'enabled': True,
                'validated': is_valid,
                'message': error_msg if not is_valid else 'API-Key validiert'
            }
            
            if not is_valid:
                logger.warning(f"[API-KEY-VALIDATOR] {provider}: {error_msg}")
            else:
                logger.info(f"[API-KEY-VALIDATOR] {provider}: API-Key Format korrekt")
        
        return results
    
    @classmethod
    def mask_key(cls, api_key: str) -> str:
        """
        Maskiert einen API-Key für sichere Anzeige
        
        Args:
            api_key: Zu maskierender API-Key
            
        Returns:
            Maskierter API-Key
        """
        if not api_key or len(api_key) < 8:
            return "***"
        
        # Zeige erste 4 und letzte 4 Zeichen
        return f"{api_key[:4]}...{api_key[-4:]}"