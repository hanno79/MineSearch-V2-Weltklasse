"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Dokumentation der Active Source Crawling Implementation
"""

# Active Source Crawling Implementation

## Problem
- 42 Quellen wurden "entdeckt" aber 0 tatsächlich durchsucht
- Perplexity erhielt nur "Hinweise" auf Quellen, crawlte sie aber nicht aktiv
- Deep Research dauerte nur 27 Sekunden statt 30+ Minuten

## Lösung: Aktives Source Crawling

### 1. WebFetchService (web_fetch_service.py)
- Aktives Abrufen und Analysieren von Webseiten
- BeautifulSoup für HTML-Parsing
- Kontextuelle Suche nach Mine-spezifischen Informationen
- Extraktion von:
  - Restaurationskosten / Closure Costs
  - Betreiber / Operator
  - Koordinaten
  - Rohstoffe / Commodities
  - Produktionsdaten
  - Status (aktiv/geschlossen)
  - PDF-Links

### 2. Enhanced Source Discovery (enhanced_source_discovery.py)
- Neue Methode: `actively_search_sources()`
- Paralleles Crawling (max 5 gleichzeitig)
- Tracking aller durchsuchten Quellen
- Session-Updates für korrekte Statistiken

### 3. Search Service Integration (search_service.py)
- Bei Deep Research: Automatisches aktives Crawling der Top 10 Quellen
- Crawl-Ergebnisse werden in Perplexity-Prompt integriert
- Two-Phase nutzt ebenfalls aktives Crawling

### 4. Session Tracking Verbesserungen (models.py)
- Korrekte Zählung von durchsuchten vs. erfolgreichen Quellen
- Status-Updates möglich (failed → successful)
- Genauere Statistiken

## Erwartete Verbesserungen

### Vorher:
- 42 Quellen entdeckt, 0 durchsucht
- Suche dauert 27 Sekunden
- Wenige konkrete Daten gefunden

### Nachher:
- 42 Quellen entdeckt, 10-20 aktiv durchsucht
- Deep Research dauert wirklich 30+ Minuten
- Deutlich mehr Daten durch aktives Crawling
- PDFs werden identifiziert (Download noch nicht implementiert)

## Nächste Schritte

1. **PDF-Download und Analyse**:
   - PDFs herunterladen
   - Text extrahieren
   - Nach Schlüsselinformationen suchen

2. **GESTIM-Integration**:
   - Direkte API-Aufrufe
   - Spezifisches Parsing

3. **Performance-Optimierung**:
   - Mehr parallele Anfragen
   - Intelligentere Priorisierung
   - Caching von Ergebnissen

4. **Erweiterte Datenextraktion**:
   - Tabellen aus HTML extrahieren
   - Strukturierte Daten erkennen
   - Mehrsprachige Unterstützung