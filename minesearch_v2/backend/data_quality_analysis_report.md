# Data Quality Analysis - Platzhalter Pattern Detection Report

**Author:** Data-Quality-Analyst Agent  
**Datum:** 06.08.2025  
**Task:** Analyse von Platzhalter-Mustern in konsolidierten Ergebnissen

## Executive Summary

Die Analyse identifizierte **kritische Platzhalter-Muster** im System, die durch den Best-Value-Algorithmus **nicht erkannt** werden. Insbesondere CSV-Spalten-Template-Werte werden als "echte Daten" behandelt.

## Findings Overview

### 1. CSV_COLUMNS Template-Werte als Platzhalter

**KRITISCH:** Die CSV_COLUMNS Definition enthält Template-Beispiele:

```python
# /app/minesearch_v2/backend/config/base.py:22-23
'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
'Minentyp (Untertage/ Open-Pit/ usw.)',
```

**Problem:** Diese Template-Texte werden von AI-Modellen als "echte Werte" zurückgegeben.

**Datenbank-Findings:**
- 15 Einträge mit Pattern "usw.)"
- 15 Einträge mit Pattern "Gold/ Kupfer/ Kohle/ usw.)"
- 15 Einträge mit Pattern "Untertage/ Open-Pit/ usw.)"

### 2. Best-Value-Algorithmus Gap

**Location:** `/app/minesearch_v2/backend/api/routes/consolidated_results.py:204`

**Current Logic:**
```python
if display_val in ['X', 'N/A', 'UNBEKANNT', 'KEINE ANGABEN', 'NICHT VERFÜGBAR', '']:
    non_x_bonus = 0  # Keine Bonus für Platzhalter-Werte
else:
    non_x_bonus = 10.0  # Erhöhter Bonus für echte Daten
```

**Gap:** Template-Werte wie "Untertage/ Open-Pit/ usw.)" werden als "echte Daten" bewertet!

### 3. Platzhalter-Pattern Inventory

#### Template-artige Strukturen:
- `"(Gold/ Kupfer/ Kohle/ usw.)"`
- `"(Untertage/ Open-Pit/ usw.)"`  
- `"Feld1/ Feld2/ usw.)"`

#### Feldname-als-Inhalt Pattern:
- AI-Modelle geben den Feldnamen selbst als Wert zurück
- Beispiel: Feld "Minentyp" enthält Wert "Minentyp (Untertage/ Open-Pit/ usw.)"

#### Generische Endungen:
- Pattern `/ usw.)`
- Pattern `/ etc.)`
- Pattern `etc.)` (0 Einträge aktuell)

### 4. Extraction-System Analysis

**Positive:** Das System hat bereits Pattern-Recognition für template-Werte:

```python
# /app/minesearch_v2/backend/enhanced_extraction_patterns.py:117
r'(?:Minentyp\s*)?(?:\(Untertage/\s*Open-Pit/\s*usw\.\))?\s*:?\s*(Open-Pit|Tagebau|Underground|Untertage|Surface|Strip\s+mine|Quarry|Steinbruch)',
```

**Gap:** Aber diese Pattern greifen nicht bei direkten Template-Rückgaben.

### 5. Validation System Gap

**Current Placeholder Detection** (`extraction_validators.py:15`):
- Erkennt "k.a.", "n/a", "unbekannt" etc.
- **Erkennt NICHT** Template-Strukturen mit "usw.)"

**Missing Pattern:**
```python
# FEHLT: Template-Pattern Recognition
if re.search(r'/ usw\.\)$', value):
    logger.debug(f"[PLACEHOLDER] '{value}' ist Template-Struktur")
    return True
```

## Root Cause Analysis

### 1. Provider-Level Issue
AI-Provider interpretieren CSV-Spalten-Namen als Anweisungen:
- Spalte: `"Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)"`
- AI-Antwort: `"Gold/ Kupfer/ Kohle/ usw.)"`

### 2. Validation Gap
- `is_placeholder_value()` prüft nicht auf Template-Strukturen
- Best-Value-Algorithmus bevorzugt Template-Werte (non_x_bonus = 10.0)

### 3. Extraction Gap
- Enhanced patterns greifen nur bei Präfix-Strukturen
- Nicht bei direkten Template-Rückgaben

## Impact Assessment

### Data Quality Impact:
- **15 Minen** mit Template-Platzhaltern in kritischen Feldern
- **Minentyp** und **Rohstoffabbau** besonders betroffen
- Frontend zeigt Template-Text statt "Unbekannt"

### User Experience Impact:
- Nutzer sehen `"Gold/ Kupfer/ Kohle/ usw.)"` als scheinbar valide Daten
- Verwirrung über Datenqualität
- Falsche Interpretation von Mining-Daten

## Recommendations

### 1. URGENT: Best-Value-Algorithmus Enhancement
```python
# Erweitere _calculate_best_value() um Template-Pattern
if re.search(r'/ usw\.\)$|/ etc\.\)$', display_val):
    template_penalty = -50.0  # Starker Malus für Templates
```

### 2. URGENT: Validation Enhancement
```python
# Erweitere is_placeholder_value() um Template-Recognition
template_patterns = [
    r'/ usw\.\)$',
    r'/ etc\.\)$', 
    r'\(.*/ .* usw\.\)',
    r'Gold/ Kupfer/ Kohle/ usw\.\)'
]
```

### 3. MEDIUM: CSV_COLUMNS Redesign
Entferne Template-Beispiele aus Feldnamen:
- `'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'` → `'Rohstoffabbau'`
- `'Minentyp (Untertage/ Open-Pit/ usw.)'` → `'Minentyp'`

### 4. MEDIUM: Provider Prompt Enhancement
Anti-Template-Instruktionen für alle Provider:
```
CRITICAL: Do not return field name examples like "(Gold/ Kupfer/ Kohle/ usw.)"
If no data found, leave field EMPTY, not template text!
```

## Technical Implementation Plan

### Phase 1: Immediate Fix (Backend-Specialist)
1. Erweitere `_calculate_best_value()` um Template-Pattern-Detection
2. Erweitere `is_placeholder_value()` um Template-Recognition
3. Deploy + Test mit aktuellen Daten

### Phase 2: System Enhancement
1. CSV_COLUMNS Feldnamen-Bereinigung
2. Provider-Prompt-Updates
3. Enhanced extraction pattern für Template-Strukturen

### Phase 3: Verification
1. Re-Test aller 15 betroffenen Minen
2. Verify Best-Value-Algorithmus bevorzugt echte Daten
3. Frontend-Test für korrekte "Unbekannt"-Anzeige

## Test Cases für Backend-Specialist

### Test Case 1: Template Pattern Detection
```python
assert is_placeholder_value("Gold/ Kupfer/ Kohle/ usw.)", "Rohstoffabbau") == True
assert is_placeholder_value("Untertage/ Open-Pit/ usw.)", "Minentyp") == True
```

### Test Case 2: Best-Value Template Penalty  
```python
# Template-Wert sollte niedriger score haben als echte Daten
template_value = "Gold/ Kupfer/ Kohle/ usw.)"
real_value = "Gold"
# real_value sollte höheren score haben
```

### Test Case 3: Konsolidierte Ergebnisse
```python
# Nach Fix: Template-Werte sollten als "Unbekannt" erscheinen
# Nicht als scheinbar valide Daten
```

## Monitoring Recommendations

### 1. Template-Pattern-Monitoring
Query für kontinuierliche Überwachung:
```sql
SELECT COUNT(*) FROM search_results 
WHERE structured_data LIKE '%/ usw.)%'
```

### 2. Data Quality Metrics
- Prozentualer Anteil Template-Werte pro Provider
- Trend-Monitoring nach Provider-Updates

### 3. User Feedback Integration
- Frontend-Feedback für "verdächtige" Werte
- User kann Template-Werte melden

## Conclusion

Das System hat eine **kritische Lücke** in der Platzhalter-Erkennung. Template-Strukturen aus CSV-Feldnamen werden als valide Daten behandelt und vom Best-Value-Algorithmus bevorzugt.

**Priorität: URGENT** - Betrifft Datenqualität und User Experience direkt.

**Nächste Schritte:** Backend-Specialist implementiert Enhanced Template-Pattern-Detection in Best-Value-Algorithmus und Validation-System.

---

**Report Ende** - Alle kritischen Platzhalter-Muster identifiziert und Lösungsweg definiert.