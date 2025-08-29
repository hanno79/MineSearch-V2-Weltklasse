# MineSearch - Multi-Agent Mining Research System

## Schnellstart (Backend v2 – FastAPI)

- Entwicklung (SAFE_MODE – nur Static & Health, keine Provider/DB):

```bash
SAFE_MODE=1 uvicorn minesearch.main:app --host 0.0.0.0 --port 8000
# UI: http://localhost:8000/static/index.html
```

- Vollbetrieb (Provider/DB werden initialisiert):

```bash
uvicorn minesearch.main:app --host 0.0.0.0 --port 8000
```

- UI‑Smoketest (Playwright):

```bash
UI_BASE_URL=http://127.0.0.1:8000/static/index.html node scripts/ui_smoke_test.js
```

### Projektstruktur (v2)

```
backend/minesearch/        # FastAPI Backend (Python‑Paket `minesearch`)
frontend/                  # Statisches Frontend, über /static ausgeliefert
minesearch/                # Adapter‑Paket, mapped auf backend.minesearch (Entrypoint)
documentation/             # Reorg/TODO & Architektur‑Dokumente
```

Wichtige Invarianten:
- Port 8000 exklusiv für MineSearch (UI unter `/static/index.html`)
- `.env` im Projekt‑Root (nicht committen), DB unter `/app/data/minesearch.db`


Ein hochperformantes, KI-gestütztes System zur automatisierten Recherche von Bergbauinformationen weltweit. Entwickelt mit modernster Multi-Agent-Architektur für umfassende Datenerfassung aus diversen Quellen.

## 🚀 Features

### Core Features
- **🤖 33+ Spezialisierte AI-Agenten**: Claude, GPT-4, Perplexity, Tavily, OpenRouter Models und mehr
- **⚡ Optimierte Performance**: 6-20x schnellere Suchen durch Parallelisierung
- **🔍 Intelligente Datenextraktion**: Automatische Erkennung von Betreibern, Koordinaten, Produktionsdaten
- **📊 Smart Aggregation**: Konfidenz-basiertes Scoring und Deduplizierung
- **🌍 Mehrsprachige Unterstützung**: Recherche in 10+ Sprachen
- **💾 Caching-System**: Reduzierte API-Kosten durch intelligentes Result-Caching
- **📁 Flexible Exports**: CSV, JSON, Excel mit konfigurierbaren Formaten
- **🔄 Robustes Session Management**: Automatische Wiederherstellung bei Verbindungsfehlern

### Technische Highlights
- **Async/Await Architektur**: Maximale Parallelität und Ressourceneffizienz
- **Connection Pooling**: Optimierte HTTP-Verbindungen mit RobustSession
- **Modular Design**: Alle Module < 500 Zeilen für beste Wartbarkeit (100% regelkonform)
- **Test Coverage**: Umfassendes Test-Framework mit pytest
- **Performance Monitoring**: Integrierte Metriken und Statistiken
- **Cancellation Support**: Unterbrechbare Suchen mit GlobalCancellationRegistry

## 📋 Version

**Aktuelle Version**: 3.0 (27.06.2025)
- SessionManager vereinheitlicht (Timeout-Fehler behoben)
- Codebasis vollständig bereinigt und modularisiert
- Alle Projektregeln eingehalten

## Installation

1. Python Virtual Environment erstellen:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Playwright Browser installieren (für Browser Agent):
```bash
playwright install chromium
# Oder für alle Browser:
playwright install
```

4. Konfiguration:
   - Kopiere `config/.env.example` nach `.env`
   - Füge deine API-Keys ein

## 📁 Projekt-Struktur

```
minesearch/
├── src/
│   ├── agents/                 # Agent-Implementierungen
│   │   ├── base_agent.py      # Basis-Klasse für alle Agenten
│   │   ├── perplexity_agent.py # Perplexity Web-Recherche
│   │   ├── tavily_agent.py    # Tavily Search API
│   │   └── ...                # 30+ weitere Agenten
│   ├── core/                  # Kern-Funktionalitäten
│   │   ├── orchestrator.py    # Agent-Koordination
│   │   ├── database.py        # Datenpersistierung
│   │   ├── validators/        # Modularisierte Validierung
│   │   └── config.py          # Konfigurationsmanagement
│   ├── ui/                    # Streamlit UI
│   │   ├── main.py           # Haupt-UI (v3.0)
│   │   └── components/        # UI-Komponenten
│   └── utils/                 # Hilfsfunktionen
│       ├── session_manager.py # HTTP Session Management
│       ├── pdf_extractors/    # PDF-Verarbeitung
│       └── ...
├── tests/                     # Unit & Integration Tests
├── documentation/             # Projektdokumentation
├── logs/                      # Log-Dateien
├── data/                      # SQLite Datenbank
└── config/                    # Konfigurationsdateien
```

## 🚀 Verwendung

### Web-Interface (Streamlit)
```bash
streamlit run src/ui/main.py
```

### Python API
```python
from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestratorV2
from src.agents.base_agent import MineQuery
from src.utils.session_manager import SessionManager

# Initialisierung
config = Config()
session_manager = SessionManager()
orchestrator = MineSearchOrchestratorV2(config, session_manager)

# Suche durchführen
query = MineQuery(
    mine_name="Lac Expanse",
    region="Quebec", 
    country="Canada",
    languages=["en", "fr"],
    required_fields=["betreiber", "koordinaten", "aktivitaetsstatus"]
)

results = await orchestrator.search(
    query=query,
    strategy="staged",
    selected_agents=["perplexity", "tavily", "scraper"]
)
```

## 🛠️ Konfiguration

### Benötigte API-Keys
- **OPENROUTER_KEY**: Für Claude, GPT-4 und 15+ weitere Modelle
- **PERPLEXITY_KEY**: Für Perplexity Web-Recherche
- **TAVILY_KEY**: Für Tavily Search API
- **EXA_KEY**: Für Exa Semantic Search (optional)
- **APIFY_KEY**: Für Apify Web Scraping (optional)
- **FIRECRAWL_KEY**: Für Firecrawl Crawling (optional)
- **SCRAPINGBEE_KEY**: Für ScrapingBee (optional)
- **BRIGHTDATA_KEY**: Für Bright Data (optional)

### Umgebungsvariablen
```env
# API Keys
OPENROUTER_KEY=your_key_here
PERPLEXITY_KEY=your_key_here
TAVILY_KEY=your_key_here

# Optional APIs
EXA_KEY=your_key_here
APIFY_KEY=your_key_here

# Performance Settings
MAX_CONCURRENT_REQUESTS=10
CACHE_TTL_MINUTES=60
REQUEST_TIMEOUT_SECONDS=30

# Database
# Hinweis: Für das Backend wird primär `DATABASE_URL` verwendet. 
# Wartungs-/Analyse‑Skripte (z. B. `backend/analyze_database_contamination.py`) 
# akzeptieren zusätzlich `DATABASE_PATH` (höchste Priorität) und 
# `MINES_DB_PATH` (Kompatibilität für Tests/CI). 
# Auflösung in Priorität: DATABASE_PATH → MINES_DB_PATH → DATABASE_URL (sqlite) → Fallback.
DATABASE_PATH=data/minesearch.db
# Optional für Tests/CI (falls gesetzt, sonst intern in conftest verwaltet)
MINES_DB_PATH=/absolute/pfad/zur/mines.db
 
# Monitoring‑Status‑Skript
# `backend/monitoring_status.py` verwendet dieselbe Auflösung und validiert den Pfad
# vor Nutzung. Falls die Datei nicht existiert, wird eine klare Fehlermeldung mit
# Hinweis auf `DATABASE_PATH`/`MINES_DB_PATH`/`DATABASE_URL` ausgegeben.
```

## 📊 Features im Detail

### Such-Strategien
- **Direct**: Schnelle, direkte Suche
- **Staged**: Mehrstufige Suche mit Source Discovery
- **Comprehensive**: Umfassende Suche mit allen verfügbaren Agenten

### Datenfelder
- Betreiber/Operator
- GPS-Koordinaten
- Aktivitätsstatus
- Rohstofftyp
- Produktionsdaten
- Umweltkosten
- Mitarbeiterzahl
- Fläche
- Und viele mehr...

### Export-Formate
- CSV mit konfigurierbaren Spalten
- JSON für API-Integration
- Excel mit Formatierung
- PDF-Reports (geplant)

## 🧪 Testing

```bash
# Alle Tests ausführen
pytest

# Spezifische Test-Kategorie
pytest tests/test_agents_base.py
pytest tests/test_orchestrator.py

# Mit Coverage
pytest --cov=src tests/
```

## 📈 Performance

- **Durchschnittliche Suchzeit**: 30-120 Sekunden pro Mine
- **Parallelität**: Bis zu 33 Agenten gleichzeitig
- **Cache-Hit-Rate**: ~40% bei wiederholten Suchen
- **Speichernutzung**: < 500MB bei normaler Nutzung

## 🔧 Wartung

### Log-Dateien
- `logs/minesearch.log`: Hauptlog mit JSON-Format
- `logs/streamlit.log`: UI-spezifische Logs

### Datenbank-Wartung
```python
# Backup erstellen
python scripts/backup_database.py

# Statistiken anzeigen
python scripts/show_stats.py
```

## 📚 Dokumentation

Weitere Dokumentation finden Sie im `documentation/` Ordner:
- `PROJEKTREGELN.md`: Entwicklungsrichtlinien
- `ARCHITEKTUR.md`: System-Architektur
- `API_REFERENCE.md`: API-Dokumentation
- `CODEBASIS_BEREINIGUNG_27062025.md`: Aktuelle Bereinigungsdokumentation

## 🤝 Contributing

Bitte beachten Sie die Projektregeln in `/app/CLAUDE.md`:
- Max. 500 Zeilen pro Datei
- Deutscher Code und Kommentare
- Autor-Header in jeder Datei
- Keine Duplikatdateien mit _fixed, _new, etc.

## 📄 Lizenz

Proprietär - Alle Rechte vorbehalten

## 👥 Team

- **Author**: rahn
- **Entwicklung**: 2025
- **Kontakt**: [Kontaktinformationen]

---

**Hinweis**: Dieses System ist für professionelle Mining-Research-Zwecke entwickelt. Die Nutzung unterliegt den jeweiligen API-Nutzungsbedingungen der integrierten Dienste.