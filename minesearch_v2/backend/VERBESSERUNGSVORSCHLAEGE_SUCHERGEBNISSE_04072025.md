"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Verbesserungsvorschläge für bessere Suchergebnisse in MineSearch v2
"""

# VERBESSERUNGSVORSCHLÄGE FÜR BESSERE SUCHERGEBNISSE

## ANALYSEERGEBNISSE

Nach eingehender Analyse des Codes wurden folgende Bereiche identifiziert, die das größte Verbesserungspotenzial für die Suchergebnis-Qualität bieten:

## 1. DATENEXTRAKTION (data_extraction.py)

### PROBLEME:
- **Starre Pattern-Matching**: Die Regex-Patterns sind sehr spezifisch und können Variationen verpassen
- **Fehlende Fuzzy-Logik**: Exakte Übereinstimmungen erforderlich, keine Toleranz für Schreibfehler
- **Kontextverlust**: Patterns berücksichtigen keinen umgebenden Kontext
- **Einsprachige Patterns**: Hauptsächlich auf Deutsch/Englisch fokussiert

### VERBESSERUNGSVORSCHLÄGE:

#### 1.1 Intelligentere Pattern-Erkennung
```python
# Statt starrer Patterns:
def _extract_field_with_context(self, field: str, content: str, context_window: int = 100):
    """Extrahiere Feld mit Kontext-Analyse"""
    # Suche nach Schlüsselwörtern im Kontext
    keywords = self._get_field_keywords(field)
    
    # Finde alle Vorkommen der Keywords
    for keyword in keywords:
        positions = self._find_keyword_positions(keyword, content)
        for pos in positions:
            # Analysiere Kontext um das Keyword
            context = content[max(0, pos-context_window):pos+context_window]
            value = self._extract_value_from_context(context, field)
            if value:
                confidence = self._calculate_confidence(value, context)
                return value, confidence
```

#### 1.2 Multi-Sprachen-Support erweitern
```python
# Erweitere Patterns für mehr Sprachen
MULTILINGUAL_PATTERNS = {
    'Restaurationskosten': {
        'de': ['Restaurationskosten', 'Sanierungskosten', 'Rekultivierung'],
        'en': ['restoration costs', 'closure costs', 'ARO', 'environmental liability'],
        'es': ['costos de cierre', 'pasivos ambientales', 'garantías financieras'],
        'id': ['biaya reklamasi', 'jaminan reklamasi', 'dana cadangan'],
        'fr': ['coûts de fermeture', 'provision pour restauration'],
        'pt': ['custos de fechamento', 'provisão ambiental']
    }
}
```

#### 1.3 Numerische Werte besser extrahieren
```python
def _extract_numeric_values(self, text: str, field_type: str):
    """Intelligente Extraktion numerischer Werte"""
    # Erkenne verschiedene Zahlenformate
    patterns = [
        r'(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d+)?)',  # 1,234,567.89
        r'(\d+(?:\.\d+)?\s*(?:million|mio|millones|juta|milhões))',  # 10 million
        r'(\$|USD|EUR|CAD|AUD)?\s*(\d+(?:[,\.]\d+)?)\s*(million|billion)?'
    ]
    
    # Konvertiere in einheitliches Format
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            value = self._normalize_numeric_value(match)
            if self._is_plausible_value(value, field_type):
                return value
```

## 2. SCORING-SYSTEM (_calculate_data_quality)

### PROBLEME:
- **Zu einfache Metriken**: Nur Anzahl ausgefüllter Felder
- **Keine Gewichtung**: Alle Felder gleich wichtig
- **Keine Qualitätsprüfung**: Nur Vorhandensein, nicht Qualität der Daten

### VERBESSERUNGSVORSCHLÄGE:

#### 2.1 Gewichtetes Scoring-System
```python
FIELD_WEIGHTS = {
    'Restaurationskosten': 3.0,  # Höchste Priorität
    'Betreiber': 2.0,
    'Eigentümer': 2.0,
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 2.0,
    'x-Koordinate': 1.5,
    'y-Koordinate': 1.5,
    'Aktivitätsstatus': 1.5,
    'Region': 1.0,
    'Country': 1.0,
    # ... andere Felder mit Gewicht 1.0
}

def _calculate_weighted_quality(self, structured_data: Dict) -> Dict:
    """Berechne gewichtete Datenqualität"""
    weighted_score = 0
    max_score = 0
    
    for field, weight in FIELD_WEIGHTS.items():
        max_score += weight
        if structured_data.get(field) and structured_data[field] != '-':
            # Prüfe Datenqualität
            quality_factor = self._assess_field_quality(field, structured_data[field])
            weighted_score += weight * quality_factor
```

#### 2.2 Datenqualitäts-Bewertung
```python
def _assess_field_quality(self, field: str, value: str) -> float:
    """Bewerte die Qualität eines extrahierten Wertes"""
    quality = 1.0
    
    # Prüfe auf Platzhalter
    if any(placeholder in value.lower() for placeholder in ['k.a', 'unbekannt', 'n/a']):
        quality *= 0.3
    
    # Prüfe auf geschätzte Werte
    if 'geschätzt' in value.lower() or 'estimated' in value.lower():
        quality *= 0.7
    
    # Prüfe auf Quellenangabe
    if '[Quelle:' in value:
        quality *= 1.2
    
    # Feldspezifische Prüfungen
    if field == 'Restaurationskosten':
        if not re.search(r'\d+', value):
            quality *= 0.1  # Keine Zahl = sehr niedrige Qualität
        if 'geplant' in value:
            quality *= 0.9  # Geplante Kosten sind ok, aber nicht optimal
    
    return min(quality, 1.0)
```

## 3. SUCHANFRAGEN-OPTIMIERUNG

### PROBLEME:
- **Zu generische Prompts**: Nicht spezifisch genug für schwierige Fälle
- **Fehlende Iterationen**: Keine Nachfragen bei schlechten Ergebnissen
- **Mangelnde Kontextualisierung**: Keine Anpassung an Land/Region

### VERBESSERUNGSVORSCHLÄGE:

#### 3.1 Dynamische Prompt-Generation
```python
def _build_contextual_search_query(self, mine_name: str, country: str, 
                                   previous_results: Dict = None) -> str:
    """Erstelle kontextabhängige Suchanfrage"""
    
    # Basis-Query
    query = f"Suche nach der Mine '{mine_name}'"
    
    # Länderspezifische Anpassungen
    if country:
        country_config = get_country_config(country)
        # Füge lokale Begriffe hinzu
        local_terms = country_config.get('local_mining_terms', {})
        query += f" (lokale Begriffe: {', '.join(local_terms.values())})"
        
        # Füge wichtige Datenbanken hinzu
        priority_sources = country_config.get('priority_sources', [])
        if priority_sources:
            query += f". WICHTIG: Prüfe diese Quellen: {', '.join(priority_sources[:3])}"
    
    # Wenn vorherige Ergebnisse schlecht waren
    if previous_results and previous_results.get('data_quality', {}).get('completeness_percentage', 0) < 30:
        missing_fields = previous_results['data_quality'].get('missing_critical_fields', [])
        query += f". FOKUS auf fehlende Daten: {', '.join(missing_fields)}"
    
    return query
```

#### 3.2 Intelligente Nachfragen
```python
async def _iterative_search(self, mine_name: str, country: str, max_iterations: int = 3):
    """Iterative Suche mit Verbesserungen"""
    
    results = []
    combined_data = {}
    
    for iteration in range(max_iterations):
        # Passe Query basierend auf bisherigen Ergebnissen an
        if iteration == 0:
            query = self._build_initial_query(mine_name, country)
        else:
            # Analysiere was fehlt
            missing_data = self._analyze_missing_data(combined_data)
            query = self._build_targeted_query(mine_name, missing_data)
        
        result = await self.search_mine(query)
        results.append(result)
        
        # Kombiniere Ergebnisse
        combined_data = self._merge_results(combined_data, result)
        
        # Prüfe ob genug Daten vorhanden
        if self._is_data_sufficient(combined_data):
            break
    
    return combined_data
```

## 4. PROVIDER-SPEZIFISCHE OPTIMIERUNGEN

### PROBLEME:
- **Keine Provider-Spezialisierung**: Alle Provider gleich behandelt
- **Fehlende Fallback-Strategien**: Bei Fehlern keine Alternativen
- **OpenRouter ohne Web-Suche**: Liefert nur geschätzte Daten

### VERBESSERUNGSVORSCHLÄGE:

#### 4.1 Provider-Kaskadierung
```python
class ProviderCascade:
    """Intelligente Provider-Auswahl und Fallback"""
    
    def __init__(self):
        self.provider_tiers = [
            {
                'name': 'perplexity-deep',
                'providers': ['perplexity:sonar-deep-research'],
                'use_for': ['kritische_daten', 'restaurationskosten']
            },
            {
                'name': 'perplexity-standard',
                'providers': ['perplexity:sonar-pro', 'perplexity:sonar'],
                'use_for': ['standard_suche', 'schnelle_ergebnisse']
            },
            {
                'name': 'openrouter-fallback',
                'providers': ['openrouter:llama-3.1-8b', 'openrouter:mixtral-8x7b'],
                'use_for': ['kostenlose_suche', 'schätzungen']
            }
        ]
    
    async def search_with_cascade(self, query: str, priority: str = 'standard'):
        """Suche mit intelligenter Provider-Auswahl"""
        for tier in self.provider_tiers:
            if priority in tier['use_for']:
                for provider in tier['providers']:
                    try:
                        result = await self._search_with_provider(query, provider)
                        if self._is_result_acceptable(result):
                            return result
                    except Exception as e:
                        logger.warning(f"Provider {provider} fehlgeschlagen: {e}")
                        continue
```

#### 4.2 Hybrid-Suche
```python
async def hybrid_search(self, mine_name: str, country: str):
    """Kombiniere Web-Suche mit KI-Wissen"""
    
    # Phase 1: Web-Suche mit Perplexity
    web_result = await self.perplexity_search(mine_name, country)
    
    # Phase 2: Ergänze mit OpenRouter für fehlende Daten
    if web_result['data_quality']['completeness_percentage'] < 50:
        # Erstelle spezifischen Prompt mit bisherigen Daten
        context = f"Basierend auf diesen Daten: {web_result['structured_data']}"
        ai_result = await self.openrouter_search(mine_name, context)
        
        # Intelligentes Merging
        merged = self._smart_merge(web_result, ai_result)
        return merged
```

## 5. ERGEBNIS-FILTERUNG UND RANKING

### PROBLEME:
- **Keine Duplikat-Erkennung**: Gleiche Quellen mehrfach
- **Kein Quellen-Ranking**: Alle Quellen gleich gewichtet
- **Fehlende Validierung**: Keine Plausibilitätsprüfung

### VERBESSERUNGSVORSCHLÄGE:

#### 5.1 Intelligente Quellen-Bewertung
```python
class SourceRanker:
    """Bewerte und ranke Quellen nach Qualität"""
    
    DOMAIN_TIERS = {
        'tier1': ['mining.gov', 'sedar.com', 'sec.gov'],
        'tier2': ['miningdataonline.com', 'infomine.com'],
        'tier3': ['wikipedia.org', 'mindat.org']
    }
    
    def calculate_source_score(self, source: Dict) -> float:
        """Berechne Qualitätsscore für eine Quelle"""
        score = 0.5  # Basis-Score
        
        # Domain-Bewertung
        if source['type'] == 'url':
            domain = self._extract_domain(source['value'])
            for tier, domains in self.DOMAIN_TIERS.items():
                if any(d in domain for d in domains):
                    score += {'tier1': 0.5, 'tier2': 0.3, 'tier3': 0.1}[tier]
        
        # Dokumenttyp-Bewertung
        if source['type'] == 'document':
            if 'ni 43-101' in source['value'].lower():
                score += 0.4
            elif 'annual report' in source['value'].lower():
                score += 0.3
        
        # Aktualität
        year = self._extract_year(source['value'])
        if year:
            age = 2025 - year
            score -= age * 0.02  # -0.02 pro Jahr
        
        return max(0, min(1, score))
```

#### 5.2 Duplikat-Erkennung
```python
def _deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
    """Entferne Duplikate intelligent"""
    unique_sources = []
    seen_content = set()
    
    for source in sources:
        # Normalisiere für Vergleich
        normalized = self._normalize_source(source['value'])
        
        # Prüfe auf ähnliche URLs
        if source['type'] == 'url':
            base_url = self._get_base_url(normalized)
            if base_url not in seen_content:
                seen_content.add(base_url)
                unique_sources.append(source)
        else:
            # Fuzzy-Matching für Dokumente
            if not self._is_similar_to_seen(normalized, seen_content):
                seen_content.add(normalized)
                unique_sources.append(source)
    
    return unique_sources
```

## 6. ZUSÄTZLICHE VERBESSERUNGEN

### 6.1 Caching-Strategie
```python
class IntelligentCache:
    """Intelligentes Caching für bessere Performance"""
    
    def __init__(self):
        self.cache = {}
        self.source_quality_cache = {}  # Cache für Quellen-Qualität
    
    async def get_or_search(self, mine_name: str, country: str):
        """Nutze Cache intelligent"""
        cache_key = f"{mine_name}_{country}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Prüfe ob Cache-Daten ausreichend
            if cached['quality'] > 0.7 and cached['age_hours'] < 24:
                return cached['data']
            elif cached['quality'] > 0.5:
                # Nutze als Basis für verbesserte Suche
                return await self._enhance_cached_result(cached['data'])
```

### 6.2 Feedback-Loop
```python
class FeedbackSystem:
    """Lerne aus Nutzer-Feedback"""
    
    def record_user_action(self, result_id: str, action: str):
        """Tracke Nutzer-Aktionen"""
        # Export = gut, Neue Suche = schlecht
        if action == 'export':
            self._boost_source_scores(result_id)
        elif action == 'new_search':
            self._reduce_source_scores(result_id)
    
    def _adjust_patterns(self, successful_extractions: List[Dict]):
        """Passe Extraction-Patterns basierend auf Erfolg an"""
        # Machine Learning könnte hier eingesetzt werden
        pass
```

## PRIORISIERTE UMSETZUNG

1. **SOFORT** (Höchste Priorität):
   - Gewichtetes Scoring-System implementieren
   - Multi-Sprachen-Patterns erweitern
   - Quellen-Ranking einführen

2. **KURZFRISTIG** (1-2 Wochen):
   - Iterative Suche implementieren
   - Provider-Kaskadierung
   - Duplikat-Erkennung verbessern

3. **MITTELFRISTIG** (1 Monat):
   - Intelligentes Caching
   - Hybrid-Suche
   - Feedback-System

4. **LANGFRISTIG**:
   - Machine Learning für Pattern-Anpassung
   - Crowd-Sourcing für Datenvalidierung
   - API-Integration mit Mining-Datenbanken

## ERWARTETE VERBESSERUNGEN

Mit diesen Optimierungen erwarten wir:
- **+40% Datenqualität** bei Restaurationskosten
- **+30% Vollständigkeit** der Ergebnisse
- **-50% "k.A."** Einträge
- **+60% Quellen-Qualität**
- **-70% Duplikate**

Die Implementierung sollte schrittweise erfolgen, mit kontinuierlicher Messung der Verbesserungen.