"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Scraper-Implementierungen für Brightdata
"""

import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BrightdataScraper:
    """Scraper-Implementierungen für verschiedene Brightdata-APIs"""
    
    def __init__(self, customer_id: str, password: str):
        self.customer_id = customer_id
        self.password = password
    
    async def scrape_with_web_unlocker(self, session: aiohttp.ClientSession,
                                      url: str, headers: Dict[str, str] = None) -> Optional[str]:
        """Scraped URL mit Web Unlocker Proxy"""
        
        # ÄNDERUNG 05.07.2025: Korrigiertes Proxy-URL Format
        # Wenn customer_id bereits das volle Format hat (mit Hash), verwende es direkt
        if len(self.customer_id) > 20 and '-' in self.customer_id:
            # Vollständige customer_id mit Hash
            proxy_url = f"http://{self.customer_id}-zone-web_unlocker:@brd.superproxy.io:22225"
        else:
            # Kurze customer_id - füge Präfix hinzu
            proxy_url = f"http://brd-customer-{self.customer_id}-zone-web_unlocker:{self.password}@brd.superproxy.io:22225"
        
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            async with session.get(
                url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers=default_headers
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"[Brightdata] HTTP {response.status} für {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"[Brightdata] Fehler beim Scrapen von {url}: {e}")
            return None
    
    async def scrape_with_browser_api(self, session: aiohttp.ClientSession,
                                     url: str, wait_selector: str = 'body',
                                     execute_js: str = None) -> Optional[str]:
        """Scraped URL mit Browser API für JavaScript-Rendering"""
        
        proxy_url = f"http://brd-customer-{self.customer_id}-zone-browser_api:{self.password}@brd.superproxy.io:22225"
        
        headers = {
            'X-BRD-Browser-Render': 'true',
            'X-BRD-Wait-For-Selector': wait_selector,
            'X-BRD-Screenshot': 'false',
            'X-BRD-JavaScript': 'true'
        }
        
        if execute_js:
            headers['X-BRD-Execute-JS'] = execute_js
        
        try:
            async with session.get(
                url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=60),
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"[Brightdata] Browser API HTTP {response.status} für {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"[Brightdata] Browser API Fehler für {url}: {e}")
            return None
    
    async def scrape_google_search(self, session: aiohttp.ClientSession,
                                  query: str, num_results: int = 10) -> Optional[str]:
        """Scraped Google Suchergebnisse"""
        
        from urllib.parse import quote_plus
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
        
        proxy_url = f"http://brd-customer-{self.customer_id}-zone-serp:{self.password}@brd.superproxy.io:22225"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
        }
        
        try:
            async with session.get(
                search_url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"[Brightdata] Google SERP HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"[Brightdata] Google SERP Fehler: {e}")
            return None
    
    async def batch_scrape_urls(self, urls: List[str], max_concurrent: int = 3,
                               use_browser_api: bool = False) -> List[Dict[str, Any]]:
        """Scraped mehrere URLs parallel"""
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(urls), max_concurrent):
                batch = urls[i:i + max_concurrent]
                batch_tasks = []
                
                for url in batch:
                    if use_browser_api:
                        task = self.scrape_with_browser_api(session, url)
                    else:
                        task = self.scrape_with_web_unlocker(session, url)
                    batch_tasks.append(task)
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for url, result in zip(batch, batch_results):
                    if isinstance(result, str) and result:
                        results.append({
                            'url': url,
                            'html': result,
                            'success': True
                        })
                    else:
                        results.append({
                            'url': url,
                            'html': None,
                            'success': False,
                            'error': str(result) if isinstance(result, Exception) else 'No content'
                        })
        
        return results


import asyncio  # Import hier am Ende für batch_scrape_urls