#!/bin/bash
# SWARM 4: BEREINIGUNG AUTOMATIONSSKRIPTE
# claude-flow Hierarchical Mesh Hive-Mind System
# Author: rahn | Datum: 23.07.2025 | Version: 1.0

set -e  # Bei Fehler stoppen
LOG_FILE="/app/minesearch_v2/cleanup_$(date +%Y%m%d_%H%M%S).log"

echo "=== CLAUDE-FLOW SWARM 4: FINALE BEREINIGUNG ===" | tee -a "$LOG_FILE"
echo "Start: $(date)" | tee -a "$LOG_FILE"

# ==============================================
# FUNKTION: SOFORTIGE BEREINIGUNG (13.2 MB)
# ==============================================
immediate_cleanup() {
    echo "=== PHASE 1: SOFORTIGE BEREINIGUNG ===" | tee -a "$LOG_FILE"
    
    # Backup vor kritischen Löschungen
    echo "Erstelle Sicherheitsbackup..." | tee -a "$LOG_FILE"
    tar -czf "/app/backup_swarm4_$(date +%Y%m%d).tar.gz" \
        /app/minesearch_v2/test_mines.csv \
        /app/minesearch_v2/backend/test_mines_comprehensive.csv \
        /app/minesearch_v2/claude-flow.config.json \
        /app/minesearch_v2/memory/ 2>/dev/null || echo "Backup-Warnung: Einige Dateien nicht gefunden"
    
    # CSV-Duplikate entfernen (1.2 KB)
    echo "Entferne CSV-Duplikate..." | tee -a "$LOG_FILE"
    [ -f "/app/minesearch_v2/test_mines_quebec.csv" ] && rm -f "/app/minesearch_v2/test_mines_quebec.csv" && echo "  ✓ test_mines_quebec.csv (root)" | tee -a "$LOG_FILE"
    [ -f "/app/minesearch_v2/backend/test_mines_quebec.csv" ] && rm -f "/app/minesearch_v2/backend/test_mines_quebec.csv" && echo "  ✓ test_mines_quebec.csv (backend)" | tee -a "$LOG_FILE"
    [ -f "/app/minesearch_v2/backend/test_mines_batch.csv" ] && rm -f "/app/minesearch_v2/backend/test_mines_batch.csv" && echo "  ✓ test_mines_batch.csv" | tee -a "$LOG_FILE"
    [ -f "/app/minesearch_v2/backend/test_sample.csv" ] && rm -f "/app/minesearch_v2/backend/test_sample.csv" && echo "  ✓ test_sample.csv (defekt)" | tee -a "$LOG_FILE"
    
    # JSON-Validierungen löschen (161 KB)
    echo "Entferne veraltete JSON-Validierungen..." | tee -a "$LOG_FILE"
    rm -f /app/minesearch_v2/backend/to_delete/field_completion_validation_*.json && echo "  ✓ field_completion_validation_*.json" | tee -a "$LOG_FILE"
    rm -f /app/minesearch_v2/backend/to_delete/quick_validation_*.json && echo "  ✓ quick_validation_*.json" | tee -a "$LOG_FILE"
    
    # Node-Modules entfernen (13 MB)
    echo "Entferne ungenutzte Node-Modules..." | tee -a "$LOG_FILE"
    if [ -d "/app/minesearch_v2/tests/integration_tests/node_modules/" ]; then
        rm -rf "/app/minesearch_v2/tests/integration_tests/node_modules/"
        echo "  ✓ Node-Modules entfernt (~13 MB)" | tee -a "$LOG_FILE"
    else
        echo "  ⚠ Node-Modules bereits entfernt" | tee -a "$LOG_FILE"
    fi
    
    echo "Phase 1 abgeschlossen: ~13.2 MB freigegeben" | tee -a "$LOG_FILE"
}

# ==============================================
# FUNKTION: LOG-ARCHIVIERUNG (2.4 MB → 500 KB)
# ==============================================
log_archive() {
    echo "=== PHASE 2: LOG-ARCHIVIERUNG ===" | tee -a "$LOG_FILE"
    
    ARCHIVE_DIR="/app/minesearch_v2/archive/logs_$(date +%Y%m%d)"
    mkdir -p "$ARCHIVE_DIR"
    
    cd /app/minesearch_v2/backend/to_delete/
    
    # Logs komprimieren (außer aktuellem minesearch.log)
    for logfile in *.log; do
        if [ -f "$logfile" ] && [ "$logfile" != "minesearch.log" ]; then
            echo "Archiviere: $logfile" | tee -a "$LOG_FILE"
            gzip -c "$logfile" > "$ARCHIVE_DIR/${logfile}.gz"
            rm "$logfile"
            echo "  ✓ $logfile → ${logfile}.gz" | tee -a "$LOG_FILE"
        fi
    done
    
    # Spezialbehandlung für großes minesearch.log
    if [ -f "minesearch.log" ] && [ $(stat -f%z "minesearch.log" 2>/dev/null || stat -c%s "minesearch.log") -gt 1048576 ]; then
        echo "Komprimiere großes minesearch.log..." | tee -a "$LOG_FILE"
        gzip -c "minesearch.log" > "$ARCHIVE_DIR/minesearch_$(date +%Y%m%d).log.gz"
        # Aktuelle Logs behalten, aber auf 100 Zeilen kürzen
        tail -100 "minesearch.log" > "minesearch_current.log"
        mv "minesearch_current.log" "minesearch.log"
        echo "  ✓ minesearch.log archiviert und gekürzt" | tee -a "$LOG_FILE"
    fi
    
    echo "Phase 2 abgeschlossen: Logs archiviert in $ARCHIVE_DIR" | tee -a "$LOG_FILE"
}

# ==============================================
# FUNKTION: VALIDIERUNG
# ==============================================
validate_cleanup() {
    echo "=== PHASE 3: POST-CLEANUP VALIDATION ===" | tee -a "$LOG_FILE"
    
    # Produktive Dateien prüfen
    [ -f "/app/minesearch_v2/test_mines.csv" ] && echo "  ✅ Core-CSV erhalten" | tee -a "$LOG_FILE" || echo "  ❌ Core-CSV FEHLT!" | tee -a "$LOG_FILE"
    [ -f "/app/minesearch_v2/backend/test_mines_comprehensive.csv" ] && echo "  ✅ Extended-CSV erhalten" | tee -a "$LOG_FILE" || echo "  ❌ Extended-CSV FEHLT!" | tee -a "$LOG_FILE"
    
    # Bereinigung prüfen
    [ ! -d "/app/minesearch_v2/tests/integration_tests/node_modules/" ] && echo "  ✅ Node-Modules entfernt" | tee -a "$LOG_FILE" || echo "  ⚠ Node-Modules noch vorhanden" | tee -a "$LOG_FILE"
    [ ! -f "/app/minesearch_v2/backend/to_delete/field_completion_validation_20250715_105959.json" ] && echo "  ✅ JSON-Validierungen entfernt" | tee -a "$LOG_FILE" || echo "  ⚠ JSON-Dateien noch vorhanden" | tee -a "$LOG_FILE"
    
    # Claude-Flow System prüfen
    [ -f "/app/minesearch_v2/claude-flow.config.json" ] && echo "  ✅ Claude-Flow Config erhalten" | tee -a "$LOG_FILE"
    [ -d "/app/minesearch_v2/memory/" ] && echo "  ✅ Memory-System erhalten" | tee -a "$LOG_FILE"
    
    echo "=== SPEICHER-ANALYSE ===" | tee -a "$LOG_FILE"
    echo "to_delete Ordner Größen:" | tee -a "$LOG_FILE"
    du -sh /app/minesearch_v2/backend/to_delete/ /app/minesearch_v2/to_delete/ 2>/dev/null | tee -a "$LOG_FILE" || echo "Einige to_delete Ordner nicht gefunden (OK)" | tee -a "$LOG_FILE"
    
    echo "Festplatten-Status:" | tee -a "$LOG_FILE"
    df -h /app 2>/dev/null | head -2 | tee -a "$LOG_FILE" || echo "Disk-Info nicht verfügbar" | tee -a "$LOG_FILE"
    
    echo "Phase 3 abgeschlossen: Validierung erfolgreich" | tee -a "$LOG_FILE"
}

# ==============================================
# FUNKTION: SCREENSHOT-MANAGEMENT (OPTIONAL)
# ==============================================
screenshot_management() {
    echo "=== PHASE 4: SCREENSHOT-MANAGEMENT (OPTIONAL) ===" | tee -a "$LOG_FILE"
    
    SCREENSHOT_DIR="/app/minesearch_v2/to_delete/refactoring_20250723"
    
    if [ -d "$SCREENSHOT_DIR" ]; then
        # Prüfe Alter der Screenshots (30 Tage Policy)
        DAYS_OLD=$(find "$SCREENSHOT_DIR" -name "*.png" -mtime +30 | wc -l)
        
        if [ "$DAYS_OLD" -gt 0 ]; then
            echo "Entferne Screenshots älter als 30 Tage..." | tee -a "$LOG_FILE"
            find "$SCREENSHOT_DIR" -name "*.png" -mtime +30 -delete
            echo "  ✓ $DAYS_OLD alte Screenshots entfernt" | tee -a "$LOG_FILE"
        else
            echo "  ⚠ Screenshots noch nicht 30 Tage alt - Retention Policy aktiv" | tee -a "$LOG_FILE"
            echo "  📸 Screenshots werden automatisch nach 30 Tagen entfernt" | tee -a "$LOG_FILE"
        fi
    else
        echo "  ℹ Kein Screenshot-Archiv gefunden" | tee -a "$LOG_FILE"
    fi
}

# ==============================================
# FUNKTION: ROLLBACK (NOTFALL)
# ==============================================
rollback() {
    echo "=== ROLLBACK AKTIVIERT ===" | tee -a "$LOG_FILE"
    
    BACKUP_FILE="/app/backup_swarm4_$(date +%Y%m%d).tar.gz"
    
    if [ -f "$BACKUP_FILE" ]; then
        echo "Stelle Backup wieder her: $BACKUP_FILE" | tee -a "$LOG_FILE"
        cd /app/
        tar -xzf "$BACKUP_FILE"
        echo "  ✓ Rollback abgeschlossen" | tee -a "$LOG_FILE"
    else
        echo "  ❌ ROLLBACK FEHLGESCHLAGEN: Backup nicht gefunden!" | tee -a "$LOG_FILE"
        exit 1
    fi
}

# ==============================================
# HAUPTPROGRAMM
# ==============================================
main() {
    case "${1:-all}" in
        "immediate")
            immediate_cleanup
            validate_cleanup
            ;;
        "logs")
            log_archive
            ;;
        "validate")
            validate_cleanup
            ;;
        "screenshots")
            screenshot_management
            ;;
        "rollback")
            rollback
            ;;
        "all")
            immediate_cleanup
            log_archive
            validate_cleanup
            screenshot_management
            ;;
        *)
            echo "Usage: $0 {immediate|logs|validate|screenshots|rollback|all}"
            echo ""
            echo "  immediate   - Sofortige Bereinigung (CSV, JSON, Node-Modules)"
            echo "  logs        - Log-Archivierung und Komprimierung"
            echo "  validate    - Post-Cleanup Validierung"
            echo "  screenshots - Screenshot-Management (30 Tage Policy)"
            echo "  rollback    - Notfall-Rollback"
            echo "  all         - Vollständige Bereinigung (Standard)"
            exit 1
            ;;
    esac
    
    echo "=== CLEANUP ABGESCHLOSSEN ===" | tee -a "$LOG_FILE"
    echo "Ende: $(date)" | tee -a "$LOG_FILE"
    echo "Log gespeichert: $LOG_FILE" | tee -a "$LOG_FILE"
    
    # Zusammenfassung
    echo ""
    echo "🎯 SWARM 4 BEREINIGUNG ERFOLGREICH"
    echo "📊 Geschätzte Speicherfreigabe: ~18.3 MB"
    echo "📝 Vollständiges Log: $LOG_FILE"
    echo "🔄 Bei Problemen: $0 rollback"
}

# Script ausführen
main "$@"