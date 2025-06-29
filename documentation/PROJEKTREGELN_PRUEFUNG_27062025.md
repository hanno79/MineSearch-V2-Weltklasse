# Projektregeln-Überprüfung
Author: rahn
Datum: 27.06.2025
Version: 1.0

## Zusammenfassung der Regelüberprüfung

### REGEL 1: Datei-Größenbeschränkung (>500 Zeilen)
**Status:** ❌ VERSTÖSSE GEFUNDEN

Folgende Python-Dateien überschreiten die 500-Zeilen-Grenze:
- `/app/src/agents/tavily_agent.py` - 748 Zeilen
- `/app/src/agents/perplexity_agent.py` - 725 Zeilen
- `/app/src/utils/pdf_processor.py` - 660 Zeilen
- `/app/src/utils/pdf/document_types.py` - 547 Zeilen
- `/app/src/core/validators.py` - 535 Zeilen
- `/app/src/ui/components/sidebar.py` - 514 Zeilen

**Empfehlung:** Diese Dateien müssen refaktoriert werden, um die 500-Zeilen-Grenze einzuhalten.

### REGEL 2: Keine Duplikatdateien bei Fixes
**Status:** ❌ VERSTÖSSE GEFUNDEN

Folgende Dateien haben verbotene Endungen:
- `/app/minesearch_new.out`
- `/app/streamlit_fixed.log`
- `/app/streamlit_import_fixed.log`
- `/app/streamlit_new.log`
- `/app/streamlit_token_fixed.log`

**Empfehlung:** Diese Dateien sollten umbenannt oder nach `/to_delete` verschoben werden.

### REGEL 3: Versionierung nach Bedarf
**Status:** ❌ VERSTÖSSE GEFUNDEN

Folgende Datei hat eine falsche Versionsbenennung:
- `/app/tests/conftest_backup.py`

**Empfehlung:** Diese Datei sollte entweder nach `/to_delete` verschoben oder in `conftest_v1.py` umbenannt werden.

### REGEL 4: Kommunikationssprache (Deutsch)
**Status:** ✅ OK

Stichprobenprüfung zeigt, dass Kommentare und Dokumentation auf Deutsch verfasst sind.

### REGEL 6: Datei-Organisation
**Status:** ⚠️ TEILWEISE VERSTÖSSE

Folgende Python-Dateien befinden sich im Root-Verzeichnis statt in der korrekten Ordnerstruktur:
- `comprehensive_system_test.py`
- `csv_column_detection_demo.py`
- `run.py`
- `run_all_tests.py`
- `run_tests.py`
- `simple_functionality_test.py`
- `start_fresh.py`
- `start_minesearch.py`
- `start_streamlit.py`
- `test_cancel_functionality.py`
- `test_new_perplexity.py`

**Empfehlung:** Test-Dateien sollten nach `/tests` verschoben werden, Start-Skripte könnten in einen `/scripts` Ordner.

### REGEL 7: Codebasis-Bereinigung
**Status:** ✅ OK

Der `/to_delete` Ordner wird aktiv genutzt und enthält bereits viele alte Dateien.

### REGEL 8: Autor-Kennzeichnung
**Status:** ❌ VERSTÖSSE GEFUNDEN

Folgende Dateien haben keinen Autor-Header:
- `/app/setup.py`
- `/app/src/core/migrations/__init__.py`
- `/app/src/core/scoring.py`
- `/app/src/core/database.py`
- `/app/src/core/logger.py`
- `/app/src/core/config.py`
- `/app/src/core/__init__.py`
- `/app/src/utils/text_normalization.py`
- `/app/src/utils/__init__.py`
- `/app/src/agents/rate_limiter.py`
- `/app/src/agents/__init__.py`
- `/app/src/agents/base_agent.py`
- `/app/src/ui/utils/__init__.py`
- `/app/src/ui/components/__init__.py`
- `/app/src/ui/__init__.py`
- `/app/src/ui/handlers/__init__.py`
- `/app/src/ui/pages/__init__.py`
- `/app/src/data/aggregator.py`
- `/app/src/data/models.py`
- `/app/src/data/exporter.py`

**Empfehlung:** Allen Dateien sollte ein korrekter Autor-Header hinzugefügt werden.

### REGEL 10: Keine Dummy- und Fallback-Werte
**Status:** ✅ OK

Keine ungekennzeichneten Dummy- oder Fallback-Werte gefunden.

### REGEL 13: Code-Qualitätsstandards (Naming Conventions)
**Status:** ✅ OK

Alle Python-Dateien folgen der Naming Convention (lowercase mit underscores).

### REGEL 15: Konfiguration & Umgebung
**Status:** ✅ OK

Keine hardcodierten API-Keys oder Secrets im Code gefunden.

## Gesamtbewertung

Von 10 überprüften Regeln:
- ✅ 5 Regeln werden eingehalten
- ❌ 4 Regeln werden verletzt
- ⚠️ 1 Regel wird teilweise verletzt

## Prioritäre Handlungsempfehlungen

1. **HOCH**: Refaktorierung der 6 Python-Dateien über 500 Zeilen
2. **HOCH**: Hinzufügen von Autor-Headern zu allen Dateien ohne Header
3. **MITTEL**: Verschieben/Umbenennen der Dateien mit verbotenen Endungen
4. **MITTEL**: Reorganisation der Test- und Skript-Dateien im Root-Verzeichnis
5. **NIEDRIG**: Umbenennung von `conftest_backup.py`

## Nächste Schritte

1. Erstellen Sie einen Refactoring-Plan für die zu großen Dateien
2. Fügen Sie systematisch Autor-Header zu allen Dateien hinzu
3. Bereinigen Sie die Dateistruktur entsprechend den Projektregeln