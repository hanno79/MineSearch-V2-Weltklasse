# MineSearch V2 - Konkrete Verbesserungsvorschläge
Datum: 29.06.2025
Author: Claude

## 1. SUCHBEGRIFF-ERWEITERUNGEN

### A. Mining-spezifische Begriffe ergänzen

**Aktuell in config.py definiert:**
```python
'mining_terms': {
    'mine': ['mine', 'site minier', 'tambang', 'mina'],
    'operator': ['operator', 'opérateur', 'exploitant', 'PT', 'operador'],
    'commodity': ['commodity', 'produit', 'minerai', 'komoditas', 'mineral']
}
```

**Erweiterungsvorschlag:**
```python
MINING_SEARCH_TERMS = {
    # Grundbegriffe
    'mine': ['mine', 'site minier', 'tambang', 'mina', 'faena minera', 'bergwerk', 
             'grube', 'tagebau', 'untertagebergwerk', 'quarry', 'cantera'],
    
    # Betreiber-Varianten
    'operator': ['operator', 'opérateur', 'exploitant', 'PT', 'operador', 'empresa minera',
                'compañía minera', 'mining company', 'bergbauunternehmen', 'owner',
                'subsidiary', 'joint venture', 'JV', 'partnership'],
    
    # Rohstoff-Begriffe
    'commodity': ['commodity', 'produit', 'minerai', 'komoditas', 'mineral', 'metal',
                 'ore', 'resource', 'reserve', 'deposit', 'vorkommen', 'yacimiento'],
    
    # Restaurationskosten-Begriffe (KRITISCH!)
    'restoration': ['restoration cost', 'closure cost', 'reclamation cost', 'rehabilitation cost',
                   'decommissioning cost', 'environmental bond', 'financial assurance',
                   'surety bond', 'closure bond', 'ARO', 'asset retirement obligation',
                   'coût de restauration', 'coût de fermeture', 'garantie financière',
                   'provisión para cierre', 'fianza de cierre', 'garantía ambiental'],
    
    # Umwelt-Begriffe
    'environmental': ['environmental impact', 'EIA', 'ESIA', 'environmental assessment',
                     'impact assessment', 'umweltverträglichkeit', 'estudio de impacto',
                     'étude d\'impact', 'AMDAL', 'environmental management plan', 'EMP'],
    
    # Dokument-Typen
    'documents': ['NI 43-101', 'JORC', 'SAMREC', 'technical report', 'feasibility study',
                 'PEA', 'preliminary economic assessment', 'DFS', 'definitive feasibility',
                 'annual report', 'quarterly report', 'MD&A', 'AIF', 'annual information form',
                 '10-K', '10-Q', '8-K', 'SEDAR filing', 'EDGAR filing', 'ASX announcement']
}
```

### B. Sprachvarianten für verschiedene Regionen

**Erweiterung der Länderkonfiguration:**
```python
LANGUAGE_VARIANTS = {
    'südafrika': {
        'languages': ['en', 'af', 'zu'],
        'terms': {
            'mine': ['mine', 'myn', 'mgodi'],
            'restoration': ['rehabilitation', 'rehabilitasie', 'ukuvuselela']
        }
    },
    'brasilien': {
        'languages': ['pt', 'en'],
        'terms': {
            'mine': ['mina', 'lavra', 'garimpo'],
            'operator': ['mineradora', 'empresa de mineração'],
            'restoration': ['recuperação ambiental', 'reabilitação', 'fechamento de mina']
        }
    },
    'russland': {
        'languages': ['ru', 'en'],
        'terms': {
            'mine': ['рудник', 'шахта', 'карьер', 'mine'],
            'restoration': ['рекультивация', 'восстановление', 'ликвидация']
        }
    },
    'china': {
        'languages': ['zh', 'en'],
        'terms': {
            'mine': ['矿山', '矿井', '采矿场', 'mine'],
            'restoration': ['矿山修复', '生态恢复', '闭坑费用']
        }
    }
}
```

### C. Branchenspezifische Abkürzungen

```python
MINING_ACRONYMS = {
    # Technische Berichte
    'NI43-101': ['NI 43-101', 'National Instrument 43-101', '43-101 report'],
    'JORC': ['JORC', 'JORC Code', 'Joint Ore Reserves Committee'],
    'SAMREC': ['SAMREC', 'South African Mineral Resource Committee'],
    
    # Umwelt & Restauration
    'ARO': ['ARO', 'Asset Retirement Obligation', 'Stilllegungsverpflichtung'],
    'EIA': ['EIA', 'Environmental Impact Assessment', 'Umweltverträglichkeitsprüfung'],
    'ESIA': ['ESIA', 'Environmental and Social Impact Assessment'],
    'EMP': ['EMP', 'Environmental Management Plan'],
    'ESMP': ['ESMP', 'Environmental and Social Management Plan'],
    
    # Bergbautypen
    'OP': ['OP', 'open pit', 'open-pit', 'tagebau'],
    'UG': ['UG', 'underground', 'untertage', 'souterrain'],
    'ISL': ['ISL', 'in-situ leaching', 'solution mining'],
    
    # Projektphasen
    'PEA': ['PEA', 'Preliminary Economic Assessment'],
    'PFS': ['PFS', 'Pre-Feasibility Study'],
    'DFS': ['DFS', 'Definitive Feasibility Study', 'bankable feasibility'],
    
    # Rohstoffe (Periodensystem)
    'Au': ['Au', 'gold', 'oro', 'or', 'Gold'],
    'Cu': ['Cu', 'copper', 'cobre', 'cuivre', 'Kupfer'],
    'Ni': ['Ni', 'nickel', 'níquel'],
    'Zn': ['Zn', 'zinc', 'cinc'],
    'Pb': ['Pb', 'lead', 'plomo', 'plomb', 'Blei']
}
```

## 2. NAMENVARIANTEN-VERBESSERUNG

### A. Automatische Varianten-Generierung

```python
def generate_mine_name_variants(mine_name: str) -> List[str]:
    """Generiere verschiedene Schreibweisen eines Minennamens"""
    variants = [mine_name]
    
    # 1. Groß-/Kleinschreibung
    variants.extend([
        mine_name.upper(),
        mine_name.lower(),
        mine_name.title()
    ])
    
    # 2. Mit/ohne "Mine" Suffix
    if not any(suffix in mine_name.lower() for suffix in ['mine', 'mina', 'project']):
        variants.extend([
            f"{mine_name} Mine",
            f"{mine_name} Project",
            f"{mine_name} Mina",
            f"{mine_name} Operation"
        ])
    
    # 3. Sonderzeichen-Varianten
    # Bindestriche vs. Leerzeichen
    if '-' in mine_name:
        variants.append(mine_name.replace('-', ' '))
    elif ' ' in mine_name:
        variants.append(mine_name.replace(' ', '-'))
    
    # 4. Phonetische Varianten für häufige Schreibfehler
    phonetic_replacements = {
        'ck': 'k', 'k': 'ck',
        'ph': 'f', 'f': 'ph',
        'v': 'w', 'w': 'v',
        'y': 'i', 'i': 'y',
        'z': 's', 's': 'z'
    }
    
    # 5. Lokale Schreibweisen
    if country:
        variants.extend(get_localized_variants(mine_name, country))
    
    # 6. Historische Namen (aus Datenbank)
    # variants.extend(get_historical_names(mine_name))
    
    # 7. Abkürzungen
    words = mine_name.split()
    if len(words) > 1:
        # Akronym
        acronym = ''.join(w[0].upper() for w in words)
        variants.append(acronym)
    
    return list(set(variants))  # Duplikate entfernen
```

### B. Lokalisierte Varianten

```python
LOCALIZED_NAME_PATTERNS = {
    'kanada_französisch': {
        'lake': 'lac',
        'river': 'rivière',
        'mountain': 'mont',
        'north': 'nord',
        'south': 'sud',
        'east': 'est',
        'west': 'ouest'
    },
    'spanisch': {
        'lake': 'lago',
        'river': 'río',
        'mountain': 'cerro',
        'hill': 'loma',
        'valley': 'valle',
        'saint': 'san/santa'
    },
    'portugiesisch': {
        'lake': 'lago',
        'river': 'rio',
        'mountain': 'serra',
        'mine': 'mina',
        'project': 'projeto'
    }
}
```

## 3. QUELLENINTEGRATION

### A. Priorisierte Domains für Mining-Daten

```python
PRIORITY_MINING_SOURCES = {
    'tier_1_official': [
        # Kanadische Behörden
        'gestim.mines.gouv.qc.ca',
        'nrcan.gc.ca',
        'mining.ca',
        
        # US Behörden
        'blm.gov',
        'usgs.gov',
        
        # Australische Behörden
        'sarig.sa.gov.au',
        'ga.gov.au',
        'minex.com.au',
        
        # Internationale Organisationen
        'mining.com',
        'infomineinc.com',
        'spglobal.com'
    ],
    
    'tier_2_databases': [
        # Kommerzielle Datenbanken
        'sedar.com',
        'sec.gov/edgar',
        'asx.com.au',
        'tsx.com',
        
        # Mining-News Portale
        'northernminer.com',
        'miningweekly.com',
        'mining-journal.com'
    ],
    
    'tier_3_company': [
        # Direkte Unternehmensseiten
        '*.corporate-ir.net',
        '*.q4cdn.com',
        '*annual-report*',
        '*sustainability-report*'
    ]
}
```

### B. GESTIM-Integration

```python
def build_gestim_search_query(mine_name: str, region: str = None) -> str:
    """Erstelle spezifische GESTIM-Suchanfrage"""
    base_url = "gestim.mines.gouv.qc.ca"
    
    query_parts = [
        f'site:{base_url}',
        f'("{mine_name}" OR "{mine_name} mine" OR "{mine_name} project")'
    ]
    
    if region:
        query_parts.append(f'("{region}" OR "région {region}")')
    
    # Spezifische GESTIM-Felder
    query_parts.extend([
        '("titre minier" OR "mining title")',
        '("claims" OR "claim")',
        '("titulaire" OR "holder")',
        '("restoration" OR "restauration" OR "garantie")'
    ])
    
    return ' '.join(query_parts)
```

### C. PDF-Download-Optimierung

```python
MINING_PDF_PATTERNS = {
    'technical_reports': [
        'ni-43-101*.pdf',
        'technical-report*.pdf',
        'feasibility-study*.pdf',
        '*-pea-*.pdf',
        '*-dfs-*.pdf'
    ],
    
    'environmental': [
        '*closure-plan*.pdf',
        '*restoration*.pdf',
        '*reclamation*.pdf',
        '*environmental-bond*.pdf',
        '*eia*.pdf'
    ],
    
    'financial': [
        '*annual-report*.pdf',
        '*aif*.pdf',
        '*md-a*.pdf',
        '*financial-statements*.pdf'
    ]
}
```

## 4. TIEFENSUCHE-OPTIMIERUNG

### A. 2-Phasen-Suche Verbesserung

```python
class EnhancedTwoPhaseSearch:
    """Verbesserte 2-Phasen-Suche für Mining-Daten"""
    
    def phase_1_discovery(self, mine_name: str, country: str) -> List[str]:
        """Phase 1: Entdecke relevante Hauptquellen"""
        queries = []
        
        # 1. Direkte Suche nach Mine
        queries.append(f'"{mine_name}" mine {country} operator company')
        
        # 2. Suche nach technischen Berichten
        queries.append(f'"{mine_name}" "NI 43-101" OR "technical report" filetype:pdf')
        
        # 3. Suche nach Umwelt/Restauration
        queries.append(f'"{mine_name}" "closure cost" OR "restoration" OR "reclamation" OR "environmental bond"')
        
        # 4. Behörden-spezifische Suche
        if country.lower() == 'kanada':
            queries.append(f'site:sedar.com "{mine_name}"')
            queries.append(f'site:gestim.mines.gouv.qc.ca "{mine_name}"')
        
        return queries
    
    def phase_2_deep_dive(self, discovered_sources: List[str]) -> List[str]:
        """Phase 2: Tiefensuche in gefundenen Quellen"""
        deep_queries = []
        
        for source in discovered_sources:
            domain = extract_domain(source)
            
            # Erstelle domain-spezifische Tiefensuchen
            deep_queries.extend([
                f'site:{domain} "restoration cost" OR "closure cost" OR "ARO"',
                f'site:{domain} "environmental bond" OR "financial assurance"',
                f'site:{domain} "NI 43-101" filetype:pdf',
                f'site:{domain} "annual report" filetype:pdf'
            ])
        
        return deep_queries
```

### B. Dokumenttypen-Priorisierung

```python
DOCUMENT_PRIORITY_MATRIX = {
    'restoration_costs': {
        'high': [
            'closure plan',
            'closure cost estimate',
            'asset retirement obligation',
            'financial assurance',
            'environmental bond'
        ],
        'medium': [
            'feasibility study',
            'technical report',
            'annual report',
            'sustainability report'
        ],
        'low': [
            'news release',
            'presentation',
            'fact sheet'
        ]
    }
}
```

## 5. DATENEXTRAKTION-VERBESSERUNG

### A. Zusätzliche Felder

```python
ENHANCED_DATA_FIELDS = {
    # Bestehende Felder...
    
    # NEUE FELDER:
    'Umweltgenehmigungen': {
        'patterns': [
            r'environmental permit[s]?\s*[:]\s*([^,\n]+)',
            r'umweltgenehmigung[en]?\s*[:]\s*([^,\n]+)',
            r'permiso ambiental\s*[:]\s*([^,\n]+)'
        ],
        'required': True
    },
    
    'Bond/Sicherheitsleistung': {
        'patterns': [
            r'bond amount\s*[:]\s*\$?([0-9,\.]+\s*(?:million|M|mio))',
            r'financial assurance\s*[:]\s*\$?([0-9,\.]+)',
            r'garantie financière\s*[:]\s*([0-9,\.]+)'
        ],
        'required': True
    },
    
    'Restaurations-Timeline': {
        'patterns': [
            r'closure schedule\s*[:]\s*([^,\n]+)',
            r'expected closure\s*[:]\s*(\d{4})',
            r'mine life\s*[:]\s*([0-9]+\s*years)'
        ]
    },
    
    'Behördliche Auflagen': {
        'patterns': [
            r'regulatory requirement[s]?\s*[:]\s*([^,\n]+)',
            r'compliance obligation[s]?\s*[:]\s*([^,\n]+)'
        ]
    },
    
    'Wassernutzungslizenz': {
        'patterns': [
            r'water (?:use )?license\s*[:]\s*([^,\n]+)',
            r'water permit\s*[:]\s*([^,\n]+)'
        ]
    },
    
    'Kontaminierte Flächen': {
        'patterns': [
            r'contaminated area[s]?\s*[:]\s*([0-9,\.]+\s*(?:ha|hectares|km2))',
            r'affected area[s]?\s*[:]\s*([0-9,\.]+)'
        ]
    },
    
    'Monitoring-Dauer': {
        'patterns': [
            r'post-closure monitoring\s*[:]\s*([0-9]+\s*years)',
            r'monitoring period\s*[:]\s*([^,\n]+)'
        ]
    }
}
```

### B. Quellenreferenzierung nach Mining-Standards

```python
class MiningStandardsSourceFormatter:
    """Formatiere Quellen nach Mining-Industriestandards"""
    
    @staticmethod
    def format_ni43101_reference(doc_info: Dict) -> str:
        """NI 43-101 Standard-Referenzierung"""
        # Format: Company (Year). "Report Title". Report Type. Date. Authors.
        return (
            f"{doc_info.get('company', 'Unknown')} "
            f"({doc_info.get('year', 'n.d.')}). "
            f"\"{doc_info.get('title', 'Technical Report')}\" "
            f"NI 43-101 Technical Report. "
            f"{doc_info.get('effective_date', '')}. "
            f"Prepared by: {doc_info.get('authors', 'Various authors')}."
        )
    
    @staticmethod
    def format_sedar_reference(filing_info: Dict) -> str:
        """SEDAR Filing Referenzierung"""
        return (
            f"{filing_info.get('issuer', 'Unknown')} "
            f"({filing_info.get('date', 'n.d.')}). "
            f"{filing_info.get('document_type', 'Filing')}. "
            f"SEDAR Profile No: {filing_info.get('profile_no', 'N/A')}. "
            f"Document No: {filing_info.get('doc_no', 'N/A')}."
        )
```

### C. Mining-Standards Integration

```python
MINING_REPORTING_STANDARDS = {
    'kanada': {
        'standard': 'NI 43-101',
        'required_sections': [
            'Summary',
            'Property Description',
            'Mineral Resource Estimate',
            'Economic Analysis',
            'Environmental Studies'
        ],
        'qp_required': True  # Qualified Person
    },
    
    'australien': {
        'standard': 'JORC Code',
        'required_sections': [
            'Sampling Techniques',
            'Resource Estimation',
            'Cut-off Parameters',
            'Mining Factors',
            'Environmental'
        ],
        'competent_person_required': True
    },
    
    'südafrika': {
        'standard': 'SAMREC',
        'similar_to': 'JORC',
        'additional_requirements': ['BEE compliance']
    }
}
```

## 6. IMPLEMENTIERUNGS-PRIORITÄTEN

### Phase 1 (Sofort umsetzbar):
1. **Erweiterte Suchbegriffe** in config.py ergänzen
2. **Namenvarianten-Generator** implementieren
3. **Priorisierte Domains** hinzufügen

### Phase 2 (Mittelfristig):
4. **GESTIM-Integration** mit spezifischen Queries
5. **2-Phasen-Suche** optimieren
6. **Zusätzliche Datenfelder** implementieren

### Phase 3 (Langfristig):
7. **Mining-Standards** Integration
8. **PDF-Parser** für technische Berichte
9. **Multi-Sprach-Support** erweitern

## 7. PERPLEXITY PROMPT-OPTIMIERUNG

### Verbesserter Prompt-Template:

```python
ENHANCED_PERPLEXITY_PROMPT = """
Recherchiere detaillierte Informationen zur Mine "{mine_name}" in {country}.

PRIORITÄT 1 - RESTAURATIONSKOSTEN:
- Suche explizit nach: "closure cost", "restoration cost", "reclamation cost", "ARO", "asset retirement obligation"
- Prüfe Quellen: Jahresberichte, NI 43-101 Reports, Umweltgutachten, SEDAR/EDGAR Filings
- Suche in verschiedenen Sprachen: {local_terms}

PRIORITÄT 2 - OFFIZIELLE QUELLEN:
- Behördendatenbanken: {priority_sources}
- Betreiberwebseiten und Investor Relations
- Technische Berichte (NI 43-101, JORC, Feasibility Studies)

DATENEXTRAKTION:
Extrahiere ALLE folgenden Informationen mit Quellenangaben:
1. Vollständiger Minenname und Alternativnamen
2. Exakte Koordinaten (Latitude/Longitude)
3. Betreiber (aktuell und historisch)
4. Restaurationskosten (WICHTIG: Mit Jahr und Währung)
5. Umweltanleihen/Sicherheitsleistungen
6. Produktionsdaten und Rohstoffe
7. Minentyp und Betriebsstatus
8. Umweltgenehmigungen und Auflagen

FORMAT:
- Nutze [Quelle: X] für JEDEN extrahierten Datenpunkt
- Bei Restaurationskosten: IMMER Jahr und Währung angeben
- Bei mehreren Werten: Alle mit jeweiliger Quelle aufführen

QUELLEN-SEKTION:
Liste am Ende ALLE verwendeten Quellen nummeriert auf:
[1] Vollständige URL oder Dokumentname
[2] ...
"""
```

Diese Verbesserungen würden MineSearch V2 zu einem deutlich leistungsfähigeren Tool für die Mining-Recherche machen, insbesondere für die kritische Erfassung von Restaurationskosten und Umweltdaten.