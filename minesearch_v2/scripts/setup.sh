#!/bin/bash
# MineSearch 2.0 Setup Script
# Author: rahn
# Datum: 27.06.2025

echo "==================================="
echo "MineSearch 2.0 Setup"
echo "==================================="
echo ""

# Prüfe Python Version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo " Python Version: $python_version"

# Erstelle virtuelle Umgebung
echo ""
echo "’ Erstelle virtuelle Umgebung..."
python3 -m venv venv

# Aktiviere venv
echo "’ Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Upgrade pip
echo "’ Aktualisiere pip..."
pip install --upgrade pip

# Installiere Dependencies
echo ""
echo "’ Installiere Dependencies..."
pip install -r requirements.txt

# Erstelle .env aus .env.example
if [ ! -f .env ]; then
    echo ""
    echo "’ Erstelle .env Datei..."
    cp .env.example .env
    echo " .env erstellt - BITTE PERPLEXITY_API_KEY EINTRAGEN!"
fi

# Erstelle Datenbank-Verzeichnis für später
mkdir -p data

echo ""
echo "==================================="
echo " Setup abgeschlossen!"
echo "==================================="
echo ""
echo "Nächste Schritte:"
echo "1. Bearbeite .env und trage deinen PERPLEXITY_API_KEY ein"
echo "2. Starte den Server mit: cd backend && python main.py"
echo "3. Öffne http://localhost:8000"
echo ""
echo "Viel Erfolg mit MineSearch 2.0!"