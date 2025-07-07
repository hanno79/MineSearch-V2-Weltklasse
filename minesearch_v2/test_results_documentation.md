# MineSearch Modell-Test Dokumentation

**Autor:** rahn  
**Datum:** 04.07.2025  
**Version:** 1.0

## Übersicht

Diese Dokumentation fasst die Tests der verschiedenen MineSearch-Modelle zusammen. Die API unterstützt zwei Hauptmodi:
1. **Einzelmodell-Suche** (`/api/search`)
2. **Multi-Modell-Suche** (`/api/search/multi`)

## Verfügbare Modelle

### Perplexity Provider
1. **perplexity:sonar** - Schnelle Suche
   - Günstig und schnell für einfache Anfragen
   - Timeout: 30s
   - Web-Suche: ✓

2. **perplexity:sonar-pro** - Erweiterte Suche (Empfohlen)
   - Beste Balance zwischen Qualität und Geschwindigkeit
   - Timeout: 60s
   - Web-Suche: ✓

3. **perplexity:sonar-deep-research** - Tiefenrecherche
   - Umfassende Recherche (kann 30+ Minuten dauern)
   - Timeout: 2000s
   - Web-Suche: ✓

4. **perplexity:sonar-reasoning-pro** - Analyse mit Reasoning
   - Für komplexe Analysen mit logischem Denken
   - Timeout: 120s
   - Web-Suche: ✓

### OpenRouter Provider
1. **openrouter:deepseek-free** - DeepSeek Reasoner (Kostenlos)
   - Fortschrittliches Reasoning-Modell ohne Kosten
   - Timeout: 120s
   - Web-Suche: ✗

2. **openrouter:deepseek-chat** - DeepSeek Chat
   - Verbessertes Chat-Modell
   - Timeout: 60s
   - Web-Suche: ✗

## API-Endpunkte

### 1. Einzelmodell-Suche
```bash
POST /api/search?model={model_name}
```

**Beispiel:**
```bash
curl -X POST "http://localhost:8000/api/search?model=sonar-pro" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}'
```

**Wichtig:** Für Einzelsuche wird nur der Modell-Name ohne Provider-Präfix verwendet:
- Richtig: `model=sonar-pro`
- Falsch: `model=perplexity:sonar-pro`

### 2. Multi-Modell-Suche
```bash
POST /api/search/multi
```

**Beispiel:**
```bash
curl -X POST "http://localhost:8000/api/search/multi" \
-H "Content-Type: application/json" \
-d '{
  "model_ids": ["perplexity:sonar-pro", "openrouter:deepseek-free"],
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}'
```

**Wichtig:** Für Multi-Modell-Suche wird das vollständige Format mit Provider-Präfix verwendet.

## Test-Szenarien

### Test-Mine 1: Jeffrey Mine
- **Land:** Canada
- **Rohstoff:** Asbestos
- **Region:** Quebec
- **Besonderheit:** Historische Mine mit Umweltproblemen

### Test-Mine 2: Escondida
- **Land:** Chile
- **Rohstoff:** Copper
- **Region:** Antofagasta
- **Besonderheit:** Aktive Großmine

### Test-Mine 3: Jwaneng Diamond Mine
- **Land:** Botswana
- **Rohstoff:** Diamond
- **Besonderheit:** Afrikanische Diamantmine

## Empfohlene Test-Kombinationen

### Für schnelle Tests:
1. **perplexity:sonar** + **openrouter:deepseek-free**
   - Kombination aus Web-Suche und kostenlosem Reasoning

### Für umfassende Analysen:
1. **perplexity:sonar-pro** + **openrouter:deepseek-chat**
   - Balance zwischen Qualität und Geschwindigkeit

### Für kritische Recherchen:
1. **perplexity:sonar-deep-research** (Einzelmodell)
   - Wenn Zeit keine Rolle spielt und maximale Tiefe gewünscht ist

## Bekannte Einschränkungen

1. **Timeouts:** Die angegebenen Timeouts sind Maximalwerte. Tatsächliche Antwortzeiten können erheblich variieren.

2. **Web-Suche:** Nur Perplexity-Modelle unterstützen direkte Web-Suche. OpenRouter-Modelle nutzen Source Discovery für relevante URLs.

3. **API-Response-Zeit:** Bei ersten Anfragen nach Serverstart können längere Wartezeiten auftreten.

## Test-Durchführung

### Automatisierte Tests
Verwenden Sie die bereitgestellten Test-Skripte:
- `test_models_quick.py` - Schnelltest der wichtigsten Modelle
- `test_models_detailed.py` - Umfassende Analyse mit mehreren Minen

### Manuelle Tests
Nutzen Sie die oben genannten curl-Beispiele oder Tools wie Postman/Insomnia.

## Erwartete Ergebnisse

### Kritische Datenfelder
Bei Mining-Suchen sollten folgende Felder idealerweise gefüllt sein:
- Betreiber
- Restaurationskosten
- GPS Koordinaten
- Status (aktiv/stillgelegt)
- Rohstoffabbau-Details

### Qualitätsmetriken
Die API liefert automatisch Qualitätsmetriken:
- **completeness_percentage**: Prozentsatz der ausgefüllten Felder
- **quality_level**: Hoch/Mittel/Niedrig
- **missing_critical_fields**: Liste fehlender kritischer Felder

## Fazit

Die Multi-Provider-Architektur ermöglicht flexible Nutzung verschiedener AI-Modelle je nach Anforderung:
- **Schnelle Suchen:** perplexity:sonar
- **Ausgewogene Suchen:** perplexity:sonar-pro
- **Tiefenanalysen:** perplexity:sonar-deep-research
- **Kostenlose Alternative:** openrouter:deepseek-free

Die Kombination mehrerer Modelle über die Multi-Search-API kann die Ergebnisqualität verbessern, indem verschiedene Stärken genutzt werden.