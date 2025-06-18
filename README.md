# Multi-Agent Mining Research System

Ein automatisiertes System zur Recherche von Mineninformationen weltweit mit Fokus auf Umwelt- und Finanzdaten.

## Features

- 🤖 Multi-Agent-System mit paralleler Verarbeitung
- 🔍 Automatisierte Informationsextraktion aus verschiedenen Quellen
- 📊 Intelligente Datenaggregation mit Scoring-System
- 🌍 Mehrsprachige Recherche
- 📁 CSV-Export mit konfigurierbaren Trennzeichen

## Installation

1. Python Virtual Environment erstellen:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Konfiguration:
   - Kopiere `config/.env.example` nach `.env`
   - Füge deine API-Keys ein

## Projekt-Struktur

```
mine-search/
├── src/
│   ├── agents/        # AI-Agenten (Claude, GPT-4, etc.)
│   ├── core/          # Kern-Funktionalität
│   ├── data/          # Datenverarbeitung
│   └── ui/            # Streamlit GUI
├── tests/             # Unit-Tests
├── logs/              # Log-Dateien
└── data/              # Ein-/Ausgabedaten
```

## Verwendung

```bash
streamlit run src/ui/main.py
```

## Entwicklung

- Python 3.10+
- Asyncio für parallele Verarbeitung
- SQLite für lokale Datenhaltung
- Streamlit für die Benutzeroberfläche

## Dokumentation

Siehe `/documentation/` für detaillierte Informationen.