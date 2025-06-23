# Mining Research System - Agent Dokumentation

## Übersicht

Das Mining Research System verwendet verschiedene spezialisierte Agenten für die Datensammlung. Jeder Agent hat spezifische Fähigkeiten und Anforderungen.

## Agent-Typen

### 🤖 AI-Agenten
Nutzen Large Language Models für intelligente Analyse und Recherche.

| Agent | API-Key | Beschreibung | Kosten/Anfrage |
|-------|---------|--------------|----------------|
| **claude** | OPENROUTER_API_KEY | Claude-3 via OpenRouter für komplexe Analyse | $0.015 |
| **gpt4** | OPENROUTER_API_KEY | GPT-4 via OpenRouter für Mining-Recherche | $0.020 |
| **deepseek** | OPENROUTER_API_KEY | DeepSeek für erweiterte Research-Aufgaben | $0.001 |

### 🔍 Such-Agenten
Spezialisiert auf Web-Suche und Informationsbeschaffung.

| Agent | API-Key | Beschreibung | Kosten/Anfrage |
|-------|---------|--------------|----------------|
| **perplexity** | PERPLEXITY_API_KEY | Web-Suche mit Echtzeit-Daten | $0.001 |
| **perplexity_deep** | PERPLEXITY_API_KEY | Deep Research Mode (experimentell) | $0.005 |
| **tavily** | TAVILY_API_KEY | Erweiterte Web-Suche mit Domain-Filterung | $0.001 |
| **exa** | EXA_API_KEY | Semantische Suche | $0.001 |

### 🕷️ Scraping-Agenten
Extrahieren Daten direkt von Websites.

| Agent | API-Key | Beschreibung | Kosten/Anfrage |
|-------|---------|--------------|----------------|
| **scraper** | - | Basis Web-Scraper (kein API-Key nötig) | $0.000 |
| **apify** | APIFY_API_KEY | Professionelles Web-Scraping | $0.002 |
| **scrapingbee** | SCRAPINGBEE_API_KEY | JavaScript-Rendering und Proxies | $0.001 |
| **firecrawl** | FIRECRAWL_API_KEY | Intelligentes Crawling mit Markdown-Export | $0.002 |
| **brightdata** | BRIGHTDATA_API_KEY | Enterprise-Scraping mit Premium-Proxies | $0.005 |

## Agent-Capabilities

### 🌐 WEB_SEARCH
Agenten die im Web nach Informationen suchen können:
- perplexity, perplexity_deep
- tavily
- exa

### 🔧 WEB_SCRAPING
Agenten die Websites direkt scrapen können:
- scraper
- apify, scrapingbee, firecrawl, brightdata

### 🧠 AI_ANALYSIS
Agenten mit KI-Analysefähigkeiten:
- claude, gpt4
- deepseek

### 🔬 DEEP_RESEARCH
Agenten für tiefgehende Recherche:
- perplexity_deep
- deepseek

### 📄 DOCUMENT_PARSING
Agenten die Dokumente (PDF, etc.) verarbeiten können:
- tavily
- scrapingbee, firecrawl

### 🌍 MULTI_LANGUAGE
Agenten mit Mehrsprachunterstützung:
- claude, gpt4

### 🏛️ GOVERNMENT_ACCESS
Agenten optimiert für Regierungsseiten:
- apify
- brightdata

### 💎 PREMIUM_SOURCES
Agenten mit Zugang zu Premium-Datenquellen:
- perplexity_deep
- brightdata

## Konfiguration

### Umgebungsvariablen (.env)

```bash
# OpenRouter (für Claude, GPT-4, DeepSeek)
OPENROUTER_API_KEY=your_key_here

# Perplexity
PERPLEXITY_API_KEY=your_key_here

# Such-APIs
TAVILY_API_KEY=your_key_here
EXA_API_KEY=your_key_here

# Scraping-APIs
APIFY_API_KEY=your_key_here
SCRAPINGBEE_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
BRIGHTDATA_API_KEY=your_key_here
```

## Fallback-Mechanismen

Das System wählt automatisch alternative Agenten wenn der primäre Agent nicht verfügbar ist:

1. **AI-Analyse**: claude → gpt4 → deepseek
2. **Web-Suche**: perplexity → tavily → exa
3. **Web-Scraping**: brightdata → firecrawl → scrapingbee → apify → scraper

## Best Practices

### Minimale Konfiguration
Für grundlegende Funktionalität:
- Kein API-Key nötig (nutzt nur `scraper`)
- Eingeschränkte Datenquellen

### Empfohlene Konfiguration
Für optimale Ergebnisse:
- OPENROUTER_API_KEY (für AI-Analyse)
- PERPLEXITY_API_KEY oder TAVILY_API_KEY (für Web-Suche)
- Ein Scraping-API-Key (APIFY, SCRAPINGBEE, oder FIRECRAWL)

### Premium-Konfiguration
Für beste Ergebnisse:
- Alle API-Keys konfiguriert
- Nutzt automatisch beste verfügbare Agenten
- Parallele Suche mit mehreren Agenten

## Fehlerbehandlung

### Fehlende API-Keys
- Agent wird als DISABLED markiert
- System nutzt automatisch Fallback-Agenten
- Warnung in Status-Dashboard

### Rate Limits
- Eingebautes Rate-Limiting pro Agent
- Automatische Wiederholung mit Backoff
- Status: RATE_LIMITED im Dashboard

### API-Fehler
- Detailliertes Error-Logging
- Automatischer Fallback zu anderen Agenten
- Fehlerstatistiken im Dashboard

## Performance-Optimierung

### Caching
- Ergebnisse werden gecacht
- Duplikate werden vermieden
- Cache kann manuell geleert werden

### Parallelisierung
- Mehrere Agenten arbeiten parallel
- Konfigurierbar via MAX_CONCURRENT_REQUESTS
- Intelligente Lastverteilung

### Kosten-Optimierung
- Kostenberechnung pro Suche
- Priorisierung günstiger Agenten
- Premium-Agenten nur bei Bedarf

## Erweiterte Features

### Agent Status Dashboard
```python
from src.agents.agent_status import AgentStatusDashboard

dashboard = AgentStatusDashboard(config)
await dashboard.initialize()
print(dashboard.format_status_table())
```

### Manuelle Agent-Auswahl
```python
from src.agents.factory import AgentFactory

# Spezifischen Agenten erstellen
agent = AgentFactory.create_agent("tavily", config)
results = await agent.search_mine(query)
```

### Custom Agent Integration
Neue Agenten können durch Erben von `BaseAgent` hinzugefügt werden:

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def initialize(self) -> bool:
        # Initialisierung
        pass
    
    async def validate_credentials(self) -> bool:
        # Credential-Validierung
        pass
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        # Haupt-Suchlogik
        pass
```

## Troubleshooting

### Agent funktioniert nicht
1. Prüfen Sie den API-Key in .env
2. Führen Sie `test_agent_status.py` aus
3. Prüfen Sie das Error-Log

### Langsame Suchen
1. Prüfen Sie Rate-Limits
2. Reduzieren Sie MAX_CONCURRENT_REQUESTS
3. Nutzen Sie günstigere/schnellere Agenten

### Keine Ergebnisse
1. Prüfen Sie Agent-Verfügbarkeit
2. Erweitern Sie Suchbegriffe
3. Aktivieren Sie mehr Agenten