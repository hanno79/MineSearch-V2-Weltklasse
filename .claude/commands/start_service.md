---
description: Startet oder startet das MineSearch v2.1 System neu - Single-Port FastAPI Service
allowed-tools: Task, Bash, Read, Write, Edit
---

# MineSearch v2.1 Service Management

Dieses Kommando verwaltet den Start und Neustart des MineSearch v2.1 Systems mit intelligenter Service-Erkennung.

## Funktionalität

- **Automatische Erkennung**: Prüft ob Service bereits läuft
- **Smart Restart**: Startet Service neu wenn bereits aktiv
- **Clean Start**: Startet Service sauber wenn nicht aktiv
- **Health Check**: Überprüft Service-Status nach Start
- **Port Management**: Verwaltet den einzigen Service-Port 8000

## System-Architektur

**Einzelner Service**: FastAPI-Anwendung auf Port 8000
- **API-Endpoints**: Alle Such- und Verwaltungs-APIs
- **Frontend-Integration**: Statische Dateien über FastAPI StaticFiles
  - `/static` → Frontend-Dateien (HTML, CSS, JS)
  - `/csv` → CSV-Export-Dateien
- **Datenbank**: SQLite-basierte Persistierung
- **Provider Registry**: Alle konfigurierten AI-Provider (33+ Modelle)

## Service-Erkennung

Das System erkennt automatisch:
- Laufende uvicorn/FastAPI Prozesse
- Belegten Port 8000
- Process IDs für sauberes Beenden
- Service-Health-Status über /health endpoint

## Verwendung

```bash
# Startet Service (oder Restart falls bereits aktiv)
/start_service

# Zusätzliche Optionen:
/start_service --force-restart  # Erzwingt kompletten Neustart
```

## Systemvoraussetzungen

- Python 3.8+ mit FastAPI, uvicorn
- Alle Dependencies aus requirements.txt installiert
- Gültige API-Keys in Umgebungsvariablen (.env)
- SQLite-Datenbank (wird automatisch erstellt)

## Logs und Monitoring

- Service-Logs werden in `logs/` gespeichert
- Health-Check URL: http://localhost:8000/health
- Frontend-Zugriff: http://localhost:8000/static/index.html
- Process-Tracking für automatisches Management

## Fehlerbehandlung

- Automatisches Cleanup bei fehlgeschlagenen Starts
- Port-Konflikt-Erkennung und -Auflösung
- Retry-Mechanismus für instabile Services
- Detaillierte Fehlermeldungen und Lösungsvorschläge
- API-Key Validation beim Start