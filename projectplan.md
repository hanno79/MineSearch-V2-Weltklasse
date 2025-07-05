"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Detaillierter Plan für Code-Bereinigung MineSearch v2
"""

# Code-Bereinigungsplan für MineSearch v2

## 🎯 Ziele
- Version 1 spezifischen Code entfernen
- Code-Basis gemäß CLAUDE.md Regeln bereinigen
- Strukturelle Verbesserungen durchführen
- Performance und Wartbarkeit verbessern

## 📊 Analyse-Ergebnisse

### Version 2 Architektur
- **Frontend**: HTMX-basiert (index.html, sources.html, style.css)
- **Backend**: FastAPI mit Multi-Provider-System
- **Provider**: 8 Provider (5 aktiv, 3 deaktiviert)
- **Datenbank**: SQLite mit strukturiertem Schema

### Identifizierte Probleme

#### 1. Dateigrößen-Verstöße (Regel 1)
- `search_service_multi.py`: 1102 Zeilen ❌
- `firecrawl_provider.py`: 834 Zeilen ❌
- `brightdata_provider.py`: 724 Zeilen ❌
- `perplexity_provider.py`: 627 Zeilen ❌
- `config.py`: 627 Zeilen ❌
- `data_extraction.py`: 571 Zeilen ❌
- `index.html`: 570 Zeilen ❌
- `abacus_provider.py`: 547 Zeilen ❌
- `enhanced_source_discovery.py`: 542 Zeilen ❌

#### 2. Strukturelle Probleme
- 16 Test-Dateien liegen direkt in `/backend/` statt in `/tests/`
- `data_extraction_old.py` sollte nach `to_delete` verschoben werden
- Fehlender `/config/` Ordner für Konfigurationsdateien

#### 3. Version 1 Überbleibsel
- Kompletter `/v1_backup/` Ordner (kann entfernt werden)
- Verweise auf alte Agenten-Struktur in Kommentaren
- Alte Import-Statements die nicht mehr benötigt werden

## 📋 Aufgaben-Plan

### Phase 1: Strukturelle Bereinigung (Priorität: Hoch)

1. **Test-Dateien verschieben**
   - [ ] Erstelle `/backend/tests/` Ordner
   - [ ] Verschiebe alle test_*.py Dateien nach `/backend/tests/`
   - [ ] Aktualisiere Import-Pfade in Test-Dateien

2. **Veraltete Dateien entfernen**
   - [ ] Verschiebe `data_extraction_old.py` nach `/backend/to_delete/`
   - [ ] Entferne `/v1_backup/` Ordner komplett
   - [ ] Bereinige `/backend/archived_tests/` (prüfen ob noch benötigt)

3. **Config-Struktur**
   - [ ] Erstelle `/backend/config/` Ordner
   - [ ] Teile `config.py` in kleinere Module auf:
     - `base_config.py`: Basis-Konfiguration
     - `provider_config.py`: Provider-spezifische Configs
     - `extraction_config.py`: Extraktions-Patterns und Regeln

### Phase 2: Datei-Refactoring (Priorität: Hoch)

1. **search_service_multi.py (1102 → <500 Zeilen)**
   - [ ] Extrahiere `SourceAggregator` in eigene Datei
   - [ ] Erstelle `search_phases.py` für Phasen-Logik
   - [ ] Erstelle `search_utils.py` für Helper-Funktionen
   - [ ] Behalte nur Haupt-Service-Klasse in Hauptdatei

2. **Provider-Refactoring**
   - [ ] Erstelle `providers/utils/` Ordner
   - [ ] Extrahiere gemeinsame Provider-Funktionen
   - [ ] Reduziere Code-Duplikation zwischen Providern

3. **data_extraction.py (571 → <500 Zeilen)**
   - [ ] Validierungs-Logik ist bereits ausgelagert ✓
   - [ ] Weitere Helper-Funktionen in `extraction_utils.py` auslagern

### Phase 3: Code-Qualität (Priorität: Mittel)

1. **Exception Handling verbessern**
   - [ ] Ersetze generische `except Exception:` durch spezifische Exceptions
   - [ ] Entferne `except: pass` Statements
   - [ ] Implementiere einheitliches Error-Logging

2. **Performance-Optimierungen**
   - [ ] Implementiere Connection-Pooling für API-Calls
   - [ ] Optimiere Batch-Processing
   - [ ] Verbessere Caching-Strategie

3. **Code-Dokumentation**
   - [ ] Füge fehlende Docstrings hinzu
   - [ ] Aktualisiere veraltete Kommentare
   - [ ] Erstelle API-Dokumentation

### Phase 4: Frontend-Bereinigung (Priorität: Niedrig)

1. **index.html aufteilen**
   - [ ] Extrahiere JavaScript in separate Datei
   - [ ] Erstelle HTML-Templates für wiederkehrende Elemente
   - [ ] Optimiere CSS-Organisation

## 🚀 Durchführungsplan

### Woche 1: Strukturelle Bereinigung
- Tag 1-2: Test-Reorganisation und veraltete Dateien
- Tag 3-4: Config-Refactoring
- Tag 5: Tests und Validierung

### Woche 2: Datei-Refactoring
- Tag 1-2: search_service_multi.py aufteilen
- Tag 3-4: Provider-Refactoring
- Tag 5: data_extraction.py und Tests

### Woche 3: Qualitätsverbesserungen
- Tag 1-2: Exception Handling
- Tag 3-4: Performance-Optimierungen
- Tag 5: Dokumentation und Abschluss

## ✅ Erfolgs-Kriterien
- Alle Dateien < 500 Zeilen
- Keine Version 1 spezifischen Dateien mehr
- Saubere Ordnerstruktur gemäß Regel 6
- Alle Tests laufen erfolgreich
- Performance gleich oder besser als vorher

## 🔍 Überprüfung
Nach jeder Phase:
1. Führe alle Tests aus
2. Prüfe Funktionalität im Browser
3. Validiere Dateigrößen mit Skript
4. Dokumentiere Änderungen

## 📝 Notizen
- Version 2 ist bereits gut strukturiert und funktional
- Fokus auf Wartbarkeit und CLAUDE.md Compliance
- Keine funktionalen Änderungen, nur Refactoring
- Bei Unsicherheit: Backup erstellen

## 🎉 ABGESCHLOSSENE AUFGABEN (05.07.2025)

### Phase 1: Strukturelle Bereinigung ✅
1. **Test-Dateien reorganisiert**
   - Alle test_*.py Dateien von /backend/ nach /backend/tests/ verschoben
   - 16 Test-Dateien erfolgreich migriert

2. **Alte Dateien entfernt**
   - data_extraction_old.py nach to_delete verschoben
   - /v1_backup/ komplett entfernt
   - config_old.py nach to_delete verschoben

### Phase 2: Code-Refactoring ✅
1. **search_service_multi.py refactoriert** (1102 → 497 Zeilen)
   - source_aggregator.py erstellt
   - search_phases.py erstellt
   - search_utils.py erstellt
   - search_result_combiner.py erstellt
   - search_async_utils.py erstellt
   - shared_sources_analyzer.py erstellt

2. **Provider refactoriert**
   - **firecrawl_provider.py** (834 → 445 Zeilen)
     - /providers/utils/firecrawl_utils.py erstellt
     - /providers/utils/firecrawl_url_builder.py erstellt
     - /providers/utils/firecrawl_api_client.py erstellt
   
   - **brightdata_provider.py** (724 → 485 Zeilen)
     - /providers/utils/brightdata_utils.py erstellt
     - /providers/utils/brightdata_api_client.py erstellt
     - /providers/utils/brightdata_search_utils.py erstellt
     - /providers/utils/brightdata_scraper.py erstellt

3. **config.py aufgeteilt** (639 → 36 Zeilen)
   - /config/ Ordner erstellt
   - config/base.py - Basis-Konfiguration
   - config/api_keys.py - API Keys
   - config/providers.py - Provider-Konfiguration
   - config/models.py - Model-Definitionen
   - config/country_config.py - Länderspezifische Konfiguration
   - config/source_sharing.py - Source Sharing & Cache Config

### NOCH AUSSTEHEND
- Phase 3: Code-Qualität (Exception Handling, Performance, Dokumentation)
- Phase 4: Frontend-Bereinigung (index.html aufteilen)