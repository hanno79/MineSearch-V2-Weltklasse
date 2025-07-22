#!/usr/bin/env python3
"""
Debug-Skript für Test Model Selection Analysis
Author: rahn
Datum: 13.07.2025
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_test_model_selection():
    """Debug Test Framework Model Selection"""
    logger.info("🔍 [TEST-DEBUG] Starting Test Model Selection Analysis")
    
    try:
        # Import Test Framework und Registry
        from provider_test_framework import ProviderTestFramework
        from providers.registry import provider_registry
        from config.providers import PROVIDERS_CONFIG
        
        # Initialize Registry (wie in echten Tests)
        provider_registry.initialize(PROVIDERS_CONFIG)
        
        # Initialize Test Framework
        framework = ProviderTestFramework()
        
        # Test different filter scenarios
        test_scenarios = [
            ("all", "All models"),
            ("anthropic", "Anthropic only"),
            ("gemini", "Gemini only"),
            ("grok", "Grok only"),
            ("openai", "OpenAI only"),
            ("perplexity", "Perplexity only"),
            ("openrouter", "OpenRouter only")
        ]
        
        logger.info("🧪 [TEST-DEBUG] TESTING MODEL SELECTION FOR DIFFERENT FILTERS:")
        
        for filter_value, description in test_scenarios:
            logger.info(f"\n📋 [TEST-DEBUG] Testing filter: '{filter_value}' ({description})")
            
            try:
                # Test _get_models_for_filter method
                models_selected = framework._get_models_for_filter(filter_value)
                logger.info(f"  📊 Selected: {len(models_selected)} models")
                
                if models_selected:
                    # Group by provider for analysis
                    provider_groups = {}
                    for model_id in models_selected:
                        provider_name = model_id.split(':')[0] if ':' in model_id else 'unknown'
                        if provider_name not in provider_groups:
                            provider_groups[provider_name] = []
                        provider_groups[provider_name].append(model_id)
                    
                    for provider_name in sorted(provider_groups.keys()):
                        models = provider_groups[provider_name]
                        logger.info(f"    {provider_name}: {len(models)} models")
                        for model_id in models:
                            logger.info(f"      - {model_id}")
                else:
                    logger.error(f"  ❌ NO MODELS SELECTED for filter '{filter_value}'")
                
                # Test provider availability validation
                logger.info(f"  🔍 Testing provider availability validation...")
                available_models = []
                
                # Simulate _validate_provider_availability method logic
                for model_id in models_selected:
                    try:
                        provider_name = model_id.split(':')[0]
                        model_name = model_id.split(':')[1]
                        
                        # Check if provider enabled and model configured
                        provider_config = PROVIDERS_CONFIG.get(provider_name, {})
                        if (provider_config.get('enabled', False) and 
                            model_name in provider_config.get('models', {})):
                            available_models.append(model_id)
                        else:
                            logger.warning(f"    ⚠️  {model_id}: Provider disabled or model not configured")
                    except Exception as e:
                        logger.error(f"    ❌ {model_id}: Validation error - {e}")
                
                logger.info(f"  ✅ Available after validation: {len(available_models)}/{len(models_selected)} models")
                
                if len(available_models) != len(models_selected):
                    filtered_out = len(models_selected) - len(available_models)
                    logger.warning(f"  ⚠️  {filtered_out} models filtered out during validation")
                
            except Exception as e:
                logger.error(f"  ❌ ERROR testing filter '{filter_value}': {e}")
                import traceback
                logger.error(f"  🔍 Traceback: {traceback.format_exc()}")
        
        # Special analysis for Premium LLMs
        logger.info(f"\n🎯 [TEST-DEBUG] PREMIUM LLM SPECIAL ANALYSIS:")
        
        expected_premium_models = [
            'anthropic:claude-sonnet-4',
            'anthropic:claude-opus-4', 
            'anthropic:claude-3.7-sonnet',
            'gemini:gemini-2.5-pro',
            'gemini:gemini-2.5-flash',
            'gemini:gemini-2.5-flash-lite',
            'grok:grok-4',
            'grok:grok-3',
            'grok:grok-3-mini',
            'grok:grok-3-fast'
        ]
        
        # Check if these models would be selected by "all" filter
        all_models = framework._get_models_for_filter("all")
        
        found_premium = []
        missing_premium = []
        
        for model_id in expected_premium_models:
            if model_id in all_models:
                found_premium.append(model_id)
                logger.info(f"  ✅ {model_id}: Would be selected for testing")
            else:
                missing_premium.append(model_id)
                logger.error(f"  ❌ {model_id}: NOT selected for testing")
        
        logger.info(f"\n📊 [TEST-DEBUG] PREMIUM MODEL SELECTION SUMMARY:")
        logger.info(f"  Selected for testing: {len(found_premium)}/10")
        logger.info(f"  NOT selected: {len(missing_premium)}/10")
        
        if missing_premium:
            logger.error(f"  🚨 PROBLEM: These premium models won't be tested: {missing_premium}")
        
        # Test Registry availability for premium models
        logger.info(f"\n🔍 [TEST-DEBUG] REGISTRY AVAILABILITY CHECK FOR MISSING MODELS:")
        registry_models = provider_registry.get_all_models()
        
        for model_id in missing_premium:
            if model_id in registry_models:
                logger.info(f"  ✅ {model_id}: Available in Registry")
                
                # Check provider config
                provider_name = model_id.split(':')[0]
                model_name = model_id.split(':')[1]
                provider_config = PROVIDERS_CONFIG.get(provider_name, {})
                
                if not provider_config.get('enabled', False):
                    logger.error(f"    ❌ Provider {provider_name} is DISABLED in config")
                elif model_name not in provider_config.get('models', {}):
                    logger.error(f"    ❌ Model {model_name} not in {provider_name} config")
                else:
                    logger.info(f"    ✅ Provider and model properly configured")
            else:
                logger.error(f"  ❌ {model_id}: NOT available in Registry")
        
        return {
            'premium_selected': len(found_premium),
            'premium_missing': len(missing_premium),
            'missing_models': missing_premium,
            'test_scenarios': len(test_scenarios)
        }
        
    except Exception as e:
        logger.error(f"🚨 [TEST-DEBUG] CRITICAL ERROR: {e}")
        import traceback
        logger.error(f"🔍 [TEST-DEBUG] Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    result = debug_test_model_selection()
    
    if result:
        print(f"\n{'='*80}")
        print("🎯 TEST MODEL SELECTION DEBUG SUMMARY")
        print("="*80)
        print(f"Premium Models Selected: {result['premium_selected']}/10")
        print(f"Premium Models Missing: {result['premium_missing']}/10")
        
        if result['premium_missing'] == 0:
            print("✅ STATUS: ALL PREMIUM MODELS WOULD BE TESTED")
        else:
            print("❌ STATUS: PREMIUM MODELS MISSING FROM TEST SELECTION")
            print(f"Missing: {result['missing_models']}")
            
        print("="*80)
    else:
        print("❌ TEST SELECTION DEBUG FAILED")