"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Direkter Test der ScrapingBee API
"""

import asyncio
import aiohttp
from config import Config

async def test_scrapingbee():
    """Teste ScrapingBee API direkt"""
    
    api_key = Config.SCRAPINGBEE_API_KEY
    base_url = 'https://app.scrapingbee.com/api/v1'
    
    # Test 1: Einfacher Request
    print("=== SCRAPINGBEE API TEST ===")
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"Base URL: {base_url}")
    
    # Test mit einer einfachen URL
    test_url = "https://www.mining.com"
    
    params = {
        'api_key': api_key,
        'url': test_url
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"\nTeste: {test_url}")
            async with session.get(base_url, params=params) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Erfolg! Content-Länge: {len(content)} Zeichen")
                    print(f"Erste 200 Zeichen: {content[:200]}...")
                else:
                    error = await response.text()
                    print(f"❌ Fehler: {error}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Test 2: Mit mehr Parametern
    print("\n\nTest 2: Mit erweiterten Parametern")
    params2 = {
        'api_key': api_key,
        'url': test_url,
        'render_js': 'false',
        'premium_proxy': 'false'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(base_url, params=params2) as response:
                print(f"Status: {response.status}")
                if response.status != 200:
                    error = await response.text()
                    print(f"Fehler: {error}")
                else:
                    print("✅ Erfolg mit erweiterten Parametern!")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapingbee())