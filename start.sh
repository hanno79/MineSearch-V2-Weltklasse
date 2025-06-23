#!/bin/bash
# Hauptstarter für MineSearch UI

echo "🚀 Starte MineSearch UI..."
echo "================================"
echo "Öffne Browser unter: http://localhost:8501"
echo "================================"

# Aktiviere Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Starte Streamlit im Headless-Modus (überspringt Email-Abfrage)
echo "" | python -m streamlit run src/ui/main.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false