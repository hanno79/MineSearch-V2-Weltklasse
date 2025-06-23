"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Apify Actor-Definitionen und -Verwaltung
"""

from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime
import asyncio

from src.core.logger import get_logger


class ApifyActorManager:
    """Verwaltet Apify Actor Runs und Results"""
    
    def __init__(self, api_key: str, base_url: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.base_url = base_url
        self.session = session
        self.logger = get_logger("apify.actors")
        
        # Apify Actor IDs für verschiedene Scraping-Aufgaben
        self.actors = {
            'google_search': 'apify/google-search-scraper',
            'web_scraper': 'apify/web-scraper',
            'cheerio_scraper': 'apify/cheerio-scraper',
            'website_content': 'apify/website-content-crawler'
        }
    
    async def start_actor_run(self, actor_id: str, input_data: Dict[str, Any]) -> Optional[str]:
        """Startet einen Apify Actor Run"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # ÄNDERUNG 18.06.2025: Fix für Apify API Endpoint
        # Actor IDs mit "/" müssen zu "~" konvertiert werden
        actor_id_encoded = actor_id.replace('/', '~')
        
        try:
            async with self.session.post(
                f"{self.base_url}/acts/{actor_id_encoded}/runs",
                headers=headers,
                json=input_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return data.get('data', {}).get('id')
                else:
                    error_text = await response.text()
                    self.logger.error(f"Actor Start Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Actor Start Fehler: {e}")
            return None
    
    async def get_actor_results(self, run_id: str, max_wait: int = 60) -> Optional[List[Dict[str, Any]]]:
        """Wartet auf Actor-Ergebnisse"""
        # Warte auf Completion
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            try:
                # Check Run Status
                async with self.session.get(
                    f"{self.base_url}/actor-runs/{run_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('data', {}).get('status')
                        
                        if status == 'SUCCEEDED':
                            # Hole Ergebnisse
                            dataset_id = data.get('data', {}).get('defaultDatasetId')
                            if dataset_id:
                                return await self._get_dataset_items(dataset_id)
                        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                            self.logger.error(f"Actor Run fehlgeschlagen: {status}")
                            return None
                            
            except Exception as e:
                self.logger.error(f"Status Check Fehler: {e}")
                
        return None
    
    async def _get_dataset_items(self, dataset_id: str) -> Optional[List[Dict[str, Any]]]:
        """Holt Items aus Apify Dataset"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with self.session.get(
                f"{self.base_url}/datasets/{dataset_id}/items",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Dataset Abruf Fehler: {e}")
            return None
    
    def get_google_search_input(self, query: str) -> Dict[str, Any]:
        """Erstellt Input für Google Search Actor"""
        return {
            "queries": query,  # ÄNDERUNG 20.06.2025: API erwartet String, nicht Array
            "maxPagesPerQuery": 1,
            "resultsPerPage": 20,  # Mehr Ergebnisse für Mining-Suche
            "languageCode": "en",
            "includeUnfilteredResults": False
        }
    
    def get_web_scraper_input(self, url: str, mine_name: str = "") -> Dict[str, Any]:
        """Erstellt Input für Web Scraper Actor"""
        return {
            "startUrls": [{"url": url}],
            "pseudoUrls": [{"purl": f"{url.split('/')[0]}//{url.split('/')[2]}/[.*]"}],
            "maxPagesPerCrawl": 5,
            "pageFunction": f"""
            async function pageFunction(context) {{
                const $ = context.jQuery;
                const mineName = "{mine_name}";
                
                // Suche nach Minennamen
                const found = $('body').text().toLowerCase().includes(mineName.toLowerCase());
                if (!found) return null;
                
                // Extrahiere relevante Daten
                const data = {{
                    mineName: mineName,
                    pageTitle: $('title').text(),
                    content: {{}}
                }};
                
                // Suche nach Tabellen mit Mining-Daten
                $('table').each((i, table) => {{
                    const headers = [];
                    const values = [];
                    
                    $(table).find('th').each((j, th) => {{
                        headers.push($(th).text().trim());
                    }});
                    
                    $(table).find('tr').first().find('td').each((j, td) => {{
                        values.push($(td).text().trim());
                    }});
                    
                    headers.forEach((header, idx) => {{
                        if (values[idx]) {{
                            data.content[header] = values[idx];
                        }}
                    }});
                }});
                
                return data;
            }}
            """
        }
    
    def get_cheerio_scraper_input(self, url: str) -> Dict[str, Any]:
        """Erstellt Input für Cheerio Scraper Actor"""
        return {
            "startUrls": [{"url": url}],
            "maxPagesPerCrawl": 1,
            "useChrome": False,
            "waitForLoadEvent": True,
            "pageFunction": """
            async function pageFunction(context) {
                const $ = context.jQuery;
                const data = {
                    title: $('title').text(),
                    text: $('body').text().substring(0, 5000),
                    tables: []
                };
                
                // Extrahiere Tabellen
                $('table').each((i, table) => {
                    if (i < 3) {  // Max 3 Tabellen
                        const tableData = [];
                        $(table).find('tr').each((j, row) => {
                            const rowData = [];
                            $(row).find('td, th').each((k, cell) => {
                                rowData.push($(cell).text().trim());
                            });
                            tableData.push(rowData);
                        });
                        data.tables.push(tableData);
                    }
                });
                
                return data;
            }
            """
        }