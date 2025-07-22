# MineSearch v2.1 - API & Database Investigation Tests

**Author:** rahn  
**Datum:** 16.07.2025  
**Version:** 1.0

## Übersicht

Diese Tests wurden entwickelt, um die API-Endpoints und Datenbankanzeigeprobleme in MineSearch v2.1 zu untersuchen. Das Hauptproblem sind "Zeros" oder "No data" Anzeigen in der Datenbank-Statistik, obwohl Daten vorhanden sein sollten.

## Verfügbare Tests

### 1. Quick API Diagnosis (`quick_api_diagnosis.js`)
**Zweck:** Schnelle erste Diagnose der API-Endpoints  
**Dauer:** ~2-3 Minuten  
**Ausgabe:** Console-Log mit Status aller APIs

```bash
npx playwright test quick_api_diagnosis.js
```

### 2. Comprehensive Investigation (`comprehensive_api_database_investigation.js`)
**Zweck:** Vollständige Analyse aller Aspekte  
**Dauer:** ~10-15 Minuten  
**Ausgabe:** Detaillierte Reports und Screenshots

```bash
./run_investigation.sh
```

## Voraussetzungen

### Backend muss laufen
```bash
cd ../../backend
python main.py
```

### Node.js und npm installiert
```bash
node --version
npm --version
```

## Installation

```bash
# In diesem Verzeichnis
npm install
npx playwright install
```

## Verwendung

### Option 1: Schnelle Diagnose (Empfohlen für ersten Check)
```bash
npx playwright test quick_api_diagnosis.js
```

### Option 2: Vollständige Investigation
```bash
./run_investigation.sh
```

### Option 3: Manuelle Ausführung
```bash
# Vollständige Tests
npx playwright test comprehensive_api_database_investigation.js

# Mit Browser-Anzeige (für Debugging)
npx playwright test comprehensive_api_database_investigation.js --headed

# Debug-Modus
npx playwright test comprehensive_api_database_investigation.js --debug
```

## Ausgabe-Struktur

```
tests/integration_tests/
├── test-reports/                          # Markdown & JSON Reports
│   ├── minesearch_investigation_report_*.md
│   └── minesearch_investigation_data_*.json
├── test-screenshots/                      # Screenshots aller UI-Zustände
│   ├── api_*_response.png
│   ├── frontend_main_page.png
│   ├── field_statistics_display.png
│   └── field_comparison_display.png
└── playwright-report/                     # HTML-Report
    └── index.html
```

## Getestete Bereiche

### API-Endpoints
- `/api/sources/grouped` - Gruppierte Quellen
- `/api/results` - Suchergebnisse
- `/api/benchmark/summary` - Benchmark-Übersicht
- `/api/benchmark/field-statistics` - Feld-Statistiken
- `/api/benchmark/field-comparison` - Feld-Vergleiche
- `/api/models` - Verfügbare Modelle

### Frontend-Funktionen
- Tab-Navigation (Main Search, Batch Search, Database)
- Button-Klicks (Field Statistics, Field Comparison)
- Netzwerk-Request-Überwachung
- Console-Fehler-Erkennung

### Spezifische Probleme
- **Zeros-Problem:** Überprüfung warum Statistiken "0" anzeigen
- **No Data:** Identifikation fehlender Daten in APIs
- **UI-Responsivität:** Reagieren Buttons korrekt
- **API-Connectivity:** Sind alle Endpoints erreichbar

## Erwartete Ergebnisse

### Bei funktionierendem System
- Alle APIs geben Status 200 zurück
- APIs liefern JSON-Daten mit tatsächlichen Werten
- UI-Buttons sind klickbar und lösen API-Calls aus
- Keine Console-Fehler

### Bei defektem System (aktueller Zustand)
- APIs geben Status 200 zurück (erreichbar)
- APIs liefern JSON mit Null-Werten oder leeren Objekten
- UI zeigt "0" oder "No data" an
- Mögliche Console-Fehler bei Datenverarbeitung

## Debugging-Tipps

### 1. API-Probleme
```bash
# Teste API direkt
curl http://localhost:8000/api/benchmark/field-statistics
```

### 2. Frontend-Probleme
- Öffne Browser-Developer-Tools
- Schaue in Network-Tab für Failed-Requests
- Prüfe Console für JavaScript-Fehler

### 3. Datenbank-Probleme
```bash
# Prüfe Datenbankinhalt direkt
cd ../../backend
python -c "
import sqlite3
conn = sqlite3.connect('mines.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM search_results')
print('Search Results:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM field_statistics')
print('Field Statistics:', cursor.fetchone()[0])
"
```

## Häufige Probleme

### Backend läuft nicht
```bash
cd ../../backend
python main.py
```

### Node.js fehlt
```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS
brew install node
```

### Playwright-Browser fehlen
```bash
npx playwright install
```

### Permissions-Fehler
```bash
chmod +x run_investigation.sh
```

## Report-Interpretation

### Markdown-Report
- **🟢 Funktionierende Features:** Was funktioniert korrekt
- **🔴 Defekte Features:** Was ist kaputt
- **💡 Empfehlungen:** Konkrete Lösungsvorschläge

### JSON-Report
- Vollständige Rohdaten für programmatische Analyse
- Netzwerk-Requests mit Timing
- Console-Fehler mit Timestamps
- UI-Interaktions-Details

### Screenshots
- Visuelle Dokumentation des Zeros-Problems
- Vor/Nach-Zustand von UI-Interaktionen
- API-Response-Ansichten

## Nächste Schritte nach Investigation

1. **Wenn APIs keine Daten liefern:**
   - Prüfe Backend-Datenbankabfragen
   - Validiere Datenbank-Schema
   - Teste SQL-Queries manuell

2. **Wenn APIs Daten liefern, aber UI zeigt Zeros:**
   - Prüfe Frontend-JavaScript-Datenverarbeitung
   - Validiere JSON-Parsing
   - Teste UI-Rendering-Logik

3. **Wenn Console-Fehler auftreten:**
   - Analysiere JavaScript-Fehler
   - Prüfe API-Response-Format
   - Validiere Frontend-Backend-Kommunikation

## Support

Bei Fragen oder Problemen:
1. Prüfe die generierten Reports
2. Schaue dir Screenshots an
3. Analysiere Console-Ausgaben
4. Teste APIs manuell mit curl

Die Tests sind designed, um das Root-Cause-Problem zu identifizieren und konkrete Lösungswege aufzuzeigen.