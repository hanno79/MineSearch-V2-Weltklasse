# TODO – Projekt-Reorganisation (Stand: 08.08.2025)

Ziel: Struktur-Aufräumung ohne Funktionsänderung (API stabil, Port 8000, bestehende Flows bleiben). Inkrementell, mit schneller Rückkehr zu grünem Build nach jeder Phase.

## Invarianten (müssen immer gelten)
- [x] Port 8000 ist exklusiv für MineSearch (Start: `http://localhost:8000/`, UI: `/static/index.html`)
- [x] `.env` nur im Root, nie committen; `data/`, `logs/`, `*.db` git-ignored
- [x] DB-Pfad: `DATABASE_PATH=/app/data/minesearch.db` (oder Ableitung), Schreibrechte gesichert
- [x] UI statisch über FastAPI unter `/static` ausgeliefert

## P0 – Backup & Sicherung
- [ ] Git-Branch erstellen: `backup/pre-restructure-2025-08-08`
- [ ] Git-Tag erstellen: `pre-restructure-2025-08-08`
- [ ] CI-Lauf auf Backup-Branch prüfen (Dokumentation des Status)

## P1 – Rehoming (nur verschieben/umbennen, keine Logik-Änderungen)
- [x] `minesearch_v2/backend` nach `backend/minesearch/` (Python-Paket) verschieben
- [x] `minesearch_v2/frontend` nach `frontend/` verschieben
- [x] Transitional Shims belassen:
  - [x] Dünner Wrapper in `minesearch_v2/backend/main.py`, der `backend/minesearch/main.py` importiert (Kompatibilität alter Startpfade)
- [ ] Pfade in Start-/Hilfs-Skripten temporär kompatibel halten (PYTHONPATH)
- [ ] `.github/workflows/tests.yml` Pfade auf neue Struktur vorbereiten (noch keine Lint-Änderungen)

### Akzeptanzkriterien P1
- [x] App startet auf Port 8000: `uvicorn backend.minesearch.main:app --host 0.0.0.0 --port 8000`
- [x] `GET /static/index.html` liefert 200
- [x] Playwright-UI-Smoketest (Tabs) grün

## P2 – Imports & Entrypoints konsolidieren
- [ ] Einheitliche absolute Imports: `from minesearch ...` innerhalb `backend/minesearch`
- [x] Offizieller Startkommando: `uvicorn minesearch.main:app --port 8000` (SAFE_MODE validiert)
- [x] Static Mount zeigt auf `frontend/`
- [ ] CI aktualisieren (Install, Test, Artefakte, Pfade):
  - [ ] Dependencies aus `minesearch_v2/requirements.txt` → ggf. `requirements.txt` vereinheitlichen (später)
  - [ ] Test-Run: `python minesearch_v2/run_tests.py` → Übergang/Adapter oder neues Script (ohne Logik-Änderungen)
  - [ ] Playwright-Smoketest gegen `http://localhost:8000/static/index.html`

### Akzeptanzkriterien P2
- [ ] Alle Imports funktionieren ohne `sys.path`-Hacks
- [ ] CI‑Job grün (Build + UI‑Smoke)

## Fortschritt/Log
- 2025-08-08: SAFE_MODE nur `static`; API-Init entschärft; Static 200; UI‑Smoke grün (Tabs)
- 2025-08-08: `style.css` nach `frontend/` verschoben (404 behoben)
- 2025-08-08: Übergangs‑Entrypoint `minesearch.main:app` angelegt (P2)
- 2025-08-08: `get_api_router()` mit lazy Imports, `main` nutzt `get_api_router()` außerhalb SAFE_MODE
 - 2025-08-08: CI-Workflow ergänzt: SAFE_MODE‑Start (8000) + UI‑Smoketest gegen `/static/index.html`

## P3 – Cleanup & Dokumentation
- [ ] Entfernen/Archivieren veralteter V1‑Reste in `legacy/` (nur falls erforderlich)
- [ ] README aktualisieren (Start, Struktur, .env, Port 8000)
- [ ] ARCHITECTURE_GUIDELINES aktualisieren (neue Pfade/Module)
- [ ] `.gitignore` prüfen: `node_modules/`, `data/*.db`, `logs/`, `.env` etc.

### Akzeptanzkriterien P3
- [ ] Repository-Root übersichtlich; keine doppelten .env/.db/.example Dateien
- [ ] Doku deckt Setup/Start/Coverage/Smoke ab

## P4 – Tests, Linting, Qualität (optional in kleinen Schritten)
- [ ] Minimale Tests stabilisieren (DB‑Smoke, Endpunkte, Statistik‑Stub)
- [ ] Linter/Formatter schrittweise reaktivieren (ruff/black/mypy) mit passenden Pfaden
- [ ] Coverage-Ziel festlegen (z. B. 60% initial)

## Bekannte Probleme (Stand jetzt)
- SAFE_MODE nötig: Ohne SAFE_MODE schlagen Importe/Initialisierung fehl (siehe unten), daher temporär nur Static + Health aktiv
- Statische Auslieferung: `/` soll auf `/static/index.html` weiterleiten; `/static` ist auf `/app/frontend` gemountet
- Harte Pfade: Zahlreiche Verweise auf `/app/minesearch_v2/frontend/index.html` in `api/routes/static.py` u.a. → auf `/app/frontend` korrigieren (teilweise erledigt)
- Fehlende/verschobene Module: Müssen nach `backend/minesearch/` umgezogen und relativ importiert werden:
  - `utils`, `data_extraction`, `extraction_patterns`, `extraction_processors`, `extraction_validators`,
    `source_manager`, `model_tier_strategy`, `model_id_parser`, `service_manager`
- Importfehler protokolliert (chronologisch):
  - `ModuleNotFoundError: No module named 'utils'`
  - `attempted relative import beyond top-level package` (config/base Pfadtiefe; nach Rehome angepasst)
  - `No module named 'backend.minesearch.data_extraction'` → Datei verschoben/Importe angepasst
  - `No module named 'extraction_patterns'` → nach `backend/minesearch/` verschoben, relative Importe gesetzt
  - `No module named 'source_manager'` → nach `backend/minesearch/` verschoben, relative Importe gesetzt
  - `No module named 'model_tier_strategy'` → ausstehend (verschieben + relative Importe)
- UI‑Smoke via Playwright sollte erst nach stabiler `/static/index.html` laufen

## Risiken & Abfederung
- [ ] Risiko: Verdeckte relative Importe brechen → Übergangs‑Adapter/Wrapper + CI früh erkennen lassen
- [ ] Risiko: CI‑Pfade/Artefakte fehlschlagen → vor Merge Dry‑Run auf Branch
- [ ] Risiko: Provider/Keys beim Lifespan blockieren → Startup‑Validierungen tolerant halten, Fehler nur warnen (keine Blockade)

## Rollback / Recovery
- [ ] Bei Problemen: `git checkout backup/pre-restructure-2025-08-08`
- [ ] Hotfix-Branch von Backup erstellen, Hotfixes einpflegen, erneut planen

## Beobachtungen/Nacharbeiten (optional)
- [ ] Vereinheitlichung `requirements.txt` vs. `pyproject.toml` (später)
- [ ] Start‑Scripts (`make`/`just`) hinzufügen
- [ ] Docker/Compose (später) mit Port 8000 Fix

