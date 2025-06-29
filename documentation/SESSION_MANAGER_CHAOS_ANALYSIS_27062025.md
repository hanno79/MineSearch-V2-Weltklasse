"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Analyse des SessionManager-Chaos in der Codebasis
"""

# SessionManager Chaos-Analyse

## Übersicht

Die Codebasis enthält derzeit zwei verschiedene SessionManager-Implementierungen, die parallel existieren und zu Verwirrung führen:

1. **SessionManager** (`src/utils/session_manager.py`) - Version 2.1
2. **SimpleSessionManager** (`src/utils/simple_session_manager.py`) - Version 1.0

## 1. SessionManager (Original)

### Eigenschaften:
- **Version**: 2.1-TIMEOUT-FIX-27062025
- **Datei**: `/app/src/utils/session_manager.py`
- **Komplexität**: Hoch
- **Features**:
  - RobustSession mit Context Manager (`async with`)
  - Automatische Session-Wiederherstellung
  - Periodic Cleanup Task
  - Cancellation Token Support
  - WeakReference-basiertes Memory Management
  - Timeout-Konvertierung (int/float → ClientTimeout)

### Problembereiche:
- Zeile 118-129: Komplexe Timeout-Behandlung mit Task-Prüfung (wurde in v2.1 entfernt)
- Context Manager kann in bestimmten Situationen Probleme verursachen
- Hohe Komplexität macht Debugging schwierig

### Verwendung:
```python
session_manager = SessionManager()
robust_session = await session_manager.get_robust_session("agent_id")
async with robust_session.request("GET", url) as response:
    # Verarbeitung
```

## 2. SimpleSessionManager (Vereinfacht)

### Eigenschaften:
- **Version**: 1.0-NO-CONTEXT-MANAGER
- **Datei**: `/app/src/utils/simple_session_manager.py`
- **Komplexität**: Niedrig
- **Features**:
  - Kein Context Manager - direkte Requests
  - Timeout auf Session-Ebene (nicht pro Request)
  - Einfacheres Error Handling
  - Keine Task-Prüfungen

### Vorteile:
- Zeile 90-111: Direkte Request-Methode ohne Context Manager
- Zeile 97-98: Timeout wird aus kwargs entfernt (auf Session-Ebene gesetzt)
- Einfachere Fehlerbehandlung

### Verwendung:
```python
session_manager = SimpleSessionManager()
simple_session = await session_manager.get_session("agent_id")
response = await simple_session.request("GET", url)
# Manuelle Response-Verarbeitung
```

## 3. Agent-Verwendung

### Agents mit SessionManager (Original):
- **PerplexityAgent** (Zeile 23: `from src.utils.session_manager import SessionManager`)
- **TavilyAgent**
- **GPTAgent**
- **ExaAgent**
- **ScraperAgent**
- **OpenRouterAgent**
- **PerplexityDeepAgent**
- **BrightDataAgent**
- **FirecrawlAgent**
- **ApifyAgent**
- **DeepSeekResearchAgent**
- **ClaudeAgent**

### Agents mit SimpleSessionManager:
- **Keine** (nur in test_new_perplexity.py verwendet)

## 4. Timeout-Problem im PerplexityAgent

Der PerplexityAgent verwendet den normalen SessionManager, aber die Timeout-Behandlung ist problematisch:

### Problem-Stelle (Zeile 437-442):
```python
async with self._session.post(
    self.base_url,
    headers=headers,
    json=payload
) as response:
```

Hier wird der Context Manager des normalen SessionManagers verwendet, was zu den beschriebenen Timeout-Problemen führen kann.

### Mögliche Lösungen:

1. **Migration zu SimpleSessionManager**: 
   - PerplexityAgent auf SimpleSessionManager umstellen
   - Timeout-Probleme würden verschwinden
   - Einfacheres Debugging

2. **Fix im SessionManager**:
   - Context Manager robuster machen
   - Timeout-Behandlung vereinfachen
   - Task-Prüfungen komplett entfernen

## 5. Inkonsistenzen

### Doppelte Initialisierung:
- PerplexityAgent erstellt SessionManager in `initialize()` (Zeile 54)
- Und nochmal in `_ensure_session()` (Zeile 111)

### Session-Verwaltung:
- Mischung aus `_session` und `_robust_session` Attributen
- Unklare Verantwortlichkeiten

## 6. Empfehlungen

### Kurzfristig:
1. **Test-Migration**: PerplexityAgent testweise auf SimpleSessionManager umstellen
2. **Monitoring**: Logging erweitern um Timeout-Probleme besser zu identifizieren
3. **Dokumentation**: Klare Richtlinien welcher Manager wann verwendet werden soll

### Langfristig:
1. **Konsolidierung**: Nur einen SessionManager behalten
2. **Vereinfachung**: Features des SimpleSessionManager in Haupt-SessionManager integrieren
3. **Tests**: Umfassende Unit-Tests für Session-Management
4. **Migration**: Alle Agenten auf einheitlichen Manager umstellen

## 7. Test-Datei

Die Datei `test_new_perplexity.py` zeigt einen Versuch, den SimpleSessionManager zu verwenden, aber:
- Zeile 25: Import von `SIMPLE_SESSION_VERSION` 
- Aber der PerplexityAgent selbst verwendet weiterhin den normalen SessionManager

Dies zeigt, dass eine echte Migration noch nicht stattgefunden hat.

## Fazit

Das aktuelle Setup mit zwei parallelen SessionManager-Implementierungen ist verwirrend und fehleranfällig. Eine klare Entscheidung für eine Implementierung und konsequente Migration aller Agenten wäre sinnvoll. Der SimpleSessionManager scheint die robustere Lösung für die aktuellen Timeout-Probleme zu sein.