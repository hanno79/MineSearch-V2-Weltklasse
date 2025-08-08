# TODO – Codebasis-Audit (Stand: 08.08.2025)

Diese Liste basiert auf der Analyse der aktuellen Codebasis und den Projektregeln (`CLAUDE.md`). Sie ist priorisiert und als Checkliste nutzbar.

## Sofort (Prio 0)
- [x] `.env` konsolidiert und aus Git ausgeschlossen; vorhandene Keys werden weiterverwendet (keine Rotation mangels neuer Keys)
  - [x] `.env` zentral auf Root konsolidiert; doppelte `.env` nach `to_delete/env/` verschoben
  - [x] `.gitignore` bestätigt (enthält `.env`/`*.env`); keine `.env` im Index
  - [x] Ladelogik in `minesearch_v2/backend/config/base.py` auf Root‑`.env` umgestellt (Fallbacks aktiv)
  - [x] Validiert: Keys laden korrekt; fehlende optionale Keys: `ABACUS_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROK_API_KEY`
  - [x] DB‑Dateien geprüft: keine eingecheckten `.db` gefunden

## Kritische Bugs (Prio 1)
- [x] `minesearch_v2/backend/database/manager.py`: `cleanup_old_results` → `timedelta` korrekt importiert/verwendet
- [x] `minesearch_v2/backend/api/routes/results.py`: `delete_result` nutzt jetzt direkt `SearchResult`

## Konfiguration (Prio 1)
- [x] `.env`-Ladepfad in `minesearch_v2/backend/config/base.py` korrigiert (Root bevorzugt, Fallbacks aktiv)
- [x] DB-Konfiguration vereinheitlicht: `DATABASE_URL` wird bevorzugt, sonst Ableitung aus `DATABASE_PATH` (absoluter Pfad → sqlite URL)

## CI/CD (Prio 1)
- [x] `.github/workflows/tests.yml` an Projektstruktur angepasst
  - [x] Dependencies über `minesearch_v2/requirements.txt` installieren
  - [x] Test-Run via `python minesearch_v2/run_tests.py`
  - [x] Lint/Format/Typecheck vorerst deaktiviert bzw. Pfade korrigiert (können später reaktiviert werden)
  - [x] Überflüssige `-e ".[dev]"` entfernt
- [ ] Playwright-Setup konsolidieren (Python/Node doppelt?) und unnötige `node_modules` nicht versionieren

## Regel-Compliance (CLAUDE.md) (Prio 2)
- [ ] 500‑Zeilen‑Regel: `minesearch_v2/backend/config/models.py` (>500 Zeilen) in Provider-Module aufteilen
- [ ] Verbotene Suffixe/Dubletten bereinigen (Regel 2): Dateien mit `_fixed`, `.backup`, etc. zusammenführen oder nach `to_delete/`
- [ ] Autor‑Header in allen Skripten sicherstellen (Regel 8); optional Pre‑Commit‑Check einführen
- [ ] Ordnerstruktur glätten (Regel 6): Debug-/Ad‑hoc‑Skripte und Einzeltests modulnah oder nach `to_delete/`

## API/Qualität (Prio 2)
- [ ] `results.py`: `sort_by`-Beschreibung vs. Implementierung angleichen (aktuell wird `fields_found` nicht unterstützt)
- [ ] `Source.update_access`: `typical_content_types` sicher initialisieren, damit Typen gepflegt werden
- [ ] `DatabaseManager.get_statistics`: Iteration über `.all()` bei großen Tabellen reduzieren (Aggregationen/Chunking)

## Dokumentation (Prio 2)
- [ ] `README.md`/`README_SETUP.md` an reale Struktur anpassen (derzeit Verweise auf `src/`/Dockerdateien, die so nicht vorhanden sind)
- [ ] GitHub‑Setup‑Anleitung gegen vorhandene Workflows abgleichen oder Workflows gemäß Anleitung erstellen

## Tests (Prio 2)
- [ ] Tests unter `minesearch_v2/tests` konsolidieren; Legacy/Duplikate entfernen oder nach `to_delete/`
- [ ] Coverage ≥ 70% sicherstellen (pytest.ini/run_tests.py konsistent); fehlende Tests für neue Routen/Validatoren ergänzen

## Aufräumen & Repo‑Hygiene (Prio 3)
- [ ] Große Screenshots/HTML‑Artefakte bündeln (z. B. `documentation/` oder `to_delete/`) und Referenzen prüfen
- [ ] Alte Konfigurationsreste/Dubletten (z. B. `config/production_settings.py`, Varianten in `to_delete/...`) final entscheiden und vereinheitlichen

## Konsistenz/API‑Schicht (Prio 3)
- [ ] Doppelte Schemas konsolidieren (`api/models.py` vs. `api/schemas.py`) → eine Quelle der Wahrheit
- [ ] Standardisierte Responses per `standard_api_endpoint` sukzessive auf alle Routen anwenden

## Migrationen/DB (Prio 3)
- [ ] Strategie festlegen: Foreign Keys (derzeit in Modellen deaktiviert, Migrationen mit FKs vorhanden)
  - [ ] Entweder FKs aktivieren und Migrationen durchführen
  - [ ] Oder bewusst ohne FKs weiterarbeiten und Migrationen bereinigen

---

### Nächste Schritte
1. Secrets-Rotation + `.env`/DB aus Repo entfernen (Sofort)
2. Zwei Hard‑Bugs fixen (`timedelta`, `SearchResult`‑Query)
3. CI‑Workflow anpassen, damit Tests grün laufen

Bei Bedarf erstellen wir pro Block eine eigene Task‑Liste im `projectplan.md` und haken sie iterativ ab.
