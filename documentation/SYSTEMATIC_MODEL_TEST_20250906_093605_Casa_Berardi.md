# MineSearch v3.0.0 - Casa Berardi Model-Test Report

**Test Datum:** 2025-09-06 09:36:05  
**Test Parameter:**
- **Mine:** Casa Berardi
- **Land:** Kanada  
- **Region:** Quebec

---

## 📊 Zusammenfassung

- **Getestete Modelle:** 8
- **Einzelsuche Erfolgsrate:** 87.5%
- **Gesamterfolgsrate:** 87.5%
- **Test-Dauer:** 3.5 Minuten

---

## 🔍 Phase 1: Einzelsuche Ergebnisse

### openrouter:deepseek-free
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 6.71 Sekunden
- **Gefundene Felder:** 9/18 (50.0% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp
- **Nicht gefundene Felder:** Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten, Fläche, Quellenangaben, Tiefe, Reserven, Ressourcen (9/18)
- **Quality Score:** 0.45
- **Quellen gefunden:** 146 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 9/18 Felder

### openrouter:deepseek-chat
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 11.55 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten, Fläche
- **Nicht gefundene Felder:** Quellenangaben, Tiefe, Reserven, Ressourcen (4/18)
- **Quality Score:** 0.51
- **Quellen gefunden:** 170 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 14/18 Felder

### openrouter:claude-3.5-sonnet
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 9.66 Sekunden
- **Gefundene Felder:** 13/18 (72.2% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten
- **Nicht gefundene Felder:** Fläche, Quellenangaben, Tiefe, Reserven, Ressourcen (5/18)
- **Quality Score:** 0.90
- **Quellen gefunden:** 138 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 13/18 Felder

### openrouter:gpt-4o-mini
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 9.24 Sekunden
- **Gefundene Felder:** 16/18 (88.9% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten, Fläche, Quellenangaben, Tiefe
- **Nicht gefundene Felder:** Reserven, Ressourcen (2/18)
- **Quality Score:** 0.84
- **Quellen gefunden:** 97 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 16/18 Felder

### openrouter:mistral-small-free
**Status:** ❌ FEHLGESCHLAGEN
- **Funktioniert:** NEIN
- **Laufzeit:** 10.83 Sekunden
- **Gefundene Felder:** 9/18 (50.0% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp
- **Nicht gefundene Felder:** Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten, Fläche, Quellenangaben, Tiefe, Reserven, Ressourcen (9/18)
- **Quality Score:** 0.51
- **Quellen gefunden:** 157 verschiedene URLs
- **Fehler/Probleme:** Timeout oder Netzwerkfehler
- **Besonderheiten:** Casa Berardi Test fehlgeschlagen

### scrapingbee:basic-scrape
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 8.35 Sekunden
- **Gefundene Felder:** 11/18 (61.1% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende
- **Nicht gefundene Felder:** Fördermenge, Restaurationskosten, Fläche, Quellenangaben, Tiefe, Reserven, Ressourcen (7/18)
- **Quality Score:** 0.63
- **Quellen gefunden:** 112 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 11/18 Felder

### scrapingbee:ai-extract
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 9.21 Sekunden
- **Gefundene Felder:** 12/18 (66.7% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende, Fördermenge
- **Nicht gefundene Felder:** Restaurationskosten, Fläche, Quellenangaben, Tiefe, Reserven, Ressourcen (6/18)
- **Quality Score:** 0.53
- **Quellen gefunden:** 176 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 12/18 Felder

### firecrawl:scrape
**Status:** ✅ ERFOLGREICH
- **Funktioniert:** JA
- **Laufzeit:** 11.14 Sekunden
- **Gefundene Felder:** 14/18 (77.8% Vollständigkeit)
  - Name, Land, Region, Eigentümer, Betreiber, Koordinaten, Aktivitätsstatus, Rohstoff, Minentyp, Produktionsstart, Produktionsende, Fördermenge, Restaurationskosten, Fläche
- **Nicht gefundene Felder:** Quellenangaben, Tiefe, Reserven, Ressourcen (4/18)
- **Quality Score:** 0.52
- **Quellen gefunden:** 69 verschiedene URLs
- **Fehler/Probleme:** KEINE
- **Besonderheiten:** Casa Berardi erfolgreich analysiert: 14/18 Felder

---

## 🏆 Gesamtbewertung

**🎯 EXZELLENT - System ist produktionsreif!**

### Casa Berardi Spezifische Erkenntnisse:
- ✅ Mine erfolgreich in 7/8 Modellen gefunden
- ✅ Kanadische Quebec-Region korrekt identifiziert
- ✅ Goldmine-spezifische Datenfelder extrahiert
- ✅ Durchschnittliche Datenqualität: 0.61

---

*Automatisch generiert durch MineSearch v3.0.0 Test-Workflow am 2025-09-06 09:36:05*
