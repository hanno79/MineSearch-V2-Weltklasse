# MineSearch v2 - Umfassender Testplan

Author: rahn  
Datum: 06.07.2025  
Version: 2.0  
Beschreibung: Systematischer Testplan mit Fokus auf Restaurationskosten und Source-Sharing

=====================================

## 1. TESTZIELE

### Primäre Ziele (Priorität: HOCH)
- **Restaurationskosten-Validierung**: Test der verbesserten Extraktion (Schwellenwert: $1.000)
- **Source-Sharing-Optimierung**: Cross-Provider Quellennutzung maximieren
- **Beste Modelle identifizieren**: Für Finanzdaten und kritische Felder
- **Keine Dummy-Daten**: Validierung dass keine Platzhalter verwendet werden

### Sekundäre Ziele
- Vollständige Überprüfung aller Provider einzeln
- Test aller Multi-Model Kombinationen
- Analyse der Suchtiefe und Quellenqualität
- Performance-Optimierung

## 2. TEST-MINEN (Beispiel-CSV)

### Quebec-Minen mit unterschiedlichen Charakteristika:
1. **Jeffrey Mine** (Asbest)
   - Große, gut dokumentierte Mine
   - Erwartung: Hohe Datenverfügbarkeit

2. **LAB Chrysotile Mine** (Chrysotil)
   - Mittlere Bekanntheit
   - Erwartung: Moderate Datenverfügbarkeit

3. **Horne Mine** (Kupfer)
   - Historische Mine
   - Erwartung: Gute historische Daten

4. **East Malartic Mine** (Gold)
   - Aktive Mine
   - Erwartung: Aktuelle Betreiberdaten

5. **Niobec Mine** (Niob)
   - Spezialisierte Mine
   - Erwartung: Technische Daten

## 3. TESTSZENARIEN

### 3.1 EINZELMODELL-TESTS
Jeder Provider wird einzeln getestet:

#### Perplexity:
- perplexity:sonar
- perplexity:sonar-pro
- perplexity:sonar-deep-research
- perplexity:sonar-reasoning-pro

#### OpenRouter:
- openrouter:deepseek-free

#### Tavily:
- tavily:search
- tavily:deep-research

#### Exa:
- exa:neural-search
- exa:similarity-search

#### Abacus (wenn aktiviert):
- abacus:deep-agent

#### OpenAI (Premium):
- openai:gpt-4.1
- openai:gpt-4.1-mini

#### Anthropic (Premium):
- anthropic:claude-4-sonnet
- anthropic:claude-3.7-sonnet

#### Gemini (Premium):
- gemini:gemini-2.5-pro
- gemini:gemini-2.5-flash

#### Grok (Premium):
- grok:grok-3-beta
- grok:grok-3-beta-mini

### 3.2 MULTI-MODEL KOMBINATIONEN

#### 2er-Kombinationen:
1. Perplexity + Tavily
2. Perplexity + Exa
3. Tavily + Exa
4. OpenRouter + Perplexity
5. OpenRouter + Tavily
6. OpenAI + Gemini (Premium-Kombination)
7. Anthropic + Grok (Premium-Kombination)
8. Perplexity + OpenAI (Such + Premium)
9. Tavily + Anthropic (Such + Premium)
10. Exa + Gemini (Such + Premium)

#### 3er-Kombinationen:
1. Perplexity + Tavily + Exa
2. Perplexity + OpenRouter + Tavily
3. Tavily + Exa + OpenRouter
4. OpenAI + Anthropic + Gemini (Premium-Trio)
5. Perplexity + OpenAI + Anthropic (Such + Premium Mix)
6. Tavily + Gemini + Grok (Such + Premium Mix)
7. Exa + OpenAI + Grok (Such + Premium Mix)

#### Premium-Fokus Kombinationen (Restaurationskosten):
1. OpenAI + Anthropic + Perplexity:deep-research
2. Gemini + Grok + Tavily:deep-research
3. Alle Premium: OpenAI + Anthropic + Gemini + Grok

#### Vollständige Kombination:
- Alle verfügbaren Provider gleichzeitig (27 Modelle)

### 3.3 SPEZIALTESTS

#### Zwei-Phasen-Suche:
- Phase 1: Schnelle Quellensuche
- Phase 2: Detaillierte Datenextraktion
- Phase 3: Deep Research (wenn nötig)

#### Sprachspezifische Tests:
- Englische Suche
- Französische Suche (für Quebec)
- Mehrsprachige Suche

## 4. METRIKEN

### 4.1 Quantitative Metriken:
- **Datenabdeckung**: % der ausgefüllten Felder
- **Kritische Felder**: Restaurationskosten, Koordinaten, Betreiber
- **Quellenanzahl**: Anzahl gefundener Quellen
- **Quellenqualität**: Offizielle vs. inoffizielle Quellen
- **Suchtiefe**: Wurden Unterseiten/PDFs durchsucht?
- **Response-Zeit**: Durchschnittliche Antwortzeit

### 4.2 Qualitative Metriken:
- **Datenqualität**: Plausibilität der Werte
- **Aktualität**: Wie aktuell sind die Daten?
- **Vollständigkeit**: Wurden alle relevanten Aspekte abgedeckt?
- **Konsistenz**: Stimmen Daten zwischen Quellen überein?

## 5. DEBUG-SCHRITTE FÜR TAVILY/EXA

### 5.1 API-Verbindung prüfen:
1. Health-Check durchführen
2. API-Key Validierung
3. Request/Response Logging aktivieren

### 5.2 Query-Analyse:
1. Generierte Queries ausgeben
2. Parameter-Validierung
3. Response-Struktur prüfen

### 5.3 Fehleranalyse:
1. HTTP Status Codes prüfen
2. Error Messages analysieren
3. Timeout-Probleme identifizieren

## 6. TESTDURCHFÜHRUNG

### Phase 1: Vorbereitung
- [ ] Test-CSV erstellen
- [ ] Logging auf DEBUG setzen
- [ ] Cache deaktivieren für Tests

### Phase 2: Einzeltests
- [ ] Jeden Provider einzeln mit jeder Mine testen
- [ ] Fehler und Probleme dokumentieren
- [ ] Response-Zeiten messen

### Phase 3: Kombinationstests
- [ ] Alle 2er-Kombinationen
- [ ] Alle 3er-Kombinationen
- [ ] Vollständige Kombination

### Phase 4: Analyse
- [ ] Ergebnisse aggregieren
- [ ] Beste Konfigurationen identifizieren
- [ ] Probleme mit Tavily/Exa lösen

## 7. ERWARTETE ERGEBNISSE

### Optimale Konfiguration sollte:
- Mindestens 70% Datenabdeckung erreichen
- Kritische Felder zuverlässig finden
- Unter 30 Sekunden Response-Zeit bleiben
- Keine Platzhalter-Werte generieren

### Problem-Identifikation:
- Warum liefern Tavily/Exa keine Ergebnisse?
- Welche Provider sind am zuverlässigsten?
- Welche Kombinationen sind optimal?

## 8. SOURCE-SHARING SPEZIAL-TESTS

### 8.1 Cross-Provider Quellenanalyse
1. **Quellen-Sammlung Phase**:
   - Jedes Modell sammelt Quellen unabhängig
   - Dokumentiere unique Quellen pro Provider
   - Identifiziere Überschneidungen

2. **Quellen-Sharing Phase**:
   - Teile Perplexity-Quellen mit DeepSeek
   - Teile DeepSeek-Quellen mit Perplexity
   - Teile Scraping-Quellen mit AI-Modellen
   - Messe Verbesserung der Ergebnisse

3. **Iterative Verbesserung**:
   - Nutze neue Quellen für weitere Suchen
   - Priorisiere Restaurationskosten-Quellen
   - Dokumentiere Synergie-Effekte

### 8.2 Erwartete Verbesserungen
- Mehr gefundene Restaurationskosten
- Bessere Quellenabdeckung
- Höhere Datenqualität
- Reduzierte Suchzeit durch gezielte Quellen

## 9. RESTAURATIONSKOSTEN FOKUS-TESTS

### 9.1 Spezielle Test-Szenarien
1. **Kleine Minen**: Explorationsprojekte mit Kosten $5.000-$50.000
2. **Geschlossene Minen**: Hohe Restaurationskosten erwartet
3. **Aktive Minen**: ARO und Provisions
4. **GESTIM-Integration**: Quebec-spezifische Quellen

### 9.2 Validierung
- Alle Beträge ab $1.000 müssen erkannt werden
- Keine Filterung kleiner Beträge
- Korrekte Währungsangaben
- Jahr der Kostenschätzung

## 10. DOKUMENTATION

Alle Testergebnisse werden dokumentiert in:
- comprehensive_test_results_[timestamp].json
- test_analysis_[timestamp].md
- best_practices_[timestamp].md
- source_sharing_analysis_[timestamp].json

## 11. ÄNDERUNGS-HISTORIE

- **05.07.2025 v1.0**: Initialer Testplan
- **06.07.2025 v2.0**: Erweiterung um Restaurationskosten-Fokus und Source-Sharing
- **06.07.2025 v2.1**: Integration der Premium LLM Provider (OpenAI, Anthropic, Gemini, Grok)