REFACTORING PLAN - Agent Files
===============================

Author: rahn
Datum: 22.06.2025
Version: 1.0

ÜBERSICHT
=========

Drei große Agent-Dateien müssen gemäß CLAUDE.md Regel 1 (max. 500 Zeilen) refaktoriert werden:

1. search_strategies.py (702 Zeilen)
2. brightdata_agent.py (701 Zeilen)  
3. premium_mining_research.py (694 Zeilen)

VERFÜGBARE BASE MODULE
======================

Folgende gemeinsame Module stehen zur Verfügung:
- cache_manager.py: Caching-Funktionalität
- http_client.py: HTTP Client mit Retry-Logic
- query_builder.py: Query-Building Funktionalität
- result_processor.py: Ergebnis-Verarbeitung

REFACTORING STRATEGIE
=====================

## 1. search_strategies.py

AKTUELL:
- Enthält SearchScope, SearchDepth Enums
- SearchStrategy Dataclass
- SearchStrategies Klasse mit vielen Methoden

AUFTEILUNG:
- search_strategies_core.py (< 200 Zeilen)
  - Enums und Dataclasses
  - Basis-Initialisierung
  
- search_strategies_executor.py (< 300 Zeilen)
  - Ausführungs-Logik
  - Parallel-Suche Koordination
  
- search_strategies_analyzer.py (< 200 Zeilen)
  - Analyse-Funktionen
  - Ergebnis-Bewertung

NUTZUNG BASE MODULE:
- QueryBuilder für Keyword-Generierung
- CacheManager für Strategy-Caching

## 2. brightdata_agent.py  

AKTUELL:
- Viel Duplikation mit anderen Scraping-Agenten
- Eigene HTTP-Logik
- Proxy-Management
- Scraping-Logik

AUFTEILUNG:
- brightdata_agent.py (< 250 Zeilen)
  - Basis Agent-Klasse
  - Initialisierung und Konfiguration
  
- brightdata_scraper.py (< 250 Zeilen)
  - Scraping-spezifische Logik
  - Proxy-Handling
  
- brightdata_parser.py (< 200 Zeilen)
  - HTML-Parsing
  - Daten-Extraktion

NUTZUNG BASE MODULE:
- BaseHTTPClient statt eigener HTTP-Implementierung
- ResultProcessor für Ergebnis-Verarbeitung
- CacheManager für Response-Caching

## 3. premium_mining_research.py

AKTUELL:
- Koordiniert mehrere andere Agenten
- Research-Phasen Management
- Viel orchestrierungs-Logik

AUFTEILUNG:
- premium_mining_research.py (< 200 Zeilen)
  - Basis-Klasse und Initialisierung
  - Research-Phasen Definition
  
- research_phase_executor.py (< 250 Zeilen)
  - Phasen-Ausführung
  - Agenten-Koordination
  
- research_result_aggregator.py (< 250 Zeilen)
  - Ergebnis-Aggregation
  - Scoring und Ranking

NUTZUNG BASE MODULE:
- ResultProcessor für einheitliche Ergebnis-Verarbeitung
- CacheManager für Zwischen-Ergebnisse
- QueryBuilder für dynamische Query-Generierung

GEMEINSAME VERBESSERUNGEN
=========================

1. REDUNDANZ ELIMINIEREN:
   - HTTP-Handling → BaseHTTPClient
   - Result-Erstellung → ResultProcessor
   - Query-Building → QueryBuilder
   - Caching → CacheManager

2. EINHEITLICHE PATTERNS:
   - Alle Agenten nutzen gleiche Base-Module
   - Konsistente Error-Handling
   - Einheitliches Logging

3. TESTBARKEIT:
   - Kleinere Module sind einfacher zu testen
   - Klare Trennung von Verantwortlichkeiten
   - Mocking wird einfacher

PRIORITÄT
=========

1. brightdata_agent.py (höchste Redundanz mit Base-Modulen)
2. search_strategies.py (zentrale Komponente)
3. premium_mining_research.py (abhängig von anderen)

NÄCHSTE SCHRITTE
================

1. BrightData Agent refaktorieren
2. Tests für neue Module schreiben
3. Schrittweise die anderen Dateien angehen
4. Dokumentation aktualisieren