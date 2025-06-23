# Mining Research System - Umfassender Verbesserungsplan

**Autor**: Assistant
**Datum**: 21.06.2025
**Version**: 1.0

## Executive Summary

Das Mining Research System findet aktuell nur begrenzte Informationen über Minen. Hauptprobleme sind:
- Keine systematische Quellensammlung
- Oberflächliche Websuchen ohne Dokumentenverarbeitung  
- Fehlende Nutzung der vorhandenen Datenbank
- Viele nicht funktionierende Agenten

Dieser Plan beschreibt konkrete Verbesserungen in 4 Phasen mit einer Gesamtdauer von 10 Tagen.

## Aktuelle Situation

### Funktionsfähige Komponenten
- 3 von 11 Agenten liefern Ergebnisse (Claude, GPT-4, Exa)
- Grundlegende Orchestrator-Funktionalität
- SQLite Datenbank mit Schema
- Streamlit UI

### Hauptprobleme
1. **Keine Quellensammlung**: Agenten suchen direkt nach Daten statt erst Quellen zu finden
2. **Oberflächliche Suche**: Nur API-Calls, keine tiefen Website-Crawls oder PDF-Verarbeitung
3. **Fehlende Persistenz**: Ergebnisse werden nicht in DB gespeichert
4. **Keine Dokumentenverarbeitung**: PDFs, Excel-Dateien etc. werden ignoriert
5. **Isolierte Agenten**: Keine Koordination oder Wissensaustausch

## Phase 1: Sofortige Verbesserungen (1-2 Tage)

### 1.1 SourceManager Integration

**Vorhandene Datei**: `/app/src/core/source_manager.py`

```python
# Integration in orchestrator.py
async def search_mine_staged(self, query: MineQuery, search_params: Dict) -> List[SearchResult]:
    # NEU: Source Discovery Phase
    source_manager = SourceManager()
    discovered_sources = await source_manager.discover_sources(query)
    
    # Sources in DB speichern
    for source in discovered_sources:
        await self._save_source_to_db(source)
    
    # Sources an Agenten weitergeben
    search_params['discovered_sources'] = discovered_sources
```

### 1.2 Deep Web Crawler Vervollständigung

**Neue Datei**: `/app/src/agents/deep_web_crawler.py`

```python
class DeepWebCrawler(BaseAgent):
    """Crawlt Websites in die Tiefe für Mining-Informationen"""
    
    async def crawl_website(self, url: str, max_depth: int = 3):
        """Crawlt Website rekursiv bis zur angegebenen Tiefe"""
        visited = set()
        to_visit = [(url, 0)]
        results = []
        
        while to_visit:
            current_url, depth = to_visit.pop(0)
            if depth > max_depth or current_url in visited:
                continue
                
            visited.add(current_url)
            content = await self._fetch_page(current_url)
            
            # Mining-relevante Links extrahieren
            mining_links = self._extract_mining_links(content)
            for link in mining_links:
                to_visit.append((link, depth + 1))
            
            # Inhalte extrahieren
            extracted = self._extract_mining_data(content)
            results.extend(extracted)
            
        return results
```

### 1.3 Datenbank-Schema Erweiterungen

```sql
-- Quellen-Tabelle
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    source_type TEXT CHECK(source_type IN ('website', 'pdf', 'api', 'database', 'news')),
    mine_id INTEGER,
    discovered_by TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_crawled TIMESTAMP,
    content_hash TEXT,
    reliability_score REAL DEFAULT 0.5,
    metadata JSON,
    FOREIGN KEY (mine_id) REFERENCES mines(id)
);

-- Agent-Ergebnisse
CREATE TABLE IF NOT EXISTS agent_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    mine_id INTEGER NOT NULL,
    source_id INTEGER,
    field_name TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status TEXT DEFAULT 'pending',
    metadata JSON,
    FOREIGN KEY (mine_id) REFERENCES mines(id),
    FOREIGN KEY (source_id) REFERENCES sources(id),
    INDEX idx_agent_mine (agent_name, mine_id),
    INDEX idx_field (field_name)
);

-- Content Cache
CREATE TABLE IF NOT EXISTS content_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    content TEXT,
    content_type TEXT,
    headers JSON,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    INDEX idx_url (url),
    INDEX idx_expires (expires_at)
);
```

## Phase 2: Browser-basiertes Scraping (3-5 Tage)

### 2.1 Playwright Integration

**Neue Datei**: `/app/src/agents/browser_agent.py`

```python
from playwright.async_api import async_playwright
import asyncio

class BrowserAgent(BaseAgent):
    """Browser-basierter Agent für JavaScript-heavy Websites"""
    
    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='MiningResearchBot/1.0'
        )
    
    async def scrape_dynamic_site(self, url: str, wait_for_selector: str = None):
        """Scrapt JavaScript-gerenderte Seiten"""
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='networkidle')
            
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=30000)
            
            # Screenshots für Debugging
            await page.screenshot(path=f'/tmp/screenshot_{hash(url)}.png')
            
            # Inhalte extrahieren
            content = await page.content()
            
            # Spezielle Extraktion für bekannte Portale
            if 'sedar.com' in url:
                return await self._extract_sedar_data(page)
            elif 'nrcan.gc.ca' in url:
                return await self._extract_nrcan_data(page)
            else:
                return self._extract_generic_data(content)
                
        finally:
            await page.close()
```

### 2.2 Regierungsportale Handler

```python
class GovernmentPortalHandler:
    """Spezialisierte Handler für Regierungsportale"""
    
    PORTAL_CONFIGS = {
        'canada': {
            'nrcan.gc.ca': {
                'search_endpoint': '/gms/search',
                'requires_auth': False,
                'pagination': 'offset'
            },
            'mern.gouv.qc.ca': {
                'search_endpoint': '/mines/recherche',
                'requires_auth': False,
                'language': 'fr'
            }
        },
        'australia': {
            'ga.gov.au': {
                'search_endpoint': '/data/search',
                'api_available': True
            }
        }
    }
    
    async def search_portal(self, country: str, mine_name: str):
        """Durchsucht länderspezifische Portale"""
        portals = self.PORTAL_CONFIGS.get(country.lower(), {})
        results = []
        
        for domain, config in portals.items():
            if config.get('api_available'):
                results.extend(await self._search_via_api(domain, mine_name))
            else:
                results.extend(await self._search_via_scraping(domain, mine_name))
                
        return results
```

## Phase 3: Dokumentenverarbeitung (3-5 Tage)

### 3.1 PDF Processor

**Neue Datei**: `/app/src/utils/pdf_processor.py`

```python
import PyPDF2
import pdfplumber
import camelot
from PIL import Image
import pytesseract

class PDFProcessor:
    """Verarbeitet PDF-Dokumente für Mining-Daten"""
    
    async def process_pdf(self, pdf_path: str, pdf_type: str = 'auto'):
        """Hauptmethode für PDF-Verarbeitung"""
        
        # Typ erkennen
        if pdf_type == 'auto':
            pdf_type = self._detect_pdf_type(pdf_path)
        
        if pdf_type == 'ni43-101':
            return await self._process_ni43101(pdf_path)
        elif pdf_type == 'environmental':
            return await self._process_environmental_report(pdf_path)
        elif pdf_type == 'financial':
            return await self._process_financial_report(pdf_path)
        else:
            return await self._process_generic_pdf(pdf_path)
    
    async def _process_ni43101(self, pdf_path: str):
        """Spezialisierte Verarbeitung für NI 43-101 Reports"""
        extracted_data = {
            'report_type': 'NI 43-101',
            'sections': {}
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            # Inhaltsverzeichnis parsen
            toc = self._extract_table_of_contents(pdf)
            
            # Wichtige Sektionen extrahieren
            for section in ['Summary', 'Property Description', 'Mineral Resources', 
                          'Mining Methods', 'Economic Analysis']:
                section_data = self._extract_section(pdf, section, toc)
                extracted_data['sections'][section] = section_data
            
            # Tabellen extrahieren
            tables = self._extract_all_tables(pdf)
            extracted_data['tables'] = tables
            
        return extracted_data
    
    def _extract_all_tables(self, pdf):
        """Extrahiert alle Tabellen aus PDF"""
        tables = []
        
        for page_num, page in enumerate(pdf.pages):
            # Versuche erst mit pdfplumber
            page_tables = page.extract_tables()
            
            if not page_tables:
                # Fallback zu camelot für komplexe Tabellen
                try:
                    camelot_tables = camelot.read_pdf(
                        pdf.path, 
                        pages=str(page_num + 1),
                        flavor='lattice'
                    )
                    page_tables = [table.df.to_dict() for table in camelot_tables]
                except:
                    pass
            
            for table in page_tables:
                tables.append({
                    'page': page_num + 1,
                    'data': table
                })
        
        return tables
```

### 3.2 Dokumenten-Finder

```python
class DocumentFinder:
    """Findet relevante Dokumente für Minen"""
    
    DOCUMENT_PATTERNS = {
        'technical_reports': [
            'ni 43-101', 'jorc report', 'feasibility study',
            'preliminary economic assessment', 'pea report'
        ],
        'environmental': [
            'environmental impact', 'eia', 'closure plan',
            'rehabilitation plan', 'water management'
        ],
        'financial': [
            'annual report', 'quarterly report', 'md&a',
            'financial statements', 'investor presentation'
        ]
    }
    
    async def find_documents(self, mine_name: str, document_type: str = 'all'):
        """Sucht nach relevanten Dokumenten"""
        documents = []
        
        # Google Custom Search für PDFs
        search_queries = self._build_document_queries(mine_name, document_type)
        
        for query in search_queries:
            results = await self._search_for_pdfs(query)
            documents.extend(results)
        
        # SEDAR/EDGAR durchsuchen
        if document_type in ['all', 'financial', 'technical_reports']:
            sedar_docs = await self._search_sedar(mine_name)
            documents.extend(sedar_docs)
        
        return self._deduplicate_documents(documents)
```

## Phase 4: Erweiterte Features

### 4.1 Intelligente Agent-Koordination

```python
class AgentCoordinator:
    """Koordiniert Agenten für optimale Ergebnisse"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.agent_capabilities = {
            'source_discovery': ['tavily', 'exa', 'deep_crawler'],
            'document_search': ['browser_agent', 'firecrawl'],
            'data_extraction': ['claude', 'gpt4', 'openrouter'],
            'validation': ['perplexity', 'claude']
        }
    
    async def coordinate_search(self, query: MineQuery):
        """Koordiniert mehrstufige Suche"""
        
        # Phase 1: Quellen entdecken
        sources = await self._discover_sources(query)
        
        # Phase 2: Quellen priorisieren
        prioritized_sources = self._prioritize_sources(sources, query)
        
        # Phase 3: Daten extrahieren
        extraction_tasks = []
        for source in prioritized_sources[:20]:  # Top 20 Quellen
            agent = self._select_best_agent_for_source(source)
            task = agent.extract_from_source(source, query)
            extraction_tasks.append(task)
        
        results = await asyncio.gather(*extraction_tasks)
        
        # Phase 4: Ergebnisse validieren
        validated_results = await self._validate_results(results)
        
        return validated_results
```

### 4.2 ML-basierte Relevanz-Bewertung

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RelevanceScorer:
    """Bewertet Relevanz von gefundenen Informationen"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.load_mining_corpus()
    
    def score_relevance(self, text: str, field: str, mine_context: Dict):
        """Bewertet wie relevant ein Text für ein bestimmtes Feld ist"""
        
        # Kontext-spezifische Keywords
        field_keywords = self.FIELD_KEYWORDS.get(field, [])
        context_text = f"{mine_context['name']} {mine_context['region']} {mine_context['country']}"
        
        # TF-IDF Vektorisierung
        corpus = [text, ' '.join(field_keywords), context_text]
        vectors = self.vectorizer.fit_transform(corpus)
        
        # Cosine Similarity berechnen
        text_vector = vectors[0]
        keyword_vector = vectors[1]
        context_vector = vectors[2]
        
        keyword_similarity = cosine_similarity(text_vector, keyword_vector)[0][0]
        context_similarity = cosine_similarity(text_vector, context_vector)[0][0]
        
        # Kombinierter Score
        relevance_score = (keyword_similarity * 0.7) + (context_similarity * 0.3)
        
        return relevance_score
```

## Erwartete Ergebnisse

### Quantitative Verbesserungen
- **Quellenanzahl**: Von ~3 auf 50+ pro Mine
- **Datenabdeckung**: Von 30% auf 80% der Felder
- **Geschwindigkeit**: 5x schneller durch Parallelisierung
- **Erfolgsrate**: Von 60% auf 95% für Standardfelder

### Qualitative Verbesserungen
- **Datenqualität**: Kreuzvalidierung durch mehrere Quellen
- **Aktualität**: Neueste Dokumente werden gefunden
- **Vollständigkeit**: Auch seltene Informationen werden erfasst
- **Nachvollziehbarkeit**: Alle Quellen werden dokumentiert

## Implementierungs-Timeline

### Woche 1
- **Tag 1-2**: Phase 1 (SourceManager, DB-Schema, Deep Crawler)
- **Tag 3-5**: Phase 2 Start (Browser Agent Setup)

### Woche 2  
- **Tag 6-7**: Phase 2 Fertigstellung (Portal Handler)
- **Tag 8-10**: Phase 3 (PDF Processing)

### Testing & Optimierung
- Kontinuierliches Testing nach jeder Phase
- Performance-Monitoring
- Fehleranalyse und Fixes

## Risiken und Mitigationen

### Technische Risiken
- **Browser-Instabilität**: Robuste Fehlerbehandlung, Retry-Mechanismen
- **Rate Limiting**: Intelligente Request-Verteilung, Caching
- **PDF-Parsing-Fehler**: Multiple Fallback-Strategien

### Rechtliche Überlegungen
- **robots.txt**: Immer respektieren
- **Terms of Service**: Prüfung für jede Quelle
- **Rate Limits**: Konservative Defaults

## Erfolgsmetriken

1. **Primär**: Anzahl gefundener valider Datenpunkte pro Mine
2. **Sekundär**: Quellenvielfalt, Aktualität der Daten
3. **Tertiär**: Systemperformance, Fehlerrate

## Zusammenfassung

Dieser Plan transformiert das Mining Research System von einer oberflächlichen Suchmaschine zu einem umfassenden Intelligence-Gathering-System. Die schrittweise Implementierung minimiert Risiken und ermöglicht kontinuierliche Verbesserungen.

Die Kombination aus tiefem Web-Crawling, Dokumentenverarbeitung und intelligenter Koordination wird die Datenqualität und -vollständigkeit dramatisch verbessern.