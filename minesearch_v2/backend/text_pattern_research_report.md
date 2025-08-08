# Text Pattern Research Report

**Author:** Text Pattern Researcher  
**Datum:** 30.07.2025  
**Auftrag:** Recherche problematischer Textmuster in Mining-Feldwerten  
**Analysierte Datensätze:** 255 search_results Einträge

## Executive Summary

**45 problematische Textmuster** in 4 Hauptkategorien identifiziert:
- **LEER-Varianten (32 Fälle):** Verschiedene Ausdrücke für "leer/unbekannt"
- **Lange Beschreibungen (11 Fälle):** Ausführliche Erklärungen statt Werte  
- **Wert + Erklärung (1 Fall):** Format "Gold. Lapa is a gold mine..."
- **Anweisungen (1 Fall):** "Leave blank if..." Direktiven

## 1. LEER-Varianten (32 Fälle)

### Identifizierte Muster:
```
"LEER - Minentyp nicht spezifiziert"
"(leer)"
"Unbekannt, da keine Explorations- oder Produktionsberichte gefunden"
"Unbekannter Abbauzweck aufgrund fehlender technischer Dokumentation"
"Possibly exploration, but not sure. Leave blank"
"leave blank"
```

### Normalisierungsregeln:
- **Ziel:** Alle zu "X" (offizieller "nicht gefunden" Marker)
- **Pattern:** `(leer|leave blank|unbekannt|unknown|keine .*|no data|not found|not available|n/a|k\.a\.)`

### Code-Implementation:
```python
def normalize_leer_variants(value: str) -> str:
    """Normalisiert LEER-Varianten zu 'X'"""
    if not value:
        return "X"
    
    leer_patterns = [
        r'\(leer\)',
        r'leer\s*-[^,]*',
        r'unbekannt.*(?:aufgrund|da).*',
        r'leave blank.*',
        r'possibly.*leave blank',
        r'keine.*(?:daten|angabe|informationen).*',
        r'not?\s*(?:found|available|specified).*'
    ]
    
    val_lower = value.lower().strip()
    for pattern in leer_patterns:
        if re.search(pattern, val_lower):
            return "X"
    
    return value
```

## 2. Lange Beschreibungen (11 Fälle)

### Typische Beispiele:
```
"derzeit etwa 270.000 Unzen Gold pro Jahr. Die Mine befindet sich in der Nähe von Eeyou Istchee James Bay in Nord-Quebec"
→ Extrahieren: "Gold"

"junior mining companies or subsidiaries of larger firms. Without specific data..."
→ Extrahieren: "X" (keine spezifische Information)
```

### Extraktionsregeln:

#### Für Rohstoffe-Feld:
```python
def extract_commodity_from_description(text: str) -> str:
    """Extrahiert Rohstoff aus langen Beschreibungen"""
    
    # Pattern: "etwa X Unzen ROHSTOFF pro Jahr"
    production_match = re.search(r'(\d+[,.]?\d*)\s*(?:unzen|ounces)\s+(\w+)\s+pro\s+jahr', text.lower())
    if production_match:
        return production_match.group(2).title()  # z.B. "Gold"
    
    # Pattern: Direkte Rohstoff-Erwähnung
    commodities = ['gold', 'kupfer', 'copper', 'nickel', 'eisenerz', 'iron ore', 'kohle', 'coal']
    for commodity in commodities:
        if commodity in text.lower():
            return commodity.title()
    
    return "X"
```

#### Für Eigentümer-Feld:
```python
def extract_owner_from_description(text: str) -> str:
    """Extrahiert spezifischen Eigentümer oder gibt 'X' zurück"""
    
    # Wenn nur generische Beschreibung ("junior mining companies")
    generic_terms = ['junior mining', 'subsidiaries', 'without specific', 'typical structures']
    if any(term in text.lower() for term in generic_terms):
        return "X"
    
    # Pattern: "Eigentum von FIRMA"
    owner_patterns = [
        r'(?:owned by|property of|belongs to|eigentum von)\s+([A-Z][^.]+?)(?:\.|$)',
        r'([A-Z][a-zA-Z\s&]+(?:Inc|Corp|Ltd|GmbH|AG))[^A-Z]*'
    ]
    
    for pattern in owner_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return "X"
```

## 3. Wert + Erklärung (1 Fall)

### Beispiel:
```
"Gold. Lapa is a gold mine, so primary commodity is gold"
```

### Extraktionsregel:
```python
def extract_value_from_explanation(text: str) -> str:
    """Extrahiert Wert aus 'Wert. Erklärung...' Format"""
    
    # Pattern: "WERT. Erklärung..."
    match = re.match(r'^(\w+)\.\s+.*', text)
    if match:
        return match.group(1)
    
    return text
```

## 4. Anweisungen/Instructions (1 Fall)

### Beispiel:
```
"Leave blank if unknown"
```

### Behandlung:
- **Regel:** Alle Anweisungen zu "X" normalisieren
- **Pattern:** `(leave blank|lassen.*leer|fill only if|ausfüllen nur)`

## 5. Zusätzliche Problemmuster (nicht in aktueller Analyse)

### A. Gemischte Sprachen:
```python
def detect_mixed_languages(text: str) -> bool:
    """Erkennt gemischte Sprachen in einem Feld"""
    german_indicators = ['die mine', 'befindet sich', 'gehört', 'wird betrieben']
    english_indicators = ['the mine', 'located in', 'owned by', 'operated by']
    
    has_german = any(ind in text.lower() for ind in german_indicators)
    has_english = any(ind in text.lower() for ind in english_indicators)
    
    return has_german and has_english
```

### B. Koordinaten als Jahre:
```python
def detect_year_in_coordinate_field(value: str, field: str) -> bool:
    """Erkennt Jahre in Koordinaten-Feldern"""
    if field in ['x-Koordinate', 'y-Koordinate', 'latitude', 'longitude']:
        return re.match(r'^(19|20)\d{2}$', str(value).strip())
    return False
```

## 6. Implementierungs-Empfehlungen

### Neue Funktion in extraction_validators.py:
```python
def clean_problematic_text_patterns(value: str, field: str) -> str:
    """
    Master-Funktion zur Bereinigung aller problematischen Textmuster
    
    Args:
        value: Ursprünglicher Feldwert
        field: Feldname für kontextuelle Bereinigung
        
    Returns:
        Bereinigter Wert oder 'X' wenn nicht extrahierbar
    """
    if not value:
        return "X"
    
    # 1. LEER-Varianten normalisieren
    cleaned = normalize_leer_variants(value)
    if cleaned == "X":
        return "X"
    
    # 2. Anweisungen entfernen
    if re.search(r'leave blank|lassen.*leer', cleaned.lower()):
        return "X"
    
    # 3. Lange Beschreibungen nach Feld verarbeiten
    if len(cleaned) > 80:
        if field == "Rohstoffe":
            return extract_commodity_from_description(cleaned)
        elif field == "Eigentümer":
            return extract_owner_from_description(cleaned)
        # Weitere feldspezifische Behandlung...
    
    # 4. Wert + Erklärung Format
    if re.match(r'^\w+\.\s+.*', cleaned):
        return extract_value_from_explanation(cleaned)
    
    return cleaned
```

### Integration in data_extraction.py:
```python
# In der extract_field_data Funktion:
extracted_value = extract_field_from_text(text, field, patterns)
if extracted_value:
    # NEUE BEREINIGUNG
    cleaned_value = clean_problematic_text_patterns(extracted_value, field)
    if cleaned_value != "X":
        results[field] = cleaned_value
```

## 7. Koordination mit Data Cleaning Analyst

### Übergabe-Informationen:
1. **45 dokumentierte Fälle** problematischer Muster
2. **4 Hauptkategorien** mit spezifischen Regex-Patterns
3. **Feldspezifische Extraktionslogik** für Rohstoffe und Eigentümer
4. **Normalisierungsstrategie** zu "X" für nicht-extrahierbare Werte

### Nächste Schritte:
- Data Cleaning Analyst implementiert `clean_problematic_text_patterns()`
- Integration in bestehende Extraction-Pipeline
- Rückwärts-Bereinigung existierender Daten
- Validierung mit Test-Cases

## 8. Test-Cases für Validierung

```python
test_cases = [
    # LEER-Varianten
    ("LEER - Minentyp nicht spezifiziert", "Minentyp", "X"),
    ("Unbekannt, da keine Daten", "Eigentümer", "X"),
    ("Leave blank if unknown", "Aktivitätsstatus", "X"),
    
    # Lange Beschreibungen
    ("derzeit etwa 270.000 Unzen Gold pro Jahr. Die Mine...", "Rohstoffe", "Gold"),
    ("junior mining companies or subsidiaries...", "Eigentümer", "X"),
    
    # Wert + Erklärung
    ("Gold. Lapa is a gold mine, so primary commodity is gold", "Rohstoffe", "Gold"),
    
    # Normale Werte (sollten unverändert bleiben)
    ("Canadian Malartic Corporation", "Eigentümer", "Canadian Malartic Corporation"),
    ("Aktiv", "Aktivitätsstatus", "Aktiv")
]
```

## Fazit

Die Analyse zeigt systematische Probleme in der LLM-generierten Datenextraktion:
- **32 Fälle** von inkonsistenten LEER-Markierungen  
- **11 Fälle** von ausschweifenden Beschreibungen statt präziser Werte
- Bedarf für **kontextuelle Feldbereinigung** und **Normalisierung**

Mit den entwickelten Extraktionsregeln kann die Datenqualität signifikant verbessert werden.