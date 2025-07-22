#!/bin/bash

# Author: rahn
# Datum: 16.07.2025
# Version: 1.0
# Beschreibung: Script zur Ausführung der umfassenden API- und Datenbankanalyse für MineSearch v2.1

set -e

echo "🔍 MineSearch v2.1 - Comprehensive API & Database Investigation"
echo "============================================================="

# Prüfe ob Node.js verfügbar ist
if ! command -v node &> /dev/null; then
    echo "❌ Node.js ist nicht installiert. Bitte installiere Node.js zuerst."
    exit 1
fi

# Prüfe ob npm verfügbar ist
if ! command -v npm &> /dev/null; then
    echo "❌ npm ist nicht verfügbar. Bitte installiere npm zuerst."
    exit 1
fi

echo "📦 Installiere Playwright Dependencies..."
npm install

echo "🎭 Installiere Playwright Browser..."
npx playwright install

# Prüfe ob Backend läuft
echo "🔍 Prüfe Backend-Verfügbarkeit..."
if ! curl -s http://localhost:8000/api/models > /dev/null; then
    echo "⚠️  Backend läuft nicht auf localhost:8000"
    echo "   Bitte starte das Backend zuerst:"
    echo "   cd ../../backend && python main.py"
    read -p "   Drücke Enter wenn Backend bereit ist..."
fi

# Erstelle Ausgabeverzeichnisse
echo "📁 Erstelle Ausgabeverzeichnisse..."
mkdir -p test-reports
mkdir -p test-screenshots

# Führe Tests aus
echo "🧪 Starte umfassende Investigation..."
echo "   Dies kann einige Minuten dauern..."

# Führe Test mit verschiedenen Optionen aus
echo "🎯 Führe Tests aus..."
if npx playwright test comprehensive_api_database_investigation.js --reporter=html; then
    echo "✅ Tests erfolgreich abgeschlossen!"
else
    echo "⚠️  Tests abgeschlossen mit Problemen (erwartet für Investigation)"
fi

# Zeige Ergebnisse
echo ""
echo "📊 Untersuchungsergebnisse:"
echo "=========================="

if [ -d "test-reports" ]; then
    echo "📋 Reports erstellt in: test-reports/"
    ls -la test-reports/
    echo ""
fi

if [ -d "test-screenshots" ]; then
    echo "🖼️  Screenshots erstellt in: test-screenshots/"
    ls -la test-screenshots/
    echo ""
fi

if [ -d "playwright-report" ]; then
    echo "📊 Playwright HTML-Report verfügbar:"
    echo "   npx playwright show-report"
    echo ""
fi

echo "🔍 Investigation abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "1. Öffne die Markdown-Reports in test-reports/"
echo "2. Schaue dir die Screenshots in test-screenshots/ an"
echo "3. Prüfe den HTML-Report mit: npx playwright show-report"
echo "4. Analysiere die API-Responses und UI-Probleme"
echo ""
echo "Für detaillierte Analyse der gefundenen Probleme siehe:"
echo "- test-reports/minesearch_investigation_report_*.md"
echo "- test-reports/minesearch_investigation_data_*.json"