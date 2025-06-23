# Mining Research System - Systemdokumentation

**Version**: 1.0  
**Datum**: 21.06.2025  
**Autor**: Mining Research Team

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Systemarchitektur](#systemarchitektur)
3. [Hauptkomponenten](#hauptkomponenten)
4. [Workflow](#workflow)
5. [Agenten](#agenten)
6. [Installation & Konfiguration](#installation--konfiguration)
7. [Verwendung](#verwendung)
8. [Datenmodell](#datenmodell)
9. [API-Referenz](#api-referenz)
10. [Troubleshooting](#troubleshooting)

## Überblick

Das Mining Research System ist eine Multi-Agent-Plattform zur automatisierten Informationsbeschaffung über Bergbauminen weltweit. Das System nutzt verschiedene spezialisierte Agenten, um Daten aus unterschiedlichen Quellen zu sammeln, zu verarbeiten und zu aggregieren.

### Hauptziele
- **Automatisierte Datensammlung**: Sammlung von Mining-Informationen aus öffentlichen Quellen
- **Multi-Source-Aggregation**: Kombination von Daten aus verschiedenen Quellen für höhere Genauigkeit
- **Deep Web Mining**: Tiefgreifende Analyse von Websites und Dokumenten
- **Strukturierte Ausgabe**: Standardisierte Datenformate für weitere Verarbeitung

### Kernfunktionen
- Parallele Suche mit mehreren spezialisierten Agenten
- Intelligente Quellenentdeckung und -priorisierung
- PDF- und Dokumentenverarbeitung
- Browser-basiertes Scraping für JavaScript-heavy Websites
- Adaptive Agent-Koordination basierend auf Performance
- Datenbank-gestützte Persistenz und Caching

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│                    (src/ui/main.py)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Orchestrator                             │
│              (src/core/orchestrator.py)                     │
│  ┌─────────────┬──────────────┬────────────────────────┐  │
│  │   Source    │    Agent     │      Staged            │  │
│  │  Discovery  │ Coordinator  │     Search             │  │
│  └─────────────┴──────────────┴────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Agent Layer                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │  Search  │ Scraping │ Document │ Browser  │    AI     │ │
│  │  Agents  │  Agents  │  Finder  │  Agent   │  Agents   │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Data Layer                                 │
│  ┌──────────────┬───────────────┬────────────────────────┐ │
│  │   Database   │  Aggregator   │      Exporter          │ │
│  │   (SQLite)   │               │   (CSV/JSON)           │ │
│  └──────────────┴───────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Hauptkomponenten

### 1. UI Layer (src/ui/)
- **main.py**: Streamlit-basierte Web-Oberfläche
- Single-Page Application mit Sidebar-Navigation
- Unterstützt manuelle Eingabe und CSV-Upload
- Echtzeit-Statusupdates während der Suche

### 2. Core Layer (src/core/)

#### Orchestrator
- Zentrale Koordination aller Agenten
- Implementiert mehrstufige Suchstrategien
- Verwaltet Cancellation und Timeouts
- Integriert Source Discovery und Agent Assignment

#### Config
- Zentrale Konfigurationsverwaltung
- Lädt API-Keys aus Umgebungsvariablen
- Validiert Konfiguration beim Start

#### Database
- SQLAlchemy-basierte Datenbankabstraktion
- Tabellen für Mines, Searches, Results, Sources
- Content-Caching für Performance

#### Logger
- Strukturiertes JSON-Logging
- Performance-Metriken
- Agent-spezifisches Logging

### 3. Agent Layer (src/agents/)

#### Base Agent
- Abstrakte Basisklasse für alle Agenten
- Gemeinsame Funktionalität:
  - Feldextraktion mit Kontext
  - Rate Limiting
  - Error Handling
  - Statistiken

#### Agent-Kategorien

**Search Agents**:
- **Tavily**: Erweiterte Web-Suche mit Domain-Filterung
- **Exa**: Semantische Suche mit Neural Search
- **Perplexity**: KI-gestützte Informationsextraktion

**Scraping Agents**:
- **Scraper**: Basis HTML-Scraping
- **ScrapingBee**: JavaScript-Rendering
- **Firecrawl**: Intelligentes Crawling
- **BrightData**: Enterprise-Scraping
- **Apify**: Cloud-basiertes Scraping

**AI Agents**:
- **Claude**: Komplexe Dokumentenanalyse
- **GPT-4**: Textverständnis und Extraktion
- **OpenRouter**: Multi-Model-Zugriff

**Spezialisierte Agents**:
- **Deep Web Crawler**: Mehrstufiges Website-Crawling
- **Browser Agent**: Playwright-basiertes Browser-Scraping
- **Document Finder**: PDF und Dokumentenverarbeitung

### 4. Data Layer (src/data/)

#### Aggregator
- Deduplizierung von Ergebnissen
- Konfidenz-basierte Aggregation
- Kreuzvalidierung zwischen Agenten

#### Exporter
- CSV-Export mit konfigurierbaren Trennzeichen
- JSON-Export für maschinelle Weiterverarbeitung
- Summary Reports

## Workflow

### Phase 1: Initialisierung
1. **Konfiguration laden**: API-Keys und Einstellungen
2. **Agenten initialisieren**: Verfügbare Agenten basierend auf Keys
3. **Datenbank vorbereiten**: Schema erstellen/migrieren

### Phase 2: Source Discovery
1. **Quellensuche**: Spezielle Agenten suchen nach relevanten URLs
2. **Quellenklassifizierung**: Government, Company, Technical Report, etc.
3. **Priorisierung**: Relevanz-Scoring basierend auf Quellentyp

### Phase 3: Gestaffelte Suche

#### Stage 0: Source Discovery
- Findet Websites, Portale, Dokumente
- Baut Quellen-Datenbank auf
- Klassifiziert nach Typ und Relevanz

#### Stage 1: Basic Information
- Betreiber, Standort, Status
- Nutzt schnelle Agenten
- Timeout: 30 Sekunden

#### Stage 2: Technical Data  
- Produktionsdaten, Rohstofftyp
- Nutzt spezialisierte Agenten
- Timeout: 60 Sekunden

#### Stage 3: Environmental/Financial
- Sanierungskosten, Umweltdaten
- Nutzt AI-Agenten und Document Finder
- Timeout: 120 Sekunden

#### Stage 4: Deep Research
- Detaillierte Analyse gefundener Quellen
- Browser-basiertes Scraping
- PDF-Verarbeitung

### Phase 4: Aggregation
1. **Deduplizierung**: Entfernung doppelter Ergebnisse
2. **Konfidenz-Bewertung**: Scoring basierend auf Quellenqualität
3. **Kreuzvalidierung**: Vergleich zwischen Agenten
4. **Finale Aggregation**: Beste Werte pro Feld

### Phase 5: Export
1. **Formatierung**: Strukturierung der Daten
2. **Export**: CSV/JSON/Report Generation
3. **Persistierung**: Speicherung in Datenbank

## Agenten

### Agent-Fähigkeiten Matrix

| Agent | Koordinaten | Betreiber | Produktion | Umwelt | Dokumente |
|-------|------------|-----------|------------|--------|-----------|
| Tavily | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Exa | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| Claude | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Browser | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| Deep Crawler | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Document Finder | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Agent-Koordination

Der `AgentCoordinator` weist Agenten basierend auf:
1. **Feld-Stärken**: Vordefinierte Fähigkeiten pro Agent
2. **Historische Performance**: Erfolgsraten werden getrackt
3. **Quellentyp**: Bestimmte Agenten für bestimmte Quellen
4. **Verfügbarkeit**: Nur aktive Agenten werden genutzt

## Installation & Konfiguration

### Systemanforderungen
- Python 3.10+
- SQLite3
- Optional: Playwright für Browser Agent
- Optional: PDF-Bibliotheken (PyPDF2, pdfplumber)

### Installation

```bash
# Repository klonen
git clone <repository-url>
cd mining-research-system

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Playwright Browser installieren (optional)
playwright install chromium
```

### Konfiguration

1. **Umgebungsvariablen** (.env Datei):
```env
# API Keys
OPENROUTER_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
EXA_API_KEY=your_key_here

# Optional APIs
APIFY_API_TOKEN=your_key_here
SCRAPINGBEE_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
BRIGHTDATA_API_KEY=your_key_here

# Konfiguration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
DEBUG_MODE=false
```

2. **Erweiterte Konfiguration** (config.yaml):
```yaml
search:
  max_agents_per_field: 5
  timeout_basic: 30
  timeout_extended: 120
  
export:
  column_separator: ";"
  cell_separator: "|"
  default_path: "./exports"
```

## Verwendung

### Über die Web-UI

1. **Starten der Anwendung**:
```bash
streamlit run src/ui/main.py
```

2. **Einzelne Mine suchen**:
   - Mine Name eingeben
   - Region und Land auswählen
   - Gewünschte Felder wählen
   - Agenten auswählen (oder Auto-Selektion)
   - "Suche starten" klicken

3. **Batch-Verarbeitung (CSV)**:
   - CSV-Datei mit Minen hochladen
   - Format: `mine_name,region,country`
   - System verarbeitet alle Einträge sequenziell

### Über die API

```python
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery

# Orchestrator initialisieren
orchestrator = MineSearchOrchestrator(config)
await orchestrator.initialize()

# Query erstellen
query = MineQuery(
    mine_name="Example Mine",
    region="Quebec",
    country="Canada",
    languages=["en", "fr"],
    required_fields=["betreiber", "koordinaten", "jahresproduktion"]
)

# Suche durchführen
results = await orchestrator.search_mine_staged(query)

# Ergebnisse exportieren
from src.data.exporter import DataExporter
exporter = DataExporter()
csv_path = exporter.export_to_csv(results)
```

## Datenmodell

### Haupttabellen

#### mines
- `id`: Primary Key
- `name`: Minenname
- `region`: Region/Provinz
- `country`: Land
- `languages`: JSON Array der Sprachen
- `created_at`: Erstellungsdatum
- `updated_at`: Letztes Update

#### searches
- `id`: Primary Key
- `mine_id`: Foreign Key zu mines
- `started_at`: Startzeit
- `completed_at`: Endzeit
- `status`: running/completed/failed
- `agents_used`: JSON Array der verwendeten Agenten
- `total_results`: Anzahl gefundener Ergebnisse

#### results
- `id`: Primary Key
- `mine_id`: Foreign Key zu mines
- `search_id`: Foreign Key zu searches
- `field_name`: Name des Datenfelds
- `value`: Gefundener Wert
- `source`: Quelle der Information
- `source_url`: URL der Quelle
- `confidence_score`: Konfidenz (0-1)
- `agent_name`: Agent der das Ergebnis fand

#### sources (NEU)
- `id`: Primary Key
- `url`: Unique URL
- `source_type`: website/pdf/api/database/news/government
- `mine_id`: Foreign Key zu mines
- `discovered_by`: Agent Name
- `reliability_score`: Zuverlässigkeit (0-1)
- `last_crawled`: Letzter Crawl-Zeitpunkt

#### agent_results (NEU)
- `id`: Primary Key
- `agent_name`: Name des Agenten
- `mine_id`: Foreign Key zu mines
- `source_id`: Foreign Key zu sources
- `field_name`: Datenfeld
- `value`: Wert
- `confidence`: Konfidenz
- `extracted_at`: Extraktionszeitpunkt

### Unterstützte Datenfelder

| Feld | Beschreibung | Beispiel |
|------|--------------|----------|
| betreiber | Minenbetreiber/Eigentümer | "Teck Resources Ltd." |
| koordinaten | GPS-Koordinaten | "49.123, -123.456" |
| latitude | Breitengrad | "49.123" |
| longitude | Längengrad | "-123.456" |
| aktivitaetsstatus | Betriebsstatus | "active" / "closed" |
| sanierungskosten | Umweltsanierungskosten | "$150 million" |
| kostenerfassungsjahr | Jahr der Kostenerfassung | "2023" |
| rohstofftyp | Geförderte Rohstoffe | "Copper, Gold" |
| minentyp | Art des Bergbaus | "Open Pit" |
| produktionsbeginn | Start der Produktion | "1995" |
| jahresproduktion | Jährliche Produktion | "50,000 tonnes" |
| minenflaeche | Fläche in km² | "25.5" |

## API-Referenz

### MineQuery

```python
@dataclass
class MineQuery:
    mine_name: str
    region: str
    country: str
    languages: List[str]
    required_fields: List[str]
```

### SearchResult

```python
@dataclass
class SearchResult:
    mine_name: str
    field_name: str
    value: str
    source: str
    source_url: str
    source_date: int
    confidence_score: float
    agent_name: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

### Orchestrator Methoden

#### search_mine_staged()
```python
async def search_mine_staged(
    self, 
    query: MineQuery, 
    search_params: Optional[Dict[str, Any]] = None
) -> List[SearchResult]
```

Führt eine gestaffelte Suche durch alle Phasen durch.

**Parameter**:
- `query`: MineQuery Objekt mit Suchinformationen
- `search_params`: Optionale Parameter (timeout, active_agents, etc.)

**Returns**: Liste von SearchResult Objekten

#### discover_sources()
```python
async def discover_sources(
    self, 
    query: MineQuery
) -> List[SourceInfo]
```

Entdeckt relevante Informationsquellen für eine Mine.

### Agent Interface

Alle Agenten implementieren das BaseAgent Interface:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        
    @abstractmethod
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt die Suche durch"""
        
    async def cleanup(self):
        """Räumt Ressourcen auf"""
```

## Troubleshooting

### Häufige Probleme

#### 1. "No agents available"
**Ursache**: Keine API-Keys konfiguriert
**Lösung**: Mindestens einen API-Key in .env setzen

#### 2. "Timeout during search"
**Ursache**: Zu viele Agenten oder langsame Antworten
**Lösung**: 
- Weniger Agenten auswählen
- Timeout in Konfiguration erhöhen
- Schnellere Agenten priorisieren

#### 3. "Database locked"
**Ursache**: Mehrere gleichzeitige Zugriffe auf SQLite
**Lösung**: 
- Nur eine Instanz gleichzeitig laufen lassen
- Auf PostgreSQL migrieren für Produktivbetrieb

#### 4. "Playwright not installed"
**Ursache**: Browser-Binaries fehlen
**Lösung**: `playwright install chromium` ausführen

#### 5. "PDF extraction failed"
**Ursache**: PDF-Bibliotheken nicht installiert
**Lösung**: `pip install PyPDF2 pdfplumber camelot-py[cv]`

### Debug-Modus

Aktivierung über:
1. Umgebungsvariable: `DEBUG_MODE=true`
2. UI: "Debug Mode" Checkbox
3. Code: `logger.setLevel(logging.DEBUG)`

Debug-Output enthält:
- Detaillierte Agent-Kommunikation
- HTTP Request/Response Details
- SQL Queries
- Performance Metriken

### Performance-Optimierung

1. **Agent-Auswahl**: Nur benötigte Agenten aktivieren
2. **Feld-Priorisierung**: Wichtigste Felder zuerst
3. **Caching**: Content-Cache nutzen für wiederholte Suchen
4. **Parallelität**: `MAX_CONCURRENT_REQUESTS` anpassen
5. **Datenbank**: Indizes prüfen mit `EXPLAIN QUERY PLAN`

### Logging

Log-Dateien:
- `logs/app.log`: Allgemeine Anwendungslogs
- `logs/agents.log`: Agent-spezifische Logs
- `logs/performance.log`: Performance-Metriken

Log-Level:
- ERROR: Kritische Fehler
- WARNING: Nicht-kritische Probleme
- INFO: Normale Operationen
- DEBUG: Detaillierte Informationen

## Weiterentwicklung

### Geplante Features

1. **Machine Learning Integration**
   - Automatische Quellenklassifizierung
   - Konfidenz-Vorhersage
   - Anomalie-Erkennung

2. **Erweiterte Dokumentverarbeitung**
   - OCR für gescannte Dokumente
   - Tabellen-Extraktion aus Bildern
   - Multi-Language Support

3. **Real-time Monitoring**
   - WebSocket-basierte Updates
   - Dashboard mit Live-Metriken
   - Alert-System

4. **API-Erweiterungen**
   - REST API für externe Integration
   - Webhook-Support
   - Batch-Processing API

### Architektur-Verbesserungen

1. **Microservices**: Agenten als separate Services
2. **Message Queue**: RabbitMQ/Kafka für Skalierung
3. **Container**: Docker/Kubernetes Deployment
4. **Monitoring**: Prometheus/Grafana Integration

---

Für weitere Informationen oder Support kontaktieren Sie das Development Team.