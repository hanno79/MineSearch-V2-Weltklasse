"""
PHASE 2: DATEI-BEREINIGUNG ANALYSE
==================================

Author: rahn
Datum: 06.08.2025
Version: 1.0

ANALYSEERGEBNISSE:
==================

## 1. VERBOTENE ENDUNGEN (REGEL 2)

### Dateien mit "_fixed", "_backup", "_final", etc.:
- /app/minesearch_v2/frontend/index_broken_backup.html (BACKUP)
- /app/minesearch_v2/backend/server_fixed.log (LOG - kann bleiben)
- /app/minesearch_v2/backend/perplexity_final_validation.py (VALIDATION SCRIPT)
- /app/minesearch_v2/frontend/quick_final_test.js (TEST SCRIPT)

AKTION: 4 Dateien nach to_delete/ verschieben

## 2. DATABASE BACKUPS (BEHALTEN)

### Legitime Backups (nicht löschen):
- /app/minesearch_v2/backups/*.db (System-Backups)
- /app/minesearch_v2/backend/database_backups/ (DB-Backups)
- /app/minesearch_v2/backend/mines_backup_*.db (Migrations-Backups)

AKTION: Backups behalten - sind wichtig für Recovery

## 3. DEBUG/TEST-DATEIEN (BEREINIGUNG NÖTIG)

### Temporäre Debug-Scripte (31 Dateien):
- live_log_batch_test.py
- simple_detail_modal_test.py  
- browser_simulation_test.py
- final_batch_debug.py
- quick_provider_test.py
- comprehensive_provider_test.py
- etc.

BEWERTUNG:
- BEHALTEN: integration_test_suites.py (produktive Tests)
- BEHALTEN: database_validation.py (produktive Validierung)
- VERSCHIEBEN: *_debug*, *_test*, *_temp* Scripts (31 Dateien)

## 4. DUPLIKAT-ANALYSE

### Potentielle Duplikate:
- comprehensive_test.py (Root vs. to_delete/)
- quick_test.py (Root vs. to_delete/) 
- final_verification.py (Root vs. Frontend)

AKTION: Funktionale Duplikate konsolidieren

## BEREINIGUNGSPLAN:
==================

### ZU VERSCHIEBEN nach to_delete/:

**Verbotene Endungen (4):**
- frontend/index_broken_backup.html
- backend/perplexity_final_validation.py  
- frontend/quick_final_test.js
- Screenshots mit "_final"

**Debug/Test Scripts (25):**
- live_log_batch_test.py
- simple_detail_modal_test.py
- browser_simulation_test.py
- final_batch_debug.py
- quick_provider_test.py
- comprehensive_provider_test.py
- detail_modal_analysis_test.py
- [weitere 18 Test-Scripts]

**Legacy/Broken Dateien (4):**
- api/routes/batch_broken.py
- search_service_legacy.py
- legacy_data_analysis_report.py
- to_delete/refactoring_20250723/batch_broken.py

GESAMT: ~33 Dateien zur Bereinigung

### ZU BEHALTEN (Produktive Funktionen):

**Test-Infrastruktur:**
- integration_test_suites.py
- database_validation.py  
- end_to_end_workflow_validation.py
- cross_service_validation.py

**System-Backups:**
- Alle *.db Backup-Dateien
- database_backups/ Ordner
- backups/ Ordner

**Log-Dateien:**
- server_fixed.log (wichtige Logs)

BEREINIGUNG REDUZIERT CODEBASE UM ~30 OBSOLETE DATEIEN
======================================================
"""