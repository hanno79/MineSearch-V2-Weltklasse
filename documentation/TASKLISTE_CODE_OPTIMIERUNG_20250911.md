# TASKLISTE CODE OPTIMIERUNG - MineSearch
**Datum:** 11.09.2025  
**Author:** rahn  
**Version:** 1.0  
**Beschreibung:** Umsetzbare Taskliste für Code-Optimierung basierend auf Audit-Bericht

## Übersicht
Diese Taskliste basiert auf dem `CODE_AUDIT_BERICHT_20250911.md` und strukturiert die Maßnahmen in konkrete, abarbeitbare Tasks.

---

## 🔴 PHASE 0: KRITISCHE FIXES (1-2 Tage)

### Task 0.1: Frontend Environment-Konfiguration reparieren
**Priorität:** KRITISCH  
**Geschätzte Zeit:** 4-6 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **0.1.1** Betroffene Dateien identifizieren
  - `frontend/js/api.js` analysieren
  - Weitere `process.env` Vorkommen suchen
  - Dokumentation der gefundenen Stellen

- [ ] **0.1.2** Lösung implementieren
  - Option A: Build-Tool (Vite/Webpack) Setup
  - Option B: Backend-Config-Endpoint erstellen
  - Frontend-Code entsprechend anpassen

- [ ] **0.1.3** Testing
  - Frontend ohne `process.env` Fehler testen
  - Browser-Konsole auf Fehler prüfen

#### Akzeptanzkriterien:
- ✅ Frontend läuft ohne `process.env` Runtime-Fehler
- ✅ Environment-Variablen korrekt geladen
- ✅ Keine Browser-Konsole-Fehler

---

### Task 0.2: Kritische Syntax-Fehler beheben
**Priorität:** KRITISCH  
**Geschätzte Zeit:** 2-3 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **0.2.1** `batch_broken.py` analysieren
  - Syntax-Fehler identifizieren
  - Entscheidung: Reparieren oder entfernen
  - Import-Abhängigkeiten prüfen

- [ ] **0.2.2** Import-Fehler beheben
  - Selenium-Module prüfen
  - Fehlende Dependencies dokumentieren
  - Linter-Errors reduzieren

#### Akzeptanzkriterien:
- ✅ Keine Syntax-Fehler in Python-Dateien
- ✅ Linter läuft ohne kritische Fehler
- ✅ Import-Pfade funktional

---

### Task 0.3: Environment-Setup vervollständigen
**Priorität:** HOCH  
**Geschätzte Zeit:** 1-2 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **0.3.1** `.env.example` erstellen
  - Alle benötigten Variablen dokumentieren
  - Beispiel-Werte bereitstellen
  - Kommentare für Erklärung

- [ ] **0.3.2** `.gitignore` prüfen
  - `.env` Dateien sicherstellen
  - Backup-Dateien ausschließen
  - Sensible Daten schützen

#### Akzeptanzkriterien:
- ✅ `.env.example` vollständig und verständlich
- ✅ `.gitignore` schützt sensible Daten
- ✅ Setup-Dokumentation aktualisiert

---

## 🟠 PHASE 1: STRUKTURELLE VERBESSERUNGEN (1 Woche)

### Task 1.1: Autor-Header Mass-Insert
**Priorität:** HOCH  
**Geschätzte Zeit:** 3-4 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **1.1.1** Fehlende Header identifizieren
  - Script erstellen: Alle JS/Py-Dateien ohne "Author:" finden
  - Liste der betroffenen Dateien erstellen

- [ ] **1.1.2** Header-Template definieren
  ```python
  """
  Author: rahn
  Datum: [TT.MM.YYYY]
  Version: 1.0
  Beschreibung: [Funktionsbeschreibung]
  """
  ```

- [ ] **1.1.3** Automatisches Script erstellen
  - Python-Script für Mass-Insert
  - Intelligente Beschreibungen basierend auf Dateinamen
  - Backup vor Änderungen

- [ ] **1.1.4** Script ausführen und validieren
  - Alle Dateien prüfen
  - Header-Qualität kontrollieren

#### Akzeptanzkriterien:
- ✅ Alle JS/Py-Skripte haben vollständige Header
- ✅ Header-Format einheitlich
- ✅ Beschreibungen aussagekräftig

---

### Task 1.2: Dateinamen bereinigen (Batch 1)
**Priorität:** HOCH  
**Geschätzte Zeit:** 4-5 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **1.2.1** "final/FINAL" Dateien umbenennen
  - Liste aller `*_final*` Dateien erstellen
  - Umbenennungsplan definieren
  - Import-Referenzen aktualisieren

- [ ] **1.2.2** "fixed" Dateien umbenennen
  - `tests/statistics_tab_fixed_validation.py` → `tests/statistics_tab_validation.py`
  - JSON/PNG-Dateien entsprechend anpassen

- [ ] **1.2.3** "old" Dateien archivieren
  - `frontend/index_old_*` nach `/to_delete` verschieben
  - Oder in `frontend/archive/` ablegen

- [ ] **1.2.4** "backup" Dateien organisieren
  - Aktuelle Backups (<30 Tage) behalten
  - Ältere nach `/to_delete` verschieben
  - Backup-Strategie dokumentieren

#### Akzeptanzkriterien:
- ✅ Keine `*_final*`, `*_fixed*`, `*_old*` Namen in produktiven Ordnern
- ✅ Import-Referenzen funktional
- ✅ Backup-Strategie klar definiert

---

### Task 1.3: Top 5 übergroße Dateien refaktorisieren
**Priorität:** HOCH  
**Geschätzte Zeit:** 2-3 Tage  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **1.3.1** `frontend/data-cards.js` (2.473 Zeilen)
  - Logische Module identifizieren
  - Card-Rendering, Event-Handling, Utilities trennen
  - Neue Dateien: `data-cards-renderer.js`, `data-cards-events.js`, `data-cards-utils.js`

- [ ] **1.3.2** `frontend/display.js` (2.408 Zeilen)
  - Display-Logic, UI-Updates, Formatting trennen
  - Neue Dateien: `display-manager.js`, `ui-updater.js`, `formatter.js`

- [ ] **1.3.3** `frontend/search.js` (1.990 Zeilen)
  - Search-Logic, API-Calls, Result-Processing trennen
  - Neue Dateien: `search-engine.js`, `search-api.js`, `result-processor.js`

- [ ] **1.3.4** `backend/minesearch/data_extraction.py` (1.358 Zeilen)
  - Extraction-Logic, Validation, Normalization trennen
  - Neue Module: `extraction_core.py`, `extraction_validators.py`, `extraction_normalizers.py`

- [ ] **1.3.5** `backend/minesearch/extraction_processors.py` (1.085 Zeilen)
  - Processor-Classes, Utilities, Config trennen
  - Neue Module: `processors_core.py`, `processors_utils.py`, `processors_config.py`

#### Akzeptanzkriterien:
- ✅ Alle neuen Dateien <500 Zeilen
- ✅ Funktionalität unverändert
- ✅ Tests angepasst und funktional
- ✅ Import-Pfade aktualisiert

---

### Task 1.4: JS-Teststruktur vereinheitlichen
**Priorität:** HOCH  
**Geschätzte Zeit:** 3-4 Stunden  
**Abhängigkeiten:** Task 1.2

#### Subtasks:
- [ ] **1.4.1** Test-Dateien identifizieren
  - Alle JS-Tests im Root/`frontend` finden
  - Kategorisierung: Unit, Integration, E2E

- [ ] **1.4.2** Test-Ordnerstruktur erstellen
  ```
  tests/
  ├── unit/
  │   ├── frontend/
  │   └── backend/
  ├── integration/
  │   ├── frontend/
  │   └── backend/
  └── e2e/
      ├── frontend/
      └── backend/
  ```

- [ ] **1.4.3** Tests verschieben und umbenennen
  - Alle Tests nach `tests/` verschieben
  - Benennung: `*_test.js` Schema
  - Import-Pfade anpassen

- [ ] **1.4.4** Redundante Tests konsolidieren
  - Ähnliche "final/comprehensive" Tests zusammenführen
  - Test-Coverage prüfen

#### Akzeptanzkriterien:
- ✅ Alle JS-Tests unter `tests/`
- ✅ Einheitliche `*_test.js` Benennung
- ✅ Keine redundanten Test-Varianten
- ✅ Test-Runner funktional

---

### Task 1.5: Dummy/Fallback-Audit durchführen
**Priorität:** MITTEL  
**Geschätzte Zeit:** 2-3 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **1.5.1** Fallback-Stellen identifizieren
  - Alle "DUMMY/FALLBACK" Vorkommen analysieren
  - Kontext und Verwendung dokumentieren

- [ ] **1.5.2** Kennzeichnung prüfen
  - Sichtbare Markierung in UI vorhanden?
  - WARNUNG-Logging implementiert?
  - Kommentare im Code vorhanden?

- [ ] **1.5.3** Stille Fallbacks entfernen
  - Unmarkierte Fallbacks identifizieren
  - Entweder kennzeichnen oder entfernen
  - Proper Error Handling implementieren

#### Akzeptanzkriterien:
- ✅ Alle Fallbacks sichtbar gekennzeichnet
- ✅ WARNUNG-Logs bei Fallback-Nutzung
- ✅ Keine stillen Fallbacks
- ✅ Proper Error Handling

---

## 🟡 PHASE 2: QUALITÄTSSICHERUNG (2 Wochen)

### Task 2.1: Linter-Fixes implementieren
**Priorität:** MITTEL  
**Geschätzte Zeit:** 1-2 Tage  
**Abhängigkeiten:** Task 1.3

#### Subtasks:
- [ ] **2.1.1** Linter-Report analysieren
  - Aktuelle Fehler kategorisieren
  - Prioritäten definieren

- [ ] **2.1.2** Format-Fixes
  - Trailing Whitespace entfernen
  - Line Length anpassen
  - Import-Order korrigieren

- [ ] **2.1.3** Code-Quality-Fixes
  - Unused Imports entfernen
  - Unused Variables bereinigen
  - Code-Duplikation reduzieren

- [ ] **2.1.4** CI-Integration
  - Linter in CI-Pipeline integrieren
  - Pre-commit Hooks einrichten

#### Akzeptanzkriterien:
- ✅ Linter läuft ohne Fehler
- ✅ CI-Pipeline mit Linter-Gates
- ✅ Pre-commit Hooks aktiv

---

### Task 2.2: Backup-Strategie umsetzen
**Priorität:** NIEDRIG  
**Geschätzte Zeit:** 2-3 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **2.2.1** Backup-Policy definieren
  - Retention-Zeit: 30 Tage
  - Archivierung: `/to_delete` oder `/archive`
  - Automatisierung: Script für Rotation

- [ ] **2.2.2** Alte Backups bereinigen
  - Backups >30 Tage identifizieren
  - Nach `/to_delete` verschieben
  - Dokumentation aktualisieren

- [ ] **2.2.3** Backup-Script erstellen
  - Automatische Rotation
  - Logging der Aktionen
  - Cron-Job Setup

#### Akzeptanzkriterien:
- ✅ Klare Backup-Policy dokumentiert
- ✅ Alte Backups archiviert
- ✅ Automatisierung funktional

---

### Task 2.3: Änderungsdokumentation ergänzen
**Priorität:** NIEDRIG  
**Geschätzte Zeit:** 2-3 Stunden  
**Abhängigkeiten:** Task 1.1

#### Subtasks:
- [ ] **2.3.1** Fehlende Änderungslogs identifizieren
  - Dateien ohne "ÄNDERUNG TT.MM.JJJJ" finden
  - Letzte Änderungen analysieren

- [ ] **2.3.2** Änderungslogs ergänzen
  - Template für Änderungsdokumentation
  - Mass-Insert für fehlende Logs
  - Qualität kontrollieren

- [ ] **2.3.3** CHANGELOG.txt erstellen
  - Zentrale Änderungsdokumentation
  - Chronologische Auflistung
  - Kategorisierung: Bugfix, Feature, Refactor

#### Akzeptanzkriterien:
- ✅ Alle geänderten Dateien dokumentiert
- ✅ CHANGELOG.txt aktuell
- ✅ Änderungsformat einheitlich

---

### Task 2.4: Dependency-Audit durchführen
**Priorität:** MITTEL  
**Geschätzte Zeit:** 1-2 Stunden  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **2.4.1** Python Dependencies prüfen
  - `requirements.txt` analysieren
  - Security-Vulnerabilities scannen
  - Updates verfügbar?

- [ ] **2.4.2** Node Dependencies prüfen
  - `package.json` aufräumen
  - Autor, Scripts, Lockfile-Policy
  - Security-Scan durchführen

- [ ] **2.4.3** Dependency-Update-Plan
  - Sichere Updates identifizieren
  - Breaking Changes dokumentieren
  - Update-Strategie definieren

#### Akzeptanzkriterien:
- ✅ Alle Dependencies aktuell und sicher
- ✅ `package.json` vollständig
- ✅ Update-Strategie dokumentiert

---

## 🟢 PHASE 3: OPTIMIERUNG (1 Monat)

### Task 3.1: Performance-Monitoring implementieren
**Priorität:** NIEDRIG  
**Geschätzte Zeit:** 1-2 Tage  
**Abhängigkeiten:** Task 1.3

#### Subtasks:
- [ ] **3.1.1** Performance-Critical-Paths identifizieren
  - Große Dateien analysieren
  - Bottlenecks dokumentieren

- [ ] **3.1.2** Timing-Logs implementieren
  - Funktionen >5s messen
  - Performance-Metriken sammeln
  - Dashboard erstellen

- [ ] **3.1.3** Monitoring-System
  - Alerts bei Performance-Problemen
  - Regelmäßige Reports
  - Trend-Analyse

#### Akzeptanzkriterien:
- ✅ Performance-Monitoring aktiv
- ✅ Alerts bei Problemen
- ✅ Regelmäßige Reports

---

### Task 3.2: Dokumentation konsolidieren
**Priorität:** NIEDRIG  
**Geschätzte Zeit:** 1 Tag  
**Abhängigkeiten:** Keine

#### Subtasks:
- [ ] **3.2.1** Dokumentationsstruktur analysieren
  - `documentation/` Ordner prüfen
  - Redundanzen identifizieren

- [ ] **3.2.2** "FINAL_*" Reports umbenennen
  - Versionierte Namen verwenden
  - Chronologische Sortierung
  - Index erstellen

- [ ] **3.2.3** Dokumentationsstandards
  - Template für neue Docs
  - Review-Prozess definieren
  - Wartung automatisieren

#### Akzeptanzkriterien:
- ✅ Dokumentation strukturiert
- ✅ Keine "FINAL_*" Namen
- ✅ Standards dokumentiert

---

## 📊 FORTSCHRITTS-TRACKING

### Wöchentliche Reviews
- [ ] **Woche 1:** Phase 0 + Task 1.1-1.2 abgeschlossen
- [ ] **Woche 2:** Task 1.3-1.5 abgeschlossen
- [ ] **Woche 3:** Phase 2 Tasks abgeschlossen
- [ ] **Woche 4:** Phase 3 Tasks abgeschlossen

### Erfolgsmetriken
- [ ] **Kurzfristig (1 Woche):**
  - ✅ Keine Dateien >500 Zeilen
  - ✅ Keine `*_final*`, `*_fixed*` Namen
  - ✅ Alle Tests unter `tests/`
  - ✅ Frontend läuft ohne `process.env` Fehler

- [ ] **Mittelfristig (1 Monat):**
  - ✅ Alle Skripte haben vollständige Header
  - ✅ Linter-Reports sauber
  - ✅ Backup-Strategie implementiert
  - ✅ Änderungsdokumentation vollständig

- [ ] **Langfristig (3 Monate):**
  - ✅ Monitoring/Performance-Logs aktiv
  - ✅ Dokumentation konsolidiert
  - ✅ CI/CD Pipeline mit Qualitätsgates
  - ✅ Regelmäßige Code-Reviews

---

## 🚀 NÄCHSTE SCHRITTE

1. **Sofort starten:** Task 0.1 (Frontend Environment)
2. **Parallel:** Task 0.2 (Syntax-Fehler)
3. **Danach:** Task 1.1 (Autor-Header)
4. **Wöchentlich:** Review und Anpassung

### Ressourcen
- **Entwickler:** 1-2 Personen
- **Zeit:** 2-4 Wochen für komplette Umsetzung
- **Tools:** IDE, Linter, Git, CI/CD

### Risiken
- **Refactoring:** Funktionalität könnte beeinträchtigt werden
- **Testing:** Umfangreiche Tests erforderlich
- **Zeit:** Schätzungen könnten unterschritten werden

### Mitigation
- **Backup:** Vor jeder größeren Änderung
- **Testing:** Nach jedem Task
- **Review:** Wöchentliche Checkpoints
- **Rollback:** Plan für Rückgängigmachung

---

**Erstellt:** 11.09.2025  
**Nächste Review:** 18.09.2025  
**Status:** Bereit für Umsetzung
