#!/usr/bin/env python3
"""
Debug the provider registry to see how many models are available
"""

import sys
sys.path.append('/app/backend')

from minesearch.providers.registry import provider_registry

print("🔍 DEBUG: Provider Registry Analysis")
print("=" * 50)

# Get all models from registry
all_models = provider_registry.get_all_models()
print(f"📊 Total models in provider registry: {len(all_models)}")

# Group by provider
providers = {}
for model_id in all_models.keys():
    if ':' in model_id:
        provider = model_id.split(':')[0]
        if provider not in providers:
            providers[provider] = 0
        providers[provider] += 1

print(f"\n🏢 Models by provider:")
for provider, count in providers.items():
    print(f"  {provider}: {count} models")

print(f"\n📋 First 10 model IDs:")
for i, model_id in enumerate(sorted(all_models.keys())[:10]):
    print(f"  {i+1}. {model_id}")

print(f"\n🎯 Expected: ~55 models")
print(f"🔍 Found: {len(all_models)} models")

if len(all_models) < 30:
    print(f"\n⚠️ WARNING: Provider registry might not be fully initialized!")
    print("This could be why we're not seeing all 55 models.")
