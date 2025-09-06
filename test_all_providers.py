#!/usr/bin/env python3
"""
Comprehensive test for all MineSearch providers
Tests Tavily, ScrapingBee, Firecrawl and other providers
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
API_URL = "http://localhost:8000/api/search"
MINE_NAME = "Mont Wright"
COUNTRY = "Kanada"
REGION = "Quebec"

# Provider groups
PROVIDERS = {
    'Tavily': ['tavily:search', 'tavily:deep-research'],
    'ScrapingBee': ['scrapingbee:basic-scrape', 'scrapingbee:js-render', 'scrapingbee:ai-extract'],
    'Firecrawl': ['firecrawl:scrape', 'firecrawl:crawl', 'firecrawl:extract'],
    'BrightData': ['brightdata:web-scraper', 'brightdata:browser-api', 'brightdata:serp'],
    'Exa': ['exa:neural-search', 'exa:research', 'exa:research-pro'],
    'OpenRouter (Sample)': [
        'openrouter:deepseek-free',
        'openrouter:kimi-k2',
        'openrouter:claude-3.5-haiku'
    ]
}

def test_model(model_id: str) -> Dict[str, Any]:
    """Test a single model"""
    try:
        print(f"  Testing {model_id}...", end=" ", flush=True)
        
        start_time = time.time()
        response = requests.post(
            API_URL,
            json={
                'model': model_id,
                'mine_name': MINE_NAME,
                'country': COUNTRY,
                'region': REGION
            },
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"❌ ERROR: {result['error'][:50]}... ({elapsed:.1f}s)")
                return {'success': False, 'error': result['error']}
            else:
                fields_count = len(result.get('data', {}))
                print(f"✅ SUCCESS - {fields_count} fields ({elapsed:.1f}s)")
                return {'success': True, 'fields': fields_count, 'time': elapsed}
        else:
            print(f"❌ HTTP {response.status_code} ({elapsed:.1f}s)")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:50]}...")
        return {'success': False, 'error': str(e)}

def main():
    print("=" * 80)
    print(f"MINESEARCH COMPREHENSIVE PROVIDER TEST")
    print(f"Testing mine: {MINE_NAME} in {COUNTRY}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    overall_results = {}
    total_models = 0
    successful_models = 0
    
    for provider_name, models in PROVIDERS.items():
        print(f"\n{provider_name} Provider ({len(models)} models)")
        print("-" * 40)
        
        provider_results = {}
        for model_id in models:
            result = test_model(model_id)
            provider_results[model_id] = result
            total_models += 1
            if result['success']:
                successful_models += 1
            time.sleep(1)  # Small delay between requests
        
        overall_results[provider_name] = provider_results
        
        # Provider summary
        provider_success = sum(1 for r in provider_results.values() if r['success'])
        print(f"\n{provider_name} Summary: {provider_success}/{len(models)} successful")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    for provider_name, results in overall_results.items():
        success_count = sum(1 for r in results.values() if r['success'])
        total = len(results)
        percentage = (success_count / total * 100) if total > 0 else 0
        status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{status} {provider_name}: {success_count}/{total} ({percentage:.1f}%)")
    
    print("-" * 80)
    overall_percentage = (successful_models / total_models * 100) if total_models > 0 else 0
    status = "✅ SUCCESS" if overall_percentage >= 80 else "⚠️ PARTIAL" if overall_percentage >= 50 else "❌ FAILED"
    print(f"{status}: {successful_models}/{total_models} models working ({overall_percentage:.1f}%)")
    
    # Save results to file
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'mine': MINE_NAME,
            'country': COUNTRY,
            'overall_success_rate': overall_percentage,
            'results': overall_results
        }, f, indent=2)
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main()