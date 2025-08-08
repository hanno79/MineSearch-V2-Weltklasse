# MINESEARCH V2 - DETAILLIERTE DATENBANKANALYSE

**Author:** rahn  
**Datum:** 26.07.2025  
**Version:** 1.0  
**Analysezeitpunkt:** 26.07.2025 16:00:25  

---

## ZUSAMMENFASSUNG DER ERKENNTNISSE

Diese Analyse untersuchte drei kritische Probleme in der `minesearch_v2/backend/mines.db` Datenbank:

1. **Fehlende Modelle:** "nemotron super" und "cypher alpha" 
2. **Details-Tabelle Anomalien:** "0 Quellen mit 100% Erfolgsrate"
3. **Performance-Daten Anomalien:** Werte über 100%

---

## 1. DATENBANKSTRUKTUR

### Identifizierte Tabellen (7):
- **sources** (30 Datensätze) - Datenquellen-Konfiguration
- **mines** (0 Datensätze) - Leere Mine-Datenbank
- **search_results** (1.400 Datensätze) - Suchergebnisse
- **model_statistics** (1.714 Datensätze) - Detaillierte Modell-Performance
- **field_consistency** (0 Datensätze) - Leere Konsistenz-Daten
- **model_summary** (6 Datensätze) - Aggregierte Modell-Zusammenfassung
- **field_statistics** (1.044 Datensätze) - Feld-spezifische Statistiken

---

## 2. PROBLEM 1: FEHLENDE MODELLE

### Analyseergebnis: BESTÄTIGT
Die Modelle "nemotron super" und "cypher alpha" wurden in **KEINER** der Datenbank-Tabellen gefunden.

### Gefundene Alternative Modelle:
```
✓ openrouter:llama-3.3-nemotron-super    (ähnlich zu "nemotron super")
✓ openrouter:cypher-alpha-free           (ähnlich zu "cypher alpha")
```

### Verfügbare Modelle (58 gesamt):
- **Anthropic:** claude-3-haiku, claude-3.7-sonnet, claude-opus-4, claude-sonnet-4
- **OpenAI:** gpt-3.5-turbo, gpt-4-turbo, gpt-4.1, gpt-4o, o3, o3-deep-research, o4-mini
- **Gemini:** gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash, gemini-2.5-pro
- **Grok:** grok-2, grok-3, grok-3-fast, grok-4
- **OpenRouter:** deepseek-chat, llama-3.1-nemotron-ultra, **llama-3.3-nemotron-super**, **cypher-alpha-free**

### Ursache:
Die gesuchten Modelle existieren unter **leicht abweichenden Namen**:
- "nemotron super" → `openrouter:llama-3.3-nemotron-super`
- "cypher alpha" → `openrouter:cypher-alpha-free`

---

## 3. PROBLEM 2: DETAILS-TABELLE ANOMALIEN

### Analyseergebnis: SCHWERWIEGENDE DATENKONSISTENZ-PROBLEME

#### Identifizierte Anomalien in `model_summary`:

| Modell | Erfolgsrate | Tests (Summary) | Records (Statistics) | Status |
|--------|-------------|----------------|---------------------|--------|
| openrouter:deepseek-chimera-free | 1.0% | 31 | 76 | ⚠️ Inkonsistent |
| openrouter:deepseek-free | 1.0% | 33 | 78 | ⚠️ Inkonsistent |
| openrouter:kimi-k2 | 1.0% | 33 | 78 | ⚠️ Inkonsistent |
| openrouter:llama-3.1-nemotron-ultra | 1.0% | 30 | 75 | ⚠️ Inkonsistent |
| openrouter:minimax-m1 | 1.0% | 31 | 73 | ⚠️ Inkonsistent |
| openrouter:mistral-small-free | 1.0% | 31 | 76 | ⚠️ Inkonsistent |

#### Kritische Erkenntnisse:
- **ALLE** Modelle zeigen unrealistisch niedrige 1.0% Erfolgsrate
- **ALLE** Modelle haben mehr Records in `model_statistics` als in `model_summary` angegeben
- Durchschnittlich **2.5x mehr** tatsächliche Tests als in Summary erfasst
- Alle Timestamps identisch: `2025-07-26 10:33:47` (vermutlich fehlerhafte Bulk-Operation)

---

## 4. PROBLEM 3: PERFORMANCE-ANOMALIEN

### Analyseergebnis: KEINE DIREKTEN >100% ANOMALIEN GEFUNDEN

#### Feststellungen:
- Keine Erfolgsraten > 100% in aktuellen Daten
- Keine Performance-Metriken > 100% gefunden
- **ABER:** Unrealistisch niedrige 1.0% Erfolgsraten deuten auf Berechnungsfehler hin

#### Verdächtige Muster:
- Identische 1.0% Erfolgsraten für alle Modelle
- Identische 10.0 durchschnittliche Quellen für alle Modelle
- NULL-Werte bei Kostenschätzungen

---

## 5. DETAILLIERTE SQL-ANALYSE

### Verwendete Queries für Problemidentifikation:

#### Modell-Suche:
```sql
-- Alle verfügbaren Modelle
SELECT DISTINCT model_id FROM model_statistics ORDER BY model_id;
SELECT DISTINCT model_used FROM search_results WHERE model_used IS NOT NULL;
SELECT model_id FROM model_summary ORDER BY model_id;
```

#### Datenkonsistenz-Prüfung:
```sql
-- Inkonsistenz zwischen Summary und Statistics
SELECT 
    ms.model_id,
    ms.total_tests as summary_tests,
    COUNT(stat.id) as statistics_records
FROM model_summary ms
LEFT JOIN model_statistics stat ON ms.model_id = stat.model_id
GROUP BY ms.model_id, ms.total_tests;
```

#### Anomalien-Suche:
```sql
-- Erfolgsraten über 100%
SELECT model_id, success_rate, data_success_rate 
FROM model_summary 
WHERE success_rate > 100 OR data_success_rate > 100;

-- Verdächtige 100% Werte mit 0 Quellen
SELECT model_id, success_rate, avg_sources_count, total_tests
FROM model_summary 
WHERE success_rate = 100 AND avg_sources_count = 0;
```

---

## 6. LÖSUNGSVORSCHLÄGE

### PRIORITÄT 1: Datenkonsistenz reparieren

#### SQL-Fix für model_summary:
```sql
-- Testzahlen korrigieren
UPDATE model_summary 
SET total_tests = (
    SELECT COUNT(*) 
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
last_updated = datetime('now');

-- Erfolgsraten neu berechnen
UPDATE model_summary 
SET success_rate = (
    SELECT CAST(COUNT(CASE WHEN success = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
data_success_rate = (
    SELECT CAST(COUNT(CASE WHEN success = 1 AND structured_data IS NOT NULL AND structured_data != '{}' THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
last_updated = datetime('now');
```

### PRIORITÄT 2: Durchschnittswerte korrigieren

```sql
UPDATE model_summary 
SET avg_response_time_ms = (
    SELECT AVG(response_time_ms)
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
avg_fields_found = (
    SELECT AVG(fields_found)
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
avg_sources_count = (
    SELECT AVG(sources_count)
    FROM model_statistics 
    WHERE model_statistics.model_id = model_summary.model_id
),
last_updated = datetime('now');
```

### PRIORITÄT 3: Field_statistics neu aufbauen

```sql
-- Alte Daten löschen
DELETE FROM field_statistics;

-- Neu berechnen basierend auf model_statistics
INSERT INTO field_statistics (
    model_id, field_name, total_searches, times_found, times_empty, 
    success_rate, avg_confidence, last_updated, excluded_count, 
    conditional_logic_applied
)
SELECT 
    model_id,
    json_extract(value, '$.field') as field_name,
    COUNT(*) as total_searches,
    COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) as times_found,
    COUNT(CASE WHEN json_extract(value, '$.found') = 0 THEN 1 END) as times_empty,
    CAST(COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*) as success_rate,
    AVG(COALESCE(json_extract(value, '$.confidence'), 0.0)) as avg_confidence,
    datetime('now') as last_updated,
    0 as excluded_count,
    0 as conditional_logic_applied
FROM model_statistics, json_each(structured_data)
WHERE structured_data IS NOT NULL 
    AND json_valid(structured_data)
    AND json_extract(value, '$.field') IS NOT NULL
GROUP BY model_id, json_extract(value, '$.field');
```

---

## 7. PRIORISIERTE HANDLUNGSEMPFEHLUNGEN

### SOFORT (Kritisch):
1. **Backup der aktuellen Datenbank erstellen**
2. **Datenkonsistenz-Fixes anwenden** (database_fixes.py ausführen)
3. **model_summary Werte neu berechnen**

### KURZFRISTIG (Hoch):
4. **Modell-Namen überprüfen** und korrekte IDs verwenden
5. **Datenvalidierung implementieren** vor dem Einfügen neuer Datensätze
6. **Automatische Konsistenz-Checks** einbauen

### MITTELFRISTIG (Medium):
7. **Monitoring für Datenanomalien** einrichten
8. **Regelmäßige Datenbereinigung** etablieren
9. **Test-Suite für Datenbankintegrität** entwickeln

---

## 8. VERWENDETE TOOLS UND SKRIPTE

### Analyseskripte:
- `database_analysis.py` - Grundlegende Datenbankstruktur-Analyse
- `detailed_problem_analysis.py` - Vertiefte Problemanalyse
- `database_fixes.py` - SQL-basierte Lösungsansätze

### Backup und Rollback:
- `backup_data.json` - Automatisches Backup vor Fixes
- Rollback-Funktionalität in database_fixes.py integriert

---

## 9. FAZIT

Die Datenbankanalyse hat **schwerwiegende Datenkonsistenz-Probleme** aufgedeckt:

### Bestätigte Probleme:
✅ **Fehlende Modelle:** Existieren unter abweichenden Namen  
✅ **Datenkonsistenz:** Massive Diskrepanzen zwischen verwandten Tabellen  
✅ **Unrealistische Werte:** Einheitlich niedrige 1.0% Erfolgsraten  

### Nicht bestätigte Probleme:
❌ **>100% Werte:** Derzeit keine direkten Anomalien gefunden  

### Empfohlenes Vorgehen:
1. Sofortiges Anwenden der bereitgestellten SQL-Fixes
2. Implementierung von Datenvalidierung
3. Regelmäßige Konsistenz-Checks etablieren

Die bereitgestellten Lösungsansätze sollten alle identifizierten Probleme beheben und die Datenintegrität wiederherstellen.

---

**Ende des Berichts**  
*Alle SQL-Queries und Skripte sind in den zugehörigen Python-Dateien verfügbar und bereit zur Ausführung.*