# Projektplan: Code-Refactoring data_extraction.py

## Analyse
Die Datei data_extraction.py hat 719 Zeilen und muss gemäß CLAUDE.md auf maximal 500 Zeilen aufgeteilt werden.

## Struktur der aktuellen Datei
- DataExtractor Klasse mit folgenden Hauptbereichen:
  1. Pattern-Initialisierung (_initialize_patterns, _get_restoration_cost_patterns)
  2. Validierungsfunktionen (_is_placeholder_value, _validate_coordinate)
  3. Extraktionsfunktionen (_extract_field, extract_structured_data)
  4. Post-Processing (_post_process_data, _process_restoration_costs, etc.)
  5. Hilfsfunktionen (assign_sources_to_data, _find_source_references)

## Geplante Aufteilung

### 1. extraction_patterns.py (neu, ~200 Zeilen)
- Alle Pattern-Definitionen
- Pattern-Initialisierung
- Pattern-Helper-Funktionen

### 2. extraction_validators.py (neu, ~150 Zeilen)
- _is_placeholder_value()
- _validate_coordinate()
- Weitere Validierungsfunktionen

### 3. extraction_processors.py (neu, ~200 Zeilen)
- _process_restoration_costs()
- _process_activity_status()
- _split_country_region()
- Weitere Verarbeitungsfunktionen

### 4. data_extraction.py (reduziert auf ~400 Zeilen)
- Haupt-DataExtractor Klasse
- extract_structured_data() als Hauptmethode
- Import und Nutzung der neuen Module

## Umsetzungsschritte
1. ✅ extraction_patterns.py erstellen
2. ✅ extraction_validators.py erstellen  
3. ✅ extraction_processors.py erstellen
4. ✅ data_extraction.py refactoren
5. ✅ Imports in anderen Dateien prüfen und anpassen
6. ✅ Funktionalität testen

## Ergebnis
✅ Erfolgreich refactoriert!
- data_extraction.py: 371 Zeilen (vorher 719)
- extraction_patterns.py: 242 Zeilen
- extraction_validators.py: 251 Zeilen
- extraction_processors.py: 302 Zeilen

## Zusätzliche Verbesserungen implementiert
1. ✅ Erweiterte Koordinaten-Extraktion mit DMS-Format-Unterstützung
2. ✅ Validierung unrealistischer Restaurationskosten
3. ✅ Bessere Feldvalidierung für Jahre und Flächen

## Wichtige Hinweise
- Keine Funktionalität darf verloren gehen
- Alle Imports müssen angepasst werden
- Tests sollten weiterhin funktionieren