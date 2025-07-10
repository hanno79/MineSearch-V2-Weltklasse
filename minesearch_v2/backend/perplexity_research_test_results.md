# Perplexity Research Modelle Test-Ergebnisse

**Datum:** 09.07.2025  
**Autor:** rahn

## Zusammenfassung

Die Tests der beiden fehlenden Perplexity Research Modelle wurden erfolgreich durchgeführt.

## Testergebnisse

### 1. perplexity:sonar-deep-research
- **Status:** ✅ Erfolgreich getestet
- **Erfolgsrate:** 100%
- **Durchschnittliche Felder:** 10.0
- **Durchschnittliche Zeit:** 218.2 Sekunden (~3.6 Minuten)
- **Getestete Mine:** Éléonore (Gold, Quebec, Canada)
- **Besonderheiten:** 
  - Sehr lange Antwortzeit (über 3 Minuten)
  - Höchste Feldanzahl aller Perplexity Modelle
  - 9 Quellen verwendet, 142 angeboten

### 2. perplexity:sonar-reasoning
- **Status:** ✅ Erfolgreich getestet  
- **Erfolgsrate:** 100%
- **Durchschnittliche Felder:** 8.0
- **Durchschnittliche Zeit:** 21.7 Sekunden
- **Getestete Mine:** Éléonore (Gold, Quebec, Canada)
- **Besonderheiten:**
  - Deutlich schneller als Deep Research
  - Gute Feldabdeckung
  - 5 Quellen verwendet, 142 angeboten

## Vergleich aller Perplexity Modelle

Nach den Tests sind nun alle 4 Perplexity Modelle in der Datenbank:

1. **perplexity:sonar-deep-research** - 10.0 Felder, 218.2s, 100% Erfolg
2. **perplexity:sonar-pro** - 9.0 Felder, 24.7s, 100% Erfolg  
3. **perplexity:sonar-reasoning** - 8.0 Felder, 21.7s, 100% Erfolg
4. **perplexity:sonar** - 6.5 Felder, 11.5s, 83% Erfolg

## Erkenntnisse

1. **Deep Research** liefert die besten Ergebnisse, benötigt aber sehr viel Zeit
2. **Reasoning** bietet ein gutes Verhältnis zwischen Qualität und Geschwindigkeit
3. Beide neuen Modelle haben eine 100% Erfolgsrate
4. Die Research-Modelle nutzen mehr Quellen für ihre Antworten

## Empfehlung

- **sonar-deep-research**: Für kritische Anfragen wo Vollständigkeit wichtiger als Zeit ist
- **sonar-reasoning**: Für normale Anfragen mit gutem Qualitäts-/Zeit-Verhältnis
- **sonar-pro**: Weiterhin Standard für die meisten Anwendungsfälle
- **sonar**: Nur für schnelle, einfache Anfragen

## Nächste Schritte

Die beiden Perplexity Research Modelle sind nun erfolgreich in das System integriert und können in der Produktionsumgebung verwendet werden.