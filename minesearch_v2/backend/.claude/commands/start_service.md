---
description: Startet oder startet das MineSearch v2 System neu - intelligente Service-Erkennung
allowed-tools: Task, Bash, Read, Write, Edit
---

# MineSearch v2 Service Management

Dieses Kommando verwaltet den Start und Neustart des kompletten MineSearch v2 Systems mit intelligenter Service-Erkennung.

## Funktionalität

- **Automatische Erkennung**: Prüft ob Services bereits laufen
- **Smart Restart**: Startet Services neu wenn bereits aktiv
- **Clean Start**: Startet alle Services sauber wenn nicht aktiv
- **Health Check**: Überprüft Service-Status nach Start
- **Port Management**: Verwaltet Frontend (8080) und Backend (8000) Ports

## Unterstützte Services

1. **Backend API**: FastAPI Service auf Port 8000
2. **Frontend**: Statischer Server auf Port 8080
3. **Datenbank**: SQLite-basierte Persistierung
4. **Provider Registry**: Alle konfigurierten AI-Provider

## Service-Erkennung

Das System erkennt automatisch:
- Laufende uvicorn/gunicorn Prozesse
- Belegte Ports (8000, 8080)
- Process IDs für sauberes Beenden
- Service-Health-Status

## Verwendung

```bash
# Startet alle Services (oder Restart falls bereits aktiv)
/start_service

# Zusätzliche Optionen über Argumente:
/start_service --force-restart  # Erzwingt kompletten Neustart
/start_service --backend-only   # Nur Backend starten
/start_service --frontend-only  # Nur Frontend starten
```

## Systemvoraussetzungen

- Python 3.8+ mit FastAPI, uvicorn
- Node.js für Frontend-Serving (optional)
- Alle Dependencies aus requirements.txt installiert
- Gültige API-Keys in Umgebungsvariablen

## Logs und Monitoring

- Service-Logs werden in `logs/` gespeichert
- Health-Check URLs: http://localhost:8000/health, http://localhost:8080
- Process-Tracking für automatisches Management

## Fehlerbehandlung

- Automatisches Cleanup bei fehlgeschlagenen Starts
- Port-Konflikt-Erkennung und -Auflösung
- Retry-Mechanismus für instabile Services
- Detaillierte Fehlermeldungen und Lösungsvorschläge