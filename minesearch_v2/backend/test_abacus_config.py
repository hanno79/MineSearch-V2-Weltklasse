#!/usr/bin/env python3
"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Test für Abacus Provider Konfiguration und API Key Loading
"""

import os
import sys
import logging

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ABACUS-FIX 18.07.2025: Force reload environment
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

from config.api_keys import APIKeysConfig
from config.providers import PROVIDERS_CONFIG
from providers.registry import provider_registry
from config.base import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_abacus_configuration():
    """Test Abacus Provider Konfiguration"""
    
    logger.info("🔧 ABACUS PROVIDER KONFIGURATION TEST")
    logger.info("=" * 50)
    
    # 1. Test Environment Variable Loading
    logger.info("1. Environment Variable Test:")
    env_key = os.getenv('ABACUS_API_KEY')
    logger.info(f"   ABACUS_API_KEY from os.getenv(): {env_key}")
    
    # 2. Test APIKeysConfig
    logger.info("2. APIKeysConfig Test:")
    config_key = APIKeysConfig.ABACUS_API_KEY
    logger.info(f"   APIKeysConfig.ABACUS_API_KEY: {config_key}")
    
    # 3. Test Provider Configuration
    logger.info("3. Provider Configuration Test:")
    abacus_config = PROVIDERS_CONFIG.get('abacus', {})
    logger.info(f"   Provider enabled: {abacus_config.get('enabled', False)}")
    logger.info(f"   Provider API key: {abacus_config.get('api_key', 'NOT_FOUND')}")
    
    # 4. Test Key Validation
    logger.info("4. API Key Validation Test:")
    is_valid = APIKeysConfig.validate_key('ABACUS_API_KEY', config_key)
    logger.info(f"   Key validation result: {is_valid}")
    
    # 5. Test Provider Registry
    logger.info("5. Provider Registry Test:")
    try:
        provider_registry.initialize(config.PROVIDERS)
        abacus_provider = provider_registry.get_provider('abacus')
        
        if abacus_provider:
            logger.info(f"   Provider instance created: ✅")
            logger.info(f"   Provider API key: {abacus_provider.api_key}")
            
            # Test validation
            is_provider_valid = abacus_provider.validate_config()
            logger.info(f"   Provider validation: {'✅' if is_provider_valid else '❌'}")
            
            # Test models
            models = abacus_provider.get_models()
            logger.info(f"   Available models: {len(models)}")
            for model_id, model_config in models.items():
                logger.info(f"     - {model_id}: {model_config.name}")
                
        else:
            logger.error("   Provider instance: ❌ NOT FOUND")
    
    except Exception as e:
        logger.error(f"   Provider Registry Error: {e}")
    
    # 6. Test Missing Keys Detection
    logger.info("6. Missing Keys Detection:")
    missing_keys = APIKeysConfig.get_missing_keys()
    if 'ABACUS_API_KEY' in missing_keys:
        logger.warning("   Abacus key detected as missing!")
    else:
        logger.info("   Abacus key NOT in missing keys list ✅")
    
    logger.info("=" * 50)
    logger.info("🏁 ABACUS CONFIGURATION TEST COMPLETE")

if __name__ == "__main__":
    test_abacus_configuration()