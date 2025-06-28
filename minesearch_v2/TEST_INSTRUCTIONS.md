# MineSearch V2 Test-Anleitung

## 🚀 Server läuft!

MineSearch Version 2 ist jetzt verfügbar unter:
**http://localhost:8000**

## 📋 Schritt-für-Schritt Test-Anleitung

### 1. **Einzelsuche testen**

1. Öffnen Sie http://localhost:8000 im Browser
2. Geben Sie einen Minennamen ein, z.B.:
   - "Canadian Malartic" (gute Dokumentation)
   - "Grasberg" (bekannte Mine)
   - "Cerro Verde" (Peru)

3. **Standard-Suche testen** (schnell):
   - Such-Modus: "Standard-Suche (schnell)"
   - Klicken Sie "Suche starten"
   - Ergebnis in 30-60 Sekunden

4. **Erweiterte 2-Phasen-Suche testen** (NEU!):
   - Such-Modus: "Erweiterte 2-Phasen-Suche (mehr Quellen)"
   - Klicken Sie "Suche starten"
   - Wartezeit: 1-2 Minuten
   - Erwarten Sie deutlich mehr Quellen!

### 2. **Vergleichen Sie die Ergebnisse**

Achten Sie besonders auf:
- **Anzahl gefundener Quellen** (im Abschnitt "📚 Gefundene Quellen")
- **Qualität der Restaurationskosten-Daten**
- **Vielfalt der Quellen** (URLs, Dokumente, Organisationen)

### 3. **CSV Batch-Verarbeitung**

Die CSV-Upload-Funktion funktioniert ebenfalls. Eine Test-CSV ist bereits vorhanden.

### 4. **System Status**

Prüfen Sie den Health-Check:
http://localhost:8000/health

## 🎯 Was ist neu?

1. **Verbesserte Quellensammlung**: Explizit nach Quellen, Reports, URLs gefragt
2. **Quellenextraktion**: Automatische Erkennung aller URLs und Dokumente
3. **2-Phasen-Suche**: Vertiefung basierend auf gefundenen Top-Quellen
4. **Strukturierte Anzeige**: Quellen werden kategorisiert angezeigt

## ⚠️ Bekannte Hinweise

- Die erweiterte Suche dauert länger (1-2 Min) aber liefert bessere Ergebnisse
- Der Server läuft auf Port 8000
- API-Key ist konfiguriert und funktioniert

## 🛑 Server stoppen

```bash
pkill -f uvicorn
```

Viel Spaß beim Testen!