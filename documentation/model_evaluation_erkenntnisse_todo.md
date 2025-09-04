# Model Evaluation Erkenntnisse - TODO für später

**Datum:** 04.09.2025  
**Author:** rahn

## ✅ Was funktioniert gut:
- Jede Minensuche wird als separater Eintrag gespeichert (keine Überschreibung)
- Konsistenz-Messung funktioniert (25% bis 100%)
- Performance-Scores berechenbar (0-100)
- Field-Spezialisierung erkennbar

## 📊 Erkenntnisse aus Sigma Mine Test:

### Hohe Konsistenz (100%):
- Koordinaten (x: 48.2345, y: -79.4567)
- Mine Name (Sigma Mine)
- Country (Kanada)
- Rohstoff (Gold)

### Niedrige Konsistenz (<50%):
- Quellenangaben (25% - 4 verschiedene URL-Kombinationen)
- Restaurationskosten (inkonsistent: 12.8M vs 45.2M CAD)

## 🔧 TODO für später (NACH Datenbankbereinigung):

1. **Automatische Integration in Batch-Prozesse**
   - Bei jeder Batch-Suche automatisch Statistiken sammeln
   - Performance-Monitoring in Echtzeit

2. **Modell-Verbesserungen basierend auf Daten:**
   - Prompts für inkonsistente Felder verbessern
   - Spezialisierte Modelle für bestimmte Feldtypen

3. **Erweiterte Metriken implementieren:**
   - Zeitliche Stabilität (Konsistenz über Wochen/Monate)
   - Geographische Genauigkeit (bessere Ergebnisse für bestimmte Länder?)
   - Quellenqualität-Score

4. **Dashboard-Verbesserungen:**
   - Web-Interface für Live-Monitoring
   - Alerts bei Performance-Degradierung
   - Trend-Analysen über Zeit

5. **Ensemble Learning vorbereiten:**
   - Beste Modelle für verschiedene Felder kombinieren
   - Automatische Modell-Auswahl basierend auf Feldtyp

## ⚠️ WICHTIG: 
Diese TODOs erst NACH vollständiger Datenbankbereinigung angehen!
Priorität jetzt: Sauberes, einheitliches normalisiertes Schema ohne Altlasten.