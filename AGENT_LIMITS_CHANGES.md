# Agent Limit Änderungen - 17.06.2025

## Übersicht

Diese Dokumentation beschreibt die Änderungen zur Erhöhung der Agent-Limits, um sicherzustellen, dass alle vom Benutzer ausgewählten Agenten tatsächlich genutzt werden.

## Problem

- Nur maximal 2-5 Agenten wurden pro Feld/Phase genutzt
- Benutzerauswahl wurde nicht respektiert
- Künstliche Limitierungen verhinderten bessere Suchergebnisse

## Lösung

### 1. Konfigurierbare Limits

Neue Umgebungsvariablen in `.env`:
```
MAX_AGENTS_PER_FIELD=20    # Vorher: hardcoded 2
MAX_AGENTS_PER_STAGE=100   # Vorher: hardcoded 3-20
```

### 2. Code-Änderungen

#### `src/core/config.py`
- Zeile 142-143: Neue Konfigurationsparameter hinzugefügt
- Dynamische Konfiguration statt hardcoded Werte

#### `src/agents/agent_coordinator.py`
- Zeile 36: Nutzt jetzt `config.max_agents_per_field` (Default: 10 → 20)
- Zeile 229: Kommentar über Erhöhung des Limits
- Zeile 255-262: Neue vierte Zuweisungsrunde für mindestens 5 Agenten pro Feld

#### `src/agents/staged_search.py`
- Zeile 34: Nutzt jetzt `config.max_agents_per_stage` (Default: 50 → 100)
- Alle Phasen nutzen jetzt das konfigurierte Limit statt hardcoded Werte

## Auswirkungen

### Positive Effekte
- **Mehr Datenquellen**: Alle ausgewählten Agenten werden genutzt
- **Bessere Abdeckung**: Höhere Chance, schwer zu findende Felder zu finden
- **Respektiert Benutzerauswahl**: Wenn 15 Agenten ausgewählt, werden auch 15 genutzt
- **Flexibilität**: Limits können über .env angepasst werden

### Trade-offs
- **Längere Suchzeit**: Mehr Agenten = mehr API-Calls
- **Höhere Kosten**: Mehr API-Nutzung
- **Mehr Ressourcen**: Höhere CPU/Memory-Nutzung

## Konfiguration

### Empfohlene Werte
- `MAX_AGENTS_PER_FIELD=20`: Erlaubt bis zu 20 Agenten pro Datenfeld
- `MAX_AGENTS_PER_STAGE=100`: Erlaubt bis zu 100 Agenten pro Suchphase

### Anpassung
Die Werte können in der `.env` Datei angepasst werden:
- Für schnellere Suchen: Werte reduzieren (z.B. 5/20)
- Für gründlichere Suchen: Werte erhöhen (z.B. 30/150)

## Monitoring

Die detaillierten Status-Updates zeigen jetzt:
- Wie viele Agenten pro Phase aktiv sind
- Welche Agenten erfolgreich waren
- Wie viele Ergebnisse gefunden wurden

## Rückwärtskompatibilität

Die Änderungen sind vollständig rückwärtskompatibel:
- Default-Werte funktionieren ohne .env Änderungen
- Alte Konfigurationen funktionieren weiterhin
- Keine Breaking Changes in der API