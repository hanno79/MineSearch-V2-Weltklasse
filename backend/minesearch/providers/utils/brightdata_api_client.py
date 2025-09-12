"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: API Client für Brightdata Web-Scraping
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class BrightdataAPIClient:
    """API Client für Brightdata-Anfragen"""

    def __init__(self, customer_id: str, password: str = ''):
        """__init__ - TODO: Dokumentation hinzufügen"""
        self.customer_id = customer_id
        self.password = password
        self.base_url = 'https://api.brightdata.com'

    def _get_auth(self):
        """Erstellt Auth für Requests"""
        if self.password:
            return aiohttp.BasicAuth(self.customer_id, self.password)
        return None

    async def create_scraping_job(self, session: aiohttp.ClientSession,
                                 zone: str, urls: List[str],
                                 options: Dict[str, Any] = None) -> Optional[str]:
        """Erstellt einen Scraping-Job"""

        payload = {
            'zone': zone,
            'urls': urls,
            'format': 'json'
        }

        if options:
            payload.update(options)

        try:
            url = f"{self.base_url}/dca/trigger_immediate"

            async with session.post(
                url,
                json=payload,
                auth=self._get_auth(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data_dict = await response.json()
                    return data.get('response_id')
                else:
                    error = await response.text()
                    logger.error(f"[Brightdata] Job-Erstellung fehlgeschlagen: {error}")
                    return None

        except Exception as e:
            logger.error(f"[Brightdata] Fehler bei Job-Erstellung: {e}")
            return None

    async def get_job_result(self, session: aiohttp.ClientSession,
                           response_id: str) -> Optional[Dict[str, Any]]:
        """Holt das Ergebnis eines Scraping-Jobs"""

        try:
            url = f"{self.base_url}/dca/get_result"
            params = {'response_id': response_id}

            async with session.get(
                url,
                params=params,
                auth=self._get_auth(),
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"[Brightdata] Ergebnis-Abruf fehlgeschlagen: {error}")
                    return None

        except Exception as e:
            logger.error(f"[Brightdata] Fehler beim Ergebnis-Abruf: {e}")
            return None

    async def wait_for_job(self, session: aiohttp.ClientSession,
                          response_id: str, max_wait: int = 120) -> Optional[Dict[str, Any]]:
        """Wartet auf Abschluss eines Jobs"""

        check_interval = 5
        max_attempts = max_wait // check_interval

        for attempt in range(max_attempts):
            result = await self.get_job_result(session, response_id)

            if result and result.get('status') == 'ready':
                return result
            elif result and result.get('status') == 'error':
                logger.error(f"[Brightdata] Job fehlgeschlagen: {result.get('error')}")
                return None

            await asyncio.sleep(check_interval)

        logger.warning(f"[Brightdata] Job-Timeout nach {max_wait}s")
        return None

    async def scrape_with_serp(self, session: aiohttp.ClientSession,
                              query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Führt SERP (Search Engine Results Page) Scraping durch"""

        try:
            # SERP API endpoint
            url = f"{self.base_url}/serp/get"

            params = {
                'customer': self.customer_id,
                'zone': 'serp',
                'query': query,
                'num': num_results,
                'format': 'json'
            }

            async with session.get(
                url,
                params=params,
                auth=self._get_auth(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data_dict = await response.json()
                    return data.get("organic_results", [])
                else:
                    error = await response.text()
                    logger.error(f"[Brightdata] SERP-Scraping fehlgeschlagen: {error}")
                    return []

        except Exception as e:
            logger.error(f"[Brightdata] SERP-Fehler: {e}")
            return []

    async def scrape_page(self, session: aiohttp.ClientSession,
                         url: str, zone: str = 'unblocker') -> Optional[Dict[str, Any]]:
        """Scraped eine einzelne Seite"""

        try:
            api_url = f"{self.base_url}/proxy"

            headers = {
                'X-Target-URL': url,
                'X-Zone': zone
            }

            async with session.get(
                api_url,
                headers=headers,
                auth=self._get_auth(),
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    return {
                        'url': url,
                        'html': html,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    error = await response.text()
                    logger.error(f"[Brightdata] Seiten-Scraping fehlgeschlagen: {error}")
                    return None

        except Exception as e:
            logger.error(f"[Brightdata] Scraping-Fehler für {url}: {e}")
            return None

    async def batch_scrape(self, urls: List[str], zone: str = 'unblocker',
                          max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Scraped mehrere URLs parallel"""

        results = []

        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_limit(url: str):
                async with semaphore:
                    return await self.scrape_page(session, url, zone)

            tasks = [scrape_with_limit(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter gültige Ergebnisse
            valid_results = []
            for result in results:
                if isinstance(result, dict) and result:
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"[Brightdata] Batch-Fehler: {str(result)}")

            return valid_results
