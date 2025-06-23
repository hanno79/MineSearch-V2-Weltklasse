"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Web Scraping Funktionalität für BrightData Agent
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from ..enhanced_search import get_mining_search_queries, get_mining_domains


class BrightDataScraper:
    """Verwaltet Web Scraping Operationen für BrightData"""
    
    def __init__(self, api_key: str, base_url: str, session: aiohttp.ClientSession, 
                 rate_limiter, logger, timeout: aiohttp.ClientTimeout):
        self.api_key = api_key
        self.base_url = base_url
        self.session = session
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.timeout = timeout
        
    async def collect_enhanced_mining_urls(self, query, mining_queries: List[str], 
                                         mining_domains: List[str], status_callback=None) -> List[str]:
        """Sammelt erweiterte Mining-URLs über Bright Data Search Collector"""
        urls = []
        
        # Verwende erweiterte Mining-Queries
        for idx, search_query in enumerate(mining_queries):
            # Status-Update
            if status_callback:
                await status_callback(f"Bright Data: Suche {idx+1}/{len(mining_queries)}")
            try:
                # Nutze Bright Data's SERP API
                collector_params = {
                    "collector": "search_engine",
                    "query": search_query,
                    "search_engine": "google",
                    "country": self._get_country_code(query.country),
                    "num_results": 30,
                    "include_domains": mining_domains[:10],
                    "language": self._get_language_code(query.languages)
                }
                
                results = await self.run_collector(collector_params)
                
                if results:
                    for result in results.get('organic_results', []):
                        url = result.get('link')
                        if url and self._is_mining_relevant(url, result.get('title', '')):
                            urls.append(url)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Search Collection Fehler: {e}")
        
        return list(set(urls))  # Deduplizieren
    
    async def run_collector(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Führt Bright Data Collector aus"""
        await self.rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/datasets/trigger",
                headers=headers,
                json=params,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    # Warte auf Ergebnisse
                    collection_id = (await response.json()).get('collection_id')
                    if collection_id:
                        return await self._get_collection_results(collection_id)
                else:
                    error = await response.text()
                    self.logger.error(f"Collector Fehler: {error}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Collector Exception: {e}")
            return None
    
    async def execute_scraping(self, params: Dict[str, Any]) -> Optional[str]:
        """Führt Scraping mit Proxy aus"""
        await self.rate_limiter.acquire()
        
        # Bright Data Web Unlocker API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/unlocker",
                headers=headers,
                json=params,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('html', '')
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Scraping Execution Fehler: {e}")
            return None
    
    async def query_dataset(self, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fragt Bright Data Dataset ab"""
        await self.rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/datasets/query",
                headers=headers,
                json=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Dataset Query Fehler: {e}")
            return None
    
    async def _get_collection_results(self, collection_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
        """Holt Collector-Ergebnisse"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            try:
                async with self.session.get(
                    f"{self.base_url}/datasets/results/{collection_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'ready':
                            return data.get('data')
                    elif response.status == 404:
                        continue  # Noch nicht fertig
                        
            except Exception as e:
                self.logger.error(f"Results Check Fehler: {e}")
        
        return None
    
    def _get_country_code(self, country: str) -> str:
        """
        Konvertiert Ländernamen zu ISO-Code
        
        ÄNDERUNG 17.06.2025: Entfernt hardcodiertes Country-Mapping
        Dynamische Lösung: Nutze Landesname direkt oder hole Code über Agent
        """
        return country.lower()[:2] if country else "int"  # "int" für international
    
    def _get_language_code(self, languages: List[str]) -> str:
        """Gibt primären Sprachcode zurück"""
        if languages and len(languages) > 0:
            return languages[0][:2]  # Erste 2 Zeichen des ersten Sprachcodes
        return "en"  # Default Englisch
    
    def _is_mining_relevant(self, url: str, title: str) -> bool:
        """Prüft ob URL/Title mining-relevant ist"""
        # Positive Indikatoren
        positive_keywords = [
            'mining', 'mine', 'mineral', 'resources', 'extraction',
            'operator', 'environmental', 'restoration', 'production',
            'mern', 'nrcan', 'gov', 'sedar'
        ]
        
        # Negative Indikatoren
        negative_keywords = [
            'jobs', 'careers', 'recruitment', 'stock', 'trading',
            'wikipedia', 'facebook', 'twitter', 'youtube'
        ]
        
        combined = (url + ' ' + title).lower()
        
        # Prüfe negative Keywords
        if any(neg in combined for neg in negative_keywords):
            return False
        
        # Prüfe positive Keywords
        return any(pos in combined for pos in positive_keywords)