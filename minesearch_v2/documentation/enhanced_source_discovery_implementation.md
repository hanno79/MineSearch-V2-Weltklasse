"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Dokumentation der Enhanced Source Discovery Implementation
"""

# Enhanced Source Discovery Implementation

## Übersicht

Die Enhanced Source Discovery wurde implementiert, um mehr Quellen zu finden und transparenter darzustellen, welche Quellen durchsucht wurden - auch wenn sie keine Ergebnisse lieferten.

## Implementierte Komponenten

### 1. Source Registry (models.py)
- **SourceRecord**: Speichert Informationen über einzelne Quellen
  - URL, Domain, Land, Region
  - Zuverlässigkeitsscore (0-100%)
  - Erfolgsstatistiken
  - Content-Typen
- **SearchSession**: Tracking einer kompletten Suchsession
  - Entdeckte vs. durchsuchte vs. erfolgreiche Quellen
  - Zeiterfassung
  - Detaillierte Statistiken
- **SourceRegistry**: In-Memory Registry für Quellenverwaltung

### 2. Enhanced Source Discovery (enhanced_source_discovery.py)
- **Active Discovery Phase**: Quellen werden VOR der Perplexity-Suche entdeckt
- **Quellentypen**:
  - Länderspezifische Priority Domains
  - Globale Mining-Datenbanken (Tier 1)
  - Börsen und Finanzdokumente (Tier 2)
  - Technische Dokumente (PDFs)
  - Bewährte Quellen aus Registry
- **Spezialbehandlung für Quebec/GESTIM**
- **Intelligente Quellenauswahl** basierend auf Land, Region und Rohstoff

### 3. Search Service Integration (search_service.py)
- Integration der Enhanced Source Discovery
- Pre-Discovery von Quellen vor API-Call
- Tracking aller durchsuchten Quellen
- Enhanced Prompts mit spezifischen Quellenhinweisen
- Session-basiertes Tracking mit Finalisierung

### 4. UI-Erweiterungen (html_utils.py)

#### Einzelergebnisse (create_result_card)
- Neuer "Source Discovery Tab" mit:
  - Statistik-Karten: Entdeckt, Durchsucht, Erfolgreich, Erfolgsquote
  - Expandierbare Listen erfolgreicher Quellen
  - Expandierbare Listen erfolgloser Quellen
  - Suchdauer-Anzeige

#### Batch-Ergebnisse (create_batch_results_table)
- Source Discovery Zusammenfassung mit:
  - Gesamtstatistiken über alle Minen
  - Durchschnittliche Erfolgsquote
  - Gesamtdauer der Suche

## Vorteile der Implementierung

1. **Transparenz**: Nutzer sehen ALLE durchsuchten Quellen, nicht nur die erfolgreichen
2. **Intelligenz**: Das System lernt, welche Quellen zuverlässig sind
3. **Effizienz**: Bewährte Quellen werden priorisiert
4. **Nachvollziehbarkeit**: Jede Quelle wird mit Erfolgsstatistiken getrackt
5. **Performance**: Pre-Discovery hilft Perplexity, gezielter zu suchen

## Nutzung

Die Enhanced Source Discovery läuft automatisch bei jeder Suche:
1. Session wird gestartet
2. Quellen werden aktiv entdeckt (basierend auf Mine, Land, Region)
3. Perplexity erhält Enhanced Prompt mit Quellenhinweisen
4. Alle Quellenzugriffe werden getrackt
5. UI zeigt detaillierte Quellenstatistiken

## Nächste Schritte

1. **GESTIM-Integration**: Spezielle Suche für Quebec-Minen
2. **Testing**: Umfassende Tests der erweiterten Suche
3. **Persistenz**: Source Registry in Datenbank speichern
4. **Optimierung**: Quellenauswahl basierend auf historischen Daten