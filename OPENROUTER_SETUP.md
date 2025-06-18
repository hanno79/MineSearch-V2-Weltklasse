# OpenRouter Setup für MineSearch

## Problem
Die OpenRouter Modelle werden nicht in der Oberfläche angezeigt, weil der API Key noch nicht konfiguriert ist.

## Lösung

1. **OpenRouter API Key erhalten:**
   - Gehen Sie zu https://openrouter.ai/
   - Registrieren Sie sich oder melden Sie sich an
   - Gehen Sie zu "API Keys" oder "Settings"
   - Erstellen Sie einen neuen API Key

2. **API Key in MineSearch konfigurieren:**
   - Öffnen Sie die Datei `/app/.env`
   - Ersetzen Sie `your-openrouter-api-key-here` mit Ihrem echten API Key:
     ```
     OPENROUTER_API_KEY=sk-or-v1-xxxxx...
     ```

3. **Anwendung neu starten:**
   - Stoppen Sie die laufende Anwendung (Ctrl+C)
   - Starten Sie sie neu mit: `python run.py`

## Verfügbare Modelle nach der Konfiguration

### Kostenlose Modelle (🆓):
- DeepSeek Chat (Empfohlen)
- Qwen 2.5 72B 
- Mistral 7B Instruct
- Llama 3.2 90B
- Gemma 2 27B
- Hermes 3 Llama 70B
- Gemini 2.0 Flash (1M Context)
- Gemini 2.0 Thinking

### Premium Modelle (💎):
- Claude 3.5 Sonnet (Neueste Version)
- Claude 3 Opus (Leistungsstärkste)
- Gemini 1.5 Pro (2M Context!)
- Grok 2 (Mit Echtzeit-Suche)
- GPT-4o (Neueste Version)
- OpenAI o1 (Advanced Reasoning)
- Llama 3.1 405B

## Wichtige Hinweise
- Premium-Modelle verursachen Kosten pro Nutzung
- Kostenlose Modelle haben möglicherweise Rate Limits
- DeepSeek Chat bietet das beste Preis-Leistungs-Verhältnis im Free Tier