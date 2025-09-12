# MineSearch v2.1

**Ein hochperformantes, KI-gestütztes System zur automatisierten Recherche von Bergbauinformationen weltweit.**

[![Version](https://img.shields.io/badge/version-2.1-blue.svg)](https://github.com/your-repo/minesearch)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🚀 Features

- **Multi-Provider AI-Integration:** OpenRouter, Perplexity, Tavily und mehr
- **Batch-Verarbeitung:** Effiziente Verarbeitung großer Datenmengen
- **Real-time Monitoring:** Live-Überwachung von Suchprozessen
- **Datenbank-Normalisierung:** Strukturierte Speicherung und Abfrage
- **REST-API:** Vollständige API für Frontend-Integration
- **Web-Interface:** Moderne, responsive Benutzeroberfläche

## 📋 Inhaltsverzeichnis

- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Konfiguration](#konfiguration)
- [API-Dokumentation](#api-dokumentation)
- [Entwicklung](#entwicklung)
- [Testing](#testing)
- [Performance](#performance)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Voraussetzungen

- Python 3.8+
- Node.js 16+
- SQLite 3
- Git

### Schritt-für-Schritt Installation

1. **Repository klonen:**
```bash
git clone https://github.com/your-repo/minesearch.git
cd minesearch
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

## 🚀 Schnellstart

### Backend starten

```bash
cd backend
uvicorn minesearch.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend starten

```bash
cd frontend
python -m http.server 8080
```

### Erste Suche durchführen

1. Öffne http://localhost:8080
2. Gib einen Mine-Namen ein (z.B. "Mont Wright")
3. Wähle ein AI-Modell aus
4. Klicke auf "Suchen"

## ⚙️ Konfiguration

### API-Keys konfigurieren

Bearbeite die `.env` Datei:

```env
# AI Provider API Keys
PERPLEXITY_API_KEY=pplx-your-perplexity-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key
TAVILY_API_KEY=tvly-your-tavily-key
EXA_API_KEY=your-exa-key

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=8080
DEBUG=false
```

### Verfügbare AI-Provider

| Provider | Model | Kosten | Qualität |
|----------|-------|--------|----------|
| OpenRouter | DeepSeek Free | Kostenlos | Hoch |
| Perplexity | Llama 3.1 Sonar | Pay-per-use | Sehr hoch |
| Tavily | Tavily Search | Pay-per-use | Hoch |
| Exa | Exa Search | Pay-per-use | Mittel |

## 📚 API-Dokumentation

### Swagger UI

Nach dem Start des Backends:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Beispiel-API-Calls

**Einfache Suche:**
```bash
curl -X POST "http://localhost:8000/api/search/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "mine_name": "Mont Wright",
    "selected_models": ["openrouter:deepseek-free"],
    "search_type": "standard"
  }'
```

**Batch-Suche:**
```bash
curl -X POST "http://localhost:8000/api/batch-search" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "csv-session-id",
    "selected_models": ["openrouter:deepseek-free"],
    "count": 10
  }'
```

**Ergebnisse abrufen:**
```bash
curl -X GET "http://localhost:8000/api/results?limit=10"
```

## 🧪 Testing

### Tests ausführen

```bash
# Alle Tests
python scripts/run_tests.py

# Unit Tests
pytest tests/unit/ -v

# Integration Tests
pytest tests/integration/ -v

# Coverage Report
pytest --cov=backend/minesearch tests/
```

### Test-Coverage

- **Unit Tests:** 70%+ Coverage
- **Integration Tests:** Kritische Workflows
- **E2E Tests:** Vollständige User Journeys

## 🚀 Performance

### Benchmarks

- **Response-Zeit:** < 2 Sekunden
- **Memory-Usage:** < 512MB
- **CPU-Usage:** < 80%
- **Durchsatz:** 100+ Requests/Minute

### Optimierungen

- **Connection Pooling:** Datenbank-Verbindungen
- **Caching:** Redis für Session-Cache
- **Async Processing:** Non-blocking I/O
- **Query Optimization:** Indizierte Datenbankabfragen

## 🐳 Deployment

### Docker

```bash
# Container bauen
docker build -t minesearch .

# Container starten
docker run -p 8000:8000 minesearch
```

### Produktions-Deployment

```bash
# Environment setzen
export ENVIRONMENT=production
export DEBUG=false

# Server starten
uvicorn minesearch.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📊 Monitoring

### Health Checks

- **System Status:** http://localhost:8000/health
- **API Status:** http://localhost:8000/api/status
- **Metrics:** http://localhost:8000/metrics

### Logs

```bash
# Logs anzeigen
tail -f logs/minesearch.log

# Error-Logs filtern
grep "ERROR" logs/minesearch.log
```

## 🔧 Entwicklung

### Code-Standards

- **Python:** PEP 8, Black, Flake8
- **JavaScript:** ESLint, Prettier
- **Tests:** pytest, Coverage
- **Documentation:** Sphinx, Markdown

### Git Workflow

```bash
# Feature Branch erstellen
git checkout -b feature/new-feature

# Änderungen committen
git add .
git commit -m "feat: add new feature"

# Push und Pull Request
git push origin feature/new-feature
```

### Projektstruktur

```
minesearch/
├── backend/           # Python FastAPI Backend
├── frontend/          # JavaScript Frontend
├── scripts/           # Utility Scripts
├── tests/             # Test Suite
├── documentation/     # Dokumentation
└── to_delete/         # Temporäre Dateien
```

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

### Development Setup

```bash
# Development Dependencies installieren
pip install -r requirements-dev.txt

# Pre-commit Hooks einrichten
pre-commit install

# Tests ausführen
pytest
```

## 📄 License

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

## 🆘 Support

### Dokumentation

- [Development Guide](documentation/DEVELOPMENT_GUIDE.md)
- [API Documentation](documentation/API_DOCUMENTATION.md)
- [Performance Guide](documentation/PERFORMANCE_GUIDE.md)

### Hilfe bekommen

1. **Dokumentation durchsuchen**
2. **Issues im Repository erstellen**
3. **Team kontaktieren**

### Häufige Probleme

**Q: API-Keys funktionieren nicht**
A: Prüfe die `.env` Datei und stelle sicher, dass alle API-Keys korrekt konfiguriert sind.

**Q: Datenbank-Fehler**
A: Lösche `mines.db` und starte den Server neu.

**Q: Frontend lädt nicht**
A: Prüfe ob der Frontend-Server auf Port 8080 läuft.

## 🎯 Roadmap

### Version 2.2 (Q4 2025)
- [ ] GraphQL API
- [ ] Real-time WebSocket Updates
- [ ] Advanced Analytics Dashboard
- [ ] Multi-language Support

### Version 2.3 (Q1 2026)
- [ ] Machine Learning Integration
- [ ] Automated Data Validation
- [ ] Export to Excel/PDF
- [ ] Mobile App

## 📈 Statistiken

- **Lines of Code:** 50,000+
- **Test Coverage:** 70%+
- **API Endpoints:** 25+
- **Supported Providers:** 8+
- **Active Contributors:** 5+

---

**Entwickelt mit ❤️ von dem MineSearch Team**

**Letzte Aktualisierung:** 11.09.2025  
**Version:** 2.1
