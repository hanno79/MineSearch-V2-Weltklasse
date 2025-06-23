"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Bright Data Scraping Funktionalität
"""

from typing import Dict, Any, Optional
import asyncio
import logging


class BrightDataScraper:
    """Handhabt Bright Data Scraping Operationen"""
    
    def __init__(self, http_client, logger: logging.Logger):
        self.http_client = http_client
        self.logger = logger
        self.base_url = "https://api.brightdata.com"
    
    async def run_collector(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Führt einen Bright Data Collector aus"""
        try:
            # API Endpoint für Collector
            endpoint = f"{self.base_url}/collectors/run"
            
            # Request Body
            body = {
                "collector_type": params.get("collector", "search_engine"),
                "parameters": params
            }
            
            response = await self.http_client.post(endpoint, json=body)
            
            if isinstance(response, dict):
                # Warte auf Collector-Ergebnis
                job_id = response.get('job_id')
                if job_id:
                    return await self._wait_for_collector_result(job_id)
                else:
                    return response
                    
        except Exception as e:
            self.logger.error(f"Collector-Fehler: {e}")
            return None
    
    async def scrape_url(self, 
                        url: str,
                        proxy_type: str = "datacenter",
                        country: str = "us",
                        render_js: bool = False) -> Optional[str]:
        """Scraped eine einzelne URL"""
        try:
            endpoint = f"{self.base_url}/scraper/fetch"
            
            body = {
                "url": url,
                "proxy": {
                    "type": proxy_type,
                    "country": country
                },
                "browser": {
                    "render_js": render_js,
                    "wait_for": "networkidle" if render_js else None,
                    "timeout": 30000
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; MineSearchBot/1.0)",
                    "Accept": "text/html,application/xhtml+xml"
                }
            }
            
            response = await self.http_client.post(endpoint, json=body)
            
            if isinstance(response, dict):
                return response.get('html', response.get('content'))
            elif isinstance(response, str):
                return response
                
        except Exception as e:
            self.logger.error(f"Scraping-Fehler für {url}: {e}")
            return None
    
    async def _wait_for_collector_result(self, job_id: str, max_wait: int = 60) -> Optional[Dict]:
        """Wartet auf Collector-Ergebnis"""
        endpoint = f"{self.base_url}/collectors/status/{job_id}"
        
        for _ in range(max_wait // 2):
            try:
                response = await self.http_client.get(endpoint)
                
                if isinstance(response, dict):
                    status = response.get('status')
                    
                    if status == 'completed':
                        return response.get('results')
                    elif status == 'failed':
                        self.logger.error(f"Collector Job {job_id} fehlgeschlagen")
                        return None
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Status-Abfrage Fehler: {e}")
                
        self.logger.warning(f"Timeout für Collector Job {job_id}")
        return None
    
    async def batch_scrape(self, 
                          urls: list[str],
                          config: Dict[str, Any]) -> list[Optional[str]]:
        """Scraped mehrere URLs im Batch"""
        try:
            endpoint = f"{self.base_url}/scraper/batch"
            
            body = {
                "urls": urls,
                "config": config
            }
            
            response = await self.http_client.post(endpoint, json=body)
            
            if isinstance(response, dict):
                batch_id = response.get('batch_id')
                if batch_id:
                    return await self._wait_for_batch_result(batch_id)
                    
        except Exception as e:
            self.logger.error(f"Batch-Scraping Fehler: {e}")
            
        return [None] * len(urls)
    
    async def _wait_for_batch_result(self, batch_id: str, max_wait: int = 120) -> list[Optional[str]]:
        """Wartet auf Batch-Ergebnis"""
        endpoint = f"{self.base_url}/scraper/batch/{batch_id}"
        
        for _ in range(max_wait // 3):
            try:
                response = await self.http_client.get(endpoint)
                
                if isinstance(response, dict):
                    status = response.get('status')
                    
                    if status == 'completed':
                        results = response.get('results', [])
                        return [r.get('content') for r in results]
                    elif status == 'failed':
                        self.logger.error(f"Batch {batch_id} fehlgeschlagen")
                        return []
                    
                await asyncio.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Batch-Status Fehler: {e}")
                
        self.logger.warning(f"Timeout für Batch {batch_id}")
        return []