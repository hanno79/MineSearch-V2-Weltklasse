---
description: Systematische Code-Bereinigung der MineSearch v2 Codebase - entfernt Duplikate, veraltete Dateien und reorganisiert die Struktur
allowed-tools: Task, Bash, Read, Write, Edit, Glob, Grep, LS, TodoWrite
---

# MineSearch v2 Code-Bereinigung

Dieses Kommando führt eine umfassende Bereinigung der MineSearch v2 Codebase durch.

## Funktionalität

- **Duplikate entfernen**: Identifiziert und entfernt doppelte/redundante Dateien
- **Veraltete Dateien bereinigen**: Entfernt alte Test-Ergebnisse, Log-Dateien und Backup-Dateien
- **Parallele Systeme konsolidieren**: Behebt konkurrierende Implementierungen
- **Ordnerstruktur optimieren**: Reorganisiert Dateien in logische Verzeichnisse
- **Import-Abhängigkeiten validieren**: Stellt sicher, dass keine funktionalen Breaks entstehen
- **to_delete Management**: Verschiebt veraltete Dateien sicher zur späteren Löschung

## Bereinigungsbereiche

1. **Python Cache**: `__pycache__` Verzeichnisse und `.pyc` Dateien
2. **Test-Artefakte**: JSON Test-Ergebnisse, veraltete Logs
3. **Service-Duplikate**: Redundante `search_service_*.py` Dateien
4. **Datenbank-Duplikate**: Mehrfache `mines.db` Dateien
5. **Dokumentations-Redundanz**: Doppelte MD-Dateien und Verbesserungsvorschläge
6. **Backup-Dateien**: Veraltete HTML/JSON Backup-Dateien

## Sicherheitsmaßnahmen

- Import-Abhängigkeiten werden vor Löschung validiert
- Kritische Produktionsdateien werden nie gelöscht
- Backup-Strategie für Datenbank-Operationen
- Schrittweise Bereinigung mit Validierung zwischen den Phasen

## Erwartete Ergebnisse

- **~120+ Dateien** werden bereinigt/reorganisiert
- **~200MB Speicherplatz** wird freigesetzt
- **Verbesserte Codebase-Übersichtlichkeit**
- **Reduzierte Maintenance-Komplexität**