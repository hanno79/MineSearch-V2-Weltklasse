# MineSearch v2 - Phase 2 Features Dokumentation

**Author:** rahn  
**Datum:** 01.07.2025  
**Version:** 1.0

## Übersicht

Dieses Dokument beschreibt die geplanten Features für Phase 2 der MineSearch v2 Entwicklung. Der Fokus liegt auf Datenpersistenz, Performance-Optimierung und verbesserter Skalierbarkeit.

## 1. Datenbankintegration mit SQLAlchemy

### 1.1 Architektur

```
minesearch_v2/
├── backend/
│   ├── models.py          # SQLAlchemy Models
│   ├── database.py        # Datenbankverbindung
│   ├── migrations/        # Alembic Migrations
│   └── repositories/      # Data Access Layer
```

### 1.2 Datenmodelle

#### Mine Model
```python
class Mine(Base):
    __tablename__ = 'mines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(100))
    coordinates = Column(String(50))
    commodities = Column(JSON)
    owner = Column(String(255))
    operator = Column(String(255))
    status = Column(String(50))
    annual_production = Column(JSON)
    reserves = Column(JSON)
    resources = Column(JSON)
    mine_life = Column(String(50))
    employees = Column(Integer)
    website = Column(String(255))
    contact_email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    description = Column(Text)
    founded_year = Column(Integer)
    mine_type = Column(String(100))
    processing_capacity = Column(String(100))
    environmental_standards = Column(JSON)
    certifications = Column(JSON)
    union_info = Column(String(255))
    investment_volume = Column(String(100))
    infrastructure = Column(Text)
    water_source = Column(String(255))
    energy_source = Column(String(255))
    environmental_permits = Column(JSON)
    security_deposit = Column(String(100))
    restoration_costs = Column(String(100))
    notes = Column(Text)
    
    # Metadaten
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_quality_score = Column(Integer)
    last_verified = Column(DateTime)
    
    # Relationships
    search_results = relationship("SearchResult", back_populates="mine")
    sources = relationship("Source", back_populates="mine")
```

#### SearchResult Model
```python
class SearchResult(Base):
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    search_query = Column(JSON)
    search_type = Column(String(50))  # standard, enhanced, smart
    model_used = Column(String(50))
    response_data = Column(JSON)
    data_quality = Column(Integer)
    search_duration = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mine = relationship("Mine", back_populates="search_results")
```

#### Source Model
```python
class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    url = Column(String(500), nullable=False)
    title = Column(String(255))
    domain = Column(String(100), index=True)
    description = Column(Text)
    publication_date = Column(Date)
    source_type = Column(String(50))  # pdf, website, database
    priority_tier = Column(Integer)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mine = relationship("Mine", back_populates="sources")
```

#### BatchSession Model
```python
class BatchSession(Base):
    __tablename__ = 'batch_sessions'
    
    id = Column(String(36), primary_key=True)  # UUID
    total_mines = Column(Integer)
    processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(20))  # pending, processing, completed, failed
    input_data = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    batch_results = relationship("BatchResult", back_populates="session")
```

### 1.3 Repository Pattern

```python
# repositories/mine_repository.py
class MineRepository:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_by_name_and_country(self, name: str, country: str) -> Mine:
        return self.db.query(Mine).filter(
            Mine.name == name,
            Mine.country == country
        ).first()
    
    def create_or_update(self, mine_data: dict) -> Mine:
        existing = self.get_by_name_and_country(
            mine_data['Minenname'], 
            mine_data['Land']
        )
        
        if existing:
            # Update existing
            for key, value in mine_data.items():
                setattr(existing, self._map_field(key), value)
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            existing = Mine(**self._map_data(mine_data))
            self.db.add(existing)
        
        self.db.commit()
        return existing
```

### 1.4 Migrations-Strategie

- Verwendung von Alembic für Datenbank-Migrations
- Automatische Migration bei App-Start in Development
- Manuelle Migration in Production
- Rollback-Strategie für fehlerhafte Migrations

### 1.5 Backup-Konzept

- Tägliche automatische Backups
- Point-in-Time Recovery
- Geografisch verteilte Backup-Speicherung
- Regelmäßige Restore-Tests

## 2. Perplexity Client Optimierung

### 2.1 Connection Pooling

```python
# perplexity_client.py
class PerplexityClient:
    def __init__(self, api_key: str, max_connections: int = 10):
        self.api_key = api_key
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=max_connections,
                limit_per_host=5,
                ttl_dns_cache=300
            ),
            timeout=aiohttp.ClientTimeout(total=120)
        )
        self._semaphore = asyncio.Semaphore(max_connections)
    
    async def search(self, prompt: str, model: str = "sonar") -> dict:
        async with self._semaphore:
            return await self._make_request(prompt, model)
```

### 2.2 Erweiterte Retry-Logic

```python
class RetryStrategy:
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.exponential_base ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, self.max_delay)

@retry_with_strategy(RetryStrategy())
async def make_api_call(self, prompt: str) -> dict:
    # API Call Implementation
```

### 2.3 Rate Limiting Design

```python
class RateLimiter:
    def __init__(self, 
                 requests_per_minute: int = 50,
                 requests_per_hour: int = 1000,
                 requests_per_day: int = 10000):
        self.minute_limiter = TokenBucket(requests_per_minute, 60)
        self.hour_limiter = TokenBucket(requests_per_hour, 3600)
        self.day_limiter = TokenBucket(requests_per_day, 86400)
    
    async def acquire(self):
        await self.minute_limiter.acquire()
        await self.hour_limiter.acquire()
        await self.day_limiter.acquire()
```

### 2.4 Request Batching

- Sammeln von Anfragen über kurze Zeitfenster (100ms)
- Batch-Verarbeitung für ähnliche Queries
- Prioritäts-Queue für dringende Anfragen

## 3. Caching-Layer

### 3.1 Cache-Architektur

```python
# cache/cache_manager.py
class CacheManager:
    def __init__(self, backend: str = "redis"):
        if backend == "redis":
            self.cache = RedisCache()
        else:
            self.cache = InMemoryCache()
    
    def generate_key(self, mine_name: str, country: str, options: dict) -> str:
        """Generiere eindeutigen Cache-Key"""
        key_parts = [
            mine_name.lower().replace(" ", "_"),
            country.lower(),
            hashlib.md5(json.dumps(options, sort_keys=True).encode()).hexdigest()[:8]
        ]
        return ":".join(key_parts)
    
    async def get_or_fetch(self, key: str, fetch_func, ttl: int = 3600):
        # Try cache first
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        
        # Fetch if not cached
        result = await fetch_func()
        
        # Cache result
        await self.cache.set(key, json.dumps(result), ttl)
        
        return result
```

### 3.2 Cache-Strategien

#### TTL-Konfiguration
- Hochwertige Daten (Score > 80): 7 Tage
- Mittlere Daten (Score 50-80): 3 Tage  
- Niedrige Daten (Score < 50): 1 Tag
- Fehlerhafte Responses: 1 Stunde

#### Cache-Invalidierung
```python
class CacheInvalidator:
    def __init__(self, cache: CacheManager):
        self.cache = cache
    
    async def invalidate_mine(self, mine_name: str, country: str):
        """Invalidiere alle Cache-Einträge für eine Mine"""
        pattern = f"{mine_name.lower()}:{country.lower()}:*"
        await self.cache.delete_pattern(pattern)
    
    async def invalidate_old_entries(self, days: int = 30):
        """Invalidiere Einträge älter als X Tage"""
        cutoff = datetime.now() - timedelta(days=days)
        await self.cache.delete_older_than(cutoff)
```

### 3.3 Cache-Warming

```python
class CacheWarmer:
    def __init__(self, mine_repo: MineRepository, search_service: MineSearchService):
        self.mine_repo = mine_repo
        self.search_service = search_service
    
    async def warm_popular_mines(self, limit: int = 100):
        """Wärme Cache für häufig gesuchte Minen auf"""
        popular_mines = await self.mine_repo.get_most_searched(limit)
        
        for mine in popular_mines:
            await self.search_service.search_mine(
                mine.name, 
                mine.country,
                cache_only=False
            )
```

### 3.4 Performance-Metriken

```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.avg_response_time = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0
    
    def record_hit(self, response_time: float):
        self.hits += 1
        self._update_avg_response_time(response_time)
    
    def record_miss(self, response_time: float):
        self.misses += 1
        self._update_avg_response_time(response_time)
```

## 4. Implementierungs-Roadmap

### Phase 2.1 - Datenbankintegration (2 Wochen)
1. SQLAlchemy Models implementieren
2. Alembic Setup und initiale Migration
3. Repository Pattern implementieren
4. Bestehende Services anpassen
5. Unit Tests für Datenbankzugriff

### Phase 2.2 - Perplexity Client (1 Woche)
1. Connection Pooling implementieren
2. Retry-Logic mit Backoff
3. Rate Limiting einbauen
4. Performance Tests

### Phase 2.3 - Caching-Layer (1 Woche)
1. Redis/In-Memory Cache Setup
2. Cache-Manager implementieren
3. TTL-Strategien umsetzen
4. Cache-Warming implementieren
5. Monitoring und Metriken

### Phase 2.4 - Integration & Testing (1 Woche)
1. Alle Komponenten integrieren
2. End-to-End Tests
3. Performance-Optimierung
4. Dokumentation aktualisieren

## 5. Erwartete Verbesserungen

- **Performance**: 30-50% schnellere Antwortzeiten durch Caching
- **Skalierbarkeit**: Unterstützung für 10x mehr gleichzeitige Nutzer
- **Zuverlässigkeit**: 99.9% Uptime durch robuste Fehlerbehandlung
- **Datenqualität**: Historische Daten für Trend-Analysen
- **Kosten**: Reduzierte API-Kosten durch intelligentes Caching

## 6. Monitoring & KPIs

### Key Performance Indicators
- Cache Hit Rate: Ziel > 60%
- Durchschnittliche Antwortzeit: < 2 Sekunden
- API Fehlerrate: < 0.1%
- Datenbankabfrage-Zeit: < 100ms
- Concurrent Users: > 100

### Monitoring-Tools
- Prometheus für Metriken
- Grafana für Dashboards
- Sentry für Error Tracking
- ELK Stack für Logs

---

**Nächste Schritte:** Nach Genehmigung dieses Konzepts beginnt die Implementierung mit der Datenbankintegration.