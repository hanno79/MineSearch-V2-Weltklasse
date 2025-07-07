# Umfassende Einschätzung der MineSearch v2 Modell-Tests

**Datum:** 03.07.2025  
**Autor:** rahn  
**Getestete Minen:** Jeffrey Mine, LAB Chrysotile Mine, Horne Mine, East Malartic Mine (alle Quebec, Kanada)

## Executive Summary

Nach umfassenden Tests mit 5 verschiedenen AI-Modellen und 4 Quebec-Minen kann ich eine klare Einschätzung zur Qualität und Eignung der verschiedenen Modelle geben. Insgesamt wurden 20 Einzeltests durchgeführt mit sehr aufschlussreichen Ergebnissen.

## Detaillierte Testergebnisse

### 1. Modell-Performance im Überblick

| Modell | Ø Zeit (s) | Ø Vollständigkeit | Kosten-Findung | Betreiber-Info | Ø Quellen |
|--------|------------|-------------------|----------------|----------------|-----------|
| **Perplexity Sonar** | 42.5s | 50.0% | 50% | 100% | 7.5 |
| **Perplexity Sonar Pro** | 62.7s | 50.0% | 50% | 100% | 9.5 |
| **Perplexity Reasoning Pro** | 54.3s | 47.4% | 50% | 75% | 7.0 |
| **DeepSeek Free** | 49.7s | 50.0% | 75% | 75% | 6.0 |
| **DeepSeek Chat** | 43.2s | 50.0% | 25% | 100% | 7.2 |

### 2. Stärken und Schwächen der einzelnen Modelle

#### **Perplexity Sonar** ⭐⭐⭐⭐
- **Stärken:** 
  - Schnellste Antwortzeit (Ø 42.5s)
  - Zuverlässige Betreiber-Informationen (100%)
  - Gute Balance zwischen Geschwindigkeit und Qualität
- **Schwächen:**
  - Nur 50% Erfolgsquote bei Restaurationskosten
  - Fehlende Koordinaten in allen Tests
- **Fazit:** Ideal für schnelle Übersichten

#### **Perplexity Sonar Pro** ⭐⭐⭐
- **Stärken:**
  - Höchste Anzahl an Quellen (Ø 9.5)
  - Zuverlässige Betreiber-Informationen (100%)
  - Gute Datenqualität
- **Schwächen:**
  - Langsamste Antwortzeit (Ø 62.7s)
  - Keine besseren Ergebnisse trotz höherer Kosten
- **Fazit:** Nicht empfehlenswert - zu langsam ohne Mehrwert

#### **Perplexity Reasoning Pro** ⭐⭐
- **Stärken:**
  - Findet manchmal spezifische Kostendaten ($50M für LAB Mine)
  - Gutes Reasoning für komplexe Zusammenhänge
- **Schwächen:**
  - Niedrigste Vollständigkeit (47.4%)
  - Unzuverlässige Betreiber-Info (nur 75%)
  - Inkonsistente Ergebnisse
- **Fazit:** Nur für spezielle Analysen geeignet

#### **DeepSeek Free** ⭐⭐⭐⭐⭐
- **Stärken:**
  - **Beste Restaurationskosten-Findung (75%)**
  - Kostenlos verfügbar
  - Solide Gesamtperformance
  - Gute Balance bei allen Metriken
- **Schwächen:**
  - Weniger Quellen als Perplexity-Modelle
  - Kein direkter Web-Zugriff (nutzt Enhanced Source Discovery)
- **Fazit:** **BESTE WAHL** für Kosten-Nutzen-Verhältnis

#### **DeepSeek Chat** ⭐⭐⭐
- **Stärken:**
  - Zweitschnellste Antwortzeit (43.2s)
  - Zuverlässige Betreiber-Informationen (100%)
- **Schwächen:**
  - Schlechteste Kosten-Findung (nur 25%)
  - Kostenpflichtig ohne klaren Mehrwert
- **Fazit:** Nicht empfehlenswert für Mining-Recherchen

### 3. Wichtige Erkenntnisse

#### Restaurationskosten-Findung
Die gefundenen Restaurationskosten zeigen interessante Muster:
- Die meisten Modelle geben Platzhalter-Werte zurück ($1-3 CAD)
- Nur Reasoning Pro findet realistische Werte:
  - LAB Chrysotile: $50,000,000 CAD
  - East Malartic: $256,980 CAD
- DeepSeek Free hat die höchste Erfolgsquote (75%)

#### Datenqualität
- Alle Modelle erreichen etwa 50% Vollständigkeit (9-10 von 19 Feldern)
- Kritische Felder oft fehlend: Koordinaten, Produktionsdaten, Fläche
- Betreiber/Eigentümer werden meist gefunden
- Quellen sind meist offizielle Regierungsdokumente

#### Performance
- Antwortzeiten variieren stark (12s - 77s)
- Keine Korrelation zwischen Antwortzeit und Qualität
- OpenRouter-Modelle nutzen Enhanced Source Discovery effektiv

### 4. Empfehlungen für verschiedene Anwendungsfälle

#### 🎯 **Für umfassende Mining-Recherchen:**
**→ DeepSeek Free**
- Beste Kosten-Findung
- Kostenlos
- Solide Gesamtperformance

#### 🎯 **Für schnelle Übersichten:**
**→ Perplexity Sonar**
- Schnellste Antwortzeit
- Zuverlässige Basisdaten
- Gute Quellenangaben

#### 🎯 **Für Spezialrecherchen mit Budget:**
**→ Perplexity Reasoning Pro**
- Findet manchmal spezifische Kostendaten
- Gut für komplexe Analysen
- Nur wenn Budget vorhanden

#### 🎯 **Beste Kombination (wenn Multi-Model funktioniert):**
**→ DeepSeek Free + Perplexity Sonar**
- Kombiniert Geschwindigkeit mit Kosten-Findung
- Kosteneffizient
- Komplementäre Stärken

### 5. Probleme und Verbesserungspotential

#### Technische Probleme:
1. Multi-Model API erwartet `model_ids` statt `models` Parameter
2. Keine Modelle finden GPS-Koordinaten zuverlässig
3. Platzhalter-Werte bei Restaurationskosten ($1-3 CAD)

#### Verbesserungsvorschläge:
1. API-Parameter für Multi-Model korrigieren
2. Spezielle Prompts für Koordinaten-Suche
3. Validierung von Restaurationskosten (unrealistische Werte filtern)
4. Deep Research Modell testen (wurde ausgelassen wegen 30+ Min Laufzeit)

### 6. Fazit

Das MineSearch v2 System funktioniert grundsätzlich gut, aber die Modelle haben unterschiedliche Stärken:

- **DeepSeek Free** ist die beste Gesamtwahl (kostenlos + beste Kosten-Findung)
- **Perplexity Sonar** ist ideal für schnelle Recherchen
- **Sonar Pro** bietet keinen Mehrwert gegenüber Standard Sonar
- **Reasoning Pro** nur für Spezialfälle mit Budget
- **DeepSeek Chat** nicht für Mining-Recherchen geeignet

Die Enhanced Source Discovery funktioniert sehr gut und kompensiert fehlende Web-Suche bei OpenRouter-Modellen. Die Datenqualität ist konsistent bei etwa 50% Vollständigkeit, was für initiale Recherchen ausreichend ist.

## Nächste Schritte

1. Multi-Model API Bug fixen
2. Deep Research Modell in separatem Test evaluieren
3. Spezial-Prompts für bessere Koordinaten-Findung entwickeln
4. Validierung für Restaurationskosten implementieren
5. Batch-Tests mit mehr Minen für statistisch signifikante Ergebnisse