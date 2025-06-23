# Active UI Documentation
## Stand: 18.06.2025

### AKTIVE UI:
**Datei:** `/app/src/ui/main.py`
**Typ:** Single-Page Streamlit Application (KEINE Wizard/Multi-Step UI)
**Version:** 18.06.2025-v2

### Warum diese UI?
- Enthält alle Bugfixes der letzten Entwicklung
- Einfachere Architektur als Multi-Step Wizard
- Bessere Performance und Wartbarkeit

### UI-Features:
1. **Sidebar-basierte Konfiguration**
   - Manual Entry oder CSV Upload
   - Agent-Auswahl mit Live-Counter
   - Debug Mode für Entwicklung

2. **Hauptbereich**
   - Suchergebnisse-Anzeige
   - Export-Funktionen
   - Status-Updates während Suche

3. **Technische Details**
   - Verwendet Form-Submit statt einfachen Button (zuverlässiger)
   - Session State für Datenübertragung zwischen Sidebar und Hauptbereich
   - Async/Await für Suchoperationen

### Wie starten:
```bash
# Option 1: Restart Script (empfohlen)
./restart_ui.sh

# Option 2: Direkt
python -m streamlit run src/ui/main.py

# Option 3: Via run.py
python run.py
```

### WICHTIG - Keine UI-Duplikate:
- NUR `/app/src/ui/main.py` ist aktiv
- Alle anderen UIs sind in `/app/to_delete/`
- NIEMALS neue UI-Dateien erstellen ohne diese Doku zu aktualisieren

### Bekannte Probleme:
1. Button-Click benötigt Form-Submit für Zuverlässigkeit
2. Session State muss zwischen Sidebar und Main synchronisiert werden

### Verzeichnisstruktur:
```
/app/src/ui/
├── main.py          <- EINZIGE AKTIVE UI
├── components/      <- Für zukünftige UI-Komponenten
└── pages/          <- Nicht verwendet (war für Multi-Page)
```

### Gelöschte/Verschobene UIs:
- `/app/to_delete/main_multipage_ui.py` - Die Wizard-UI mit Steps
- `/app/to_delete/streamlit_app_*` - Verschiedene alte Versionen
- Alle Test-UIs in `/app/to_delete/`

### Entwicklungshinweise:
1. IMMER diese Datei prüfen bevor UI-Änderungen gemacht werden
2. Keine neuen Streamlit-Apps erstellen ohne Absprache
3. Bei UI-Problemen zuerst Debug Tools aktivieren
4. Form-Submit verwenden statt einfache Buttons für kritische Aktionen