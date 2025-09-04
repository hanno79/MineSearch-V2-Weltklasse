# MineSearch v2.1 Comprehensive Workflow Test Plan
## Systematische Validierung aller geplanten Features

**Author**: rahn  
**Datum**: 19.07.2025  
**Version**: 1.0  
**Zweck**: Vollständige End-to-End Validierung der MineSearch v2.1 Quebec Mining Optimierungen

---

## ÜBERSICHT

Dieser Testplan validiert ALLE geplanten Features der MineSearch v2.1 Quebec Mining Workflow-Optimierungen systematisch durch Mikro-Tasks. Jeder Test hat spezifische Erfolgskriterien und erwartete realistische Ergebnisse.

---

## 1. MULTILINGUAL QUEBEC MINING SEARCH

### 1.1 Quebec Mining CSV Upload Validierung
**Zweck**: Prüfen ob Quebec-spezifische Mining-Daten korrekt erkannt werden  
**Erwartetes Ergebnis**: System erkennt Quebec Mining Kontext automatisch

**Test-Schritte**:
1. CSV mit Quebec Minen hochladen (Abitibi-Témiscamingue, Nord-du-Québec)
2. Validieren: Mine names wie "Lac Bloom", "Raglan", "Canadian Malartic"
3. Validieren: Französische Regionen erkannt (Abitibi-Témiscamingue, etc.)
4. Validieren: Bilingual detection aktiviert für Quebec entries

**Erfolgskriterien**:
- [ ] Quebec Region detection: ✅ "Quebec" oder "Québec" erkannt
- [ ] Französische Akzente preserved: ✅ "Abitibi-Témiscamingue" korrekt
- [ ] Mine names mit französischen Begriffen: ✅ "Lac", "Rivière" erkannt
- [ ] System aktiviert automatisch bilinguale Suche

### 1.2 Bilingual Mining Terminology Detection
**Zweck**: Prüfen ob französisch/englische Mining-Begriffe parallel gesucht werden  
**Erwartetes Ergebnis**: Beide Sprachen generieren brauchbare Resultate

**Test-Schritte**:
1. Suche nach Mine mit französischem Namen (z.B. "Lac Bloom")
2. Prüfen Query Logs: Englische UND französische Suchbegriffe verwendet
3. Validieren Terminologie-Mapping: "propriétaire" ↔ "owner"
4. Prüfen Ergebnisse: Französische UND englische Quellen gefunden

**Erfolgskriterien**:
- [ ] Query enthält: "propriétaire" UND "owner" für Eigentümer-Suche
- [ ] Query enthält: "exploitant" UND "operator" für Betreiber-Suche  
- [ ] Query enthält: "coûts de restauration" UND "restoration costs"
- [ ] Mindestens 30% der Quellen sind französischsprachig (Quebec context)

### 1.3 Französische Akzente in Suchbegriffen
**Zweck**: Prüfen ob Akzente korrekt gehandhabt werden für bessere Findability  
**Erwartetes Ergebnis**: Akzente UND ohne Akzente finden Resultate

**Test-Schritte**:
1. Suche nach "Propriétaire" (mit Akzent)
2. Suche nach "Proprietaire" (ohne Akzent)  
3. Suche nach "Québec" vs "Quebec"
4. Validieren: Beide Varianten finden dieselben Quellen

**Erfolgskriterien**:
- [ ] "Propriétaire" findet französische Quellen
- [ ] "Proprietaire" findet dieselben französischen Quellen
- [ ] "Québec" UND "Quebec" suchen parallel
- [ ] Accent-normalization in Query Building aktiv

---

## 2. STAGED QUEBEC MINING WORKFLOW

### 2.1 GESTIM Connector Integration
**Zweck**: Prüfen ob GESTIM als primäre Quebec Source automatisch genutzt wird  
**Erwartetes Ergebnis**: GESTIM Daten für alle Quebec Minen abgerufen

**Test-Schritte**:
1. Quebec Mine suchen (z.B. "Canadian Malartic")
2. Prüfen Logs: GESTIM Connector aufgerufen
3. Validieren: GESTIM-spezifische Daten extrahiert
4. Prüfen: GESTIM als high-priority Source markiert

**Erfolgskriterien**:
- [ ] Log-Entry: "[GESTIM] Connector activated for Quebec mine"
- [ ] GESTIM URL in Sources gefunden: gestim.mines.gouv.qc.ca
- [ ] Mining titles/permits aus GESTIM extrahiert
- [ ] GESTIM Reliability Score > 0.9 in source_metrics

### 2.2 Quebec Registry Connector Aktivierung
**Zweck**: Prüfen ob Quebec Mining Registry automatisch durchsucht wird  
**Erwartetes Ergebnis**: Offizielle Quebec Bergbau-Datenbanken integriert

**Test-Schritte**:
1. Quebec Mine mit bekannten Registry-Daten suchen
2. Prüfen: Quebec Registry Connector aufgerufen
3. Validieren: MERN (Ministère des Ressources naturelles) Daten
4. Prüfen: Permit/License Informationen extrahiert

**Erfolgskriterien**:
- [ ] Log-Entry: "[QUEBEC-REGISTRY] Searching official databases"
- [ ] MERN URL gefunden: mern.gouv.qc.ca
- [ ] Mining permits/licenses mit Quebec-spezifischen Nummern
- [ ] Mindestens 2 offizielle Quebec Government Sources

### 2.3 Source Discovery → Content Extraction Pipeline
**Zweck**: Prüfen ob ZUERST Quellen gesammelt, DANN Content extrahiert wird  
**Erwartetes Ergebnis**: Systematischer 2-Phasen Workflow mit Source-Quality

**Test-Schritte**:
1. Comprehensive Search für Quebec Mine starten
2. Phase 1: Prüfen Source Discovery läuft ZUERST
3. Phase 2: Content Extraction von entdeckten Sources
4. Validieren: Source Quality Metrics aktualisiert

**Erfolgskriterien**:
- [ ] Log-Entry: "[PHASE-1] Source Discovery started"
- [ ] Mindestens 10-15 relevante Sources gesammelt BEVOR Extraction
- [ ] Log-Entry: "[PHASE-2] Content Extraction from {X} sources"
- [ ] Source Quality Metrics in Database aktualisiert

### 2.4 Comprehensive Search Orchestrator Integration
**Zweck**: Prüfen ob kompletter systematischer Workflow ausgeführt wird  
**Erwartetes Ergebnis**: Orchestrator koordiniert alle Spezial-Features

**Test-Schritte**:
1. Comprehensive Search Option im Frontend aktivieren
2. Validieren: Orchestrator übernimmt Workflow-Steuerung
3. Prüfen: Alle Specialized Prompts ausgeführt
4. Validieren: Field Completion Report generiert

**Erfolgskriterien**:
- [ ] Log-Entry: "[ORCHESTRATOR] Comprehensive search initiated"
- [ ] Mindestens 5 verschiedene Extraction Strategies ausgeführt
- [ ] Field Completion Report zeigt >70% für kritische Felder
- [ ] Source Quality Report mit >5 high-quality Sources

---

## 3. SPECIALIZED EXTRACTION & PROMPTS

### 3.1 Restaurationskosten Spezielle Prompts
**Zweck**: Prüfen ob spezialisierte Restoration Cost Extraction funktioniert  
**Erwartetes Ergebnis**: Genaue Kostenwerte mit Währung und Jahr

**Test-Schritte**:
1. Mine mit bekannten Restoration Costs suchen (z.B. Canadian Malartic)
2. Prüfen: Spezielle ARO/Closure Cost Prompts verwendet
3. Validieren: Kostenwerte mit Währung extrahiert
4. Prüfen: Jahr der Kostenschätzung gefunden

**Erfolgskriterien**:
- [ ] Restoration Cost Field gefüllt mit realistischem Wert (>$1M)
- [ ] Währung erkannt: CAD, USD, oder $
- [ ] Jahr der Kostenschätzung: 2020-2025
- [ ] Französische UND englische Cost-Terminologie gesucht

### 3.2 Mining Information Separate Prompts
**Zweck**: Prüfen ob Mine-spezifische Informationen gezielt extrahiert werden  
**Erwartetes Ergebnis**: Detaillierte Mining-Parameter mit hoher Genauigkeit

**Test-Schritte**:
1. Bekannte Mine mit verfügbaren Daten suchen
2. Prüfen: Mining Type, Commodity, Production Data Prompts
3. Validieren: Produktionsmengen, Betriebsart, Rohstoffe
4. Prüfen: Quebec-spezifische Mining Terminologie

**Erfolgskriterien**:
- [ ] Mining Type: "Open Pit", "Underground", oder "Tagebau"
- [ ] Commodity: Spezifische Rohstoffe (Gold, Iron Ore, etc.)
- [ ] Production Data: Realistische Mengen mit Einheiten
- [ ] Französische Mining-Begriffe in Ergebnissen

### 3.3 Field-specific Extraction Strategies
**Zweck**: Prüfen ob verschiedene Felder unterschiedliche Suchstrategien nutzen  
**Erwartetes Ergebnis**: Optimierte Extraction je nach Datentyp

**Test-Schritte**:
1. Koordinaten-Extraktion: GPS-spezifische Patterns
2. Eigentümer-Extraktion: Corporate-spezifische Suchbegriffe
3. Restaurationskosten: Financial-spezifische Patterns
4. Validieren: Field-specific Success Rates unterschiedlich

**Erfolgskriterien**:
- [ ] Koordinaten: Decimal Degrees Format (z.B. 48.7567, -77.7824)
- [ ] Eigentümer: Corporate Namen mit korrekter Kapitalisierung
- [ ] Restaurationskosten: Numerische Werte mit Currency Symbols
- [ ] Field Statistics zeigen unterschiedliche Success Rates

---

## 4. DATABASE PERSISTENCE & ANALYTICS

### 4.1 Database Search Results Storage
**Zweck**: Prüfen ob alle Suchergebnisse vollständig persistiert werden  
**Erwartetes Ergebnis**: Strukturierte Daten mit Metadaten in Database

**Test-Schritte**:
1. Komplette Suche für Quebec Mine durchführen
2. Database prüfen: search_results Tabelle
3. Validieren: structured_data JSON vollständig
4. Prüfen: Sources und source_index korrekt

**Erfolgskriterien**:
- [ ] Search Result in Database mit allen Feldern
- [ ] structured_data JSON enthält >15 gefüllte Felder
- [ ] sources Array mit >5 Quebec-spezifischen URLs
- [ ] session_id korrekt für Batch-Gruppierung

### 4.2 Sources Quality Metrics automatische Updates
**Zweck**: Prüfen ob Source Quality automatisch basierend auf Performance aktualisiert wird  
**Erwartetes Ergebnis**: Dynamic Source Ranking basierend auf Erfolg

**Test-Schritte**:
1. Mehrere Suchen mit denselben Sources durchführen
2. Database prüfen: sources Tabelle reliability_score
3. Validieren: Scores basierend auf Success Rates
4. Prüfen: GESTIM/MERN höchste Scores für Quebec

**Erfolgskriterien**:
- [ ] GESTIM reliability_score > 0.85 für Quebec Minen
- [ ] MERN reliability_score > 0.80 für Quebec Minen
- [ ] Source total_searches und successful_searches aktualisiert
- [ ] last_successful_access timestamps korrekt

### 4.3 Model & Field Statistics Persistence
**Zweck**: Prüfen ob Modell-Performance und Feld-Erfolg getrackt werden  
**Erwartetes Ergebnis**: Detaillierte Analytics für Workflow-Optimierung

**Test-Schritte**:
1. Searches mit verschiedenen Models durchführen
2. Database prüfen: model_statistics, field_statistics
3. Validieren: Response Times, Success Rates per Model
4. Prüfen: Field-specific Performance Metrics

**Erfolgskriterien**:
- [ ] model_statistics: Response times <30s für Premium Models
- [ ] field_statistics: >60% Success Rate für kritische Felder
- [ ] Verschiedene Models zeigen unterschiedliche Performance
- [ ] Quebec-spezifische Fields höhere Success Rates

---

## 5. MULTI-PROVIDER INTEGRATION

### 5.1 Multi-Provider Parallele Ausführung
**Zweck**: Prüfen ob mehrere AI-Provider gleichzeitig Quebec Mining Daten suchen  
**Erwartetes Ergebnis**: Aggregierte Resultate von verschiedenen Providern

**Test-Schritte**:
1. Batch Search mit >5 verschiedenen Providern starten
2. Prüfen: Parallele Execution Logs
3. Validieren: Aggregation von Provider Results
4. Prüfen: Best-Result Selection Logic

**Erfolgskriterien**:
- [ ] Log-Entries: "[PROVIDER] {name} search started" für >5 Provider
- [ ] Verschiedene Provider finden unterschiedliche Daten
- [ ] Aggregation bevorzugt high-confidence Results
- [ ] Total Execution Time <5 Minuten für komplette Suche

### 5.2 Provider-specific Quebec Optimizations
**Zweck**: Prüfen ob Provider-spezifische Quebec Mining Optimierungen aktiv sind  
**Erwartetes Ergebnis**: Tailored Queries je nach Provider-Stärken

**Test-Schritte**:
1. Suche mit Perplexity: Web Search Optimization
2. Suche mit Tavily: Research-specific Queries  
3. Suche mit OpenRouter Models: Bilingual Prompts
4. Validieren: Provider-specific Query Variations

**Erfolgskriterien**:
- [ ] Perplexity: Web-optimized Queries mit site:gestim.mines.gouv.qc.ca
- [ ] Tavily: Research-specific Quebec Mining Keywords
- [ ] OpenRouter: Bilingual Prompts automatisch generiert
- [ ] Verschiedene Provider finden komplementäre Daten

---

## 6. COMPLETE END-TO-END WORKFLOW TEST

### 6.1 Playwright Browser Integration Test
**Zweck**: Vollständiger realistic User Journey durch Quebec Mining Workflow  
**Erwartetes Ergebnis**: Alle Features funktionieren nahtlos in realer Browser-Umgebung

**Test-Schritte**:
1. **CSV Upload**: Quebec Mining CSV hochladen via Browser
2. **Model Selection**: Alle verfügbaren Provider auswählen
3. **Comprehensive Search**: 10/10 System Option aktivieren
4. **Workflow Monitoring**: Progress Tracking via Browser-Console
5. **Results Validation**: Realistische Daten in UI validieren
6. **Database Verification**: Backend Database via Browser-DevTools prüfen

**Browser-specific Erfolgskriterien**:
- [ ] **CSV Upload UI**: Erfolgreiche Upload-Bestätigung mit Mine Count
- [ ] **Provider Selection**: >10 Models ausgewählt und bestätigt
- [ ] **Progress Indicators**: Live-Updates während 10-20 Min Suche
- [ ] **Results Table**: >70% gefüllte Felder mit realistischen Werten
- [ ] **Source Links**: Klickbare Links zu Quebec Government Sources
- [ ] **Export Functionality**: CSV Download mit vollständigen Daten

**Data Quality Validation**:
- [ ] **Restaurationskosten**: Realistische Beträge $1M-$500M CAD
- [ ] **Koordinaten**: Gültige Quebec Koordinaten (45°-62°N, 57°-80°W)
- [ ] **Eigentümer**: Echte Mining Companies (Barrick, Newmont, etc.)
- [ ] **Betreiber**: Korrekte Operator-Company Zuordnungen
- [ ] **Mining Type**: Logische Open Pit/Underground Zuordnungen
- [ ] **Commodities**: Quebec-typische Rohstoffe (Iron Ore, Gold, etc.)

**Quebec-specific Validation**:
- [ ] **Französische Sources**: >30% der Sources aus .qc.ca oder .gouv.qc.ca
- [ ] **GESTIM Data**: Mining Titles/Permits mit Quebec-spezifischen Nummern
- [ ] **Bilingual Results**: Französische UND englische Begriffe in Daten
- [ ] **Regional Accuracy**: Korrekte Quebec Region-Zuordnungen

---

## WORKFLOW ERFOLGS-SUMMARY

**MINIMALE ERFOLGS-SCHWELLE: 80% aller Tests bestehen**

### Critical Success Criteria:
1. **Quebec Detection**: ✅ Automatische Erkennung bei Quebec Minen
2. **Bilingual Search**: ✅ Französisch/Englisch parallel aktiv
3. **GESTIM Integration**: ✅ Primäre Quebec Source automatisch genutzt
4. **Comprehensive Workflow**: ✅ Orchestrator koordiniert alle Features
5. **Realistic Data**: ✅ >70% Felder mit sinnvollen Werten gefüllt
6. **Database Persistence**: ✅ Vollständige Speicherung aller Komponenten

### Performance Benchmarks:
- **Search Duration**: <10 Minuten für 10 Minen comprehensive search
- **Data Completeness**: >70% kritische Felder gefüllt
- **Source Quality**: >5 high-quality Quebec Sources pro Mine
- **Accuracy Rate**: >85% realistisch validierbare Daten

---

**NEXT STEPS**: Nach erfolgreichem Test-Durchlauf → Production Deployment für Quebec Mining Workflow v2.1