# Agent Test Suite - Dokumentation

## Übersicht

Diese Test-Suite bietet umfassende Unit- und Integrations-Tests für alle Agenten im Mining Research System.

## Test-Struktur

### Basis-Tests
- **`test_agents_base.py`**: Abstrakte Basis-Test-Klasse für alle Agent-Tests
  - Stellt gemeinsame Test-Funktionalität bereit
  - Alle Agent-spezifischen Tests erben von `BaseAgentTest`
  - Testet Standard-Funktionalität wie Initialisierung, Credential-Validierung, Suche, etc.

### Agent-Spezifische Tests
- **`test_claude_agent.py`**: Tests für Claude Agent
  - Multi-Language Support
  - Model-Auswahl
  - Spezifische Fehlerbehandlung

- **`test_perplexity_agent.py`**: Tests für Perplexity Agent
  - Web-Search Funktionalität
  - Citation-Parsing
  - Rate-Limit Handling

- **`test_scraper_agent.py`**: Tests für Scraper Agent
  - Google-Suche ohne API-Key
  - HTML-Parsing
  - Multi-Language Suche

### System-Tests
- **`test_agent_factory.py`**: Tests für Agent Factory
  - Agent-Erstellung
  - Verfügbarkeits-Prüfung
  - Requirements-Abfrage

- **`test_agent_status_dashboard.py`**: Tests für Status Dashboard
  - Status-Monitoring
  - Health-Reports
  - Kosten-Berechnung

- **`test_agent_integration.py`**: Integrations-Tests
  - Parallele Agent-Ausführung
  - Fallback-Mechanismen
  - Cancellation-Handling
  - Performance-Monitoring

## Test-Ausführung

### Alle Tests ausführen
```bash
pytest tests/
```

### Spezifische Test-Datei
```bash
pytest tests/test_claude_agent.py
```

### Mit Coverage
```bash
pytest tests/ --cov=src/agents --cov-report=html
```

### Nur schnelle Tests (ohne Integration)
```bash
pytest tests/ -m "not integration"
```

## Test-Patterns

### Neuen Agent testen

1. Erstelle neue Test-Datei: `test_[agent_name]_agent.py`
2. Erbe von `BaseAgentTest`:

```python
from tests.test_agents_base import BaseAgentTest

class TestMyAgent(BaseAgentTest):
    agent_class = MyAgent
    agent_name = "my_agent"
    required_api_key = "my_api_key"
    
    # Überschreibe create_agent wenn spezielle Initialisierung nötig
    def create_agent(self, config):
        return MyAgent(special_param="value", config=config)
    
    # Füge agent-spezifische Tests hinzu
    async def test_my_agent_special_feature(self, mock_config):
        agent = self.create_agent(mock_config)
        # Test implementation
```

### Mock HTTP Responses

```python
mock_response = AsyncMock()
mock_response.status = 200
mock_response.json = AsyncMock(return_value={"data": "value"})

with patch('aiohttp.ClientSession') as mock_session_class:
    mock_session = AsyncMock()
    mock_session_class.return_value.__aenter__.return_value = mock_session
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    # Execute test
```

### Test Cancellation

```python
token = CancellationToken()
agent.set_cancellation_token(token)

# In another task
token.cancel()

# Agent should raise CancellationException
```

## Best Practices

1. **Isolation**: Jeder Test sollte unabhängig laufen
2. **Mocking**: Externe API-Calls immer mocken
3. **Assertions**: Spezifische Assertions verwenden
4. **Cleanup**: Ressourcen in Fixtures aufräumen
5. **Performance**: Lange Tests mit `@pytest.mark.slow` markieren

## Typische Test-Szenarien

### Erfolgreiche Suche
- Agent findet alle required_fields
- Korrekte Confidence Scores
- Metadaten vollständig

### Fehlerbehandlung
- API-Fehler (401, 429, 500)
- Netzwerk-Timeouts
- Invalide Responses

### Edge Cases
- Leere Suchergebnisse
- Sehr lange Texte
- Spezielle Zeichen in Responses
- Multi-Language Content

## Troubleshooting

### Test schlägt fehl
1. Prüfe Mock-Setup
2. Verifiziere API-Response Format
3. Check Assertions auf Aktualität

### Async Warnings
- Nutze `pytest.mark.asyncio`
- Verwende `AsyncMock` statt `Mock`
- Await alle async Calls

### Coverage Lücken
- Prüfe Error-Handling Pfade
- Teste Edge Cases
- Mock verschiedene Response-Szenarien

## Erweiterung

### Neuer Test-Typ
1. Erstelle neue Test-Kategorie
2. Nutze pytest Markers
3. Dokumentiere in dieser README

### Performance Tests
```python
@pytest.mark.performance
async def test_agent_performance():
    # Measure execution time
    # Assert performance thresholds
```

### Load Tests
```python
@pytest.mark.load
async def test_concurrent_agents():
    # Test with many concurrent requests
    # Monitor resource usage
```