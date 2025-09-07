#!/bin/bash
"""
CRON-JOB SETUP für Duplikat-Monitoring
=====================================

Fügt folgende Cron-Jobs hinzu:
- Wöchentlicher Duplikat-Check: Montags 9:00 Uhr
- System Health Check: Alle 15 Minuten
- Monatlicher Gesamt-Report: 1. jeden Monats

INSTALLATION: bash setup_cron_jobs.sh
"""

echo "🕒 SETUP CRON-JOBS für Duplikat-Monitoring"
echo "=========================================="

# Aktueller Pfad
SCRIPT_DIR=$(pwd)

# Backup existing crontab
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt

# Add new cron jobs
(crontab -l 2>/dev/null; echo "") | grep -v "# MineSearch Duplicate Monitoring" > temp_cron
echo "# MineSearch Duplicate Monitoring Jobs" >> temp_cron
echo "0 9 * * 1 cd $SCRIPT_DIR && python3 weekly_duplicate_checker.py >> weekly_check.log 2>&1" >> temp_cron
echo "*/15 * * * * cd $SCRIPT_DIR && python3 system_health_monitor.py >> health_check.log 2>&1" >> temp_cron
echo "0 8 1 * * cd $SCRIPT_DIR && python3 monthly_duplicate_report.py >> monthly_report.log 2>&1" >> temp_cron

# Install new crontab
crontab temp_cron
rm temp_cron

echo "✅ Cron-Jobs erfolgreich hinzugefügt:"
echo "   📅 Wöchentlicher Check: Montags 9:00 Uhr"
echo "   🏥 Health Monitor: Alle 15 Minuten" 
echo "   📊 Monatlicher Report: 1. jeden Monats 8:00 Uhr"
echo ""
echo "💡 Logs werden in folgenden Dateien gespeichert:"
echo "   - weekly_check.log"
echo "   - health_check.log"
echo "   - monthly_report.log"
echo ""
echo "🔍 Cron-Jobs anzeigen: crontab -l"
