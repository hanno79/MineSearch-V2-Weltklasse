# MineSearch Test-Anleitung

## 1. Schnelltest ohne API-Keys

```bash
# Aktiviere Virtual Environment
source venv/bin/activate

# Führe den Basis-Test aus
python test_system.py
```

Dies testet:
- ✓ Konfiguration laden
- ✓ Orchestrator initialisieren
- ✓ Scraper Agent (funktioniert ohne API-Keys)
- ✓ Datenbank-Verbindung

## 2. Streamlit UI starten

```bash
# Starte die Web-Oberfläche
streamlit run src/ui/main.py
```

Dann öffne im Browser: http://localhost:8501

### Im UI kannst du:
1. Mine Name eingeben (z.B. "Malartic Mine")
2. Region eingeben (z.B. "Quebec")
3. Land eingeben (z.B. "Canada")
4. Agenten auswählen (nur "Basic Web Scraper" funktioniert ohne API-Keys)
5. "Start Search" klicken

## 3. Test mit echten Minen

### Beispiel-Minen für Tests:

**Kanada:**
- Malartic Mine, Quebec, Canada
- Detour Lake Mine, Ontario, Canada
- Highland Valley Copper, British Columbia, Canada

**Test-Skript für echte Mine:**
```bash
python -c "
import asyncio
from src.core.orchestrator import MineSearchOrchestrator
from src.core.config import Config
from src.agents.base_agent import MineQuery

async def test():
    config = Config()
    orchestrator = MineSearchOrchestrator(config)
    await orchestrator.initialize()
    
    query = MineQuery(
        mine_name='Malartic Mine',
        region='Quebec',
        country='Canada',
        languages=['en', 'fr'],
        required_fields=['betreiber', 'koordinaten']
    )
    
    orchestrator.active_agents = ['scraper']
    results = await orchestrator.search_mine(query)
    
    print(f'Gefunden: {len(results)} Ergebnisse')
    for r in results[:5]:
        print(f'- {r.field_name}: {r.value}')
    
    await orchestrator.cleanup()

asyncio.run(test())
"
```

## 4. API-Keys hinzufügen

### .env Datei erstellen:
```bash
cp config/.env.example .env
```

### API-Keys eintragen in .env:
```
OPENROUTER_API_KEY=your-key-here
PERPLEXITY_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here
EXA_API_KEY=your-key-here
APIFY_API_KEY=your-key-here
SCRAPINGBEE_API_KEY=your-key-here
FIRECRAWL_API_KEY=your-key-here
BRIGHTDATA_API_KEY=your-key-here
```

### Verfügbare Agenten prüfen:
```python
python -c "
from src.core.config import Config
from src.agents.factory import AgentFactory
config = Config()
agents = AgentFactory.get_available_agents(config)
print('Verfügbare Agenten:')
for name, available in agents.items():
    status = '✓' if available else '✗'
    print(f'{status} {name}')
"
```

## 5. Datenbank prüfen

### Datenbank-Inhalt anzeigen:
```bash
sqlite3 data/minesearch.db "SELECT name FROM sqlite_master WHERE type='table';"
```

### Suchergebnisse anzeigen:
```bash
sqlite3 data/minesearch.db "SELECT * FROM search_results LIMIT 10;"
```

## 6. Logs überwachen

### Log-Datei anzeigen:
```bash
tail -f logs/minesearch.log
```

### Debug-Modus aktivieren:
```bash
export LOG_LEVEL=DEBUG
python test_system.py
```

## 7. Performance testen

### Mehrere Agenten parallel:
```python
# In test_system.py, ändere:
orchestrator.active_agents = ['scraper', 'tavily', 'exa']  # wenn API-Keys vorhanden
```

## 8. Export testen

### JSON Export:
```python
from src.data.exporter import DataExporter
exporter = DataExporter()
# Nach einer Suche:
exporter.export_to_json(results, 'data/output/test_results.json')
```

## Häufige Probleme

### "No module named X"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Database locked"
```bash
# Alle Python-Prozesse beenden
pkill -f python
```

### "Port already in use" (Streamlit)
```bash
# Anderen Port verwenden
streamlit run src/ui/main.py --server.port 8502
```