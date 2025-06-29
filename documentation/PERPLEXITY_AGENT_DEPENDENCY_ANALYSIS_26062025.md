# Perplexity Agent Abhängigkeitsanalyse
Author: rahn
Datum: 26.06.2025
Version: 1.0

## Übersicht

Diese Analyse dokumentiert alle Abhängigkeiten des Perplexity Agents und identifiziert potenzielle Folgefehler in anderen Systemkomponenten.

## 1. Direkte Abhängigkeiten des Perplexity Agents

### 1.1 Core-Komponenten
- **BaseAgent** (src/agents/base_agent.py)
  - Basis-Klasse für alle Agenten
  - Stellt CancellationToken und Status-Management bereit
  
- **SessionManager** (src/utils/session_manager.py)
  - Verwaltet HTTP-Sessions für alle Agenten
  - Kritisch für Event Loop Management
  
- **CancellationToken** (src/core/cancellation.py)
  - Ermöglicht Abbruch von laufenden Suchen
  - Wird von BaseAgent verwaltet

### 1.2 Utility-Komponenten
- **safe_dict_access** (src/utils/safe_dict_access.py)
  - Sicherer Zugriff auf Dictionary-Strukturen
  - Verhindert KeyError und TypeError
  
- **RateLimiter** (src/agents/rate_limiter.py)
  - Begrenzt API-Anfragen
  - 5 Anfragen pro Minute für Perplexity
  
- **enhanced_search** (src/agents/enhanced_search.py)
  - Mining-spezifische Suchstrategien
  - Domain-Liste für Mining-Websites

### 1.3 Logging & Monitoring
- **Logger** (src/core/logger.py)
  - PerformanceLogger für Zeitmessungen
  - Agent-spezifische Log-Kategorien

## 2. Module die den Perplexity Agent nutzen

### 2.1 Factory & Management
- **AgentFactory** (src/agents/factory.py)
  - Erstellt Perplexity Agent Instanzen
  - Verwaltet Agent-Konfiguration
  
- **AgentManager** (src/core/agent_manager.py)
  - Initialisiert alle Agenten
  - Registriert Cancellation Cleanup
  
### 2.2 Orchestrierung
- **MineSearchOrchestratorV2** (src/core/orchestrator.py)
  - Koordiniert alle Agenten
  - Nutzt AgentManager für Initialisierung
  
- **SearchExecutor** (src/core/search_executor.py)
  - Führt parallele Suchen aus
  - Verwaltet Cancellation für alle Agenten

### 2.3 Source Discovery
- **SourceDiscoveryService** (src/core/source_discovery_service.py)
  - Nutzt Perplexity für Quellen-Entdeckung
  - Kritisch für initiale Suchphase

### 2.4 UI-Komponenten
- **SearchHandler** (src/ui/handlers/search_handler.py)
  - Verarbeitet UI-Suchanfragen
  - Übergibt Cancellation Token an Orchestrator

## 3. Identifizierte Probleme und Auswirkungen

### 3.1 Event Loop Probleme

**Problem**: SessionManager erstellt Sessions in verschiedenen Event Loops

**Betroffene Komponenten**:
- Alle Agenten die SessionManager nutzen:
  - ClaudeAgent
  - TavilyAgent
  - GPTAgent
  - ExaAgent
  - ScraperAgent
  - Alle anderen HTTP-basierten Agenten

**Auswirkung**: "Session is closed" und "Event loop is closed" Fehler

### 3.2 Cancellation Token Propagierung

**Problem**: Nicht alle Agenten prüfen Cancellation Token korrekt

**Betroffene Agenten** (nutzen _cancellation_token):
- PerplexityAgent ✓ (korrekt implementiert)
- ClaudeAgent ✓ (korrekt implementiert)
- ScraperAgent ✓ (korrekt implementiert)
- FirecrawlAgent ✓ (korrekt implementiert)

**Agenten OHNE Cancellation Support**:
- TavilyAgent ✗
- ExaAgent ✗
- GPTAgent ✗
- ApifyAgent ✗
- ScrapingBeeAgent ✗
- BrightDataAgent ✗
- OpenRouterAgent ✗
- DeepSeekResearchAgent ✗

### 3.3 Session Cleanup Probleme

**Problem**: Inkonsistente Session-Cleanup Implementierung

**Agenten mit cleanup() Methode**:
- PerplexityAgent ✓
- TavilyAgent ✓
- Andere Agenten: Teilweise oder gar nicht implementiert

## 4. Abhängigkeitsmatrix

```
┌─────────────────────────┬───────────────┬────────────────┬──────────────┬─────────────┐
│ Komponente              │ Nutzt Perpl.  │ SessionManager │ Cancellation │ Cleanup     │
├─────────────────────────┼───────────────┼────────────────┼──────────────┼─────────────┤
│ AgentFactory            │ ✓             │ ✗              │ ✗            │ ✗           │
│ AgentManager            │ ✓ (indirekt)  │ ✓              │ ✓            │ ✗           │
│ Orchestrator            │ ✓ (indirekt)  │ ✓              │ ✓            │ ✓           │
│ SearchExecutor          │ ✓ (indirekt)  │ ✗              │ ✓            │ ✗           │
│ SourceDiscovery         │ ✓ (direkt)    │ ✗              │ ✗            │ ✗           │
│ ClaudeAgent             │ ✗             │ ✓              │ ✓            │ ✓           │
│ TavilyAgent             │ ✗             │ ✓              │ ✗            │ ✓           │
│ GPTAgent                │ ✗             │ ✓              │ ✗            │ ✗           │
│ ExaAgent                │ ✗             │ ✓              │ ✗            │ ✗           │
│ ScraperAgent            │ ✗             │ ✓              │ ✓            │ ✗           │
└─────────────────────────┴───────────────┴────────────────┴──────────────┴─────────────┘
```

## 5. Kritische Abhängigkeiten

### 5.1 SessionManager (KRITISCH)
- **Genutzt von**: ALLEN HTTP-basierten Agenten
- **Problem**: Event Loop Inkompatibilität
- **Auswirkung**: System-weite Session-Fehler

### 5.2 CancellationToken (WICHTIG)
- **Genutzt von**: Nur 4 von 15+ Agenten
- **Problem**: Inkonsistente Implementierung
- **Auswirkung**: Suchen können nicht zuverlässig abgebrochen werden

### 5.3 Cleanup-Mechanismen (WICHTIG)
- **Implementiert von**: Nur wenige Agenten
- **Problem**: Ressourcen-Lecks
- **Auswirkung**: Memory Leaks, offene Connections

## 6. Empfohlene Maßnahmen

### 6.1 Sofortmaßnahmen
1. **SessionManager Event Loop Fix**
   - Sicherstellen dass Sessions im richtigen Event Loop erstellt werden
   - Robuste Event Loop Detection implementieren

2. **Cancellation Token für alle Agenten**
   - BaseAgent sollte Standard-Implementierung bereitstellen
   - Alle Agenten müssen Token in Schleifen prüfen

### 6.2 Mittelfristige Maßnahmen
1. **Einheitliches Cleanup-Pattern**
   - BaseAgent.cleanup() als Template-Method
   - Alle Agenten müssen cleanup implementieren

2. **Session-Lifecycle Management**
   - Zentralisierte Session-Verwaltung
   - Automatisches Cleanup bei Agent-Beendigung

3. **Dependency Injection**
   - SessionManager als Dependency injecten
   - Vermeidung globaler Instanzen

## 7. Zusammenfassung

Der Perplexity Agent ist ein zentraler Bestandteil des Systems mit weitreichenden Abhängigkeiten. Die identifizierten Probleme betreffen nicht nur den Perplexity Agent selbst, sondern das gesamte Agent-System:

1. **Event Loop Management** ist die kritischste Abhängigkeit
2. **Cancellation Support** ist inkonsistent implementiert
3. **Resource Cleanup** fehlt in vielen Agenten
4. **SessionManager** ist Single Point of Failure

Die Behebung dieser Probleme erfordert systematische Änderungen an der Agent-Architektur, nicht nur punktuelle Fixes am Perplexity Agent.