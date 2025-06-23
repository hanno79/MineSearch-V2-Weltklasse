# Test Framework Dokumentation

## Stand: 23.06.2025

### Übersicht

Das Mining Research System verfügt nun über ein umfassendes Test-Framework mit:

- **Unit Tests** für alle wichtigen Module
- **Integration Tests** für System-Komponenten
- **End-to-End Tests** für komplette Workflows
- **Performance Tests** für kritische Operationen
- **Coverage Reports** für Code-Qualität

### Test-Struktur

```
tests/
├── conftest.py                      # Pytest Konfiguration & Fixtures
├── test_agents_base.py             # Basis-Tests für alle Agents
├── test_claude_agent.py            # Claude Agent Tests
├── test_perplexity_agent.py        # Perplexity Agent Tests
├── test_scraper_agent.py           # Scraper Agent Tests
├── test_search_strategies.py       # NEU: Search Strategies Tests
├── test_premium_mining_research.py # NEU: Premium Research Tests
├── test_deepseek_research.py       # NEU: DeepSeek Research Tests
├── test_browser_agent.py           # NEU: Browser Agent Tests
├── test_orchestrator.py            # NEU: Orchestrator Tests
├── test_data_models.py             # NEU: Database & Models Tests
├── test_e2e.py                     # NEU: End-to-End Tests
├── test_database.py                # Database Tests
├── test_config.py                  # Configuration Tests
├── test_logger.py                  # Logger Tests
├── test_consolidation.py           # Consolidation Tests
├── test_agent_factory.py           # Agent Factory Tests
├── test_agent_integration.py       # Agent Integration Tests
└── README_TESTS.md                 # Test Dokumentation
```

### Neue Test-Features

#### 1. **Umfassende Fixtures** (`conftest.py`)
- Mock API Konfiguration
- Temporäre Datenbanken
- Sample Queries und Results
- Mock HTTP Sessions

#### 2. **Modular Tests**
- Tests für alle refaktorierten Module
- Separate Tests für Models, Processors, Builders
- Integration zwischen Modulen getestet

#### 3. **Realistische Mocks**
- Simulierte API Responses
- Zeitverzögerungen für Realismus
- Verschiedene Erfolgs/Fehler-Szenarien

#### 4. **Test Runner** (`run_all_tests.py`)
```bash
# Alle Tests mit Coverage
./run_all_tests.py

# Nur Unit Tests
./run_all_tests.py unit

# Nur Integration Tests
./run_all_tests.py integration

# Nur E2E Tests
./run_all_tests.py e2e

# Spezifische Test-Datei
./run_all_tests.py orchestrator

# Ohne Coverage
./run_all_tests.py all --no-coverage

# Verbose Output
./run_all_tests.py -v
```

### Test-Kategorien

#### Unit Tests
- Isolierte Tests einzelner Komponenten
- Keine externen Abhängigkeiten
- Schnelle Ausführung
- Marker: `@pytest.mark.unit`

#### Integration Tests
- Tests mehrerer Komponenten zusammen
- Mock externe Services
- Mittlere Ausführungszeit
- Marker: `@pytest.mark.integration`

#### End-to-End Tests
- Komplette Workflows
- Realistische Szenarien
- Längere Ausführungszeit
- Marker: `@pytest.mark.e2e`

#### Performance Tests
- Last- und Stresstests
- Zeitmessungen
- Marker: `@pytest.mark.performance`

### Coverage Report

Nach Test-Ausführung:
- **HTML Report**: `htmlcov/index.html`
- **JSON Report**: `coverage.json`
- **Terminal Report**: Direkt in der Ausgabe

Aktuelle Coverage-Ziele:
- Minimum: 70%
- Ziel: 85%
- Ideal: 90%+

### CI/CD Integration

GitHub Actions Workflow (`.github/workflows/tests.yml`):
- Tests für Python 3.10 und 3.11
- Linting mit ruff
- Formatting mit black
- Type checking mit mypy
- Coverage Upload zu Codecov
- Automatische PR Checks

### Best Practices

1. **Test Isolation**
   - Jeder Test unabhängig
   - Keine Seiteneffekte
   - Cleanup in Fixtures

2. **Mocking**
   - Externe APIs immer mocken
   - `AsyncMock` für async Funktionen
   - Realistische Response-Zeiten

3. **Assertions**
   - Spezifische Assertions
   - Aussagekräftige Fehlermeldungen
   - Multiple Assertions wenn sinnvoll

4. **Performance**
   - Langsame Tests markieren
   - Timeouts setzen
   - Parallel ausführbar

### Beispiel Test-Patterns

#### Agent Test
```python
class TestMyAgent(BaseAgentTest):
    agent_class = MyAgent
    agent_name = "my_agent"
    
    async def test_search_success(self, mock_config):
        agent = self.create_agent(mock_config)
        results = await agent.search(sample_query)
        assert len(results) > 0
```

#### Mock HTTP Response
```python
mock_response = AsyncMock()
mock_response.status = 200
mock_response.json = AsyncMock(return_value={"data": "value"})
```

#### E2E Test
```python
@pytest.mark.e2e
async def test_complete_workflow(e2e_system):
    results = await e2e_system.search_mine(
        mine_name="Test Mine",
        country="Canada"
    )
    assert results["found_fields"]["betreiber"] is not None
```

### Nächste Schritte

1. **Coverage erhöhen**
   - Aktuelle Coverage analysieren
   - Fehlende Tests identifizieren
   - Edge Cases abdecken

2. **Performance Benchmarks**
   - Baseline etablieren
   - Regression Tests
   - Optimierungen messen

3. **Continuous Monitoring**
   - Test-Metriken tracken
   - Flaky Tests identifizieren
   - Test-Zeiten optimieren

### Befehle

```bash
# Coverage Report generieren
pytest --cov=src --cov-report=html

# Nur schnelle Tests
pytest -m "not slow"

# Mit Warnings
pytest -W error

# Parallel ausführen
pytest -n auto

# Spezifisches Modul testen
pytest tests/test_orchestrator.py -v
```

Das Test-Framework bildet nun eine solide Basis für die Weiterentwicklung und Wartung des Systems.