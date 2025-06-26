"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: API Client für Exa Search
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger
from .utils import normalize_domains_for_exa

class ExaAPIClient:
    """API Client für Exa Search Calls"""
    
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
        self.base_url = "https://api.exa.ai"
        self.rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 Anfragen pro Minute
        self.logger = get_logger(__name__)
        self.timeout = aiohttp.ClientTimeout(total=120)
        # ÄNDERUNG 24.06.2025: Premium Exa Research Model
        self.model = "exa-research-pro"
        
    async def search(self, query_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Führt eine Suche über Exa API durch"""
        await self.rate_limiter.acquire()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # ÄNDERUNG 24.06.2025: Model-Parameter hinzufügen für exa-research-pro
        if "model" not in query_config:
            query_config["model"] = self.model
            query_config["enhanced_search"] = True
        
        # ÄNDERUNG 24.06.2025: Bereinige Domains auf Basis-Domains mit neuer Utility
        if "include_domains" in query_config:
            query_config["include_domains"] = normalize_domains_for_exa(
                query_config["include_domains"], 
                max_domains=20
            )
        
        try:
            async with self.session.post(
                f"{self.base_url}/search",
                headers=headers,
                json=query_config,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limit erreicht
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit erreicht. Warte {retry_after} Sekunden.")
                    await asyncio.sleep(retry_after)
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Exa API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("Exa API Timeout")
            return None
        except Exception as e:
            self.logger.error(f"Exa API Fehler: {e}")
            return None
    
    async def find_similar(self, url: str, num_results: int = 10) -> Optional[Dict[str, Any]]:
        """Findet ähnliche Seiten zu einer URL"""
        await self.rate_limiter.acquire()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "num_results": num_results,
            "use_autoprompt": True
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/findSimilar",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.logger.error(f"Exa findSimilar Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Exa findSimilar Fehler: {e}")
            return None
    
    async def get_contents(self, ids: List[str]) -> Optional[Dict[str, Any]]:
        """Holt Inhalte für gegebene IDs"""
        await self.rate_limiter.acquire()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "ids": ids,
            "text": True,
            "highlights": True
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/contents",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.logger.error(f"Exa contents Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Exa contents Fehler: {e}")
            return None
    
