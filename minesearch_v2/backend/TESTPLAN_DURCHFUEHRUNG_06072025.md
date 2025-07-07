# MineSearch v2 - Testplan Durchführung

**Author:** rahn  
**Datum:** 06.07.2025  
**Version:** 1.0  
**Beschreibung:** Strukturierte Durchführungsplanung für alle Tests mit Premium LLMs

=====================================

## 🎯 EXECUTIVE SUMMARY

Mit allen 11 Providern (27 Modellen) aktiv, führen wir nun systematische Tests durch mit Fokus auf:
1. **Restaurationskosten-Extraktion** (HÖCHSTE PRIORITÄT)
2. **Premium LLM Performance** für Finanzdaten
3. **Source-Sharing Optimierung**
4. **Beste Provider-Kombinationen**

=====================================

## 📋 TESTDURCHFÜHRUNG - PHASEN

### PHASE 1: QUICK VALIDATION (30 Minuten)
**Ziel:** Sicherstellen dass alle Provider funktionieren

1. **Single Mine Test** (Jeffrey Mine, Quebec)
   ```bash
   cd /app/minesearch_v2/backend
   python test_models_quick_quebec.py
   ```
   - Testet alle 27 Modelle einzeln
   - Validiert API-Verbindungen
   - Erste Performance-Metriken

2. **Quick Results Review**
   - Prüfe ob alle Provider Ergebnisse liefern
   - Identifiziere sofortige Probleme
   - Dokumentiere Response-Zeiten

### PHASE 2: PREMIUM MODEL FOCUS (1 Stunde)
**Ziel:** Premium LLMs für Restaurationskosten optimieren

1. **Premium Provider Einzeltests**
   ```bash
   python test_new_providers.py
   ```
   Test-Minen mit erwarteten Restaurationskosten:
   - Jeffrey Mine (große ARO erwartet)
   - Horne Mine (historische Daten)
   - East Malartic (aktive Mine mit Provisions)

2. **Premium Kombinationen**
   ```bash
   python test_combinations.py --premium-only
   ```
   Fokus-Kombinationen:
   - OpenAI + Anthropic (Maximum Intelligence)
   - Gemini + Grok (Real-time + Archive)
   - Alle 4 Premium Provider

### PHASE 3: COMPREHENSIVE TESTING (2-3 Stunden)
**Ziel:** Vollständige Systemvalidierung

1. **Alle Einzelmodelle** (27 Tests)
   ```bash
   python test_all_providers_comprehensive.py
   ```
   - 5 Test-Minen × 27 Modelle = 135 Einzeltests
   - Detaillierte Metriken pro Modell
   - Fehleranalyse

2. **Multi-Model Kombinationen**
   ```bash
   python test_combinations.py --all
   ```
   - 10 × 2er-Kombinationen
   - 7 × 3er-Kombinationen  
   - 3 × Premium-Fokus
   - 1 × Vollständige Kombination

3. **Source-Sharing Tests**
   ```bash
   python test_source_sharing.py
   ```
   - Cross-Provider Quellennutzung
   - Iterative Verbesserung
   - Synergie-Effekte messen

### PHASE 4: DEEP RESEARCH (1 Stunde)
**Ziel:** Maximale Datenextraktion für kritische Fälle

1. **Two-Phase Search Strategy**
   ```bash
   python test_complete_system.py --deep-research
   ```
   - Phase 1: Breite Quellensuche
   - Phase 2: Detailextraktion mit Premium LLMs
   - Phase 3: Deep Research für fehlende Daten

2. **Schwierige Minen**
   Test mit Minen die wenig öffentliche Daten haben:
   - Kleine Explorationsprojekte
   - Geschlossene historische Minen
   - Spezialisierte Rohstoffe

### PHASE 5: ANALYSE & OPTIMIERUNG (30 Minuten)
**Ziel:** Erkenntnisse zusammenfassen und System optimieren

1. **Ergebnisanalyse**
   - Beste Provider für Restaurationskosten
   - Optimale Kombinationen
   - Performance vs. Kosten

2. **Konfigurationsoptimierung**
   - Provider-Prioritäten anpassen
   - Timeout-Optimierung
   - Cache-Strategie

=====================================

## 🚀 SOFORT-START KOMMANDOS

```bash
# 1. Quick Test (5 Minuten)
cd /app/minesearch_v2/backend
python test_models_quick_quebec.py

# 2. Premium Provider Test (10 Minuten)
python test_new_providers.py

# 3. Beste Kombinationen (15 Minuten)
python test_combinations.py --top-5

# 4. Vollständiger Test (2+ Stunden)
python test_all_providers_comprehensive.py
```

=====================================

## 📊 ERWARTETE ERGEBNISSE

### Premium LLMs sollten exzellent sein bei:
- **Finanzberichte-Analyse** (Annual Reports, Quartalsberichte)
- **Tabellen-Extraktion** (ARO aus Bilanzen)
- **Kontextverständnis** (Fußnoten, Querverweise)
- **Mehrsprachige Dokumente** (Englisch/Französisch für Quebec)

### Optimale Provider-Kombinationen erwartet:
1. **Für Restaurationskosten:**
   - Perplexity:deep-research + OpenAI:gpt-4.1 + Anthropic:claude-4
   
2. **Für Geschwindigkeit:**
   - OpenRouter:deepseek + Gemini:flash + Grok:mini

3. **Für Vollständigkeit:**
   - Alle Premium Provider + Tavily:deep-research + Exa:neural

=====================================

## 🔍 DEBUG-FOKUS

Falls Provider keine Ergebnisse liefern:
1. API-Key Validierung prüfen
2. Request/Response Logs aktivieren
3. Timeout-Probleme identifizieren
4. Query-Generierung debuggen

Spezielle Aufmerksamkeit für:
- Tavily (hatte zuvor Probleme)
- Exa (neue Integration)
- Abacus (wenn aktiviert)

=====================================

## 📈 METRIKEN-TRACKING

Für jeden Test dokumentieren:
- ✅ Erfolgsrate (% erfolgreiche Responses)
- ⏱️ Response-Zeit (Durchschnitt und Max)
- 📊 Datenabdeckung (% ausgefüllte Felder)
- 💰 Restaurationskosten gefunden (Ja/Nein + Betrag)
- 🔗 Quellenanzahl und -qualität
- 🎯 Kritische Felder (Koordinaten, Betreiber, Status)

=====================================

## 🏁 NÄCHSTE SCHRITTE

1. **JETZT:** Quick Validation starten
2. **DANN:** Premium Provider testen
3. **PARALLEL:** Logs beobachten für Probleme
4. **ABSCHLUSS:** Beste Konfiguration dokumentieren

Die Tests sind so strukturiert, dass wir schnell erste Ergebnisse sehen und dann systematisch in die Tiefe gehen. Premium LLMs sollten besonders bei der Extraktion von Finanzdaten glänzen!