#!/usr/bin/env python3
"""
Focussed Test für Premium LLM Models - Individual Model Testing
Author: rahn
Datum: 13.07.2025
"""

import asyncio
import logging
from datetime import datetime
from provider_test_framework import ProviderTestFramework

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_premium_models_only():
    """Test nur Premium LLM Models um schnell zu verifizieren dass der Fix funktioniert"""
    
    logger.info("🎯 [PREMIUM-TEST] Teste nur Premium LLM Models mit Fixed Validation")
    
    # Premium Models die getestet werden sollen
    premium_models = [
        'anthropic:claude-sonnet-4',
        'gemini:gemini-2.5-pro', 
        'grok:grok-4'
    ]
    
    try:
        test_framework = ProviderTestFramework()
        
        for model_id in premium_models:
            logger.info(f"🔧 [PREMIUM-TEST] Teste Model: {model_id}")
            
            # Test nur 1 Mine, 1 Run für Speed
            mine = test_framework.QUEBEC_MINES[0]  # Éléonore
            
            try:
                result = await test_framework._test_single_run(model_id, mine, 1)
                
                if result.success:
                    logger.info(f"✅ [PREMIUM-TEST] {model_id} ERFOLGREICH: {result.fields_found} Felder")
                else:
                    logger.error(f"❌ [PREMIUM-TEST] {model_id} FEHLGESCHLAGEN: {result.error}")
                    
            except Exception as e:
                logger.error(f"💥 [PREMIUM-TEST] {model_id} EXCEPTION: {e}")
        
        logger.info("🏁 [PREMIUM-TEST] Premium Model Tests abgeschlossen")
        
        # Check Database
        from debug_database import debug_database_individual_models
        result = debug_database_individual_models()
        
        if result:
            premium_found = result['premium_found']
            premium_missing = result['premium_missing']
            
            print(f"\n{'='*60}")
            print("🎯 PREMIUM MODEL TEST RESULTS")
            print("="*60)
            print(f"Premium Models in Database: {premium_found}/10")
            print(f"Premium Models Missing: {premium_missing}")
            
            if premium_found > 0:
                print("✅ SUCCESS: Premium Models are now being tested!")
            else:
                print("❌ PROBLEM: Premium Models still not in database")
        
    except Exception as e:
        logger.error(f"🚨 [PREMIUM-TEST] Critical error: {e}")
        import traceback
        logger.error(f"🔍 [PREMIUM-TEST] Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_premium_models_only())