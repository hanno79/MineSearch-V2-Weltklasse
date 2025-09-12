"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: API Client für Firecrawl-Interaktionen
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FirecrawlAPIClient:
    """API Client für Firecrawl-Anfragen"""

    def __init__(self, api_key: str, base_url: str):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    async def scrape_single(self, session: aiohttp.ClientSession,
                          url: str, options: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne Seite"""

        payload = {'url': url}
        if options:
            payload.update(options)

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with session.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=payload,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    data_dict = await response.json()
                    return {
                        'url': url,
                        'markdown': data.get("markdown", ''),
                        'title': data.get("metadata", {}).get('title', ''),
                        'tokens': len(data.get("markdown", '').split())
                    }
                else:
                    error = await response.text()
                    logger.error(f"[Firecrawl] HTTP {response.status} für {url}: {error}")
                    return None

        except Exception as e:
            logger.error(f"[Firecrawl] Fehler beim Scrapen von {url}: {e}")
            return None

    async def start_crawl(self, session: aiohttp.ClientSession,
                         base_url: str, options: Dict[str, Any] = None) -> Optional[str]:
        """Startet einen Crawl-Job"""

        payload = {
            'url': base_url,
            'limit': options.get("limit", 10) if options else 10,
            'maxDepth': options.get("maxDepth", 2) if options else 2
        }

        if options and 'includePaths' in options:
            payload['includePaths'] = options['includePaths']

        try:
            timeout = aiohttp.ClientTimeout(total=300)
            async with session.post(
                f"{self.base_url}/crawl",
                headers=self.headers,
                json=payload,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    job_data = await response.json()
                    return job_data.get('id')
                else:
                    error = await response.text()
                    logger.error(f"[Firecrawl] Crawl Start fehlgeschlagen: {error}")
                    return None

        except Exception as e:
            logger.error(f"[Firecrawl] Fehler beim Crawl-Start: {e}")
            return None

    async def get_crawl_status(self, session: aiohttp.ClientSession,
                              job_id: str) -> Optional[Dict[str, Any]]:
        """Holt den Status eines Crawl-Jobs"""

        try:
            async with session.get(
                f"{self.base_url}/crawl/{job_id}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"[Firecrawl] Status-Check fehlgeschlagen")
                    return None

        except Exception as e:
            logger.error(f"[Firecrawl] Fehler beim Status-Check: {e}")
            return None

    async def wait_for_crawl_completion(self, session: aiohttp.ClientSession,
                                      job_id: str, max_wait_time: int = 300) -> List[Dict[str, Any]]:
        """Wartet auf Abschluss eines Crawl-Jobs"""

        max_attempts = max_wait_time // 10  # Check alle 10 Sekunden

        for attempt in range(max_attempts):
            data_dict = await self.get_crawl_status(session, job_id)

            if not data:
                return []

            status = data.get('status')

            if status == 'completed':
                return data.get("data", [])
            elif status == 'failed':
                logger.error(f"[Firecrawl] Crawl-Job fehlgeschlagen")
                return []

            # Warte 10 Sekunden vor nächstem Versuch
            await asyncio.sleep(10)

        logger.warning("[Firecrawl] Crawl-Job Timeout")
        return []

    async def batch_scrape(self, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """Scraped mehrere URLs parallel mit Begrenzung"""

        results = []

        async with aiohttp.ClientSession() as session:
            # Erstelle Semaphore für Concurrent-Limit
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_limit(url: str):
                async with semaphore:
                    return await self.scrape_single(session, url)

            # Führe alle Scrapes parallel aus
            tasks = [scrape_with_limit(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter None und Exceptions
            valid_results = []
            for result in results:
                if isinstance(result, dict) and result:
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"[Firecrawl] Batch-Scrape Fehler: {str(result)}")

            return valid_results
