# MineSearch v2 - Test-Dokumentation

**Author:** rahn  
**Datum:** 01.07.2025  
**Version:** 1.0

## Übersicht

Diese Dokumentation beschreibt die Test-Suite für MineSearch v2. Die Tests sind in Unit Tests und Integration Tests unterteilt und decken alle Kernfunktionalitäten ab.

## Test-Struktur

```
tests/
├── conftest.py              # Gemeinsame Test-Fixtures
├── test_perplexity.py       # Tests für Perplexity API Integration
├── test_utils.py            # Tests für Utility-Funktionen
├── test_data_extraction.py  # Tests für Datenextraktion
├── test_source_discovery.py # Tests für Source Discovery
├── test_integration.py      # Integration Tests
└── README_TESTS.md          # Diese Dokumentation
```

## Test-Ausführung

### Alle Tests ausführen
```bash
# Im minesearch_v2 Verzeichnis:
python run_tests.py
```

### Spezifische Tests ausführen
```bash
# Nur Unit Tests
python run_tests.py unit

# Nur Integration Tests  
python run_tests.py integration

# Tests mit bestimmtem Namen
python run_tests.py test_search

# Einzelne Test-Datei
pytest tests/test_utils.py -v
```

### Coverage-Report
```bash
# HTML Coverage-Report wird automatisch generiert
# Öffnen mit:
open htmlcov/index.html
```

## Test-Kategorien

### 1. Unit Tests

#### test_utils.py
- **Namenvarianten-Generierung**: 20+ Varianten pro Minenname
- **Datums-Formatierung**: Verschiedene Formate normalisieren
- **Koordinaten-Validierung**: Gültige GPS-Koordinaten prüfen
- **Text-Bereinigung**: HTML, Whitespace, Sonderzeichen
- **Zahlen-Extraktion**: Produktionswerte, Währungen
- **Datenqualitäts-Berechnung**: Scoring-Algorithmus

#### test_data_extraction.py
- **Basis-Informationen**: Minenname, Land, Region extrahieren
- **Koordinaten-Extraktion**: Verschiedene GPS-Formate
- **Produktionsdaten**: Jahresproduktion, Reserven, Ressourcen
- **Eigentümer/Betreiber**: Ownership-Strukturen
- **Umweltdaten**: Genehmigungen, Restaurationskosten
- **Kontaktinformationen**: Website, E-Mail, Telefon

#### test_source_discovery.py
- **URL-Extraktion**: Links aus Text finden
- **Quellen-Validierung**: Gültige Quellen prüfen
- **Domain-Ranking**: 3-stufige Priorisierung
- **PDF-Erkennung**: Technische Dokumente finden
- **Metadaten-Extraktion**: Titel, Datum, Beschreibung

#### test_perplexity.py
- **API-Konfiguration**: API Key vorhanden
- **Basis-Suche**: Einfache Minensuche
- **Timeout-Handling**: Robuste Fehlerbehandlung
- **2-Phasen-Suche**: Enhanced Search Feature
- **Smart Search**: Automatisches Modell-Upgrade
- **Batch-Verarbeitung**: Mehrere Minen gleichzeitig

### 2. Integration Tests

#### test_integration.py
- **API Endpoints**: Health, Search, Batch
- **Eingabe-Validierung**: Request-Parameter
- **WebSocket-Updates**: Real-time Updates
- **Batch Processing Flow**: Upload → Process → Download
- **End-to-End Szenarien**: Komplette Workflows

## Test-Fixtures (conftest.py)

### Globale Fixtures
- `test_config`: Gemeinsame Test-Konfiguration
- `mock_perplexity_success`: Erfolgreiche API Response
- `mock_perplexity_error`: Fehler-Response
- `sample_csv_data`: CSV-Testdaten
- `sample_mine_dict`: Beispiel-Minendaten

### Utility Fixtures
- `temp_test_file`: Temporäre Dateien erstellen
- `mock_env_vars`: Environment Variables mocken
- `skip_without_api_key`: Tests ohne API Key überspringen

## Coverage-Ziele

- **Minimum Coverage**: 70%
- **Ziel Coverage**: 85%
- **Kritische Module**: 90%+

### Aktuelle Coverage nach Modul
- `utils.py`: Ziel 90%
- `data_extraction.py`: Ziel 85%
- `search_service.py`: Ziel 80%
- `source_discovery.py`: Ziel 85%
- `batch_service.py`: Ziel 75%

## Test-Marker

```python
@pytest.mark.unit          # Unit Test
@pytest.mark.integration   # Integration Test
@pytest.mark.slow         # Langsamer Test
@pytest.mark.api          # API Test
@pytest.mark.skip_if_no_api_key  # Benötigt API Key
```

## Best Practices

1. **Isolation**: Jeder Test ist unabhängig
2. **Mocking**: Externe APIs werden gemockt
3. **Fixtures**: Wiederverwendbare Test-Daten
4. **Assertions**: Klare, aussagekräftige Assertions
5. **Coverage**: Mindestens 70% Code-Abdeckung

## Häufige Test-Befehle

```bash
# Tests mit Coverage
pytest --cov=backend --cov-report=html

# Tests mit Ausgabe
pytest -v -s

# Nur failed Tests wiederholen
pytest --lf

# Tests parallel ausführen
pytest -n auto

# Bestimmte Marker
pytest -m "not slow"
```

## Troubleshooting

### Problem: Import-Fehler
```bash
# Lösung: PYTHONPATH setzen
export PYTHONPATH=/app/minesearch_v2:$PYTHONPATH
```

### Problem: API Key fehlt
```bash
# Lösung: .env Datei erstellen
echo "PERPLEXITY_API_KEY=your_key_here" > .env
```

### Problem: Tests zu langsam
```bash
# Lösung: Nur schnelle Tests
pytest -m "not slow"
```

## Continuous Integration

Die Test-Suite ist bereit für CI/CD Integration:

```yaml
# Beispiel GitHub Actions
- name: Run Tests
  run: |
    cd minesearch_v2
    python run_tests.py
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.json
```

## Nächste Schritte

1. **Performance Tests**: Load Testing für API
2. **Security Tests**: Penetration Testing
3. **UI Tests**: Selenium/Playwright für Frontend
4. **Mutation Testing**: Code-Qualität verbessern

---

Bei Fragen oder Problemen mit den Tests, bitte ein Issue erstellen oder die Dokumentation erweitern.