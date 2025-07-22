#!/usr/bin/env python3
"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Einzelner Abacus Provider Test
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ABACUS-FIX 18.07.2025: Force reload environment before importing config
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

from providers.registry import provider_registry
from search_service_multi_enhanced import EnhancedMultiProviderSearchService
from config.base import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_abacus_single():
    """Test nur Abacus Provider mit einer Quebec Mine"""
    
    logger.info("🔧 ABACUS SINGLE PROVIDER TEST")
    logger.info("=" * 50)
    
    # Initialize registry
    logger.info("📋 Initialisiere Provider Registry...")
    provider_registry.initialize(config.PROVIDERS)
    
    all_models = provider_registry.get_all_models()
    logger.info(f"✅ {len(all_models)} Modelle total verfügbar")
    
    # Check if abacus is available
    if 'abacus:deep-agent' not in all_models:
        logger.error("❌ abacus:deep-agent nicht verfügbar!")
        return
    
    logger.info("✅ abacus:deep-agent gefunden")
    
    # Test the provider
    abacus_provider = provider_registry.get_provider('abacus')
    if not abacus_provider:
        logger.error("❌ Abacus Provider nicht initialisiert!")
        return
    
    logger.info(f"✅ Abacus Provider initialisiert mit API Key: {abacus_provider.api_key[:20]}...")
    
    # Initialize enhanced service
    enhanced_service = EnhancedMultiProviderSearchService()
    
    # Test search
    logger.info("🔍 Starte Abacus Test für Éléonore Mine...")
    start_time = datetime.now()
    
    try:
        result = await enhanced_service.search_single_model(
            model_id='abacus:deep-agent',
            mine_name='Éléonore',
            country='Canada',
            region='Quebec',
            commodity='Gold'
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("=" * 50)
        logger.info("🎉 ABACUS TEST ERGEBNIS")
        logger.info("=" * 50)
        logger.info(f"⏱️ Dauer: {duration:.1f} Sekunden")
        logger.info(f"✅ Erfolg: {result.get('success', False)}")
        
        if result.get('success'):
            data = result.get('data', {})
            structured_data = data.get('structured_data', {})
            sources = data.get('sources', [])
            
            # Zähle gefüllte Felder
            filled_fields = sum(1 for v in structured_data.values() if v and v != '-' and str(v).strip())
            
            logger.info(f"📊 Gefüllte Felder: {filled_fields}")
            logger.info(f"🔗 Quellen: {len(sources)}")
            logger.info(f"📝 Content Länge: {len(data.get('content', ''))}")
            
            # Zeige einige Beispiel-Felder
            logger.info("📋 Beispiel-Daten:")
            for field, value in list(structured_data.items())[:10]:
                if value and value != '-':
                    logger.info(f"   {field}: {str(value)[:100]}")
        else:
            error = result.get('error', 'Unbekannter Fehler')
            logger.error(f"❌ Fehler: {error}")
            
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Exception nach {duration:.1f}s: {e}")
    
    logger.info("=" * 50)
    logger.info("🏁 ABACUS SINGLE TEST ABGESCHLOSSEN")

if __name__ == "__main__":
    asyncio.run(test_abacus_single())