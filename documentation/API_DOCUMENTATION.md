# MineSearch v2.1 - API Documentation

**Autor:** rahn  
**Datum:** 11.09.2025  
**Version:** 2.1  

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

## Überblick

Die MineSearch API ist eine REST-API, die es ermöglicht, Bergbauinformationen zu suchen, zu verarbeiten und zu analysieren. Die API nutzt FastAPI und bietet automatische OpenAPI-Dokumentation.

**Base URL:** `http://localhost:8000`  
**API Version:** v2.1  
**Content-Type:** `application/json`

## Authentication

Die API verwendet API-Keys für die Authentifizierung. API-Keys müssen in den Request-Headern übergeben werden:

```http
X-API-Key: your-api-key-here
```

### API-Key-Konfiguration

```python
# API-Keys in .env konfigurieren
PERPLEXITY_API_KEY=pplx-your-key
OPENROUTER_API_KEY=sk-or-your-key
TAVILY_API_KEY=tvly-your-key
```

## Endpoints

### Search Endpoints

#### POST /api/search/multi

Führt eine Multi-Provider-Suche durch.

**Request Body:**
```json
{
  "mine_name": "Test Mine",
  "selected_models": ["openrouter:deepseek-free", "perplexity:llama-3.1-sonar"],
  "search_type": "standard",
  "comprehensive_search": false,
  "selected_fields": ["mine_name", "country", "annual_production"]
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-session-id",
  "results": [
    {
      "field_name": "mine_name",
      "extracted_value": "Test Mine",
      "confidence_score": 0.95,
      "model_id": "openrouter:deepseek-free",
      "source_url": "https://example.com"
    }
  ],
  "extraction_stats": {
    "total_fields": 3,
    "successful_extractions": 2,
    "success_rate": 66.7
  }
}
```

#### POST /api/batch-search

Führt eine Batch-Suche für mehrere Minen durch.

**Request Body:**
```json
{
  "session_id": "csv-session-id",
  "selected_models": ["openrouter:deepseek-free"],
  "count": 10,
  "search_type": "standard"
}
```

**Response:**
```json
{
  "success": true,
  "batch_id": "batch-uuid",
  "processed_mines": 10,
  "results": [...]
}
```

### Data Endpoints

#### GET /api/results

Ruft Suchergebnisse ab.

**Query Parameters:**
- `mine_name` (optional): Filter nach Mine-Name
- `model_id` (optional): Filter nach Modell-ID
- `days_back` (optional): Anzahl Tage zurück (default: 30)
- `limit` (optional): Maximale Anzahl Ergebnisse (default: 100)

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "mine_name": "Test Mine",
      "field_name": "country",
      "extracted_value": "Canada",
      "confidence_score": 0.9,
      "model_id": "openrouter:deepseek-free",
      "created_at": "2025-09-11T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

#### GET /api/consolidated/results

Ruft konsolidierte Ergebnisse ab.

**Query Parameters:**
- `mine_name` (optional): Filter nach Mine-Name
- `exclude_exa` (optional): Exa-Ergebnisse ausschließen (default: true)
- `sort_by` (optional): Sortierung (default: mine_name)

**Response:**
```json
{
  "success": true,
  "consolidated_results": [
    {
      "mine_name": "Test Mine",
      "fields": {
        "country": {
          "value": "Canada",
          "confidence": 0.9,
          "sources": 2
        }
      },
      "completeness_score": 0.8
    }
  ]
}
```

### Statistics Endpoints

#### GET /api/statistics/summary

Ruft Statistiken-Zusammenfassung ab.

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_mines": 150,
    "total_searches": 1250,
    "success_rate": 0.85,
    "average_confidence": 0.78,
    "top_models": [
      {
        "model_id": "openrouter:deepseek-free",
        "usage_count": 500,
        "success_rate": 0.9
      }
    ]
  }
}
```

#### GET /api/statistics/models

Ruft Modell-Statistiken ab.

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "model_id": "openrouter:deepseek-free",
      "provider": "openrouter",
      "total_searches": 500,
      "successful_extractions": 450,
      "success_rate": 0.9,
      "average_confidence": 0.85
    }
  ]
}
```

### Configuration Endpoints

#### GET /api/models

Ruft verfügbare Modelle ab.

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "id": "openrouter:deepseek-free",
      "name": "DeepSeek Free",
      "provider": "openrouter",
      "tier": "free",
      "max_tokens": 4096,
      "available": true
    }
  ]
}
```

#### GET /api/providers

Ruft Provider-Status ab.

**Response:**
```json
{
  "success": true,
  "providers": [
    {
      "name": "openrouter",
      "status": "active",
      "api_key_configured": true,
      "last_check": "2025-09-11T10:00:00Z"
    }
  ]
}
```

## Data Models

### SearchRequest

```json
{
  "mine_name": "string",
  "selected_models": ["string"],
  "search_type": "standard|comprehensive",
  "comprehensive_search": boolean,
  "selected_fields": ["string"],
  "search_options": {
    "max_tokens": number,
    "temperature": number
  }
}
```

### SearchResult

```json
{
  "id": number,
  "session_id": "string",
  "mine_name": "string",
  "model_id": "string",
  "provider": "string",
  "field_name": "string",
  "extracted_value": "string",
  "confidence_score": number,
  "extraction_method": "string",
  "source_url": "string",
  "source_domain": "string",
  "is_placeholder": boolean,
  "is_fallback": boolean,
  "validation_status": "string",
  "created_at": "string"
}
```

### ConsolidatedResult

```json
{
  "mine_name": "string",
  "fields": {
    "field_name": {
      "value": "string",
      "confidence": number,
      "sources": number,
      "model_breakdown": {
        "model_id": {
          "value": "string",
          "confidence": number
        }
      }
    }
  },
  "completeness_score": number,
  "data_quality_score": number,
  "last_updated": "string"
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details",
    "timestamp": "2025-09-11T10:00:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Ungültige Request-Parameter |
| `UNAUTHORIZED` | 401 | Fehlende oder ungültige API-Key |
| `FORBIDDEN` | 403 | Keine Berechtigung für diese Aktion |
| `NOT_FOUND` | 404 | Ressource nicht gefunden |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate Limit überschritten |
| `INTERNAL_ERROR` | 500 | Interner Server-Fehler |
| `SERVICE_UNAVAILABLE` | 503 | Service temporär nicht verfügbar |

### Error Examples

**Ungültige Request:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "mine_name ist erforderlich",
    "details": "Das Feld 'mine_name' darf nicht leer sein",
    "timestamp": "2025-09-11T10:00:00Z"
  }
}
```

**Rate Limit überschritten:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate Limit überschritten",
    "details": "Maximal 100 Requests pro Minute erlaubt",
    "timestamp": "2025-09-11T10:00:00Z"
  }
}
```

## Rate Limiting

Die API implementiert Rate Limiting basierend auf:

- **Requests pro Minute:** 100
- **Batch-Requests pro Stunde:** 10
- **Concurrent Requests:** 5

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1631880000
```

## Examples

### Python Client

```python
import requests

# API-Konfiguration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Einfache Suche
def search_mine(mine_name, models):
    url = f"{API_BASE_URL}/api/search/multi"
    data = {
        "mine_name": mine_name,
        "selected_models": models,
        "search_type": "standard"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Batch-Suche
def batch_search(session_id, models, count=10):
    url = f"{API_BASE_URL}/api/batch-search"
    data = {
        "session_id": session_id,
        "selected_models": models,
        "count": count
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Ergebnisse abrufen
def get_results(mine_name=None, limit=100):
    url = f"{API_BASE_URL}/api/results"
    params = {"limit": limit}
    if mine_name:
        params["mine_name"] = mine_name
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()
```

### JavaScript Client

```javascript
// API-Konfiguration
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Einfache Suche
async function searchMine(mineName, models) {
    const response = await fetch(`${API_BASE_URL}/api/search/multi`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            mine_name: mineName,
            selected_models: models,
            search_type: 'standard'
        })
    });
    
    return await response.json();
}

// Batch-Suche
async function batchSearch(sessionId, models, count = 10) {
    const response = await fetch(`${API_BASE_URL}/api/batch-search`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            session_id: sessionId,
            selected_models: models,
            count: count
        })
    });
    
    return await response.json();
}

// Ergebnisse abrufen
async function getResults(mineName = null, limit = 100) {
    const params = new URLSearchParams({ limit });
    if (mineName) params.append('mine_name', mineName);
    
    const response = await fetch(`${API_BASE_URL}/api/results?${params}`, {
        headers: headers
    });
    
    return await response.json();
}
```

### cURL Examples

**Einfache Suche:**
```bash
curl -X POST "http://localhost:8000/api/search/multi" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "mine_name": "Test Mine",
    "selected_models": ["openrouter:deepseek-free"],
    "search_type": "standard"
  }'
```

**Ergebnisse abrufen:**
```bash
curl -X GET "http://localhost:8000/api/results?limit=10" \
  -H "X-API-Key: your-api-key"
```

**Statistiken abrufen:**
```bash
curl -X GET "http://localhost:8000/api/statistics/summary" \
  -H "X-API-Key: your-api-key"
```

## WebSocket Support

Die API unterstützt WebSocket-Verbindungen für Real-time-Updates:

**WebSocket URL:** `ws://localhost:8000/ws`

**Message Format:**
```json
{
  "type": "search_progress",
  "data": {
    "session_id": "uuid",
    "progress": 50,
    "status": "processing",
    "current_mine": "Test Mine"
  }
}
```

---

**Letzte Aktualisierung:** 11.09.2025  
**Version:** 2.1
