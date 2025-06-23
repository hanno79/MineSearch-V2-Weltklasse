#!/bin/bash
# Stop all streamlit processes and restart main UI

echo "🛑 Stoppe alle Streamlit-Prozesse..."
pkill -f streamlit || true
sleep 2

echo "🚀 Starte MineSearch UI neu..."
echo "================================"
echo "Öffne Browser unter: http://localhost:8501"
echo "================================"

# Aktiviere Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Starte die RICHTIGE UI
python -m streamlit run src/ui/main.py --server.port 8501 --server.address localhost