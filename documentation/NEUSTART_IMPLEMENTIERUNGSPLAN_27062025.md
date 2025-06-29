# 🚀 NEUSTART - Radikaler Implementierungsplan für MineSearch 2.0

**Datum: 27.06.2025**  
**Autor: rahn**  
**Version: 1.0**

## 🎯 Executive Summary

**Problem**: 229 Dateien, 33+ Agenten, endlose Event Loop Probleme für eine simple Mining-Suchmaschine.

**Lösung**: Kompletter Neustart mit **maximal 20 Dateien** und fokus auf **einen funktionierenden Perplexity Agent**.

## 📋 Der neue Tech-Stack

### Backend: **FastAPI** (Nicht Streamlit!)
```
✅ Native Async Support
✅ Keine Event Loop Konflikte  
✅ RESTful API für klare Trennung
✅ Automatische API Dokumentation
```

### Frontend: **Vanilla HTML + HTMX**
```
✅ Kein React/Vue/Angular Overhead
✅ Server-Side Rendering
✅ 10KB statt 500KB
✅ Keine Build-Pipeline
```

### Datenbank: **SQLite** → **PostgreSQL**
```
✅ Start mit SQLite (Zero Config)
✅ Migration zu PostgreSQL wenn stabil
✅ Keine ORM - Raw SQL für Kontrolle
```

### Deployment: **Direkt auf Linux** (Kein Docker!)
```
✅ Python venv statt Container
✅ systemd für Service Management
✅ nginx als Reverse Proxy
✅ Keine Docker-Layer-Probleme
```

## 🏗️ Die neue Architektur (RADIKAL EINFACH)

```
minesearch_v2/
├── backend/
│   ├── main.py              # FastAPI App (200 Zeilen)
│   ├── perplexity_client.py # Perplexity API Client (100 Zeilen)
│   ├── models.py            # Datenmodelle (50 Zeilen)
│   ├── database.py          # DB Verbindung (50 Zeilen)
│   └── config.py            # Konfiguration (30 Zeilen)
├── frontend/
│   ├── index.html           # Hauptseite mit HTMX
│   ├── results.html         # Ergebnisseite
│   └── style.css            # Minimal CSS
├── scripts/
│   ├── setup.sh             # Installation
│   └── deploy.sh            # Deployment
├── tests/
│   └── test_perplexity.py   # Nur kritische Tests
├── .env.example
├── requirements.txt         # Max 10 Dependencies!
└── README.md
```

**Gesamtziel: < 1000 Zeilen Code!**

## 🔥 Implementierungsschritte

### Phase 1: Perplexity MVP (Tag 1-2)

#### 1. FastAPI Backend Setup
```python
# main.py - Komplette App in einer Datei!
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="MineSearch 2.0")

class SearchRequest(BaseModel):
    mine_name: str
    country: str = None

@app.post("/search")
async def search_mine(request: SearchRequest):
    """Ein einziger Endpoint für alles!"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('PERPLEXITY_KEY')}"},
            json={
                "model": "sonar-medium-online",
                "messages": [{
                    "role": "user",
                    "content": f"Find information about {request.mine_name} mine"
                }]
            }
        )
    return response.json()
```

#### 2. HTML Frontend (Ohne Build Process!)
```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body>
    <h1>MineSearch 2.0</h1>
    <form hx-post="/search" hx-target="#results">
        <input name="mine_name" placeholder="Mine Name" required>
        <button type="submit">Search</button>
    </form>
    <div id="results"></div>
</body>
</html>
```

### Phase 2: Datenbank Integration (Tag 3)

```python
# database.py - Simple SQLite
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('mines.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def save_mine_data(data):
    with get_db() as db:
        db.execute("""
            INSERT INTO mines (name, operator, latitude, longitude, commodity)
            VALUES (?, ?, ?, ?, ?)
        """, (data['name'], data['operator'], data['lat'], data['lon'], data['commodity']))
        db.commit()
```

### Phase 3: Stabilisierung (Tag 4-5)

- Error Handling mit Retry
- Logging (strukturiert, auf Deutsch)
- Rate Limiting
- Basic Tests

## 🚫 Was wir NICHT machen

1. **Keine 33 Agenten** - Nur Perplexity für den Start
2. **Kein Docker** - Direkte Installation mit venv
3. **Kein komplexes Session Management** - httpx handles alles
4. **Keine Abstraktionen** - Direkter Code ohne 10 Vererbungsebenen
5. **Kein Redux/Vuex/Context** - Server State only
6. **Keine Microservices** - Monolith bis 10k User
7. **Kein Kubernetes** - systemd reicht völlig

## 📊 Metriken für Erfolg

- **Codezeilen**: < 1000 (aktuell 20.000+)
- **Dateien**: < 20 (aktuell 229)
- **Dependencies**: < 10 (aktuell 50+)
- **Startup Zeit**: < 1 Sekunde
- **Memory Usage**: < 100MB
- **Keine Timeout Errors**
- **Keine Event Loop Probleme**

## 🎯 Konkrete Vorteile

1. **Wartbarkeit**: Ein Junior Dev kann alles in 1 Tag verstehen
2. **Performance**: 10x schneller ohne Overhead
3. **Stabilität**: Weniger bewegliche Teile = weniger Fehler
4. **Deployment**: 5 Minuten statt 5 Stunden
5. **Debugging**: Stack Traces die Sinn machen

## 💡 Philosophie-Änderung

### Alt (Enterprise-Denken):
"Was wenn wir mal 1000 verschiedene Agenten brauchen?"

### Neu (Pragmatisch):
"Wir brauchen 1 Agent der funktioniert. Punkt."

## 🔧 Migration vom alten System

1. **Datenbank Export**: Nur die Kerndaten (mines Tabelle)
2. **Perplexity API Key**: Übernehmen
3. **Alles andere**: Wegwerfen und neu denken

## ⚡ Quick Wins

- **Tag 1**: Funktionierender Perplexity Search
- **Tag 2**: Ergebnisse in DB speichern
- **Tag 3**: Basis UI fertig
- **Tag 4**: Deployment auf Server
- **Tag 5**: Erste User Tests

## 🎯 Langfristige Vision (Optional)

**Erst wenn Phase 1-3 stabil laufen:**

- Tavily Agent hinzufügen (nur wenn nötig)
- Export Funktionen
- Advanced Search
- User Accounts (nur wenn gefordert)

**Aber**: Jedes Feature muss sich rechtfertigen!

## ✅ Checkliste für Neustart

- [ ] Neues Verzeichnis `minesearch_v2` erstellen
- [ ] FastAPI + httpx + SQLite installieren
- [ ] Perplexity API Key in .env
- [ ] main.py mit einem Endpoint
- [ ] index.html mit HTMX
- [ ] Erster erfolgreicher API Call
- [ ] Ergebnis in DB speichern
- [ ] Deployment Skript
- [ ] FERTIG! (Ja, so einfach)

## 🚀 Zusammenfassung

**Von**: 229 Dateien, 33 Agenten, Event Loop Hölle  
**Zu**: 20 Dateien, 1 Agent, Funktionierende Software

**Das ist kein Rückschritt - das ist Fortschritt durch Reduktion!**

---

*"Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away." - Antoine de Saint-Exupéry*