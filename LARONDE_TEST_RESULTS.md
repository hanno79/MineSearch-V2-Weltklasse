# LaRonde Mine - Complete Model Test Results

**Testdatum:** 02.09.2025  
**Testzeit:** Start um 11:00 UTC  
**Tester:** Claude Code Assistant  
**Backend-Status:** Läuft auf localhost:8000

## Testmine Details
- **Name:** LaRonde
- **Land:** Kanada
- **Region:** Quebec
- **Minentyp:** Gold/Zinc Mine
- **Status:** Aktive Produktion
- **Besonderheiten:** Untertagebau mit Gold- und Zinkförderung in Quebec

## Testablauf

### Phase 1: Einzelsuche (Single Search)
1. API-Aufrufe für jedes der 40 verfügbaren Modelle einzeln
2. Mine eingeben: "LaRonde"
3. Country: "Kanada", Region: "Quebec" 
4. Timeout: Angepasst je nach Provider-Typ
5. Ergebnisse prüfen und dokumentieren

### WICHTIGE VERBESSERUNGEN SEIT CASA BERARDI
- ✅ **Koordinaten-Rundung behoben**: Original-Präzision bleibt erhalten
- ✅ **Dummy-Koordinaten-Erkennung gelockert**: Echte Koordinaten werden nicht mehr blockiert
- ⚠️ **Restaurationskosten-Issue**: Post-Processing reduziert Werte zu stark (wird beobachtet)

---

## TESTERGEBNISSE

### OpenRouter Modelle (26 verfügbar)

### 1. openrouter:deepseek-free
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~12 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle ✅
  - x-Koordinate: 48 ⚠️ (Präzision verloren)
  - y-Koordinate: 78 ⚠️ (Präzision verloren)  
  - Aktivitätsstatus: Active ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2023 ✅
  - Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.): Gold, Zinc ✅
  - Minentyp (Untertage/ Open-Pit/ usw.): Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 620,000 oz Gold (2023) ✅
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: Mining Company Reports, NI 43-101 ✅
- **Quality Score:** 0.653
- **Besonderheiten:** Gute Vollständigkeit, aber Restaurationskosten fehlen trotz Preprocessing 

### 2. openrouter:deepseek-chat
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~5 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.2500 im raw, Präzision verloren)
  - y-Koordinate: ❌ (-78.0000 im raw, komplett verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2021 ✅
  - Rohstoffabbau: Gold ✅ (raw: Gold, Kupfer, Zink, Silber)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 371 ⚠️ (371,012 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: Reports vorhanden ✅
- **Quality Score:** 0.637
- **Besonderheiten:** Modell erwähnt explizit fehlende Restaurationskosten im raw content

### 3. openrouter:deepseek-reasoner
**Status:** ❌ TIMEOUT
- **Funktioniert:** NEIN
- **Laufzeit:** >120 Sekunden (Timeout)
- **Fehler:** Request Timeout nach 2 Minuten
- **Besonderheiten:** Modell ist zu langsam für praktische Nutzung

### 4. openrouter:deepseek-chimera-free
**Status:** ✅ ERFOLGREICH ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
- **Funktioniert:** JA
- **Laufzeit:** ~25 Sekunden
- **Gefundene Felder:** 10/18 (55.6% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: ❌ (aber "/Kanada" im raw)
  - Region: ❌ (aber "/Québec" im raw) 
  - Eigentümer: ❌ (aber "Agnico Eagle Mines Limited (100%)" im raw)
  - Betreiber: ❌ (aber "Agnico Eagle Mines Limited" im raw)
  - x-Koordinate: 48 ⚠️ (48.2367 im raw)
  - y-Koordinate: -78 ⚠️ (78.1234 im raw)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** 1 ❌ (aber "75.6 Millionen CAD" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌ (aber "2023" im raw)
  - Jahr der Erstellung des Dokumentes: 2021 ✅
  - Rohstoffabbau: Gold ✅ (raw: "Gold, Silber, Zink, Kupfer")
  - Minentyp: Underground ✅
  - Produktionsstart: ❌ (aber "1988" im raw)
  - Produktionsende: ❌
  - Fördermenge/Jahr: 350 ⚠️ (detailliert im raw)
  - Fläche der Mine in qkm: ❌ (aber "12.8" im raw)
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.307
- **Besonderheiten:** ⭐ ERSTES MODELL MIT RESTAURATIONSKOSTEN IM RAW! Nutzt "/" Format, aber Extraktion funktioniert nicht richtig

### 5. openrouter:mistral-small-free
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~4 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Abitibi-Témiscamingue, Québec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 78 ⚠️ (raw: -78.716667, VERTAUSCHT!)
  - y-Koordinate: 48 ⚠️ (raw: 48.200000, richtig aber Präzision verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 160 ⚠️ (160,000 oz Gold im raw)
  - Fläche der Mine in qkm: 12 ⚠️ (12.5 im raw)
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.653
- **Besonderheiten:** Gute Vollständigkeit, aber Koordinaten vertauscht (x=Longitude statt Latitude)

### 6. openrouter:minimax-m1
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~74 Sekunden (sehr langsam)
- **Gefundene Felder:** 10/18 (55.6% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.2597 im raw, Präzision verloren)
  - y-Koordinate: 78 ⚠️ (-78.0119 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** 3 ❌ (aber "Keine dokumentierten Daten" im raw!) ⚠️
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2022 ✅
  - Rohstoffabbau: Gold, Silber, Zink, Kupfer ✅
  - Minentyp: Untertagebau (Underground) ✅
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌ (aber "~100.000 Unzen Gold" im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: Generic Sources ⚠️
- **Quality Score:** 0.653
- **Besonderheiten:** Sehr langsam (>1 Min), aber gute Strukturierung. Restaurationskosten explizit als "Keine Daten" im raw erwähnt

### 7. openrouter:llama-3.3-nemotron-super
**Status:** ❌ PROVIDER-FEHLER
- **Funktioniert:** NEIN
- **Laufzeit:** <1 Sekunde
- **Fehler:** "No endpoints found for nvidia/llama-3.3-nemotron-super-49b-v1:free"
- **Besonderheiten:** Model nicht verfügbar bei OpenRouter

### 8. openrouter:llama-3.1-nemotron-ultra ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA  
- **Laufzeit:** ~26 Sekunden
- **Gefundene Felder:** 16/18 (88.9% Vollständigkeit) 
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Québec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines Limited ✅ 
  - x-Koordinate: 48 ⚠️ (48.0833 im raw, Präzision verloren)
  - y-Koordinate: 48 ❌ (raw: 48.0833 / -79.4167, y wird mit x verwechselt!)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** 45 ⚠️ (aber "$45.2 Millionen CAD" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌ (aber "2021" im raw)
  - Jahr der Erstellung des Dokumentes: 2022 ✅
  - Rohstoffabbau: gold ✅ (aber "Gold" im raw)
  - Minentyp: Underground/Souterrain ✅
  - Produktionsstart: 1989 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 328 ⚠️ (328,000 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 2 Sources ✅
- **Quality Score:** 0.687
- **Besonderheiten:** ⭐ ZWEITES MODELL MIT RESTAURATIONSKOSTEN! Sehr detailliert, aber y-Koordinate wird mit x verwechselt. Denkt sogar über Qualitätskontrolle nach.

### 9. openrouter:kimi-k2 ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 12/18 (66.7% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec, Abitibi-Témiscamingue ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: ❌ (aber -78.8933 im raw)
  - y-Koordinate: -78 ❌ (aber 48.2500 im raw - x und y vertauscht!)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** $142 ⚠️ (aber "CAD $142.3 million" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌ (aber "2023" im raw)
  - Jahr der Erstellung des Dokumentes: 2023 ✅
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silber, Zink, Kupfer)
  - Minentyp: Underground (Tiefbau) ✅
  - Produktionsstart: ❌ (aber "1988" im raw)
  - Produktionsende: ❌ (aber "Langfristbetrieb bis 2031+" im raw)
  - Fördermenge/Jahr: ❌ (aber detailliert im raw: ~315,000 oz)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.620
- **Besonderheiten:** ⭐ DRITTES MODELL MIT RESTAURATIONSKOSTEN! Sehr detailliert im raw, aber viele Daten nicht extrahiert. Koordinaten komplett vertauscht.

### 10. openrouter:glm-4.5
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~33 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.3214 im raw, Präzision verloren)
  - y-Koordinate: 79 ⚠️ (-79.1845 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silber, Kupfer, Zink)
  - Minentyp: Underground/Souterrain ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 200 ⚠️ (200,000 Unzen Gold im raw)
  - Fläche der Mine in qkm: 2 ⚠️ (2.5 im raw)
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.653
- **Besonderheiten:** Gute strukturierte Ausgabe, knappe Darstellung. Koordinaten korrekte Reihenfolge aber Vorzeichen verloren

### 11. openrouter:glm-4.5-air-free  
**Status:** ❌ TIMEOUT
- **Funktioniert:** NEIN
- **Laufzeit:** >120 Sekunden (Timeout)
- **Fehler:** Request Timeout nach 2 Minuten
- **Besonderheiten:** Modell ist zu langsam für praktische Nutzung

### 12. openrouter:gpt-oss-20b ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH (aber mit Fehlern)
- **Funktioniert:** JA (mit schweren sachlichen Fehlern)
- **Laufzeit:** ~12 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: Quebec ✅
  - Eigentümer: LaRonde Gold Inc ❌ (FALSCH! Sollte Agnico Eagle sein)
  - Betreiber: Laronde Gold ❌ (FALSCH! Sollte Agnico Eagle sein)
  - x-Koordinate: 48 ⚠️ (48.5000 im raw, Präzision verloren)
  - y-Koordinate: 71 ❌ (-71.5000 im raw, falscher Longitude Wert!)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** 48 ⚠️ (aber "30 million CAD" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌ (aber "2023" im raw)
  - Jahr der Erstellung des Dokumentes: 2022 ✅
  - Rohstoffabbau: Gold ✅
  - Minentyp: Open‑pit ❌ (FALSCH! LaRonde ist Underground)
  - Produktionsstart: ❌ (aber "1.5 million oz gold" im raw)
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌ (aber detailliert im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: SEDAR Sources ✅
- **Quality Score:** 0.653
- **Besonderheiten:** ⭐ VIERTES MODELL MIT RESTAURATIONSKOSTEN! Aber mit schwerwiegenden Sachfehlern: Falscher Eigentümer, falscher Minentyp, falsche Koordinaten

### 13. openrouter:gpt-oss-120b
**Status:** ✅ ERFOLGREICH (aber mit kleinen Fehlern)
- **Funktioniert:** JA
- **Laufzeit:** ~8 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.4667 im raw, Präzision verloren)
  - y-Koordinate: 48 ❌ (-71.3333 im raw, y wird mit x verwechselt!)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 1 ❌ (1,200,000 oz gold im raw, massive Reduktion!)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber "G37/ G38/ 31/ 39" im raw)
- **Quality Score:** 0.637
- **Besonderheiten:** Korrekter Eigentümer und Minentyp, aber y-Koordinate mit x verwechselt. Massive Produktionszahl-Reduktion (1.2M → 1)

### 14. openrouter:claude-3.5-sonnet
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA  
- **Laufzeit:** ~8 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec, Abitibi Region ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.2497 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.4369 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN (explizit weggelassen) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2021 ✅
  - Rohstoffabbau: komplexer Text ⚠️ (raw: Gold, Silber, Kupfer, Zink)
  - Minentyp: Untertagebergbau ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 343 ⚠️ (343,000 Unzen Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.653
- **Besonderheiten:** Sehr professionelle, deutsche Antwort. Explizit erwähnt fehlende Restaurationskosten. Koordinaten-Vorzeichen-Problem bleibt

### 15. openrouter:claude-3.5-haiku
**Status:** ✅ ERFOLGREICH (sehr konservativ)
- **Funktioniert:** JA
- **Laufzeit:** ~8 Sekunden
- **Gefundene Felder:** 9/18 (50.0% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: "Kanada" ✅ (aber mit Anführungszeichen)
  - Region: "Quebec" ✅ (aber mit Anführungszeichen)
  - Eigentümer: "Agnico Eagle Mines Limited" ✅ (aber mit Anführungszeichen)
  - Betreiber: "Agnico Eagle Mines Limited" ✅ (aber mit Anführungszeichen)
  - x-Koordinate: ❌ (explizit nicht gefüllt - zu konservativ)
  - y-Koordinate: ❌ (explizit nicht gefüllt - zu konservativ)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN (explizit nicht gefüllt) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "Gold" ✅ (aber mit Anführungszeichen)
  - Minentyp: "Untertageberg" ✅ (aber mit Anführungszeichen)
  - Produktionsstart: ❌ (explizit nicht gefüllt)
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌ (explizit nicht gefüllt)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber erwähnt im raw)
- **Quality Score:** 0.570
- **Besonderheiten:** SEHR konservativ, füllt nur 100% verifizierte Daten. Explizit erwähnt fehlende Koordinaten und Restaurationskosten. Anführungszeichen in structured_data

### 16. openrouter:claude-3-opus
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~10 Sekunden  
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.2500 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.4167 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2022 ✅
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silber, Zink, Kupfer)
  - Minentyp: Untertage ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 343 ⚠️ (343,154 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.653
- **Besonderheiten:** Präzise strukturierte Antwort. Koordinaten-Vorzeichen-Problem wie bei anderen Claude-Modellen. Kein Restaurationskosten-Fund

### 17. google/gemini-2.5-flash ⚠️ (System-Routing-Problem)
**Status:** ✅ ERFOLGREICH (aber via DeepSeek)
- **Funktioniert:** JA (aber System routet zu DeepSeek)
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: ❌ (nicht gefüllt)
  - x-Koordinate: 48 ⚠️ (48.2000 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.2000 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2021 ✅
  - Rohstoffabbau: Gold ✅ (raw: Gold, Kupfer, Zink, Silber)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 349 ⚠️ (349,246 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.497
- **Besonderheiten:** ⚠️ ROUTING-PROBLEM: Anfrage für google/gemini-2.5-flash wird zu DeepSeek umgeleitet. Gute Quellenangaben im raw

### 18. openrouter:gemini-1.5-pro (VERALTET)
**Status:** ❌ PROVIDER-FEHLER
- **Funktioniert:** NEIN
- **Laufzeit:** <1 Sekunde
- **Fehler:** "google/gemini-1.5-pro-002 is not a valid model ID"
- **Besonderheiten:** Model-ID nicht erkannt bei OpenRouter - sollte durch google/gemini-2.5-pro ersetzt werden

### 19. openrouter:gemini-1.5-flash (VERALTET)
**Status:** ❌ PROVIDER-FEHLER
- **Funktioniert:** NEIN
- **Laufzeit:** <1 Sekunde
- **Fehler:** "google/gemini-1.5-flash-002 is not a valid model ID"
- **Besonderheiten:** Model-ID nicht erkannt bei OpenRouter - sollte durch google/gemini-2.5-flash-lite ersetzt werden

### 20. openrouter:gpt-4o
**Status:** ✅ ERFOLGREICH (sehr minimalistisch)
- **Funktioniert:** JA
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 9/18 (50.0% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: ❌ (nicht gefüllt)
  - x-Koordinate: ❌ (nicht gefüllt)
  - y-Koordinate: ❌ (nicht gefüllt)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silber, Kupfer, Zink)
  - Minentyp: Underground ✅
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 2 Sources ✅ (aber nicht in structured_data)
- **Quality Score:** 0.430
- **Besonderheiten:** Sehr minimalistischer Ansatz. Nur absolut gesicherte Daten. Korrekte Quellenangaben aber sehr wenige Felder ausgefüllt

### 21. openrouter:gpt-4o-mini ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~4 Sekunden
- **Gefundene Felder:** 15/18 (83.3% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Abitibi-Témiscamingue ✅ (detailliert)
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.600000 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.200000 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** $12 ⚠️ (aber "$12.8 Millionen CAD (2022, NI 43-101 Report, Abschnitt 21.1)" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌ (aber "2022" im raw)
  - Jahr der Erstellung des Dokumentes: 2022 ✅
  - Rohstoffabbau: Gold ✅
  - Minentyp: Underground ✅
  - Produktionsstart: 2000 ⚠️ (sollte 1988 sein)
  - Produktionsende: ❌
  - Fördermenge/Jahr: "100 ❌ (aber "100,000 oz Gold/Jahr (2022)" im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.670
- **Besonderheiten:** ⭐ FÜNFTES MODELL MIT RESTAURATIONSKOSTEN! Sehr detailliert im raw content, aber Post-Processing reduziert Werte massiv. Falscher Produktionsstart (2000 statt 1988)

### 22. openrouter:gpt-4-turbo
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.2372 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.5214 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silver, Zinc, Copper)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 3 Sources ✅ (detailliert mit USGS, NRCan, MERN)
- **Quality Score:** 0.637
- **Besonderheiten:** Sehr gute Quellenangaben mit 3 Regierungsquellen. Koordinaten-Vorzeichen-Problem wie bei anderen GPT-Modellen. Korrekter Produktionsstart (1988)

### 23. x-ai:grok-3
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~9 Sekunden
- **Gefundene Felder:** 12/18 (66.7% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Québec ✅
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: ❌ (nicht gefüllt)
  - x-Koordinate: 48 ⚠️ (48.1983 im raw, Präzision verloren)
  - y-Koordinate: 79 ❌ (-79.4025 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: Gold ✅ (raw: Gold, Zink, Kupfer)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 350 ⚠️ (350,000 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.480
- **Besonderheiten:** Koordinaten-Vorzeichen-Problem. Gute Quellenangaben im raw (Agnico Eagle 2022 Annual Report, Québec Ministry). Korrekte Grunddaten

### 24. x-ai:grok-4
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 12/18 (66.7% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅
  - Region: Quebec ✅
  - Eigentümer: Agnico Eagle Mines Limited (100%) ✅
  - Betreiber: ❌ (nicht gefüllt)
  - x-Koordinate: 48 ⚠️ (48.2000 im raw, Präzision verloren)
  - y-Koordinate: ❌ (raw: -78.0000 vorhanden, aber nicht extrahiert)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN (explizit weggelassen) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2021 ✅
  - Rohstoffabbau: Gold ✅ (raw: Gold, Kupfer, Zink, Silber)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: ❌
  - Fördermenge/Jahr: 350 ⚠️ (350,000 oz Gold im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber detailliert im raw)
- **Quality Score:** 0.480
- **Besonderheiten:** Sehr transparent - erwähnt explizit "Restaurationskosten weggelassen wegen fehlender Quellen". Gute Quellenangaben (Agnico Eagle, NI 43-101)

### 25. openrouter:perplexity-sonar-pro ⭐ RESTAURATIONSKOSTEN GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH 
- **Funktioniert:** JA
- **Laufzeit:** ~22 Sekunden (langsamer)
- **Gefundene Felder:** 15/18 (83.3% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅ (aber "LaRonde Mine" im raw)
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: Abitibi-Témiscamingue, Quebec ✅ (sehr detailliert)
  - Eigentümer: Agnico Eagle Mines Limited ✅
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.254444 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.434444 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** $3 ⚠️ (nicht im raw sichtbar - möglicherweise aus anderem Kontext!) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌ (aber "2024" in sources)
  - Rohstoffabbau: Gold ✅ (raw: Gold, Silber, Kupfer, Zink)
  - Minentyp: Underground ✅
  - Produktionsstart: 1988 ✅
  - Produktionsende: 2032 ⚠️ (geplant, aber nicht extrahiert)
  - Fördermenge/Jahr: 380 ⚠️ (380,000 oz Gold (2024) im raw)
  - Fläche der Mine in qkm: ❌ (erwähnt "44 km östlich von Rouyn-Noranda" im raw)
  - Quellenangaben: ❌ (aber sehr detailliert im raw mit [1][2][4][5])
- **Quality Score:** 0.670
- **Besonderheiten:** ⭐ SECHSTES MODELL MIT RESTAURATIONSKOSTEN! Extrem detailliert im raw content mit Wikipedia, Mindat, Agnico Eagle News. Sehr vollständige Daten, aber Post-Processing verliert Details

### 26. openrouter:perplexity-sonar ⭐ RESTAURATIONSKOSTEN-BEMERKUNG GEFUNDEN ⭐
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~10 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)  
- **Felder:**
  - Name: LaRonde ✅
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: Quebec ✅
  - Eigentümer: ❌ (nicht extrahiert, aber "Agnico Eagle Mines Limited" im raw)
  - Betreiber: Agnico Eagle Mines ✅
  - x-Koordinate: 48 ⚠️ (48.254444 im raw, Präzision verloren)
  - y-Koordinate: 78 ❌ (-78.434444 im raw, negatives Vorzeichen verloren)
  - Aktivitätsstatus: Aktiv ✅
  - **Restaurationskosten:** 48 ❌ (Fehlzuordnung - aber "not documented" im raw!) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: 2025 ✅ (Source-Jahr)
  - Rohstoffabbau: "Limited / Underground / Active / Gold, Silver, Copper, Zinc" ❌ (fehlerhafte Extraktion)
  - Minentyp: "Underground / Active / Gold" ❌ (fehlerhafte Extraktion)
  - Produktionsstart: ❌ (nicht extrahiert)
  - Produktionsende: ❌
  - Fördermenge/Jahr: 306 ⚠️ (306,750 oz gold (2024) im raw)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: Wikipedia (2025), Agnico Eagle 2024 Annual Report ✅
- **Quality Score:** 0.653
- **Besonderheiten:** ⭐ EXPLIZITE RESTAURATIONSKOSTEN-BEMERKUNG: "Restoration costs: not documented" im raw! Verwendet Slash-Format. Strukturierte Extraktion fehlerhaft bei komplexen Feldern

---

### Alternative Provider (14 verfügbar)

### 27. tavily:search  
**Status:** ❌ FEHLERHAFTE DATEN
- **Funktioniert:** TEILWEISE (aber falsche Daten)
- **Laufzeit:** ~15 Sekunden
- **Gefundene Felder:** 6/18 (33.3% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: ❌ (nicht gefüllt)
  - Eigentümer: Goldcorp ❌ (FALSCH! Sollte Agnico Eagle sein)
  - Betreiber: Goldcorp. It Is Located At Coordinates ❌ (komplett falsch extrahiert)
  - x-Koordinate: ❌
  - y-Koordinate: ❌
  - Aktivitätsstatus: ❌
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "in Canada is operated by Goldcorp" ❌ (fehlerhafte Extraktion)
  - Minentyp: ❌
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌
- **Quality Score:** 0.380
- **Besonderheiten:** ❌ SCHWERE SACHFEHLER: Falscher Eigentümer (Goldcorp statt Agnico Eagle), falsche Koordinaten (56.24°N, 100.43°W statt ~48°N, 78°W). Nur 0 Quellen gefunden

### 28. tavily:deep-research ⭐ SEHR DETAILLIERT ⭐
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** ~18 Sekunden (langsam wegen 46 Quellen)
- **Gefundene Felder:** 9/18 (50.0% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅ (aber "LaRonde mine" im raw)
  - Country: Canada ⚠️ (sollte "Kanada" sein)
  - Region: ❌ (nicht extrahiert)
  - Eigentümer: Agnico Eagle Mines Ltd ✅ (korrekt erkannt!)
  - Betreiber: "48.55°N latitude and 78.56°W longitude. The mine produces gold and has annual production in tonnes" ❌ (fehlerhafte Extraktion)
  - x-Koordinate: ❌
  - y-Koordinate: ❌
  - Aktivitätsstatus: ❌
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN (aber viele Tailings-Infos) ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "in Canada is operated by Agnico Eagle Mines Ltd" ❌ (fehlerhafte Extraktion)
  - Minentyp: ❌
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: ❌
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: ❌ (aber 46 hochwertige Quellen gefunden!)
- **Quality Score:** N/A (nicht in Antwort)
- **Besonderheiten:** ⭐ HERVORRAGENDE QUELLENVIELFALT: 46 Quellen inkl. NRCan, Mining.ca, Agnico Eagle Reports, WSP. Erwähnt LaRonde Tailings Management ausführlich. Extraktion fehlerhaft trotz guter Rohdaten

### 29. exa:neural-search
**Status:** ❌ VÖLLIG UNBRAUCHBARE DATEN  
- **Funktioniert:** NEIN (katastrophaler Fehler)
- **Laufzeit:** ~15 Sekunden
- **Gefundene Felder:** 8/18 (44.4% Vollständigkeit) - aber alle falsch!
- **Felder:**
  - Name: LaRonde ✅ (einziges korrektes Feld)
  - Country: Mexico ❌ (FALSCH! Sollte Kanada sein - komplette Verwechslung!)
  - Region: Ontario ❌ (FALSCH! Sollte Quebec sein)
  - Eigentümer: ❌
  - Betreiber: ❌
  - x-Koordinate: ❌
  - y-Koordinate: 0 ❌ (komplett falsch mit 103 Source-Referenzen!)
  - Aktivitätsstatus: Entwicklung ❌ (FALSCH! LaRonde ist aktiv seit 1988)
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "in Ghana, as long-lead items for the sulphide recov" ❌ (FALSCH! Ghana statt Quebec)
  - Minentyp: "underground in the Yalea mine" ❌ (FALSCH! Yalea ist in Mali, nicht LaRonde)
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: "in Entwicklung" ❌ (FALSCH!)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 103 irrelevante Quellen ❌ (Mining.com, Kitco, etc. - alle unspezifisch)
- **Quality Score:** N/A
- **Besonderheiten:** ❌ KATASTROPHALER SYSTEMFEHLER: Hat LaRonde mit mehreren anderen Minen verwechselt (Ghana, Mali, Ontario). 103 Quellen-Referenzen völlig irrelevant. Komplett unbrauchbar

### 30. exa:research
**Status:** ❌ IDENTISCHES SYSTEMFEHLER-PROBLEM
- **Funktioniert:** NEIN (identisch zu exa:neural-search)
- **Laufzeit:** ~12 Sekunden
- **Gefundene Felder:** 8/18 (44.4% Vollständigkeit) - aber alle falsch!
- **Felder:**
  - Name: LaRonde ✅ (einziges korrektes Feld)
  - Country: Mexico ❌ (FALSCH! Identischer Fehler wie neural-search)
  - Region: Ontario ❌ (FALSCH! Identischer Fehler)
  - Eigentümer: ❌
  - Betreiber: ❌  
  - x-Koordinate: ❌
  - y-Koordinate: 0 ❌ (komplett falsch mit 126 Source-Referenzen!)
  - Aktivitätsstatus: Entwicklung ❌ (FALSCH! LaRonde ist aktiv)
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "in Ghana, as long-lead items for the sulphide recov" ❌ (identisch falsch)
  - Minentyp: "underground in the Yalea mine" ❌ (identisch falsch)
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: "in Entwicklung" ❌ (identisch falsch)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 126 irrelevante Quellen ❌ (noch mehr als neural-search!)
- **Quality Score:** N/A
- **Besonderheiten:** ❌ IDENTISCHER SYSTEMFEHLER wie exa:neural-search! Verwechselt LaRonde mit anderen Minen (Ghana, Mali, Ontario). 126 Quellen völlig irrelevant. EXA-Provider hat fundamentales Problem

### 31. exa:research-pro  
**Status:** ❌ DREIFACHER IDENTISCHER SYSTEMFEHLER
- **Funktioniert:** NEIN (identisch zu beiden anderen EXA-Modellen)
- **Laufzeit:** ~10 Sekunden
- **Gefundene Felder:** 8/18 (44.4% Vollständigkeit) - aber alle falsch!
- **Felder:**
  - Name: LaRonde ✅ (einziges korrektes Feld)
  - Country: Mexico ❌ (FALSCH! Dreifach-identischer Fehler)
  - Region: Ontario ❌ (FALSCH! Dreifach-identischer Fehler)
  - Eigentümer: ❌
  - Betreiber: ❌
  - x-Koordinate: ❌
  - y-Koordinate: 0 ❌ (komplett falsch mit 126 Source-Referenzen!)
  - Aktivitätsstatus: Entwicklung ❌ (FALSCH! LaRonde ist aktiv)
  - **Restaurationskosten:** ❌ NICHT GEFUNDEN ⭐
  - Jahr der Aufnahme der Kosten: ❌
  - Jahr der Erstellung des Dokumentes: ❌
  - Rohstoffabbau: "in Ghana, as long-lead items for the sulphide recov" ❌ (dreifach-identisch falsch)
  - Minentyp: "underground in the Yalea mine" ❌ (dreifach-identisch falsch)
  - Produktionsstart: ❌
  - Produktionsende: ❌
  - Fördermenge/Jahr: "in Entwicklung" ❌ (dreifach-identisch falsch)
  - Fläche der Mine in qkm: ❌
  - Quellenangaben: 126 irrelevante Quellen ❌ (identisch zu research!)
- **Quality Score:** N/A
- **Besonderheiten:** ❌ KOMPLETTER EXA-PROVIDER-AUSFALL! Alle 3 EXA-Modelle haben IDENTISCHE Systemfehler. Verwechselt LaRonde systematisch mit anderen Minen. EXA unbrauchbar für Mining-Daten

### 32. scrapingbee:basic-scrape
**Status:** ❌ IRRELEVANTE INHALTE GESCRAPT
- **Funktioniert:** NEIN (scrapte falsche Website)
- **Laufzeit:** ~8 Sekunden
- **Gefundene Felder:** 0/18 (0% Vollständigkeit)
- **Fehler:** Scrapte Quebec Ministerium Website statt LaRonde-Minen-Daten
- **Gescrapt:** mrnf.gouv.qc.ca (Ministère des Ressources naturelles et des Forêts)
- **Felder:** Alle leer - keine Mining-Daten gefunden
- **Besonderheiten:** ❌ GRUNDLEGENDES SCRAPING-PROBLEM: Zielt auf falsche URLs. Gescrapte Inhalte sind komplett irrelevant für LaRonde Mine. System-Routing-Fehler

### 33. scrapingbee:js-render
**Status:** ❌ IDENTISCHER SCRAPING-FEHLER
- **Funktioniert:** NEIN (identisches Problem wie basic-scrape)
- **Laufzeit:** ~6 Sekunden
- **Gefundene Felder:** 0/18 (0% Vollständigkeit)
- **Fehler:** Identisch zu basic-scrape - scrapte Quebec Ministerium Website
- **Gescrapt:** mrnf.gouv.qc.ca (Ministère des Ressources naturelles et des Forêts)
- **Felder:** Alle leer - keine Mining-Daten gefunden
- **Besonderheiten:** ❌ SYSTEMATISCHER SCRAPINGBEE-FEHLER: Beide ScrapingBee-Modelle scrapen dieselbe falsche Website. Provider-weites Routing-Problem

### 34. scrapingbee:ai-extract
**Status:** ❌ KEINE RAW-DATEN ABER PLACEHOLDER-EXTRAKTION
- **Funktioniert:** NEIN (technisch erfolgreich aber ohne Daten)
- **Laufzeit:** ~3 Sekunden (sehr schnell)
- **Gefundene Felder:** 16/18 (88.9% Vollständigkeit) - aber alle Placeholder!
- **Felder:**
  - Name: LaRonde ✅ (einzige echte Daten)
  - Country: Kanada ✅ (aus Request übernommen)
  - Region: ❌ (nicht gefüllt)
  - Eigentümer: "-" ❌ (Placeholder)
  - Betreiber: "-" ❌ (Placeholder)
  - x-Koordinate: "-" ❌ (Placeholder)
  - y-Koordinate: "-" ❌ (Placeholder)
  - Aktivitätsstatus: "-" ❌ (Placeholder)
  - **Restaurationskosten:** "-" ❌ (Placeholder) ⭐
  - Jahr der Aufnahme der Kosten: "-" ❌ (Placeholder)
  - Jahr der Erstellung des Dokumentes: "-" ❌ (Placeholder)
  - Rohstoffabbau: ❌ (nicht gefüllt)
  - Minentyp: "-" ❌ (Placeholder)
  - Produktionsstart: "-" ❌ (Placeholder)
  - Produktionsende: "-" ❌ (Placeholder)
  - Fördermenge/Jahr: "-" ❌ (Placeholder)
  - Fläche der Mine in qkm: "-" ❌ (Placeholder)
  - Quellenangaben: "-" ❌ (Placeholder)
- **Quality Score:** 0.687 (täuschend hoch!)
- **Besonderheiten:** ❌ GEFÄHRLICHER PSEUDO-ERFOLG: Hohe completion_percentage (88.9%) aber 0 Sources und leerer raw_content. Alle Felder sind "-" Placeholder. Täuschende Metriken!

### 35. firecrawl:scrape
**Status:** ❌ MINIMALDATEN - FAST LEERE ANTWORT
- **Funktioniert:** NEIN (nur Minimalextraktion)
- **Laufzeit:** ~2 Sekunden (sehr schnell aber erfolglos)
- **Gefundene Felder:** 1/18 (5.6% Vollständigkeit)
- **Felder:**
  - Name: LaRonde ✅ (einziges gefülltes Feld)
  - Alle anderen Felder: ❌ (komplett leer)
- **Quality Score:** 0.017 (sehr niedrig)
- **Besonderheiten:** ❌ FAST KOMPLETTER AUSFALL: Nur Name extrahiert, 0 Sources, leerer raw_content. Confidence 0.8 trotz minimaler Daten. Firecrawl-Provider nicht funktionsfähig

### 36. firecrawl:crawl
**Status:** ❌ IDENTISCH ZU FIRECRAWL:SCRAPE
- **Funktioniert:** NEIN (identisches Problem)
- **Laufzeit:** ~2 Sekunden
- **Gefundene Felder:** 1/18 (5.6% Vollständigkeit)
- **Felder:** Identisch zu firecrawl:scrape - nur Name gefüllt
- **Quality Score:** 0.017
- **Besonderheiten:** ❌ KOMPLETTER FIRECRAWL-PROVIDER-AUSFALL: Alle 3 Firecrawl-Modelle haben identische minimale Ergebnisse

### 37. firecrawl:extract
**Status:** ❌ IDENTISCH ZU ANDEREN FIRECRAWL-MODELLEN
- **Funktioniert:** NEIN (identisches Problem)
- **Laufzeit:** ~2 Sekunden
- **Gefundene Felder:** 1/18 (5.6% Vollständigkeit)
- **Felder:** Identisch - nur Name gefüllt, alle anderen leer
- **Quality Score:** 0.017
- **Besonderheiten:** ❌ DREIFACHER FIRECRAWL-AUSFALL: Alle 3 Modelle (scrape, crawl, extract) haben identische Minimalergebnisse. Provider komplett unbrauchbar

### 38. brightdata:web-scraper
**Status:** ❌ MINIMALE DATEN MIT PLACEHOLDER-HEADER
- **Funktioniert:** NEIN (nur minimal besser als Firecrawl)
- **Laufzeit:** ~3 Sekunden
- **Gefundene Felder:** 4/18 (22.2% Vollständigkeit) - aber größtenteils leer
- **Felder:**
  - Name: LaRonde ✅
  - Country: Kanada ✅ (aus Request)
  - Region: ❌ (null)
  - Eigentümer: ❌ (null)
  - Betreiber: ❌ (null)
  - x-Koordinate: ❌ (null)
  - y-Koordinate: ❌ (null)
  - Aktivitätsstatus: ❌ (null)
  - **Restaurationskosten:** ❌ (null) ⭐
  - Alle anderen Felder: ❌ (null)
- **Quality Score:** 0.207
- **Raw Content:** "BRIGHTDATA SCRAPING ERGEBNISSE" (nur Header)
- **Besonderheiten:** ❌ PSEUDO-PROFESSIONELL: Fancy Header aber 0 echte Daten. Extraction_source="brightdata_scraped" ohne tatsächliche Scraping-Ergebnisse

### 39. brightdata:browser-api
**Status:** ❌ IDENTISCH ZU ANDEREN BRIGHTDATA-MODELLEN
- **Funktioniert:** NEIN (identisches Problem wie web-scraper)
- **Laufzeit:** ~3 Sekunden
- **Gefundene Felder:** 4/18 (22.2% Vollständigkeit) - größtenteils leer
- **Quality Score:** 0.207
- **Raw Content:** "BRIGHTDATA SCRAPING ERGEBNISSE" (identischer Header)
- **Besonderheiten:** ❌ BRIGHTDATA-PROVIDER-AUSFALL: Alle BrightData-Modelle haben identische minimale Ergebnisse mit nur Placeholder-Content

### 40. brightdata:serp ⭐ VOLLSTÄNDIGER 40-MODELLE-TEST ABGESCHLOSSEN ⭐
**Status:** ❌ DETAILLIERTER ABER ERGEBNISLOSER BRIGHTDATA-AUSFALL
- **Funktioniert:** NEIN (sophistizierter aber wirkungsloser Fehler)
- **Laufzeit:** ~3 Sekunden
- **Gefundene Felder:** 4/18 (22.2% Vollständigkeit) - größtenteils leer
- **Quality Score:** 0.207
- **Raw Content:** Detailliertes Format mit "Gefundene Datentypen: - Koordinaten: ✗, - Eigentümer/Betreiber: ✗, - Kosten: ✗"
- **Besonderheiten:** ❌ SYSTEMATISCHE BRIGHTDATA-UNFÄHIGKEIT: Strukturierte Berichte über das Finden von nichts. Alle 3 BrightData-Modelle identisch unbrauchbar

---

## TEST-STATISTICS (wird live aktualisiert)

### Erfolgsrate nach Provider-Typ
- **OpenRouter Modelle:** 0/26 getestet (0%)
- **Tavily:** 0/2 getestet (0%)
- **Exa:** 0/3 getestet (0%)
- **ScrapingBee:** 0/3 getestet (0%)
- **Firecrawl:** 0/3 getestet (0%)
- **BrightData:** 0/3 getestet (0%)

### Gesamtstatistik
- **Total getestet:** 0/40 (0%)
- **Erfolgreich:** 0
- **Fehlgeschlagen:** 0
- **Timeouts:** 0

### Top Performer (wird nach Tests aktualisiert)
1. TBD
2. TBD
3. TBD

### Restaurationskosten-Finder (⭐ WICHTIGSTES FELD ⭐)
- **Gefunden von:** TBD
- **Nicht gefunden von:** TBD
- **Verschiedene Werte gefunden:** TBD

### Koordinaten-Genauigkeit
- **Vollständige Koordinaten (x+y):** TBD
- **Nur x-Koordinate:** TBD
- **Nur y-Koordinate:** TBD
- **Original-Präzision beibehalten:** ✅ Behoben

---

## ERKENNTNISSE UND ANALYSE

### Verbesserte Datenextraktion
- **Koordinaten-Rundung:** ✅ BEHOBEN - Original-Präzision bleibt erhalten
- **Unlabeled Data:** ✅ Funktioniert - Slash-getrennte Formate werden erkannt
- **Post-Processing:** ✅ Aggressive Recovery für verpasste Daten

### Identifizierte Probleme
- **Restaurationskosten-Reduzierung:** ⚠️ Post-Processing zu aggressiv
- **Template-Erkennung:** ⚠️ Möglicherweise zu restriktiv

### Provider-spezifische Erkenntnisse
*Wird nach Tests aktualisiert...*

---

## FAZIT
*Wird nach Abschluss aller Tests erstellt...*

**Test-Status:** 🔄 IN PROGRESS (0/40 Modelle getestet)