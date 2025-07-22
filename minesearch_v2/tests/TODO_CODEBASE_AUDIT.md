# TODO-Liste Codebase Audit

Diese Liste enthält alle konkreten Mikrotasks, die aus der vollständigen Codebase-Analyse hervorgegangen sind. Die Aufgaben sind nach Themenblöcken sortiert und können parallel abgearbeitet werden.

---

## 1. Asynchrone Aufrufe
- [x] Alle asynchronen Endpunkte und Service-Methoden auf korrekte await-Nutzung prüfen (**abgeschlossen**)

---

## 2. Import-Bereinigung
- [x] Für jedes Python-Skript:
    - [x] Nicht verwendete Imports entfernen
    - [x] Doppelte Imports entfernen
    - [x] Veraltete oder fehlerhafte Imports identifizieren und korrigieren
    - [x] Einheitliche Importstruktur (absolute vs. relative Imports) herstellen

### Konkrete Mikrotasks (Beispiel: test_fixes_demo.py)
- [x] test_fixes_demo.py:
    - [x] `import sys` entfernen (wird nur für sys.path.append genutzt, kann durch relative Imports ersetzt werden)
    - [x] `import os` entfernen (siehe oben)
    - [x] `sys.path.append(...)` entfernen und stattdessen relative Imports nutzen, sofern möglich
    - [x] Prüfen, ob alle from-imports (`from extraction_processors ...`, `from source_manager ...`, `from data_extraction ...`) tatsächlich genutzt werden (sie werden genutzt, also belassen)
    - [x] Importstruktur vereinheitlichen: Möglichst relative Imports, falls das Projekt als Paket genutzt wird

- [x] Automatisierte Tools zur Import-Prüfung (z.B. flake8, pylint) in die CI/CD-Pipeline integrieren
- [x] Dokumentation zu Import-Standards ergänzen

---

## 3. Fehlerbehandlung
- [x] Alle Stellen mit `# Error Handling` und `logger.error` auf echte Fehlerbehandlung prüfen und ggf. ergänzen
- [x] Fehlerdifferenzierung einführen (z.B. ValueError vs. Exception)
- [x] Fehler in produktiven Modulen nicht nur loggen, sondern an Aufrufer weitergeben oder kontrolliert abbrechen
- [x] Fehlerbehandlung in Konfigurationsdateien (z.B. production_settings.py) ergänzen
- [x] Fehler in Tests als Assertion prüfen, nicht nur ausgeben
- [x] Konsistente Fehlerweitergabe (Exception oder klar strukturierte Fehlermeldung) im gesamten Code

---

## 4. Datenbankoperationen
- [x] Für jede Datenbankoperation:
    - [x] try/except-Blöcke ergänzen
    - [x] Transaktionsmanagement (commit/rollback) sicherstellen
    - [x] Fehler an Aufrufer weitergeben, nicht nur loggen
- [x] Automatisierte Tests für fehlerhafte DB-Operationen ergänzen

---

## 5. Testabdeckung
- [x] Für alle Testskripte:
    - [x] Fehlerfälle als Assertion prüfen (nicht nur print)
    - [x] Fehlende Tests für Rand- und Fehlerfälle ergänzen
- [x] Testabdeckung regelmäßig mit Coverage-Tool prüfen
- [x] Testdokumentation (README_TESTS.md) um Hinweise zu Fehlerfall-Tests und Coverage ergänzen

---

**Hinweis:**
- Die Liste kann bei der Abarbeitung weiter verfeinert werden.
- Nach Umsetzung aller Punkte empfiehlt sich eine erneute Review-Runde und die Integration automatisierter Checks.
