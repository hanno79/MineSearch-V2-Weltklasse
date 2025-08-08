# Sustainable API Architecture Guidelines

**Author:** rahn  
**Datum:** 25.07.2025  
**Version:** 1.0  
**Beschreibung:** Umfassende Architektur-Richtlinien für nachhaltige API-Entwicklung

---

## 🎯 ÜBERSICHT

Diese Guidelines definieren die nachhaltige API-Architektur für MineSearch v2, die wiederkehrende Probleme löst und langfristige Wartbarkeit sicherstellt.

## 🏗️ ARCHITEKTUR-PRINZIPIEN

### 1. **Separation of Concerns**
```
api/
├── validators.py      # Input-Validierung & Sanitization
├── error_handlers.py  # Zentrale Fehlerbehandlung  
├── schemas.py         # Request/Response-Schemas
├── standards.py       # Code-Standards & Decorators
└── routes/           # Endpoint-Implementierungen
```

### 2. **Standardisierte Response-Struktur**
```python
# ✅ KORREKT - Einheitliches Format
{
    "success": bool,
    "data": Dict[str, Any] | None,
    "error": str | None,
    "code": str | None,
    "timestamp": str,
    "request_id": str
}

# ❌ VERMEIDEN - Inkonsistente Formate
{"result": data}  # Unterschiedliche Feldnamen
{"status": "ok"}  # Verschiedene Success-Indikatoren
```

### 3. **Zentrale Validierung**
```python
# ✅ KORREKT - Verwendung der Validation Layer
from api.validators import MineSearchValidator, validate_request

@standard_api_endpoint(request_schema=MineSearchValidator)
async def search_mine(request: MineSearchValidator):
    # Automatische Validierung durch Decorator
    pass

# ❌ VERMEIDEN - Manuelle Validierung in jeder Route
async def search_mine(mine_name: str):
    if not mine_name or len(mine_name) < 2:  # Duplizierte Logik
        raise HTTPException(...)
```

## 🔒 SICHERHEITS-STANDARDS

### Input-Sanitization
```python
# Alle String-Inputs MÜSSEN sanitized werden
from api.validators import sanitize_string_input

mine_name = sanitize_string_input(raw_input, max_length=200)
```

### Error-Information-Disclosure
```python
# ✅ KORREKT - Minimale Error-Informationen
return build_error_response(
    error_message="Mine nicht gefunden",
    error_code=ErrorCodes.RESOURCE_NOT_FOUND
)

# ❌ VERMEIDEN - Interne Details preisgeben
return {"error": f"Database query failed: {internal_error}"}
```

## 📊 PERFORMANCE-STANDARDS

### Response-Zeit-Ziele
- **Standard APIs:** < 2000ms
- **Batch-Operationen:** < 10000ms
- **Health-Checks:** < 500ms

### Implementierung
```python
@performance_monitor(max_duration_ms=2000)
@standard_api_endpoint()
async def fast_endpoint():
    # Automatische Performance-Überwachung
    pass
```

## 🚦 ERROR-HANDLING-STRATEGIE

### 1. **Hierarchische Exception-Struktur**
```python
MineSearchException (Basis)
├── ValidationException (4xx)
├── ResourceNotFoundException (404)
├── BusinessLogicException (422)
└── ExternalServiceException (503)
```

### 2. **Standardisierte Error-Codes**
```python
# Alle Errors MÜSSEN definierten Codes verwenden
ErrorCodes.VALIDATION_ERROR
ErrorCodes.RESOURCE_NOT_FOUND
ErrorCodes.MODEL_UNAVAILABLE
# Siehe error_handlers.py für vollständige Liste
```

### 3. **Graceful Degradation**
```python
try:
    result = await primary_service()
except ExternalServiceException:
    # Fallback-Mechanismus
    result = await fallback_service()
    logger.warning("Using fallback service")
```

## 📝 ENDPOINT-ENTWICKLUNG

### Standard-Template
```python
from api.standards import standard_api_endpoint
from api.schemas import SingleSearchRequest, SingleSearchResponse
from api.validators import validate_request

@standard_api_endpoint(
    request_schema=SingleSearchRequest,
    response_schema=SingleSearchResponse
)
async def search_mine(request: SingleSearchRequest) -> Dict[str, Any]:
    """
    Sucht nach Informationen zu einer Mine
    
    Args:
        request: Validierte Such-Anfrage
        
    Returns:
        Standardisierte Search-Response
        
    Raises:
        ValidationException: Bei ungültigen Eingabedaten
        ResourceNotFoundException: Wenn Mine nicht gefunden
        ExternalServiceException: Bei Provider-Fehlern
    """
    
    async with api_operation_context("mine_search", request.dict()) as request_id:
        # Implementation hier
        result = await search_service.search(request.mine_name)
        
        return build_success_response(
            data=result,
            request_id=request_id
        )
```

### Batch-Endpoints
```python
@standard_api_endpoint(request_schema=BatchSearchRequest)
async def batch_search(request: BatchSearchRequest) -> Dict[str, Any]:
    # Parallel-Processing mit konfigurierbarem Limit
    semaphore = asyncio.Semaphore(request.parallel_limit)
    
    async def process_mine(mine: BatchMineEntry):
        async with semaphore:
            return await search_service.search(mine.mine_name)
    
    tasks = [process_mine(mine) for mine in request.mines]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return build_batch_response(results)
```

## 🔄 DATENVALIDIERUNG

### Request-Validierung
```python
# Pydantic-Schemas für alle Requests
class MineSearchRequest(BaseRequest):
    mine_name: str = Field(..., min_length=2, max_length=200)
    model_id: str = Field(...)
    
    @validator('mine_name')
    def validate_mine_name(cls, v):
        # Sanitization + Business-Validierung
        return sanitize_string_input(v)
```

### Response-Validierung
```python
# Automatische Response-Schema-Validierung
@validate_response_schema(SingleSearchResponse)
async def search_endpoint():
    # Response wird automatisch validiert
    return response_data
```

## 🏷️ VERSIONING-STRATEGIE

### URL-Versioning
```
/api/v1/search/mine     # Aktuelle Version
/api/v2/search/mine     # Zukünftige Version
```

### Backward-Compatibility
```python
# Legacy-Endpoints wrappen
@LegacyAPIHandler.wrap_legacy_endpoint
async def old_search_endpoint():
    # Alte Implementierung wird automatisch 
    # in neues Response-Format konvertiert
    pass
```

## 📈 MONITORING & OBSERVABILITY

### Request-Tracking
```python
# Jeder Request erhält eindeutige ID
request_id = str(uuid.uuid4())

# Logging mit strukturierten Daten
logger.info(
    "Search request started",
    extra={
        "request_id": request_id,
        "endpoint": "search_mine",
        "parameters": {"mine_name": "Eleonore"}
    }
)
```

### Performance-Metriken
```python
# Automatische Metriken-Sammlung
@performance_monitor(max_duration_ms=2000)
async def monitored_endpoint():
    # Performance wird automatisch geloggt
    pass
```

## 🧪 TESTING-STANDARDS

### Unit-Tests
```python
import pytest
from api.validators import MineSearchValidator

def test_mine_search_validator_should_accept_valid_input():
    """Test sollte gültige Eingaben akzeptieren"""
    
    request = MineSearchValidator(
        mine_name="Eleonore Mine",
        model_id="openrouter:gpt-4"
    )
    
    assert request.mine_name == "Eleonore Mine"
    assert request.model_id == "openrouter:gpt-4"

def test_mine_search_validator_should_reject_empty_name():
    """Test sollte leere Namen ablehnen"""
    
    with pytest.raises(ValidationError):
        MineSearchValidator(mine_name="", model_id="gpt-4")
```

### Integration-Tests
```python
@pytest.mark.asyncio
async def test_search_endpoint_integration():
    """Integration-Test für Search-Endpoint"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search/mine",
            json={"mine_name": "Test Mine", "model_id": "test-model"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data
```

## 🔧 CONFIGURATION-MANAGEMENT

### Environment-Specific Configs
```python
# config/development.py
API_STANDARDS = {
    "validation_strict": True,
    "error_details": True,  # Detaillierte Errors in Dev
    "performance_logging": True
}

# config/production.py  
API_STANDARDS = {
    "validation_strict": True,
    "error_details": False,  # Minimale Errors in Prod
    "performance_logging": False
}
```

## 🚀 DEPLOYMENT-GUIDELINES

### Startkommandos (FastAPI)

```bash
# SAFE_MODE: nur Static/Health, schnelle Diagnose
SAFE_MODE=1 uvicorn minesearch.main:app --host 0.0.0.0 --port 8000

# Vollbetrieb: Provider/DB‑Initialisierung aktiv
uvicorn minesearch.main:app --host 0.0.0.0 --port 8000
```

Statische Dateien werden unter `/static` aus `/app/frontend` ausgeliefert. Die Root‑Route `/` leitet in SAFE_MODE auf `/static/index.html` um.

### Health-Checks
```python
@app.get("/health")
async def health_check():
    """Standardisierte Health-Check-Response"""
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": await check_database_health(),
            "providers": await check_providers_health()
        }
    }
```

### Graceful Shutdown
```python
@app.on_event("shutdown")
async def shutdown_event():
    """Graceful Shutdown-Handler"""
    
    logger.info("API shutdown initiated")
    # Cleanup-Logik hier
```

## 📚 DOCUMENTATION-REQUIREMENTS

### API-Dokumentation
- **OpenAPI/Swagger:** Automatisch generiert aus Schemas
- **Endpoint-Descriptions:** Detaillierte Beschreibungen
- **Error-Codes:** Vollständige Error-Code-Dokumentation
- **Examples:** Request/Response-Beispiele

### Code-Dokumentation
```python
def process_mine_data(mine_name: str, model_id: str) -> Dict[str, Any]:
    """
    Verarbeitet Mine-Daten mit spezifiziertem Modell
    
    Args:
        mine_name: Name der zu verarbeitenden Mine (2-200 Zeichen)
        model_id: ID des AI-Modells im Format "provider:model"
        
    Returns:
        Dictionary mit verarbeiteten Mine-Daten
        - basic_info: Grundinformationen zur Mine
        - location: Standortdaten
        - production: Produktionsdaten
        
    Raises:
        ValidationException: Bei ungültigen Eingabeparametern
        ResourceNotFoundException: Wenn Mine nicht gefunden wird
        ExternalServiceException: Bei Provider-Kommunikationsfehlern
        
    Example:
        >>> result = await process_mine_data("Eleonore", "openrouter:gpt-4")
        >>> print(result["basic_info"]["name"])
        "Eleonore Mine"
    """
```

## 🔄 MIGRATION-PLAN

### Phase 1: Foundation (Abgeschlossen)
- ✅ Validation Layer implementiert
- ✅ Error-Handler-System erstellt  
- ✅ Standardisierte Schemas definiert
- ✅ Code-Standards dokumentiert

### Phase 2: Integration
- 🔄 Bestehende Endpoints auf neue Standards migrieren
- 🔄 Legacy-Wrapper implementieren
- 🔄 Comprehensive Testing

### Phase 3: Optimization
- ⏳ Performance-Monitoring implementieren
- ⏳ Advanced Caching-Strategien
- ⏳ Rate-Limiting-System

## 📋 COMPLIANCE-CHECKLIST

### Für neue Endpoints:
- [ ] Request-Schema definiert und validiert
- [ ] Response-Schema dokumentiert
- [ ] Error-Handling implementiert
- [ ] Performance-Monitoring aktiviert
- [ ] Unit-Tests geschrieben
- [ ] Integration-Tests erstellt
- [ ] Dokumentation aktualisiert
- [ ] Security-Review durchgeführt

### Für bestehende Endpoints:
- [ ] Auf Standard-Decorator umgestellt
- [ ] Response-Format standardisiert
- [ ] Error-Codes aktualisiert
- [ ] Validation hinzugefügt
- [ ] Performance überprüft
- [ ] Tests erweitert

## 🚨 TROUBLESHOOTING

### Häufige Probleme

#### 1. **Validierung schlägt fehl**
```python
# Problem: Pydantic ValidationError
# Lösung: Spezifische Validatoren verwenden
@validator('mine_name')
def validate_mine_name(cls, v):
    return sanitize_string_input(v)
```

#### 2. **Inkonsistente Responses**
```python
# Problem: Unterschiedliche Response-Formate
# Lösung: build_success_response() verwenden
return build_success_response(data=result)
```

#### 3. **Performance-Probleme**
```python
# Problem: Langsame Endpoints
# Lösung: Performance-Monitor verwenden
@performance_monitor(max_duration_ms=2000)
async def optimized_endpoint():
    pass
```

## 📞 SUPPORT & WEITERENTWICKLUNG

### Team-Kontakte
- **Architecture:** rahn (Lead Sustainable-Solution-Architect)
- **Development:** Development Team
- **DevOps:** Operations Team

### Verbesserungsvorschläge
- Issues über GitHub Issues einreichen
- Architecture-Änderungen über RFC-Prozess
- Performance-Optimierungen über Pull Requests

---

## ⚖️ COMPLIANCE

Diese Guidelines sind **VERBINDLICH** für alle API-Entwicklungen in MineSearch v2. 

**Letzte Aktualisierung:** 25.07.2025  
**Nächste Review:** Nach Implementierung Phase 2  
**Genehmigt von:** Sustainable-Solution-Architect Agent