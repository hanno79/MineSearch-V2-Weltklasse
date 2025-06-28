# Such-Optionen Klarstellung - MineSearch V2

**Author:** rahn  
**Datum:** 28.06.2025  
**Version:** 1.0

## 🎯 Die neue klare Struktur

### Such-Modelle (Perplexity API)

1. **⚡ Schnell (sonar-small)**
   - 30 Sekunden Timeout
   - Günstigstes Modell
   - Für einfache, schnelle Anfragen

2. **🎯 Standard (sonar-large/pro)**
   - 60 Sekunden Timeout
   - Beste Balance Qualität/Geschwindigkeit
   - Empfohlen für die meisten Suchen

3. **🌊 Deep Research**
   - 30+ Minuten Timeout
   - Perplexitys spezielles Modell
   - Macht automatisch SEHR umfassende Recherchen
   - Deutlich teurer

### 2-Phasen-Suche (Unsere Implementierung)

☐ **2-Phasen-Suche aktivieren**
- Kann mit JEDEM Modell kombiniert werden
- Fügt 1-2 Minuten zur Suchzeit hinzu
- So funktioniert's:
  - **Phase 1**: Normale Suche mit Fokus auf Quellensammlung
  - **Phase 2**: Bis zu 3 gezielte Nachfragen zu den besten Quellen

## 📊 Mögliche Kombinationen

| Modell | Ohne 2-Phasen | Mit 2-Phasen |
|--------|---------------|--------------|
| Schnell | 30 Sek | 1-2 Min |
| Standard | 60 Sek | 2-3 Min ⭐ |
| Deep Research | 30+ Min | 32+ Min |

## 🎯 Empfehlungen

### Für schnelle Übersicht:
- **Schnell** ohne 2-Phasen (30 Sek)

### Für normale Recherche:
- **Standard** ohne 2-Phasen (60 Sek)

### Für beste Ergebnisse:
- **Standard + 2-Phasen** (2-3 Min) ⭐
- Beste Balance zwischen Zeit und Qualität
- Findet deutlich mehr Quellen

### Für maximale Tiefe:
- **Deep Research** ohne 2-Phasen (30+ Min)
- 2-Phasen hier meist nicht nötig, da Deep Research schon sehr umfassend ist

## 💡 Wichtige Unterschiede

### Deep Research vs. 2-Phasen-Suche:

**Deep Research (Perplexity-Feature):**
- Eingebaute Funktion von Perplexity
- Macht automatisch viele interne Suchen
- Kann 30+ Minuten dauern
- Sehr teuer pro Anfrage

**2-Phasen-Suche (Unsere Funktion):**
- Von uns implementiert
- Nutzt gefundene Quellen für gezielte Nachfragen
- Fügt 1-2 Minuten hinzu
- Funktioniert mit jedem Modell

## ✅ Vorteile der neuen Struktur

1. **Transparenz**: User versteht genau was passiert
2. **Flexibilität**: 6 Kombinationen statt 3
3. **Kontrolle**: Bewusste Wahl von Modell UND Vertiefung
4. **Kosteneffizienz**: 2-Phasen nur wenn gewünscht

Die Checkbox macht den Unterschied zwischen Modell-Wahl und Vertiefungs-Option klar!