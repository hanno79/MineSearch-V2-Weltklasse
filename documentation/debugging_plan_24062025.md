# Umfassender Debugging- und Fehlerbehebungsplan
**Autor:** rahn  
**Datum:** 24.06.2025  
**Version:** 1.0

## Zusammenfassung der Fehleranalyse

Nach umfassender Analyse der Logs wurden folgende kritische Fehler identifiziert:

### Fehlerstatistik (nach Häufigkeit):
- **90x** Exa API Domain-Validierungsfehler
- **46x** Tavily Query-Length Überschreitungen
- **45x** Perplexity Deep ungültiges Model
- **30x** Session Management Fehler
- **7x** Browser/Playwright Fehler
- **3x** OpenRouter Model Fehler
- **Weitere** vereinzelte Fehler

## 1. Kritische API-Fehler beheben

### 1.1 Exa API Domain-Validierung (90 Fehler)
**Problem:** Domain-Listen enthalten vollständige URLs statt Basis-Domains
- **Fehler:** "Domain must be a base domain: gov.sk.ca/business/agriculture-natural-resources/mineral-exploration-and-mining"
- **Betroffene Datei:** `/app/src/agents/enhanced_search/domain_manager.py`
- **Fix:** Alle URLs auf Basis-Domains reduzieren (z.B. "gov.sk.ca" statt "gov.sk.ca/business/...")
- **Verifizierung:** Test mit Exa API durchführen

### 1.2 Tavily Query-Length (46 Fehler)  
**Problem:** Enhanced Queries überschreiten 400 Zeichen Limit
- **Fehler:** "Query is too long. Max query length is 400 characters."
- **Betroffene Datei:** `/app/src/agents/tavily_agent.py`
- **Fix:** 
  - Query-Splitting in `_make_enhanced_api_call()` implementieren
  - Queries auf maximal 380 Zeichen kürzen
- **Verifizierung:** Query-Längen vor API-Call prüfen

### 1.3 Perplexity Deep Model (45 Fehler)
**Problem:** Verwendet ungültiges Model 'sonar-medium-online'
- **Fehler:** "Invalid model 'sonar-medium-online'"
- **Betroffene Datei:** `/app/src/agents/perplexity_deep/api_client.py`
- **Fix:** Model auf 'sonar-deep-research' ändern
- **Verfügbare Modelle:**
  - sonar-pro (Advanced search)
  - sonar (Lightweight search)
  - sonar-deep-research (Expert research)
  - sonar-reasoning-pro (DeepSeek R1)
  - sonar-reasoning (Fast reasoning)
- **Verifizierung:** API-Call mit neuem Model testen

## 2. Session Management Fehler

### 2.1 Perplexity Deep Session Closed (30 Fehler)
**Problem:** Session wird geschlossen und nicht neu erstellt
- **Fehler:** "Session is closed"
- **Betroffene Datei:** `/app/src/agents/perplexity_deep/perplexity_deep_agent.py`
- **Fix:** 
  - Session-Check und Re-Initialisierung vor jedem API-Call
  - Session-Manager korrekt nutzen
- **Verifizierung:** Mehrere aufeinanderfolgende Requests testen

## 3. Browser/Playwright Setup

### 3.1 Playwright Installation
**Problem:** Playwright Browser nicht installiert
- **Fehler:** "Executable doesn't exist at /root/.cache/ms-playwright/chromium-1091/chrome-linux/chrome"
- **Fix:** `playwright install chromium` ausführen
- **Alternative:** Browser-Agent temporär deaktivieren
- **Verifizierung:** Browser-Agent initialisieren

### 3.2 NoneType Error
**Problem:** Browser-Objekt ist None
- **Fehler:** "'NoneType' object has no attribute 'new_page'"
- **Betroffene Datei:** `/app/src/agents/browser_agent.py`
- **Fix:** Null-Check vor page.new_page() Aufruf
- **Verifizierung:** Browser-Agent mit verschiedenen URLs testen

## 4. Weitere Optimierungen

### 4.1 Error Handling verbessern
- Fail-Fast bei ungültigen API-Keys
- Bessere Fehlermeldungen für Debugging
- Retry-Logic für temporäre Fehler
- Exponential Backoff bei Rate-Limiting

### 4.2 API-Verfügbarkeit prüfen
- Health-Check Endpoints implementieren
- Agenten bei dauerhaften Fehlern deaktivieren
- Status-Dashboard für API-Verfügbarkeit

### 4.3 Cancel-Button Funktionalität
**Problem:** Cancel-Button funktioniert nicht zuverlässig
- **Fix:** 
  - Event-Loop und Cancellation-Token korrekt implementieren
  - Async-Operationen auf Cancellation prüfen
- **Verifizierung:** Cancel während laufender Suche testen

## 5. Implementierungsreihenfolge

1. **Sofort (5 Min):** Perplexity Deep Model fix
2. **Priorität 1 (15 Min):** Exa Domain-Validierung
3. **Priorität 2 (20 Min):** Tavily Query-Splitting
4. **Priorität 3 (15 Min):** Session Management fixes
5. **Optional (10 Min):** Playwright installation
6. **Langfristig:** Cancel-Button und Error Handling

## 6. Verifizierungsstrategie

Nach jeder Änderung:
1. **Unit-Test** für geänderte Funktion
2. **Integration-Test** mit echten API-Calls
3. **Log-Analyse** auf verbleibende Fehler
4. **Performance-Check** (keine neuen Bottlenecks)

### Test-Kommandos:
```bash
# Logs überwachen
tail -f logs/minesearch.log | grep ERROR

# Fehlerstatistik
grep '"level": "ERROR"' logs/minesearch.log | grep -oE '"module": "[^"]*"' | cut -d'"' -f4 | sort | uniq -c | sort -nr

# Spezifische Fehler prüfen
grep "Exa API Fehler" logs/minesearch.log | wc -l
grep "Query is too long" logs/minesearch.log | wc -l
grep "Invalid model" logs/minesearch.log | wc -l
```

## 7. Erwartete Ergebnisse

Nach Implementierung aller Fixes:
- **0** Domain-Validierungsfehler bei Exa
- **0** Query-Length Fehler bei Tavily
- **0** Model-Fehler bei Perplexity
- **Reduzierte** Session-Fehler
- **Funktionierender** Browser-Agent (oder deaktiviert)
- **Verbesserte** Fehlerbehandlung und Logging

## 8. Nächste Schritte

1. Diesen Plan als Referenz nutzen
2. Mit Perplexity Deep Model fix beginnen (schnellster Fix)
3. Systematisch durch alle Prioritäten arbeiten
4. Nach jedem Fix verifizieren
5. Logs kontinuierlich überwachen
6. Bei Erfolg: Commit mit aussagekräftiger Message

---
Dieser Plan dient als vollständige Referenz für die Fehlerbehebung und kann bei Bedarf erweitert werden.