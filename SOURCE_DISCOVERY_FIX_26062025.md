# Source Discovery Agent Fix - 26.06.2025

## Problem
Bei der Source Discovery Phase wurden nur die vom Benutzer ausgewählten Agenten (z.B. perplexity, perplexity_deep) verwendet, anstatt alle verfügbaren 33 Agenten. Dies führte zu einer eingeschränkten Quellenentdeckung.

## Ursache
1. Der SearchHandler setzt über `orchestrator.set_active_agents()` nur die vom User ausgewählten Agenten als aktiv
2. Die `discover_sources` Methode im Orchestrator verwendete `agent_manager.get_active_agents()`, welche nur die aktiven Agenten zurückgibt
3. Dadurch erhielt die Source Discovery nur 2 statt 33 Agenten

## Lösung

### 1. Neue Methode in AgentManager
```python
def get_all_agents(self) -> List[BaseAgent]:
    """Gibt alle verfügbaren Agenten zurück (nicht nur die aktiven)"""
    return list(self.agents.values())
```

### 2. Anpassung in Orchestrator.discover_sources()
```python
async def discover_sources(self, query: MineQuery, cancellation_token=None) -> List:
    """Entdeckt Quellen für eine Mine"""
    # ÄNDERUNG 26.06.2025: Verwende ALLE verfügbaren Agenten für Source Discovery,
    # nicht nur die vom User ausgewählten, um maximale Quellenabdeckung zu erreichen
    agents = self.agent_manager.get_all_agents()
    
    self.logger.info(f"Source Discovery mit {len(agents)} Agenten (statt nur {len(self.agent_manager.get_active_agents())} aktiven)")
    
    sources = await self.source_discovery.discover_sources(
        query=query,
        agents=agents,
        status_callback=self.status_callback,
        cancellation_token=cancellation_token
    )
    
    return sources
```

## Auswirkungen
- Source Discovery nutzt jetzt alle 33 verfügbaren Agenten für maximale Quellenabdeckung
- Die eigentliche Suche verwendet weiterhin nur die vom User ausgewählten Agenten
- Bessere und umfassendere Quellenentdeckung für alle Minen

## Geänderte Dateien
1. `/app/src/core/agent_manager.py` - Neue Methode `get_all_agents()`
2. `/app/src/core/orchestrator.py` - `discover_sources()` nutzt jetzt alle Agenten

## Test
Die Änderung kann getestet werden, indem man:
1. Eine Suche mit nur 2 ausgewählten Agenten startet
2. In den Logs prüft, ob "Source Discovery mit 33 Agenten (statt nur 2 aktiven)" erscheint
3. Überprüft, ob mehr diverse Quellen gefunden werden