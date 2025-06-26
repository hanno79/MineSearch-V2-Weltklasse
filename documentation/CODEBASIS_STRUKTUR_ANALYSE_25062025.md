# Codebasis-Struktur-Analyse MineSearch

**Datum:** 25.06.2025  
**Author:** rahn  
**Version:** 1.0

## 1. Hauptkomponenten-Übersicht

### 1.1 Core-Komponenten (`/src/core/`)
- **Agent Manager**: Verwaltung und Koordination von Agents
- **Orchestrator**: Zentrale Ausführungslogik für Suchanfragen
- **Database**: Datenbankmodelle und -operationen
- **Validators**: Eingabevalidierung und Datenprüfung
- **Event Loop Manager**: Asynchrone Verarbeitung
- **Monitoring**: Performance-Überwachung
- **Config**: Zentrale Konfigurationsverwaltung

### 1.2 Agent-System (`/src/agents/`)
**Basis-Agents:**
- `base_agent.py`: Abstrakte Basisklasse für alle Agents
- `factory.py`: Agent-Factory für dynamische Instanziierung

**Spezialisierte Agents:**
- **Tavily Agent**: Web-Suche über Tavily API (751 Zeilen - VERLETZT 500-ZEILEN-REGEL)
- **Perplexity Agent**: KI-gestützte Suche (638 Zeilen - VERLETZT 500-ZEILEN-REGEL)
- **GPT Agent**: OpenAI GPT-Integration
- **Claude Agent**: Anthropic Claude-Integration
- **DeepSeek Research**: Tiefgreifende Forschungsanalyse
- **Browser Agent**: Browser-basiertes Web-Scraping
- **Firecrawl Agent**: Strukturiertes Web-Crawling
- **Apify Agent**: Web-Scraping über Apify-Plattform
- **ScrapingBee Agent**: Proxy-basiertes Scraping
- **Exa Agent**: Spezialisierte Datenextraktion
- **OpenRouter Agent**: Multi-Model-Router
- **BrightData Agent**: Proxy-Netzwerk-Integration

### 1.3 UI-Komponenten (`/src/ui/`)
- **Main**: Streamlit-Hauptanwendung (172 Zeilen)
- **Search Form**: Suchformular-Komponente
- **Results Display**: Ergebnisanzeige
- **Sidebar**: Seitenleiste (509 Zeilen - VERLETZT 500-ZEILEN-REGEL)
- **Metrics Dashboard**: Metriken und Statistiken

### 1.4 Utilities (`/src/utils/`)
- **PDF Processor**: PDF-Verarbeitung (660 Zeilen - VERLETZT 500-ZEILEN-REGEL)
- **Session Manager**: Session-Verwaltung
- **Model Validation**: Pydantic-Modellvalidierung
- **Safe Dict Access**: Sichere Dictionary-Zugriffe
- **Playwright Checker**: Browser-Automatisierung

### 1.5 Datenmodelle (`/src/data/`)
- **Models**: Zentrale Datenmodelle
- **Aggregator**: Datenaggregation
- **Exporter**: Datenexport-Funktionalität

## 2. Identifizierte Probleme

### 2.1 Verletzung der 500-Zeilen-Regel (CLAUDE.md Regel 1)
```
751 Zeilen: /app/src/agents/tavily_agent.py
660 Zeilen: /app/src/utils/pdf_processor.py
638 Zeilen: /app/src/agents/perplexity_agent.py
547 Zeilen: /app/src/utils/pdf/document_types.py
535 Zeilen: /app/src/core/validators.py
509 Zeilen: /app/src/ui/components/sidebar.py
```

### 2.2 Code-Duplikationen
**Agent-Duplikate:**
- `brightdata_agent.py` vs `brightdata_agent_refactored.py`
- `premium_mining_research.py` vs `premium_mining_research_refactored.py`
- `search_strategies.py` vs `search_strategies_refactored.py` vs `search_strategies_core.py` vs `search_strategies_executor.py`
- Standalone-Dateien vs. Ordner (z.B. `claude_agent.py` und `/claude/claude_agent.py`)

**Mehrfache Implementierungen:**
- 4 verschiedene Search-Strategies-Implementierungen
- 2 Brightdata-Implementierungen
- 2 Premium-Mining-Research-Implementierungen

### 2.3 Veraltete/Temporäre Dateien
**Im Root-Verzeichnis:**
- 20 Test-/Fix-Dateien (sollten in `/tests/` verschoben werden)
- Mehrere Backup-Dateien (*_backup_*)
- Fix-Skripte (fix_attributeerror_issues.py, etc.)

**Dokumentation:**
- Mehrere Summary-Dateien im Root (sollten in `/documentation/`)

### 2.4 Strukturelle Inkonsistenzen
- Manche Agents haben eigene Ordner, andere nicht
- Inkonsistente Namensgebung (underscore vs. camelCase)
- Gemischte Modularisierung (manche als Paket, manche als einzelne Datei)

## 3. Architektur-Übersicht

```
MineSearch Architektur
├── Frontend (Streamlit UI)
│   ├── Search Form
│   ├── Results Display
│   └── Metrics Dashboard
│
├── Orchestration Layer
│   ├── Orchestrator (Hauptkoordination)
│   ├── Agent Manager (Agent-Verwaltung)
│   └── Search Executor (Ausführungslogik)
│
├── Agent Layer
│   ├── Base Agent (Abstrakte Klasse)
│   ├── Web Search Agents (Tavily, Perplexity)
│   ├── AI Agents (GPT, Claude, DeepSeek)
│   ├── Scraping Agents (Browser, Firecrawl, Apify)
│   └── Specialized Agents (Exa, OpenRouter)
│
├── Data Layer
│   ├── Database (PostgreSQL)
│   ├── Models (Pydantic)
│   └── Validators
│
└── Utils Layer
    ├── PDF Processing
    ├── Session Management
    └── Async Utilities
```

## 4. Empfohlene Maßnahmen

### 4.1 Sofortige Maßnahmen
1. **Refactoring großer Dateien**: Alle Dateien über 500 Zeilen aufteilen
2. **Bereinigung von Duplikaten**: Entscheidung welche Version behalten wird
3. **Verschiebung von Test-Dateien**: Alle Test-Dateien nach `/tests/`
4. **Dokumentation organisieren**: Alle Summaries nach `/documentation/`

### 4.2 Mittelfristige Maßnahmen
1. **Konsistente Modularisierung**: Alle Agents als Pakete strukturieren
2. **Namenskonventionen vereinheitlichen**: snake_case durchgängig verwenden
3. **Veraltete Dateien entfernen**: Nach `/to_delete/` verschieben
4. **Tests aktualisieren**: Sicherstellen dass alle Tests funktionieren

### 4.3 Langfristige Maßnahmen
1. **Architektur-Dokumentation**: Detaillierte Dokumentation erstellen
2. **Dependency Injection**: Für bessere Testbarkeit
3. **API-Versioning**: Für externe Schnittstellen
4. **Performance-Optimierung**: Basierend auf Monitoring-Daten

## 5. Zusammenfassung

Die Codebasis zeigt eine solide Grundstruktur mit klarer Trennung von UI, Business-Logik und Datenverarbeitung. Hauptprobleme sind:

1. **6 Dateien verletzen die 500-Zeilen-Regel**
2. **Mehrere Code-Duplikationen vorhanden**
3. **Inkonsistente Strukturierung der Agent-Module**
4. **Viele temporäre Test-/Fix-Dateien im Root**

Die Architektur folgt einem modularen Ansatz mit spezialisierten Agents für verschiedene Datenquellen. Die Verwendung von Pydantic für Datenvalidierung und asyncio für Performance sind positive Aspekte.

**Priorität sollte auf dem Refactoring der großen Dateien und der Bereinigung von Duplikaten liegen.**