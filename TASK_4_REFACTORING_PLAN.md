# TASK 4: Refactoring Plan für große Dateien

## Priorisierung (nach Größe und Wichtigkeit)

### Gruppe 1: Utils & Core (Priorität: HOCH)
1. **pdf_processor.py** (660 Zeilen) - Wichtige Utility
2. **validators.py** (535 Zeilen) - Core-Funktionalität

### Gruppe 2: Haupt-Agenten (Priorität: HOCH)
3. **scraper_agent.py** (628 Zeilen)
4. **agent_coordinator.py** (609 Zeilen)
5. **claude_agent.py** (524 Zeilen)

### Gruppe 3: Spezial-Agenten (Priorität: MITTEL)
6. **openrouter_agent.py** (618 Zeilen)
7. **firecrawl_agent.py** (612 Zeilen)
8. **scrapingbee_agent.py** (579 Zeilen)
9. **apify_agent.py** (570 Zeilen)

### Gruppe 4: Support-Module (Priorität: MITTEL)
10. **deep_web_crawler.py** (547 Zeilen)
11. **enhanced_search.py** (546 Zeilen)
12. **dynamic_keyword_generator.py** (541 Zeilen)
13. **dynamic_source_discovery.py** (538 Zeilen)

### Gruppe 5: Weitere Agenten (Priorität: NIEDRIG)
14. **perplexity_deep_agent.py** (527 Zeilen)
15. **exa_agent.py** (509 Zeilen)
16. **deepseek_research_agent.py** (506 Zeilen)
17. **browser_agent.py** (502 Zeilen)

## Refactoring-Strategie

### Für Agenten:
- Nutze Base-Module (BaseHTTPClient, ResultProcessor, etc.)
- Extrahiere spezifische Parser/Scraper
- Trenne API-Logic von Result-Processing

### Für Utils:
- Modularisiere nach Funktionalität
- Erstelle kleinere, fokussierte Module

### Für Core:
- Trenne Validation-Types
- Erstelle spezialisierte Validator-Klassen

## Geschätzte Zeit: 
- 2-3 Dateien pro Session
- Fokus auf Code-Qualität statt Quantität