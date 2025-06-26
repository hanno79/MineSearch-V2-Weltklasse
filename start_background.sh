#!/bin/bash
# Author: rahn
# Datum: 27.06.2025
# Beschreibung: Startet MineSearch im Hintergrund

# Beende alte Prozesse falls vorhanden
pkill -f streamlit 2>/dev/null
sleep 2

# Erstelle logs Verzeichnis falls nicht vorhanden
mkdir -p logs

echo "Starte MineSearch im Hintergrund..."

# Starte Streamlit im Hintergrund
nohup python -m streamlit run src/ui/main.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false \
  > logs/streamlit.log 2>&1 & 

# Speichere PID
echo $! > minesearch.pid

# Warte kurz
sleep 3

# Prüfe ob Prozess läuft
if ps -p $(cat minesearch.pid) > /dev/null; then
    echo "✅ MineSearch erfolgreich gestartet!"
    echo "   PID: $(cat minesearch.pid)"
    echo "   URL: http://localhost:8501"
    echo "   Logs: tail -f logs/streamlit.log"
    echo ""
    echo "Zum Stoppen: ./stop_minesearch.sh"
else
    echo "❌ Fehler beim Starten von MineSearch"
    echo "   Prüfen Sie: tail logs/streamlit.log"
    rm -f minesearch.pid
    exit 1
fi