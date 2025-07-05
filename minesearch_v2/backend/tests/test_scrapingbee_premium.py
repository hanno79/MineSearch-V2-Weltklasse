"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Test ScrapingBee mit verschiedenen Proxy-Optionen
"""

import asyncio
import aiohttp
from config import Config

async def test_scrapingbee_proxies():
    """Teste verschiedene ScrapingBee Proxy-Optionen"""
    
    api_key = Config.SCRAPINGBEE_API_KEY
    base_url = 'https://app.scrapingbee.com/api/v1'
    
    test_urls = [
        "https://www.example.com",  # Einfache Seite
        "https://mern.gouv.qc.ca",  # Regierungsseite
        "https://www.mining.com"    # Cloudflare-geschützt
    ]
    
    proxy_configs = [
        {"name": "Standard", "params": {}},
        {"name": "Premium Proxy", "params": {"premium_proxy": "true"}},
        {"name": "Stealth Proxy", "params": {"stealth_proxy": "true"}},
        {"name": "No JS", "params": {"render_js": "false", "premium_proxy": "false"}}
    ]
    
    print("=== SCRAPINGBEE PROXY TEST ===\n")
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            print(f"\nTeste URL: {url}")
            print("-" * 50)
            
            for config in proxy_configs:
                params = {
                    'api_key': api_key,
                    'url': url,
                    **config['params']
                }
                
                try:
                    print(f"{config['name']}: ", end='', flush=True)
                    async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            content = await response.text()
                            print(f"✅ Erfolg ({len(content)} Zeichen)")
                        else:
                            error = await response.json()
                            print(f"❌ {response.status} - {error.get('reason', 'Unbekannt')}")
                except asyncio.TimeoutError:
                    print("❌ Timeout")
                except Exception as e:
                    print(f"❌ Exception: {str(e)[:50]}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_scrapingbee_proxies())