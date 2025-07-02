# MineSearch V2 Verbesserungen - 29.06.2025

## ✅ Implementierte Optimierungen

### Phase 1: Quick Wins (Abgeschlossen)

#### 1. **Erweiterte Suchbegriffe** (config.py)
- **Mining-spezifische Terminologie** für Restaurationskosten in 5 Sprachen
  - Englisch: restoration costs, closure costs, ARO, environmental liability
  - Französisch: coûts de restauration, passif environnemental
  - Spanisch: costos de cierre, pasivos ambientales
  - Indonesisch: biaya reklamasi, kewajiban lingkungan
  - Portugiesisch: custos de fechamento (vorbereitet)

- **Technische Abkürzungen** hinzugefügt:
  - Reports: NI 43-101, JORC, SAMREC, PERC
  - Studien: PEA, PFS, DFS, Feasibility Study
  - Ressourcen: Measured, Indicated, Inferred, P&P
  - Rohstoff-Symbole: Au, Ag, Cu, Pb, Zn, Ni, Co, Li

- **Priorisierte Domains** in 3 Stufen:
  - Tier 1: GESTIM, MERN, NRCAN, BLM, USGS, SARIG
  - Tier 2: SEDAR, SEC, ASX, TSX, JSE
  - Tier 3: mining.com, mining-technology.com

#### 2. **Verbesserte Namenvarianten** (main.py)
- **Erweiterte Präfixe**: Mine, Project, Property, Deposit, Operation
- **Phonetische Ähnlichkeiten**: ck/k, ph/f, v/w, s/z, c/k, x/ks
- **Schreibvarianten**: Groß/Klein, mit/ohne Bindestriche
- **Klammer-Inhalte**: Extrahiert und als separate Varianten
- Beispiel: "Cerro Verde" → 20+ Varianten generiert

#### 3. **Domain-Priorisierung** (main.py)
- PDF-Suchmuster für technische Dokumente
- Intelligente Quellenpriorisierung in Phase 2
- Spezielle GESTIM-Behandlung für Quebec-Minen

### Phase 2: 2-Phasen-Suche Optimierung (Abgeschlossen)

#### 1. **Erweiterte Quellenpriorisierung**
- Bis zu 3 offizielle Dokumente (NI 43-101, JORC, etc.)
- GESTIM hat höchste Priorität für Quebec
- Regierungsseiten vor kommerziellen Portalen
- PDF-Dokumente als Fallback

#### 2. **Domain-spezifische Suchanfragen**
Angepasste Queries für verschiedene Quellen:

- **NI 43-101 Reports**: Fokus auf Closure Costs Sections
- **Annual Reports**: Suche nach ARO in Financial Notes
- **GESTIM**: Claim-Nummern und technische Reports
- **SEDAR**: AIF und Financial Statements
- **Regierungsseiten**: Umweltgenehmigungen und Bonds

### Technische Details

#### Geänderte Dateien:
1. **config.py**:
   - +40 Zeilen für restoration_costs Begriffe
   - +20 Zeilen für MINING_ABBREVIATIONS
   - +15 Zeilen für PRIORITY_MINING_DOMAINS
   - +10 Zeilen für PDF_SEARCH_PATTERNS

2. **main.py**:
   - `generate_name_variants()`: Von 35 auf 85 Zeilen erweitert
   - Phase 1 Suche: Erweiterte Suchbegriffe integriert
   - Phase 2 Suche: Domain-spezifische Queries (60+ Zeilen)
   - Quellenpriorisierung: Komplett überarbeitet

#### Performance-Verbesserungen:
- Mehr Namenvarianten = höhere Trefferquote
- Priorisierte Domains = relevantere Quellen
- Spezifische Queries = bessere Datenextraktion
- Mehrsprachige Begriffe = internationale Abdeckung

### Erwartete Ergebnisse:

1. **3-5x mehr Quellen** durch erweiterte Suchbegriffe
2. **Höhere Datenqualität** durch gezielte Dokumentsuche
3. **Bessere Restaurationskosten-Erfassung** durch spezifische Begriffe
4. **GESTIM-Integration** für Quebec-Minen
5. **Internationale Abdeckung** durch mehrsprachige Unterstützung

### Nutzung:

```bash
# Server starten
cd minesearch_v2/backend
python main.py

# Browser öffnen
http://localhost:8000

# Für beste Ergebnisse:
- Wählen Sie "Erweiterte 2-Phasen-Suche"
- Geben Sie Land an für optimale Sprachunterstützung
- Bei Quebec-Minen: GESTIM wird automatisch priorisiert
```

### Nächste Schritte (Phase 3):

- [ ] Neue Datenfelder (Umweltgenehmigungen, Bonds, Timeline)
- [ ] Verbesserte Quellenreferenzierung
- [ ] API-Integration für GESTIM
- [ ] Caching-Mechanismus

Die Implementierung ist vollständig rückwärtskompatibel und erhält die Einfachheit von Version 2!