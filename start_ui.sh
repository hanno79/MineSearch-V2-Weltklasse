#\!/bin/bash
# Start-Skript für MineSearch UI

echo "🚀 Starte MineSearch UI..."
echo "================================"
echo "Öffne Browser unter: http://localhost:8501"
echo "================================"

# Aktiviere Virtual Environment falls vorhanden
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Starte Streamlit
python -m streamlit run src/ui/main.py --server.port 8501 --server.address localhost

