# MineSearch 2.0 - Native Start Guide

## System erfolgreich repariert und vollständig wiederhergestellt!

**Status**: ✅ Vollständig funktionsfähig (WELTKLASSE Version)
**Datum**: 06.09.2025
**Version**: MineSearch 2.1 native - Vollständige Docker-Version wiederhergestellt
**Frontend**: 431KB (8961 Zeilen) - Erweiterte Version aktiv

## Schnellstart

```bash
cd /home/hanno/projects/MineSearch
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="/home/hanno/projects/MineSearch/backend:$PYTHONPATH"
python3 -m uvicorn backend.minesearch.main:app --host 0.0.0.0 --port 8000 --reload
```

**Zugriff**: http://localhost:8000/static/index.html

## System Status

### ✅ Provider (12/12 aktiv)
- **Perplexity**: 4 Modelle (sonar, sonar-pro, sonar-deep-research, sonar-reasoning)
- **OpenRouter**: 13 Modelle (deepseek, mistral, llama, glm, gpt-oss, etc.)
- **Abacus**: 1 Modell (deep-agent)
- **Tavily**: 2 Modelle (search, deep-research)
- **Exa**: 3 Modelle (neural-search, research, research-pro)
- **ScrapingBee**: 3 Modelle (basic-scrape, js-render, ai-extract)
- **Firecrawl**: 3 Modelle (scrape, crawl, extract)
- **BrightData**: 3 Modelle (web-scraper, browser-api, serp)
- **OpenAI**: 8 Modelle (o3, o4, gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
- **Anthropic**: 5 Modelle (claude-sonnet-4, claude-opus-4, claude-3.7-sonnet, etc.)
- **Gemini**: 6 Modelle (gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash, etc.)
- **Grok**: 4 Modelle (grok-4, grok-3, grok-3-mini, grok-3-fast)

**Total**: 55 AI-Modelle verfügbar

### ✅ Funktionen (Vollständige WELTKLASSE Version)
- **Single Search**: Mining-Recherche mit einem Modell
- **CSV Batch Search**: Bulk-Verarbeitung mit 15+ Standard-Minen (nicht nur 3!)  
- **Model Quick Selection**: Top-3 Modelle, kostenlose Modelle, Provider-Gruppen
- **Consolidated Results**: Multi-Modell-Vergleiche mit erweiterten Features
- **Statistics**: Detaillierte Analyse-Statistiken mit umfangreichem Dashboard
- **Sources**: Quellenmanagement und -validierung
- **Advanced UI**: Professionelle Navigation, Data Cards, Comparison Engine
- **Export Functions**: Erweiterte Export-Optionen für alle Datentypen

### ✅ Database
- SQLite: `./mines.db`
- 9 Tabellen aktiv
- Connection Pool initialisiert

## Troubleshooting

### Port bereits belegt
```bash
pkill -f uvicorn
# Dann neu starten
```

### Python Module fehlen
```bash
python3 -m pip install --user -r requirements.txt --break-system-packages
```

### Environment Variablen
Die `.env` Datei muss alle API-Keys enthalten:
- PERPLEXITY_API_KEY
- OPENROUTER_API_KEY  
- ABACUS_API_KEY
- TAVILY_API_KEY
- EXA_API_KEY
- SCRAPINGBEE_API_KEY
- FIRECRAWL_API_KEY
- BRIGHTDATA_API_KEY
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY
- GROK_API_KEY

## Log-Monitoring

```bash
tail -f logs/minesearch.log
```

---

**Hinweis**: System wurde vollständig von Docker auf native Installation migriert und repariert.
Alle temporären Workaround-Dateien wurden bereinigt.