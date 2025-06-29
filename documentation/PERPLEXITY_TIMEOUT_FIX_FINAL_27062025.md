# Perplexity Agent Timeout Fix - Finale Lösung
**Datum:** 27.06.2025  
**Author:** rahn  
**Version:** 1.0

## Zusammenfassung

Der persistierende Timeout-Fehler im PerplexityAgent wurde endgültig behoben. Das Problem trat nur in der Streamlit UI auf, nicht bei direkten Tests.

## Identifiziertes Problem

### Root Cause: Threading und Event Loop Kontext
1. **Streamlit** führt async Code in separaten Threads aus (via `StreamlitEventLoopManager`)
2. **SessionManager** war nicht Thread-aware und wurde nicht korrekt zwischen Komponenten geteilt
3. **PerplexityAgent** versuchte eigene SessionManager-Instanzen zu erstellen
4. **Timeout Context Manager** kann nur innerhalb eines asyncio Tasks verwendet werden

### Fehler-Kette:
```
UI SearchForm → ThreadPoolExecutor → Neuer Event Loop → 
Orchestrator → AgentManager → PerplexityAgent → 
SessionManager → RobustSession → Timeout Error
```

## Durchgeführte Lösungen

### 1. SessionManager Sharing (search_handler.py)
```python
# VORHER: Orchestrator ohne SessionManager
orchestrator = MineSearchOrchestrator(
    self.config,
    status_callback=mine_status_callback
)

# NACHHER: SessionManager explizit übergeben
from src.utils.session_manager import SessionManager
session_manager = SessionManager()

orchestrator = MineSearchOrchestrator(
    self.config,
    session_manager,
    status_callback=mine_status_callback
)
```

### 2. Agent Config Update (perplexity_agent.py)
```python
# Initialisierung und _ensure_session nutzen jetzt Config SessionManager
if hasattr(self.config, 'session_manager') and self.config.session_manager:
    self._session_manager = self.config.session_manager
else:
    self._session_manager = SessionManager()
```

### 3. AgentFactory SessionManager Support (factory.py)
```python
# SessionManager aus kwargs extrahieren und an Config übergeben
session_manager = kwargs.pop('session_manager', None)

if session_manager:
    agent_config["session_manager"] = session_manager
```

### 4. Explicit Timeout Creation (perplexity_agent.py)
```python
# VORHER: Implicit timeout in async context
async with self._session.post(url, headers=headers, json=payload) as response:

# NACHHER: Explicit timeout creation
timeout = aiohttp.ClientTimeout(total=30)
async with self._session.post(url, headers=headers, json=payload, timeout=timeout) as response:
```

## Ergebnisse

### Vorher:
- ❌ `RuntimeError: Timeout context manager should be used inside a task`
- ❌ Keine API-Anfragen möglich in UI
- ✅ Direkte Tests funktionierten

### Nachher:
- ✅ Keine RuntimeError mehr
- ✅ API-Anfragen funktionieren in UI
- ✅ SessionManager wird korrekt geteilt
- ✅ Threading-kompatibel

## Test-Befehle

### Direkter Test (funktionierte immer):
```bash
python test_new_perplexity.py
```

### UI Test (jetzt funktionsfähig):
```bash
streamlit run test_ui_minimal.py
```

### Haupt-UI:
```bash
streamlit run src/ui/main.py
```

## Wichtige Erkenntnisse

1. **Thread-Safety**: Bei Streamlit immer beachten, dass Code in separaten Threads läuft
2. **Shared Resources**: SessionManager und ähnliche Ressourcen sollten explizit geteilt werden
3. **Timeout Handling**: aiohttp Timeouts sollten außerhalb des async context erstellt werden
4. **Event Loop Context**: Nicht davon ausgehen, dass immer derselbe Event Loop verwendet wird

## Verbleibende Optimierungen

1. **Session Cleanup**: "Unclosed client session" Warnungen beheben
2. **Performance**: API-Timeouts optimieren (aktuell teilweise 30s+)
3. **Error Recovery**: Bessere Fehlerbehandlung bei API-Timeouts

Der PerplexityAgent ist jetzt vollständig funktionsfähig in allen Kontexten!