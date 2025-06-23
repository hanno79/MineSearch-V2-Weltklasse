# MineSearch API-Dokumentation
Author: rahn  
Datum: 23.06.2025  
Version: 1.0

## Übersicht

Diese Dokumentation beschreibt die internen APIs und Schnittstellen des MineSearch Systems. Alle Komponenten nutzen Type Hints für bessere IDE-Unterstützung.

## Core APIs

### MineQuery
Zentrale Query-Klasse für alle Suchanfragen.

```python
@dataclass
class MineQuery:
    mine_name: str                    # Name der Mine
    region: Optional[str] = None      # Region/Provinz
    country: Optional[str] = None     # Land
    languages: List[str] = None       # Sprachen für Suche
    required_fields: List[str] = None # Gesuchte Felder
    metadata: Dict[str, Any] = None   # Zusätzliche Metadaten
```

**Beispiel:**
```python
query = MineQuery(
    mine_name="Cerro Vanguardia",
    region="Santa Cruz",
    country="Argentina",
    languages=["es", "en"],
    required_fields=["betreiber", "produktion", "koordinaten"]
)
```

### SearchResult
Standardisiertes Ergebnis-Format für alle Agenten.

```python
@dataclass
class SearchResult:
    field_name: str           # Feldname (z.B. "betreiber")
    value: str               # Gefundener Wert
    source: str              # Quelle/Agent
    confidence_score: float  # Konfidenz (0.0-1.0)
    metadata: Dict[str, Any] # Zusätzliche Infos
    source_url: Optional[str] = None
    source_date: Optional[int] = None  # Jahr
    extraction_method: Optional[str] = None
```

## Agent API

### BaseAgent (Abstract)
Alle Agenten müssen von dieser Klasse erben.

```python
class BaseAgent(ABC):
    @abstractmethod
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche aus und gibt Ergebnisse zurück"""
        pass
    
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        return True
    
    async def cleanup(self):
        """Cleanup-Ressourcen"""
        pass
```

### Agent-Implementierung Beispiel
```python
class MyCustomAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        self.name = "my_custom_agent"
        self.config = config
        self.logger = get_logger(self.name)
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        results = []
        
        # Implementiere Such-Logik
        data = await self._fetch_data(query)
        
        # Konvertiere zu SearchResult
        for item in data:
            result = SearchResult(
                field_name="betreiber",
                value=item["operator"],
                source=self.name,
                confidence_score=0.85,
                metadata={"method": "api"}
            )
            results.append(result)
        
        return results
```

## Orchestrator API

### MineSearchOrchestratorV2
Hauptklasse für Such-Koordination.

```python
class MineSearchOrchestratorV2:
    def __init__(self, config: Config, 
                 status_callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            config: Konfigurationsobjekt
            status_callback: Callback für Status-Updates
        """
    
    async def search_mine(self,
                         mine_name: str,
                         region: Optional[str] = None,
                         country: Optional[str] = None,
                         required_fields: Optional[List[str]] = None,
                         languages: Optional[List[str]] = None,
                         search_mode: str = "standard",
                         selected_agents: Optional[List[str]] = None,
                         cancellation_token: Optional[CancellationToken] = None
                         ) -> Dict[str, Any]:
        """
        Führt Mine-Suche aus.
        
        Returns:
            Dict mit aggregierten Ergebnissen
        """
```

**Verwendung:**
```python
orchestrator = MineSearchOrchestratorV2(config)
results = await orchestrator.search_mine(
    mine_name="Example Mine",
    country="Canada",
    search_mode="deep",
    selected_agents=["tavily", "claude", "perplexity"]
)
```

## Performance APIs

### SearchOptimizer
Optimiert Such-Performance mit Caching und Parallelisierung.

```python
class SearchOptimizer:
    async def optimize_agent_search(self,
                                  agents: List[BaseAgent],
                                  query: MineQuery,
                                  use_cache: bool = True,
                                  max_concurrent: int = 10
                                  ) -> List[SearchResult]:
        """
        Optimierte Agent-Suche.
        
        Args:
            agents: Liste der Agenten
            query: Such-Query
            use_cache: Cache verwenden
            max_concurrent: Max parallele Suchen
        
        Returns:
            Aggregierte Suchergebnisse
        """
```

### ResultCache
In-Memory Cache für API-Responses.

```python
class ResultCache:
    def get(self, agent_name: str, query: MineQuery) -> Optional[List[SearchResult]]:
        """Holt gecachte Ergebnisse"""
    
    def put(self, agent_name: str, query: MineQuery, results: List[SearchResult]):
        """Speichert Ergebnisse im Cache"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
```

## Database API

### OptimizedDatabase
Optimierte Datenbank-Operationen mit Async-Support.

```python
class OptimizedDatabase:
    async def bulk_insert_results(self, 
                                 results: List[SearchResultDB]) -> int:
        """Bulk-Insert für Ergebnisse"""
    
    async def get_mine_results_optimized(self,
                                       mine_name: str,
                                       fields: Optional[List[str]] = None,
                                       min_confidence: float = 0.0,
                                       limit: int = 100
                                       ) -> List[Dict[str, Any]]:
        """Optimierte Abfrage für Mine-Ergebnisse"""
    
    async def get_search_analytics(self) -> Dict[str, Any]:
        """Gibt Such-Analytiken zurück"""
```

## HTTP Client API

### OptimizedHTTPClient
HTTP Client mit Connection Pooling und Retry-Logic.

```python
class OptimizedHTTPClient:
    async def get(self, 
                  endpoint: str, 
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  use_cache: bool = True
                  ) -> Dict[str, Any]:
        """GET Request mit Caching"""
    
    async def post(self,
                   endpoint: str,
                   json_data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None
                   ) -> Dict[str, Any]:
        """POST Request"""
    
    async def post_batch(self,
                        endpoint: str,
                        batch_data: List[Dict[str, Any]],
                        batch_size: int = 10
                        ) -> List[Dict[str, Any]]:
        """Batch POST Requests"""
```

## Utility APIs

### DataAggregator
Intelligente Aggregation von Suchergebnissen.

```python
class DataAggregator:
    def aggregate_results(self, 
                         all_results: List[SearchResult],
                         confidence_threshold: float = 0.5
                         ) -> Dict[str, List[SearchResult]]:
        """
        Aggregiert Ergebnisse nach Feldern.
        
        Returns:
            Dict mit Feld als Key und sortierten Ergebnissen
        """
    
    def calculate_consensus_score(self, 
                                 results: List[SearchResult]) -> float:
        """Berechnet Konsens-Score für ein Feld"""
```

### ExtractionPatterns
Muster-basierte Datenextraktion.

```python
class ExtractionPatterns:
    def extract_field(self, 
                     text: str, 
                     field_type: str,
                     language: str = "en"
                     ) -> Optional[str]:
        """Extrahiert Feld aus Text"""
    
    def add_custom_pattern(self,
                          field_type: str,
                          pattern: str,
                          language: str,
                          confidence: float):
        """Fügt benutzerdefiniertes Muster hinzu"""
```

## Fehlerbehandlung

### Standard-Exceptions
```python
class AgentError(Exception):
    """Basis-Exception für Agent-Fehler"""

class SearchTimeoutError(AgentError):
    """Timeout bei Suche"""

class RateLimitError(AgentError):
    """Rate Limit erreicht"""

class InvalidQueryError(Exception):
    """Ungültige Such-Query"""
```

### Error Response Format
```python
{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded for agent",
        "agent": "tavily",
        "retry_after": 60
    }
}
```

## Callbacks & Events

### Status Callback
```python
def status_callback(message: str):
    """
    Wird aufgerufen bei Status-Updates.
    
    Args:
        message: Status-Nachricht
    """
    print(f"Status: {message}")
```

### Progress Tracking
```python
@dataclass
class SearchProgress:
    total_agents: int
    completed_agents: int
    total_results: int
    elapsed_time: float
    estimated_time_remaining: float
    current_phase: str
```

## Konfiguration

### Config Object
```python
class Config:
    def __init__(self, env_file: Optional[str] = None):
        """Lädt Konfiguration aus Environment"""
    
    @property
    def api_config(self) -> APIConfig:
        """API-Konfiguration"""
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        """Agent-spezifische Konfiguration"""
    
    @property
    def database_url(self) -> str:
        """Datenbank-URL"""
```

### Environment Variables
```bash
# API Keys
CLAUDE_API_KEY=sk-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Performance
MAX_CONCURRENT_AGENTS=10
CACHE_TTL_SECONDS=3600
CONNECTION_POOL_SIZE=100

# Database
DATABASE_URL=sqlite:///data/minesearch.db
```

## Beispiel-Integration

### Vollständiges Such-Beispiel
```python
import asyncio
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.config import Config

async def search_mine_example():
    # Konfiguration laden
    config = Config()
    
    # Status-Callback
    def on_status(message: str):
        print(f"[{datetime.now()}] {message}")
    
    # Orchestrator erstellen
    orchestrator = MineSearchOrchestratorV2(config, on_status)
    
    # Suche ausführen
    results = await orchestrator.search_mine(
        mine_name="Grasberg Mine",
        country="Indonesia",
        required_fields=[
            "betreiber",
            "produktion",
            "reserven",
            "koordinaten",
            "umweltauswirkungen"
        ],
        search_mode="deep",
        selected_agents=["tavily", "claude", "perplexity", "browser"]
    )
    
    # Ergebnisse verarbeiten
    for field, values in results["aggregated_data"].items():
        print(f"\n{field}:")
        for value in values[:3]:  # Top 3
            print(f"  - {value.value} (Score: {value.confidence_score:.2f})")
    
    return results

# Ausführen
if __name__ == "__main__":
    asyncio.run(search_mine_example())
```

## Rate Limiting

### Agent-spezifische Limits
```python
RATE_LIMITS = {
    "claude": {"requests_per_minute": 50},
    "openai": {"requests_per_minute": 60},
    "tavily": {"requests_per_day": 1000},
    "perplexity": {"requests_per_minute": 20}
}
```

### Rate Limiter Usage
```python
rate_limiter = RateLimiter(limits=RATE_LIMITS["claude"])

async with rate_limiter:
    response = await make_api_call()
```