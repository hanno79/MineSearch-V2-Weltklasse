"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: ScrapingBee API Client Modul
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode


class ScrapingBeeAPIClient:
    """Handles ScrapingBee API Kommunikation"""
    
    def __init__(self, api_key: str, rate_limiter, logger):
        self.api_key = api_key
        self.base_url = "https://app.scrapingbee.com/api/v1"
        self._rate_limiter = rate_limiter
        self.logger = logger
        self._session = None
    
    async def initialize(self):
        """Initialisiert den API Client"""
        self._session = aiohttp.ClientSession()
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein ScrapingBee API-Key konfiguriert")
            return False
            
        try:
            # Test-Scraping
            params = {
                'api_key': self.api_key,
                'url': 'https://httpbin.org/anything'
            }
            
            async with self._session.get(
                self.base_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def scrape_url(self, url: str, config: Dict[str, Any]) -> Optional[str]:
        """Scraped eine URL mit ScrapingBee"""
        await self._rate_limiter.acquire()
        
        params = {
            'api_key': self.api_key,
            'url': url,
            'render_js': str(config.get('render_js', True)).lower(),
            'premium_proxy': 'true',  # Für bessere Erfolgsrate
            'country_code': 'ca'  # Kanadische IP für lokale Seiten
        }
        
        # Zusätzliche Parameter
        if config.get('wait'):
            params['wait'] = config['wait']
        
        if config.get('javascript_snippet'):
            params['js_scenario'] = config['javascript_snippet']
        
        if config.get('block_ads'):
            params['block_ads'] = 'true'
            
        if config.get('stealth_proxy'):
            params['stealth_proxy'] = 'true'
        
        try:
            async with self._session.get(
                self.base_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    error_text = await response.text()
                    self.logger.error(f"ScrapingBee Fehler {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout beim Scraping von {url}")
            return None
        except Exception as e:
            self.logger.error(f"Scraping Fehler für {url}: {e}")
            return None
    
    @staticmethod
    def quote(text: str) -> str:
        """URL-encode Text"""
        return quote(text)
    
    @staticmethod
    def urlencode(params: Dict[str, str]) -> str:
        """URL-encode Parameter"""
        return urlencode(params)
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if self._session:
            await self._session.close()