---
description: Comprehensive provider testing for MineSearch - tests all providers with Quebec mines (Éléonore, Niobec, LaRonde), 5 runs each, with full database validation
allowed-tools: Task, Bash, Read, Write, Edit
---

# Provider Test Command: $ARGUMENTS

Du bist ein spezialisierter Test-Agent für das MineSearch v2 System. Deine Aufgabe ist es, umfassende Provider-Tests durchzuführen mit vollständiger Validierung aller Ergebnisse und Datenbank-Einträge.

## Test-Konfiguration

**Test-Minen (Quebec, Canada):**
- Éléonore (Gold-Mine)
- Niobec (Niobium-Mine) 
- LaRonde (Gold-Mine)

**Test-Parameter:**
- 5 Durchläufe pro Mine und Modell
- Vollständige Quellen-Nutzung (keine Limits)
- Alle verfügbaren Funktionalitäten
- Detaillierte Datenbank-Validierung

## Argument-Verarbeitung

Verarbeite das Argument `$ARGUMENTS`:
- `all` oder leer = Alle verfügbaren Provider testen
- `perplexity` = Nur Perplexity-Provider
- `openrouter` = Nur OpenRouter-Provider  
- `anthropic` = Nur Anthropic-Provider
- `gemini` = Nur Gemini-Provider
- `tavily` = Nur Tavily-Provider
- `exa` = Nur Exa-Provider
- Spezifische Modell-ID = Nur dieses Modell

## Arbeitsschritte

### 1. Vorbereitung
- Analysiere verfügbare Provider basierend auf Argument
- Prüfe API-Keys und Provider-Status
- Erstelle Test-Plan mit Zeitschätzungen
- Stelle sicher, dass ModelBenchmarkService verfügbar ist

### 2. Provider-Analyse
- Liste alle zu testenden Provider und Modelle auf
- Prüfe deren Konfiguration und Verfügbarkeit
- Validiere, dass alle benötigten Services laufen

### 3. Test-Durchführung
**Für jeden Provider/jedes Modell:**
- Starte 5 parallele Suchen für jede der 3 Minen
- Verwende Enhanced Multi-Provider Service wo möglich
- Fallback auf Legacy Service für ältere Provider
- Nutze ALLE verfügbaren Quellen aus der Quellendatenbank
- Dokumentiere jeden Schritt mit Zeitstempel

### 4. Ergebnis-Validierung
**Prüfe für jede Suche:**
- **API-Erfolg:** Response ohne Fehler
- **Daten-Erfolg:** Mindestens 3 gefüllte Felder mit echten Daten
- **Quellen-Nutzung:** Verwendung der Quellendatenbank
- **Strukturierte Daten:** Korrekte Formatierung

### 5. Datenbank-Validierung
**ModelStatistics Tabelle:**
- Korrekte Einträge für alle 15 Suchen (5x3 Minen)
- `run_number` von 1-5 pro Mine
- `success` Boolean korrekt gesetzt
- `response_time_ms` > 0 bei erfolgreichen Suchen
- `fields_found` entspricht tatsächlich gefüllten Feldern
- `sources_count` entspricht genutzten Quellen
- `timestamp` korrekt und realistisch

**FieldStatistics Tabelle:**
- Erfolgsraten nicht überall 0%
- `total_searches` erhöht sich korrekt
- `times_found` vs `times_empty` plausibel
- `success_rate` korrekt berechnet

**FieldConsistency Tabelle:**
- Konsistenz-Scores zwischen 0.0 und 1.0
- `is_consistent` nur True wenn wirklich konsistent
- `most_common_value` repräsentativ

**Sources Tabelle:**
- Neue Quellen korrekt eingetragen
- `last_successful_access` aktualisiert
- `last_attempted_access` bei allen Versuchen

### 6. Qualitäts-Prüfung
**Plausibilitäts-Checks:**
- Koordinaten in realistischen Bereichen für Quebec
- Betreiber-Namen sind echte Unternehmen, nicht "Company A"
- Restaurationskosten in realistischen Größenordnungen
- Aktivitätsstatus entspricht bekanntem Status
- Keine Dummy-Werte wie "$1", "$2", "N/A"

### 7. Fehler-Behandlung
- Bei API-Fehlern: 3 Retry-Versuche
- Bei Timeout: Erhöhe Timeout schrittweise
- Bei Provider-Ausfall: Dokumentiere und überspringe
- Bei Datenbank-Fehlern: Stoppe Test und melde

### 8. Reporting
**Erstelle umfassenden Report:**
- Test-Zusammenfassung mit Erfolgsraten
- Provider-Performance-Vergleich
- Gefundene Probleme und Anomalien
- Datenbank-Validierungs-Ergebnisse
- Empfehlungen für Verbesserungen

## Technische Implementation

### Task-Parallelisierung
- Verwende Task-Tool für parallele Provider-Tests
- Begrenze Parallelität auf max. 5 gleichzeitige Tests
- Implementiere Progress-Tracking

### Fehler-Logging
- Detailliertes Logging aller API-Calls
- Timestamp für jeden Test-Schritt
- Screenshot-ähnliche Datenbank-Snapshots vor/nach Tests

### Performance-Monitoring
- Messe tatsächliche Response-Zeiten
- Überwache Memory-Usage
- Dokumentiere API-Rate-Limits

## Erfolgskriterien

✅ **Test erfolgreich wenn:**
- Alle spezifizierten Provider getestet
- Datenbank-Einträge korrekt und plausibel
- Keine kritischen Fehler oder Exceptions
- Mindestens 60% Datenerfolgrate pro Provider
- Konsistenz-Scores > 0.7 für kritische Felder

❌ **Test fehlgeschlagen wenn:**
- Provider-Tests abgebrochen
- Datenbank-Inkonsistenzen gefunden
- Systematische Dummy-Werte entdeckt
- Kritische API-Fehler ohne Recovery

## Wichtige Hinweise

- **NIEMALS** Dummy-Werte als Erfolg werten
- **IMMER** vollständige Quellendatenbank nutzen
- **SOFORT** stoppen bei kritischen Datenbank-Fehlern
- **DETAILLIERT** jeden ungewöhnlichen Fund dokumentieren

Beginne jetzt mit der Analyse des Arguments `$ARGUMENTS` und erstelle einen detaillierten Test-Plan für die spezifizierten Provider.