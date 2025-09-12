# MineSearch v2.1 - Development Guide

**Autor:** rahn  
**Datum:** 11.09.2025  
**Version:** 2.1  

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Projektstruktur](#projektstruktur)
3. [Setup und Installation](#setup-und-installation)
4. [Entwicklungsumgebung](#entwicklungsumgebung)
5. [Code-Standards](#code-standards)
6. [Testing](#testing)
7. [Performance](#performance)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

## Überblick

MineSearch v2.1 ist ein hochperformantes, KI-gestütztes System zur automatisierten Recherche von Bergbauinformationen weltweit. Das System nutzt eine moderne Multi-Agent-Architektur für umfassende Datenerfassung aus diversen Quellen.

### Hauptfunktionen

- **Multi-Provider-Suche:** Integration verschiedener AI-Provider (OpenRouter, Perplexity, etc.)
- **Batch-Verarbeitung:** Effiziente Verarbeitung großer Datenmengen
- **Datenbank-Normalisierung:** Strukturierte Speicherung und Abfrage
- **REST-API:** Vollständige API für Frontend-Integration
- **Real-time Monitoring:** Live-Überwachung von Suchprozessen

## Projektstruktur

```
MineSearch/
├── backend/                    # Python FastAPI Backend
│   ├── minesearch/            # Hauptanwendung
│   │   ├── api/               # API-Routen und Handler
│   │   ├── config/            # Konfigurationsdateien
│   │   ├── database/          # Datenbank-Modelle und Manager
│   │   ├── providers/         # AI-Provider-Implementierungen
│   │   └── ...
│   └── tests/                 # Backend-Tests
├── frontend/                   # JavaScript Frontend
│   ├── index.html             # Haupt-HTML-Datei
│   ├── search.js              # Suchfunktionalität
│   └── ...
├── scripts/                    # Utility-Scripts
│   ├── migration/             # Datenbank-Migrationen
│   ├── maintenance/           # Wartungsscripts
│   └── analysis/              # Analyse-Scripts
├── tests/                      # Test-Suite
│   ├── unit/                  # Unit Tests
│   ├── integration/           # Integration Tests
│   └── e2e/                   # End-to-End Tests
├── documentation/              # Dokumentation
└── to_delete/                  # Temporäre Dateien
```

## Setup und Installation

### Voraussetzungen

- Python 3.8+
- Node.js 16+
- SQLite 3
- Git

### Installation

1. **Repository klonen:**
```bash
git clone <repository-url>
cd MineSearch
```

2. **Python-Umgebung einrichten:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren:**
```bash
cp .env.example .env
# Bearbeite .env mit deinen API-Keys
```

5. **Datenbank initialisieren:**
```bash
python backend/minesearch/main.py
```

## Entwicklungsumgebung

### Backend-Entwicklung

**FastAPI-Server starten:**
```bash
cd backend
uvicorn minesearch.main:app --reload --host 0.0.0.0 --port 8000
```

**API-Dokumentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend-Entwicklung

**Frontend-Server starten:**
```bash
cd frontend
python -m http.server 8080
```

**Frontend-URL:** http://localhost:8080

### Debugging

**Logs anzeigen:**
```bash
tail -f logs/minesearch.log
```

**Debug-Modus aktivieren:**
```bash
export DEBUG=true
python backend/minesearch/main.py
```

## Code-Standards

### Python-Standards

**PEP 8 Compliance:**
- Maximale Zeilenlänge: 79 Zeichen
- 4 Leerzeichen für Einrückung
- Leerzeilen zwischen Funktionen und Klassen

**Code-Formatierung:**
```bash
# Black für Code-Formatierung
black backend/

# Flake8 für Linting
flake8 backend/

# Pylint für Code-Analyse
pylint backend/
```

### JavaScript-Standards

**ESLint-Konfiguration:**
```bash
# ESLint für Code-Qualität
eslint frontend/
```

### Datei-Organisation

**Naming Conventions:**
- Dateien: `snake_case.py`
- Klassen: `PascalCase`
- Funktionen: `snake_case`
- Konstanten: `UPPER_CASE`

**Dateigröße:**
- Maximale Dateigröße: 500 Zeilen
- Bei Überschreitung: Aufteilen in Module

## Testing

### Test-Struktur

```
tests/
├── unit/              # Unit Tests (70% Coverage)
├── integration/       # Integration Tests
└── e2e/              # End-to-End Tests
```

### Tests ausführen

**Alle Tests:**
```bash
python scripts/run_tests.py
```

**Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Integration Tests:**
```bash
pytest tests/integration/ -v
```

**Coverage-Report:**
```bash
pytest --cov=backend/minesearch tests/
```

### Test-Writing Guidelines

**Unit Tests:**
```python
def test_function_name():
    """Test-Funktion sollte beschreibend sein"""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

## Performance

### Monitoring

**Performance-Metriken:**
- Response-Zeit: < 2 Sekunden
- Memory-Usage: < 512MB
- CPU-Usage: < 80%

**Profiling:**
```bash
# cProfile für Performance-Analyse
python -m cProfile backend/minesearch/main.py
```

### Optimierungen

**Datenbank:**
- Connection Pooling aktiviert
- Indizes für häufige Abfragen
- Query-Optimierung

**Caching:**
- Redis für Session-Cache
- Memory-Cache für häufige Daten
- CDN für statische Assets

## Deployment

### Produktions-Deployment

**Docker-Container:**
```bash
docker build -t minesearch .
docker run -p 8000:8000 minesearch
```

**Environment-Variablen:**
```bash
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO
```

### Monitoring

**Health-Checks:**
- `/health` - System-Status
- `/metrics` - Performance-Metriken
- `/api/status` - API-Status

## Troubleshooting

### Häufige Probleme

**1. Import-Fehler:**
```bash
# Python-Pfad prüfen
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

**2. Datenbank-Fehler:**
```bash
# Datenbank zurücksetzen
rm mines.db
python backend/minesearch/main.py
```

**3. API-Key-Probleme:**
```bash
# API-Keys prüfen
python -c "from minesearch.config.api_keys import APIKeysConfig; print(APIKeysConfig.get_missing_keys())"
```

### Debug-Tools

**Log-Analyse:**
```bash
grep "ERROR" logs/minesearch.log
grep "WARNING" logs/minesearch.log
```

**Datenbank-Debug:**
```bash
sqlite3 mines.db ".schema"
sqlite3 mines.db "SELECT COUNT(*) FROM search_results;"
```

## Weiterführende Dokumentation

- [API-Dokumentation](API_DOCUMENTATION.md)
- [Datenbank-Schema](DATABASE_SCHEMA.md)
- [Provider-Integration](PROVIDER_INTEGRATION.md)
- [Performance-Guide](PERFORMANCE_GUIDE.md)

## Support

Bei Fragen oder Problemen:
1. Dokumentation durchsuchen
2. Issues im Repository erstellen
3. Team kontaktieren

---

**Letzte Aktualisierung:** 11.09.2025  
**Version:** 2.1
