"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Beispiel für die Verwendung der Base-Module
"""

from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseAgent
from src.agents.base import BaseHTTPClient, ResultProcessor, QueryBuilder, CacheManager
from src.data.models import MineQuery, SearchResult

class ExampleAgentRefactored(BaseAgent):
    """Beispiel-Agent mit Base-Modulen refactoriert"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Base-Module initialisieren
        self.http_client = BaseHTTPClient(
            timeout=30,
            max_retries=3,
            rate_limit=1.0,  # 1 Request pro Sekunde
            headers={"User-Agent": "MineSearch/1.0"}
        )
        
        self.result_processor = ExampleResultProcessor("ExampleAgent")
        self.query_builder = QueryBuilder()
        self.cache_manager = CacheManager(
            cache_dir="cache/example_agent",
            default_ttl=3600
        )
    
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        await self.http_client.start()
        return True
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Führt eine Suche aus"""
        # Cache prüfen
        cached_results = await self.cache_manager.get("search", query.dict())
        if cached_results:
            return cached_results
        
        # Query bauen
        search_query = self.query_builder.build_search_query(query)
        search_url = self.query_builder.build_url_query(
            query,
            "https://api.example.com/search",
            additional_params={"limit": "50"}
        )
        
        # API-Anfrage
        try:
            response = await self.http_client.get(search_url)
            
            # Ergebnisse verarbeiten
            results = self.result_processor.process_results(
                response.get("results", []),
                query
            )
            
            # Relevanz berechnen
            for result in results:
                result.confidence = self.result_processor.calculate_relevance_score(
                    result, query
                )
            
            # Ergebnisse cachen
            await self.cache_manager.set("search", query.dict(), results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Suchfehler: {e}")
            return []
    
    async def close(self):
        """Schließt den Agenten"""
        await self.http_client.close()


class ExampleResultProcessor(ResultProcessor):
    """Spezialisierter Result Processor für Example API"""
    
    def _extract_result(self, raw: Dict[str, Any], query: MineQuery) -> Optional[SearchResult]:
        """Extrahiert ein SearchResult aus Example API Daten"""
        
        # Example API spezifisches Format
        title = raw.get("title", "")
        url = raw.get("link", "")
        snippet = raw.get("description", "")
        
        if not title or not url:
            return None
        
        # Basis-Konfidenz aus API
        api_score = raw.get("relevance_score", 0.5)
        
        # Zusätzliche Metadaten
        metadata = {
            "api_id": raw.get("id"),
            "published_date": raw.get("date"),
            "source_type": raw.get("type", "web")
        }
        
        return self.create_result(
            title=title,
            url=url,
            snippet=snippet,
            confidence=api_score,
            metadata=metadata
        )


# Alternative: Mit Decorator für Caching
class CachedExampleAgent(BaseAgent):
    """Beispiel mit Cache-Decorator"""
    
    def __init__(self, config):
        super().__init__(config)
        self.cache = CacheManager()
    
    @CacheManager.cached("example_search", ttl=1800)
    async def search_api(self, query: str) -> Dict:
        """Gecachte API-Anfrage"""
        # Diese Anfrage wird automatisch gecacht
        async with BaseHTTPClient() as client:
            return await client.get(f"https://api.example.com/search?q={query}")


# Verwendung:
async def main():
    from src.core.config import Config
    
    config = Config()
    agent = ExampleAgentRefactored(config)
    
    try:
        await agent.initialize()
        
        query = MineQuery(
            mine_name="Example Mine",
            location="Canada",
            mining_type="gold"
        )
        
        results = await agent.search(query)
        
        print(f"Gefunden: {len(results)} Ergebnisse")
        
        # Cache-Statistiken
        stats = await agent.cache_manager.get_stats()
        print(f"Cache: {stats}")
        
    finally:
        await agent.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())