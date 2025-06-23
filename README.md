# MineSearch - Multi-Agent Mining Research System

Ein hochperformantes, KI-gestütztes System zur automatisierten Recherche von Bergbauinformationen weltweit. Entwickelt mit modernster Multi-Agent-Architektur für umfassende Datenerfassung aus diversen Quellen.

## 🚀 Features

### Core Features
- **🤖 20+ Spezialisierte AI-Agenten**: Claude, GPT-4, Perplexity, Tavily, und mehr
- **⚡ Optimierte Performance**: 6-20x schnellere Suchen durch Parallelisierung
- **🔍 Intelligente Datenextraktion**: Automatische Erkennung von Betreibern, Koordinaten, Produktionsdaten
- **📊 Smart Aggregation**: Konfidenz-basiertes Scoring und Deduplizierung
- **🌍 Mehrsprachige Unterstützung**: Recherche in 10+ Sprachen
- **💾 Caching-System**: Reduzierte API-Kosten durch intelligentes Result-Caching
- **📁 Flexible Exports**: CSV, JSON, Excel mit konfigurierbaren Formaten

### Technische Highlights
- **Async/Await Architektur**: Maximale Parallelität und Ressourceneffizienz
- **Connection Pooling**: Optimierte HTTP-Verbindungen (bis zu 100 concurrent)
- **Modular Design**: Alle Module < 500 Zeilen für beste Wartbarkeit
- **Test Coverage**: Umfassendes Test-Framework mit pytest
- **Performance Monitoring**: Integrierte Metriken und Statistiken

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
│   ├── agents/                 # AI-Agenten
│   │   ├── base/              # Gemeinsame Base-Module
│   │   ├── search_strategies_module/  # Such-Strategien
│   │   ├── browser_agent/     # Browser-basierte Suche
│   │   ├── deepseek_research/ # Deep Research Agent
│   │   └── ...                # 20+ weitere Agenten
│   ├── core/                  # Kern-Funktionalität
│   │   ├── orchestrator.py    # Haupt-Koordinator
│   │   ├── performance_optimizer.py  # Performance-Module
│   │   └── database_optimized.py    # Optimierte DB
│   ├── data/                  # Datenverarbeitung
│   │   ├── models.py          # SQLAlchemy Models
│   │   └── aggregator.py      # Daten-Aggregation
│   └── ui/                    # Streamlit GUI
│       ├── main.py            # Haupt-UI
│       └── components/        # UI-Komponenten
├── tests/                     # Test-Suite
│   ├── conftest.py           # Pytest Configuration
│   └── test_*.py             # Unit/Integration Tests
├── docs/                      # Dokumentation
├── logs/                      # Log-Dateien
└── data/                      # Datenbank & Cache
    └── minesearch.db         # SQLite Datenbank
```

## 🚀 Schnellstart

### Verwendung

```bash
# Streamlit UI starten
streamlit run src/ui/main.py

# Oder mit Make
make run
```

### Erste Schritte
1. Öffne http://localhost:8501 im Browser
2. Gib den Minennamen ein (z.B. "Cerro Vanguardia")
3. Wähle Region und Land
4. Klicke auf "Suche starten"
5. Ergebnisse werden automatisch aggregiert und angezeigt

## 🧪 Testing

```bash
# Alle Tests ausführen
python run_all_tests.py all

# Nur Unit-Tests
python run_all_tests.py unit

# Mit Coverage-Report
pytest --cov=src --cov-report=html

# Spezifisches Modul testen
pytest tests/test_search_strategies.py -v
```

## ⚡ Performance

Das System nutzt fortschrittliche Optimierungen:
- **Parallele Suchen**: Bis zu 10 Agenten gleichzeitig
- **Result Caching**: Vermeidet doppelte API-Calls
- **Connection Pooling**: Wiederverwendung von HTTP-Verbindungen
- **Bulk Operations**: Optimierte Datenbank-Zugriffe

Benchmark-Ergebnisse:
- Sequentielle Suche: ~20 Sekunden für 20 Agenten
- Optimierte Suche: ~3 Sekunden (6.7x Speedup)
- Cache-Hit: <5ms pro Agent

## 🛠️ Entwicklung

### Requirements
- Python 3.10+
- 4GB RAM minimum
- SQLite 3.x
- Moderne Browser für UI

### Architektur
- **Async/Await**: Vollständig asynchrone Architektur
- **Modulares Design**: Klare Trennung der Verantwortlichkeiten
- **Event-Driven**: Status-Updates über Callbacks
- **Type Hints**: Vollständige Typ-Annotationen

### Code-Standards
- Alle Dateien < 500 Zeilen (CLAUDE.md Regel)
- Deutsche Kommentare und Dokumentation
- Comprehensive Error Handling
- Performance-orientiertes Design

## 📚 Dokumentation

- [Architektur-Übersicht](docs/ARCHITECTURE.md)
- [API-Dokumentation](docs/API.md)
- [Deployment-Guide](docs/DEPLOYMENT.md)
- [Agent-Dokumentation](src/agents/README.md)
- [Performance-Guide](PERFORMANCE_OPTIMIZATION_23062025.md)

## 🤝 Contributing

Bitte beachte die Regeln in [CLAUDE.md](CLAUDE.md) für Code-Standards und Konventionen.

## 📄 Lizenz

Copyright © 2025 rahn. Alle Rechte vorbehalten.