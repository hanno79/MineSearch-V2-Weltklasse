# MineSearch Architektur-Dokumentation
Author: rahn  
Datum: 23.06.2025  
Version: 1.0

## Übersicht

MineSearch ist ein Multi-Agent Mining Research System mit modularer, asynchroner Architektur. Das System nutzt über 20 spezialisierte AI-Agenten zur parallelen Datenerfassung aus verschiedenen Quellen.

## Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│                    (src/ui/main.py)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Orchestrator V2                          │
│              (MineSearchOrchestratorV2)                     │
│  ┌─────────────┬──────────────┬────────────────────────┐   │
│  │Agent Manager│Search Executor│Performance Optimizer    │   │
│  └─────────────┴──────────────┴────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                     Agent Layer                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Claude│ │ GPT4 │ │Tavily│ │Perplex│ │ Exa  │ │Browser│   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│                    + 15 weitere Agenten                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Data Layer                                │
│  ┌────────────┐ ┌────────────┐ ┌─────────────────────┐    │
│  │ Aggregator │ │  Database  │ │ Cache Manager       │    │
│  └────────────┘ └────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Komponenten-Beschreibung

### 1. UI Layer (Streamlit)
**Pfad**: `src/ui/`
- **main.py**: Haupt-Entry-Point (140 Zeilen)
- **components/**: Modulare UI-Komponenten
  - `search_form.py`: Such-Formular
  - `results_display.py`: Ergebnis-Anzeige
  - `metrics_dashboard.py`: Performance-Metriken
  - `sidebar.py`: Navigation und Einstellungen

### 2. Core Layer
**Pfad**: `src/core/`

#### Orchestrator V2
- **orchestrator.py**: Zentrale Koordination (262 Zeilen)
- Verwaltet Agent-Lifecycle
- Koordiniert parallele Suchen
- Aggregiert Ergebnisse

#### Performance Optimizer
- **performance_optimizer.py**: Optimierungs-Module
  - `ConnectionPoolManager`: HTTP Connection Pooling
  - `ResultCache`: In-Memory Caching
  - `AsyncBatchProcessor`: Batch-Verarbeitung
  - `PerformanceMonitor`: Metriken-Erfassung

#### Search Executor
- **search_executor_optimized.py**: Optimierte Such-Ausführung
- Parallele Agent-Aufrufe
- Cancellation-Support
- Status-Callbacks

### 3. Agent Layer
**Pfad**: `src/agents/`

#### Base Components
- **base_agent.py**: Abstrakte Basis-Klasse
- **base/**: Gemeinsame Module
  - `http_client_optimized.py`: HTTP Client mit Pooling
  - `result_processor.py`: Ergebnis-Verarbeitung
  - `query_builder.py`: Query-Generierung
  - `cache_manager.py`: Agent-spezifisches Caching

#### Spezialisierte Agenten
Jeder Agent ist für spezifische Datenquellen optimiert:

1. **LLM-basierte Agenten**
   - `claude/`: Claude AI Integration
   - `gpt_agent.py`: OpenAI GPT-4
   - `openrouter/`: Multiple LLMs

2. **Such-Agenten**
   - `tavily_agent.py`: Web-Suche
   - `perplexity_agent.py`: AI-gestützte Suche
   - `exa/`: Semantische Suche

3. **Scraping-Agenten**
   - `browser_agent/`: Playwright-basiert
   - `scraper/`: BeautifulSoup
   - `firecrawl/`: Firecrawl API

4. **Spezialisierte Research**
   - `premium_mining_research/`: Deep Mining Research
   - `deepseek_research/`: Tiefgehende Analyse
   - `search_strategies_module/`: Adaptive Strategien

### 4. Data Layer
**Pfad**: `src/data/`

#### Models
- **models.py**: SQLAlchemy ORM Models
  - `Mine`: Minen-Entität
  - `SearchResultDB`: Suchergebnisse
  - `SearchSession`: Such-Sessions
  - `AgentStatistics`: Agent-Metriken

#### Aggregator
- **aggregator.py**: Intelligente Daten-Aggregation
- Konfidenz-basiertes Scoring
- Duplikat-Erkennung
- Feld-Normalisierung

#### Database
- **database_optimized.py**: Optimierte DB-Operationen
- Connection Pooling
- Bulk Operations
- Query-Optimierung

## Datenfluss

### 1. Such-Prozess
```
User Input → UI → Orchestrator → Agent Manager → Agents (parallel)
                                                    ↓
Database ← Aggregator ← Search Executor ← ← ← ← Results
    ↓
UI Update ← Status Callbacks
```

### 2. Caching-Strategie
```
Agent Request → Cache Check → Hit: Return Cached
                    ↓
                   Miss: Execute Search → Cache Result
```

### 3. Performance-Optimierung
```
Batch Request → Batch Processor → Semaphore Control → Parallel Execution
                                        ↓
                              Connection Pool → Reused Connections
```

## Async/Await Patterns

### Parallele Agent-Aufrufe
```python
async def execute_parallel_search(agents, query):
    tasks = [agent.search(query) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return aggregate_results(results)
```

### Connection Pooling
```python
async with connection_pool.get_session() as session:
    response = await session.get(url)
    return await response.json()
```

## Skalierbarkeit

### Horizontale Skalierung
- Agent-Pool dynamisch erweiterbar
- Neue Agenten ohne Core-Änderungen
- Plugin-artiges Agent-System

### Vertikale Skalierung
- Connection Pool: bis zu 100 Verbindungen
- Parallel Searches: konfigurierbar (Standard: 10)
- Batch Processing für Bulk-Operations

## Fehlerbehandlung

### Retry-Strategien
- Exponential Backoff
- Agent-spezifische Retry-Logik
- Graceful Degradation

### Cancellation
- CancellationToken für alle Operationen
- Sauberes Cleanup bei Abbruch
- Status-Updates während Cancellation

## Monitoring & Metriken

### Performance-Metriken
- Request-Zeiten pro Agent
- Cache Hit-Rate
- Connection Pool Auslastung
- Erfolgs-/Fehlerquoten

### Logging
- Strukturiertes Logging
- Agent-spezifische Logger
- Performance-Logger für Metriken

## Sicherheit

### API-Key Management
- Umgebungsvariablen für Keys
- Keine Keys im Code
- Separate Config pro Environment

### Rate Limiting
- Agent-spezifische Limits
- Adaptive Rate Control
- Retry-After Header Support

## Erweiterbarkeit

### Neuen Agent hinzufügen
1. Erstelle Klasse von `BaseAgent` abgeleitet
2. Implementiere `search()` Methode
3. Registriere in `AgentFactory`
4. Keine Core-Änderungen nötig

### Neue Datenfelder
1. Erweitere `COMPREHENSIVE_FIELDS` 
2. Update Extraction Patterns
3. Aggregator erkennt automatisch

## Best Practices

### Code-Organisation
- Dateien < 500 Zeilen (CLAUDE.md)
- Klare Modul-Trennung
- Konsistente Namensgebung

### Performance
- Immer async/await nutzen
- Connection Pools verwenden
- Caching wo möglich
- Batch-Operations bevorzugen

### Testing
- Unit Tests für jeden Agent
- Integration Tests für Workflows
- Performance Tests für Optimierungen
- Mock External Services