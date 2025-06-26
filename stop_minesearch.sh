#!/bin/bash
# Author: rahn
# Datum: 27.06.2025
# Beschreibung: Stoppt MineSearch sauber

if [ -f minesearch.pid ]; then
    PID=$(cat minesearch.pid)
    
    # Prüfe ob Prozess läuft
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stoppe MineSearch (PID: $PID)..."
        kill $PID
        
        # Warte bis Prozess beendet ist
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ MineSearch erfolgreich gestoppt"
                rm -f minesearch.pid
                exit 0
            fi
            sleep 1
        done
        
        # Force kill falls nötig
        echo "Force kill..."
        kill -9 $PID 2>/dev/null
        rm -f minesearch.pid
        echo "✅ MineSearch gestoppt (forced)"
    else
        echo "⚠️  MineSearch Prozess (PID: $PID) läuft nicht mehr"
        rm -f minesearch.pid
    fi
else
    echo "ℹ️  MineSearch läuft nicht (keine PID-Datei gefunden)"
    
    # Zusätzlich nach Streamlit Prozessen suchen
    PIDS=$(pgrep -f "streamlit.*main.py")
    if [ ! -z "$PIDS" ]; then
        echo "Gefundene Streamlit Prozesse: $PIDS"
        echo "Stoppe alle Streamlit Prozesse..."
        pkill -f "streamlit.*main.py"
        echo "✅ Alle Streamlit Prozesse gestoppt"
    fi
fi