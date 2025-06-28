# Source Discovery Verbesserungen für MineSearch V2

**Author:** rahn  
**Datum:** 28.06.2025  
**Version:** 1.0

## 🎯 Zusammenfassung

Implementierung von umfangreichen Verbesserungen für die Quellensuche in MineSearch Version 2, um mehr und bessere Ergebnisse zu erzielen.

## ✅ Implementierte Verbesserungen

### 1. **Prompt-Optimierung** ✓
- Erweiterte System-Prompts mit expliziter Aufforderung zur Quellensammlung
- Spezifische Anfrage nach:
  - Offiziellen Betreiber-Websites
  - Regierungsdatenbanken (SEDAR, EDGAR, InfoMine)
  - Mining-Fachportalen
  - Umweltberichten und NI 43-101 Reports
  - Jahresberichten und akademischen Studien
- User-Prompts erweitert um explizite Quellenanfragen

### 2. **Verbesserte Quellenextraktion** ✓
Neue Funktion `extract_sources_from_content()` mit:
- **URL-Extraktion**: Erkennt alle URLs im Content
- **Dokument-Referenzen**: 
  - NI 43-101 Technical Reports
  - Annual Reports
  - Environmental Impact Assessments
  - SEDAR Filings
- **Organisations-Erkennung**: 
  - Mining-Portale
  - Regierungsbehörden
  - Datenbanken
- **Kontext-Extraktion**: Speichert Umgebungstext für jede Quelle

### 3. **Zwei-Phasen-Suche** ✓
Neuer Endpoint `/api/enhanced-search`:
- **Phase 1**: Basis-Suche mit Fokus auf Quellensammlung
- **Phase 2**: Vertiefende Suche für Top-Quellen
  - Priorisierung von offiziellen Dokumenten
  - Gezielte Nachfragen zu gefundenen Quellen
  - Kombination aller Ergebnisse
- **Intelligente Priorisierung**:
  - Regierungsseiten (.gov, .gc.ca)
  - Offizielle Reports (NI 43-101)
  - Mining-Fachportale

### 4. **UI-Verbesserungen** ✓
- Neuer Such-Modus-Selector (Standard vs. Erweitert)
- Anzeige gefundener Quellen mit:
  - URLs als klickbare Links
  - Gruppierung nach Typ
  - Anzahl der gefundenen Quellen
- Dynamische Form-Action basierend auf Such-Modus

## 📊 Technische Details

### Datenstruktur für Quellen
```python
{
    'type': 'url' | 'document' | 'organization',
    'value': 'Die URL oder Bezeichnung',
    'context': 'Umgebungstext für Kontext'
}
```

### API Response erweitert um:
```python
{
    'sources': [...],  # Liste aller extrahierten Quellen
    'source_summary': {
        'urls': count,
        'documents': count,
        'organizations': count,
        'total': count
    }
}
```

## 🚀 Nutzung

### Standard-Suche (wie bisher):
1. Mine eingeben
2. "Standard-Suche" wählen
3. Schnelle Ergebnisse in 30-60 Sekunden

### Erweiterte 2-Phasen-Suche:
1. Mine eingeben
2. "Erweiterte 2-Phasen-Suche" wählen
3. Wartezeit: 1-2 Minuten
4. Ergebnis: Deutlich mehr Quellen und tiefere Informationen

## 📈 Erwartete Verbesserungen

- **3-5x mehr Quellen** pro Suche
- **Bessere Datenqualität** durch gezielte Nachfragen
- **Höhere Trefferquote** bei Umweltkosten
- **Validierte Quellen** mit Kontext

## 🔄 Nächste Schritte

### Kurzfristig (bereits vorbereitet):
- [ ] Datenbank-Integration für Quellenspeicherung
- [ ] Caching von gefundenen Quellen
- [ ] Batch-Verarbeitung mit erweiterter Suche

### Mittelfristig:
- [ ] Multi-Stage Recherche (3+ Phasen)
- [ ] Automatische Dokumenten-Downloads
- [ ] PDF-Extraktion für gefundene Reports

## 🧪 Test-Empfehlungen

1. **Test mit bekannten Minen**:
   - Canadian Malartic (viele öffentliche Daten)
   - Grasberg (internationale Bekanntheit)
   - Cerro Verde (gute Dokumentation)

2. **Vergleich Standard vs. Erweitert**:
   - Anzahl gefundener Quellen
   - Qualität der Restaurationskosten-Daten
   - Vollständigkeit der Informationen

## ⚠️ Hinweise

- Die erweiterte Suche nutzt mehr API-Calls (1 + bis zu 3 zusätzliche)
- Timeout für Phase 2 ist auf 30 Sekunden pro Quelle gesetzt
- Maximal 3 vertiefte Suchen um Kosten zu kontrollieren