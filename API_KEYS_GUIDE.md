# API Keys Guide für Multi-Agent Mining Research System

Diese Anleitung erklärt, wie Sie die benötigten API-Keys für die verschiedenen Agenten erhalten.

## Übersicht der Agenten

| Agent | API-Key Variable | Kostenlos | Beschreibung |
|-------|-----------------|-----------|--------------|
| Claude | `OPENROUTER_API_KEY` | ❌ | Claude-3 AI für intelligente Suche |
| GPT-4 | `OPENROUTER_API_KEY` | ❌ | GPT-4 für Mining-Recherche |
| OpenRouter | `OPENROUTER_API_KEY` | ✅/❌ | Zugriff auf viele LLMs (kostenlose und Premium) |
| DeepSeek | `DEEPSEEK_API_KEY` | ✅ | DeepSeek Chat & Reasoning (via OpenRouter kostenlos) |
| Perplexity | `PERPLEXITY_API_KEY` | ❌ | Web-basierte AI-Suche |
| Perplexity Deep | `PERPLEXITY_API_KEY` | ❌ | Deep Research mit iterativer Suche |
| Gemini | `GEMINI_API_KEY` | ✅/❌ | Google Gemini mit Deep Research |
| OpenAI o1 | `OPENAI_API_KEY` | ❌ | Advanced Reasoning Model |
| Tavily | `TAVILY_API_KEY` | ✅ | Erweiterte Web-Suche (kostenlose Stufe verfügbar) |
| Exa | `EXA_API_KEY` | ✅ | Semantische Suche (kostenlose Stufe) |
| Apify | `APIFY_API_KEY` | ✅ | Web-Scraping (kostenlose Credits) |
| ScrapingBee | `SCRAPINGBEE_API_KEY` | ✅ | JavaScript-Rendering (kostenlose Stufe) |
| Firecrawl | `FIRECRAWL_API_KEY` | ✅ | Web-Crawling (kostenlose Stufe) |
| BrightData | `BRIGHTDATA_API_KEY` | ❌ | Enterprise Web-Scraping |
| Scraper | Keine | ✅ | Basis Web-Scraper (immer verfügbar) |

## Schritt-für-Schritt Anleitungen

### 1. OpenRouter API Key (für Claude, GPT-4 und viele andere Modelle)

1. Besuchen Sie [OpenRouter.ai](https://openrouter.ai/)
2. Klicken Sie auf "Sign Up" oder "Login"
3. Nach dem Login, gehen Sie zu "API Keys" im Dashboard
4. Klicken Sie auf "Create API Key"
5. Kopieren Sie den generierten Key
6. Fügen Sie ihn in Ihre `.env` Datei ein: `OPENROUTER_API_KEY=sk-or-v1-...`

**Kostenlose Modelle über OpenRouter:**
- DeepSeek Chat (sehr gut und kostenlos!)
- Qwen 2.5 72B
- Mistral 7B
- Llama 3.2 90B
- Gemma 2 27B
- Hermes 3 Llama 70B
- Gemini 2.0 Flash

**Premium Modelle (Kosten pro Token):**
- Claude 3.5 Sonnet
- Claude 3 Opus
- GPT-4o
- Gemini 1.5 Pro

### 2. Perplexity API Key

1. Gehen Sie zu [Perplexity.ai](https://www.perplexity.ai/)
2. Erstellen Sie einen Account
3. Navigieren Sie zu Settings → API
4. Generieren Sie einen API Key
5. In `.env`: `PERPLEXITY_API_KEY=pplx-...`

### 3. Tavily API Key (Empfohlen - Kostenlose Stufe!)

1. Besuchen Sie [Tavily.com](https://tavily.com/)
2. Klicken Sie auf "Get API Key"
3. Registrieren Sie sich kostenlos
4. Sie erhalten 1000 kostenlose Suchen pro Monat
5. In `.env`: `TAVILY_API_KEY=tvly-...`

### 4. Exa API Key (Kostenlose Stufe verfügbar)

1. Gehen Sie zu [Exa.ai](https://exa.ai/)
2. Klicken Sie auf "Get Started"
3. Erstellen Sie einen kostenlosen Account
4. API Key im Dashboard generieren
5. In `.env`: `EXA_API_KEY=...`

### 5. Apify API Key (Kostenlose Credits)

1. Besuchen Sie [Apify.com](https://apify.com/)
2. Registrieren Sie sich kostenlos
3. Sie erhalten $5 kostenlose Credits monatlich
4. Gehen Sie zu Settings → Integrations → API tokens
5. In `.env`: `APIFY_API_KEY=apify_api_...`

### 6. ScrapingBee API Key (1000 kostenlose Credits)

1. Gehen Sie zu [ScrapingBee.com](https://www.scrapingbee.com/)
2. Registrieren Sie sich für einen kostenlosen Account
3. Sie erhalten 1000 API Credits kostenlos
4. API Key im Dashboard kopieren
5. In `.env`: `SCRAPINGBEE_API_KEY=...`

### 7. Firecrawl API Key (Kostenlose Stufe)

1. Besuchen Sie [Firecrawl.dev](https://firecrawl.dev/)
2. Klicken Sie auf "Get Started Free"
3. Erstellen Sie einen Account
4. API Key im Dashboard generieren
5. In `.env`: `FIRECRAWL_API_KEY=fc-...`

### 8. BrightData API Key (Kostenpflichtig)

1. Gehen Sie zu [BrightData.com](https://brightdata.com/)
2. Kontaktieren Sie den Vertrieb für einen Account
3. Nach Aktivierung: Dashboard → API Access
4. In `.env`: `BRIGHTDATA_API_KEY=...`

## Empfohlene Minimalkonfiguration

Für einen kostenlosen Start empfehlen wir mindestens:

```env
# Kostenlose LLMs über OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Kostenlose Web-Suche
TAVILY_API_KEY=tvly-xxxxx
EXA_API_KEY=xxxxx

# Kostenlose Web-Scraping Credits
APIFY_API_KEY=apify_api_xxxxx
SCRAPINGBEE_API_KEY=xxxxx
```

## Wichtige Hinweise

1. **Sicherheit**: Teilen Sie niemals Ihre API-Keys öffentlich
2. **Kosten**: Überwachen Sie Ihre Nutzung bei kostenpflichtigen Services
3. **Rate Limits**: Beachten Sie die Limits der kostenlosen Stufen
4. **Backup**: Der Scraper-Agent funktioniert immer ohne API-Key

## Troubleshooting

- **"API Key invalid"**: Überprüfen Sie, ob der Key korrekt kopiert wurde
- **"Rate limit exceeded"**: Sie haben das kostenlose Limit erreicht
- **"Unauthorized"**: Der API Key hat möglicherweise nicht die nötigen Berechtigungen

### 9. DeepSeek API Key (Direkte Integration)

1. Besuchen Sie [platform.deepseek.com](https://platform.deepseek.com/)
2. Registrieren Sie sich für einen Account
3. Navigieren Sie zu API Keys
4. Generieren Sie einen neuen API Key
5. In `.env`: `DEEPSEEK_API_KEY=...`

**Hinweis**: DeepSeek ist bereits kostenlos über OpenRouter verfügbar! Die direkte API bietet erweiterte Funktionen.

### 10. Google Gemini API Key

1. Gehen Sie zu [console.cloud.google.com](https://console.cloud.google.com/)
2. Erstellen Sie ein neues Projekt oder wählen Sie ein bestehendes
3. Aktivieren Sie die Gemini API
4. Erstellen Sie Credentials → API Key
5. In `.env`: `GEMINI_API_KEY=...`

**Kostenlose Stufe**: $5 Credits monatlich

### 11. OpenAI API Key (für o1 Modelle)

1. Besuchen Sie [platform.openai.com](https://platform.openai.com/)
2. Registrieren Sie sich oder loggen Sie sich ein
3. Navigieren Sie zu API Keys
4. Erstellen Sie einen neuen Key
5. In `.env`: `OPENAI_API_KEY=sk-...`

**Hinweis**: o1 Modelle sind kostenpflichtig ($150/1M Input, $600/1M Output für o1-pro)

## Neue Research-Funktionen

### Deep Research APIs

Die folgenden APIs bieten spezialisierte Deep Research Funktionen:

1. **DeepSeek Research**
   - Reasoning-fokussierte Suche
   - Multi-Step Planning
   - Kostenlos über OpenRouter oder direkt

2. **Perplexity Deep Research**
   - Führt Dutzende Suchen automatisch durch
   - Liest Hunderte von Quellen
   - Pro-Subscription erforderlich

3. **Google Gemini Deep Research**
   - 1M Token Context Window
   - Asynchrone Task-Verwaltung
   - Multi-Step Research Planning

4. **OpenAI o1**
   - Advanced Chain-of-Thought Reasoning
   - Komplexe Problemlösung
   - Höchste Kosten, beste Reasoning-Performance

## Empfohlene Konfiguration für Research

### Basis Research Setup (Kostenlos)
```env
# Kostenlose LLMs mit Research-Fähigkeiten
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Für DeepSeek kostenlos

# Standard Web-Suche
TAVILY_API_KEY=tvly-xxxxx
EXA_API_KEY=xxxxx
```

### Advanced Research Setup
```env
# Research-spezialisierte APIs
DEEPSEEK_API_KEY=xxxxx           # Direkte DeepSeek Integration
PERPLEXITY_API_KEY=pplx-xxxxx    # Deep Research Mode
GEMINI_API_KEY=xxxxx              # Google Deep Research
OPENAI_API_KEY=sk-xxxxx           # o1 Reasoning

# Ergänzende Suche
TAVILY_API_KEY=tvly-xxxxx
EXA_API_KEY=xxxxx
```

## Support

Bei Problemen mit API-Keys:
1. Überprüfen Sie die Dokumentation des jeweiligen Anbieters
2. Stellen Sie sicher, dass die Keys in der `.env` Datei korrekt formatiert sind
3. Nutzen Sie `test_openrouter_config.py` zum Testen der OpenRouter-Verbindung
4. Für Research-APIs: Prüfen Sie ob Deep Research Features in Ihrem Plan enthalten sind