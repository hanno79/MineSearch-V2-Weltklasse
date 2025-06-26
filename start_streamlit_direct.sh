#!/bin/bash
# Direkter Streamlit Start-Script als Backup

echo "Starte MineSearch direkt mit Streamlit..."
python -m streamlit run src/ui/main.py --server.port 8501 --server.address 0.0.0.0 --server.headless true