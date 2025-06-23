# Agent System Analysis

## Übersicht
- **20 Agent-Dateien** über 500 Zeilen
- **Größte**: search_strategies.py (702), brightdata_agent.py (701), premium_mining_research.py (694)
- **Viele gemeinsame Patterns** erkennbar

## Identifizierte gemeinsame Funktionalitäten

### 1. HTTP Request Handling
Fast alle Agenten haben:
- Session Management (aiohttp)
- Retry Logic
- Error Handling
- Rate Limiting
- Header Management

### 2. Result Processing
Gemeinsame Patterns:
- JSON/HTML Parsing
- Data Extraction
- Result Normalization
- Confidence Scoring
- Source Attribution

### 3. Query Building
Wiederkehrende Logik:
- Keyword Generation
- Language Handling
- Search Query Construction
- URL Building

### 4. Caching
Viele Agenten implementieren:
- Result Caching
- Request Caching
- TTL Management

## Refactoring-Strategie

### 1. Neue Base-Module erstellen

#### agents/base/http_client.py
- Gemeinsamer HTTP Client
- Session Management
- Retry Logic
- Rate Limiting

#### agents/base/result_processor.py
- Result Parsing
- Data Extraction Utilities
- Confidence Calculation

#### agents/base/query_builder.py
- Query Construction
- Keyword Handling
- Language Support

#### agents/base/cache_manager.py
- Unified Caching
- TTL Management
- Cache Invalidation

### 2. Agent-spezifische Teile
Jeder Agent behält nur:
- API-spezifische Endpoints
- Unique Data Processing
- Custom Business Logic

### 3. Erwartete Reduzierung
- Durchschnittlich 40-50% weniger Code pro Agent
- Bessere Wartbarkeit
- Einheitliche Fehlerbehandlung
- Zentrale Optimierungen möglich