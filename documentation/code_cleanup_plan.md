# Code Cleanup Plan
**Autor:** rahn  
**Datum:** 24.06.2025  
**Version:** 1.0

## Identifizierte Cleanup-Bereiche

### 1. Backup-Dateien zum Löschen
- `/app/src/core/orchestrator_backup_20250622_071849.py`
- `/app/src/ui/main_backup_20250622_071733.py`

### 2. Session Management Verbesserungen
Folgende Agenten nutzen noch nicht den SessionManager:
- brightdata_agent.py
- firecrawl_agent.py
- apify_agent.py
- perplexity_agent.py
- deepseek_research_agent.py
- gpt_agent.py
- claude_agent.py
- exa_agent.py
- scrapingbee/api_client.py

### 3. Doppelte Browser Agent Struktur
- `/app/src/agents/browser_agent.py` (wrapper)
- `/app/src/agents/browser_agent/browser_agent.py` (implementation)

### 4. Model ID Probleme
- OpenRouter Model IDs werden inkonsistent generiert
- Factory generiert falsche Keys für:
  - llama-3.2-90b-instruct (sollte llama-3.2-90b-vision-instruct sein)
  - gemini-2.0-flash-thinking-exp-1219 (sollte ohne -1219 sein)

### 5. Veraltete Imports
- Viele Dateien importieren aiohttp direkt statt SessionManager zu nutzen

## Empfohlene Aktionen

1. **Backup-Dateien verschieben:**
   ```bash
   mv /app/src/core/orchestrator_backup_20250622_071849.py /app/to_delete/
   mv /app/src/ui/main_backup_20250622_071733.py /app/to_delete/
   ```

2. **Session Management Migration:**
   - Alle Agenten auf SessionManager umstellen
   - Zentrale Session-Verwaltung für bessere Performance

3. **Browser Agent Konsolidierung:**
   - Wrapper und Implementation zusammenführen

4. **Model Registry Fix:**
   - Konsistente Model ID Generierung implementieren

5. **Code Quality:**
   - Ungenutzte Imports entfernen
   - Doppelten Code konsolidieren