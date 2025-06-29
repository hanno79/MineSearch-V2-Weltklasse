"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: MineSearch 2.0 - Radikal vereinfachtes Mining-Recherche-System
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import os
import asyncio
from datetime import datetime
import logging
from config import config
import csv
import io
import re

# Logging auf Deutsch
logging.basicConfig(
    level=logging.INFO,  # ÄNDERUNG 28.06.2025: Zurück auf INFO nach erfolgreicher Implementierung
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Temporärer Speicher für CSV-Daten (in Production würde man Redis/DB nutzen)
uploaded_mines_cache = {}

# ÄNDERUNG 28.06.2025: Cache für Batch-Ergebnisse zum Download
batch_results_cache = {}

# CSV Spaltendefinition für strukturierte Ausgabe
CSV_COLUMNS = [
    'ID', 'Name', 'Country', 'Region', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus',
    'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
]

# ÄNDERUNG 28.06.2025: Felder die KEINE Quellennummern brauchen
FIELDS_WITHOUT_SOURCES = [
    'ID',
    'Name',
    'Country', 
    'Region',
    'Quellenangaben'  # Die Quellenspalte selbst
]

# FastAPI App
app = FastAPI(
    title="MineSearch 2.0",
    description="Einfaches Mining-Recherche-System mit Perplexity API",
    version="2.0.0"
)

# Statische Dateien f�r Frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Request/Response Modelle
class MineSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    commodity: Optional[str] = None

class MineSearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()
    search_query: str

# Perplexity API Konfiguration aus config.py
PERPLEXITY_API_KEY = config.PERPLEXITY_API_KEY
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Root Route - serviert die HTML Seite
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Hauptseite mit Suchformular"""
    try:
        with open("../frontend/index.html", "rb") as f:
            content = f.read()
            # Versuche verschiedene Encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Fallback: Ignoriere fehlerhafte Zeichen
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Fehler beim Laden der HTML-Datei: {e}")
        return "<h1>Fehler beim Laden der Seite</h1>"

# Hilfsfunktionen für Namensverarbeitung
def normalize_accents(text: str) -> str:
    """Normalisiere französische Akzente für bessere Suche"""
    accent_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a', 'æ': 'ae', 'ã': 'a', 'å': 'a', 'ā': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ē': 'e', 'ė': 'e', 'ę': 'e',
        'î': 'i', 'ï': 'i', 'í': 'i', 'ī': 'i', 'į': 'i', 'ì': 'i',
        'ô': 'o', 'ö': 'o', 'ò': 'o', 'ó': 'o', 'œ': 'oe', 'ø': 'o', 'ō': 'o', 'õ': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ū': 'u', 'ů': 'u', 'ű': 'u', 'ŭ': 'u',
        'ç': 'c', 'ć': 'c', 'č': 'c', 'ĉ': 'c', 'ċ': 'c'
    }
    result = text
    for accented, normalized in accent_map.items():
        result = result.replace(accented, normalized)
        result = result.replace(accented.upper(), normalized.upper())
    return result

def get_country_config(country: str) -> Dict:
    """Hole länderspezifische Konfiguration"""
    if not country:
        return {}
    
    country_lower = country.lower()
    # Suche passende Konfiguration
    for country_key, config_data in config.COUNTRY_CONFIGS.items():
        if country_key.lower() in country_lower or country_lower in country_key.lower():
            return config_data
    
    # Standard-Fallback
    return {'languages': ['en'], 'currency': 'USD'}

def generate_multilingual_search_terms(mine_name: str, country: str = None) -> List[str]:
    """Generiere mehrsprachige Suchbegriffe basierend auf Land"""
    terms = []
    country_config = get_country_config(country) if country else {}
    
    # Hole Mining-Begriffe für das Land
    mining_terms = country_config.get('mining_terms', {})
    mine_words = mining_terms.get('mine', ['mine'])
    
    # Füge verschiedene Sprachvarianten hinzu
    for mine_word in mine_words:
        terms.append(f"{mine_word} {mine_name}")
        # Mit Akzenten und ohne
        normalized = normalize_accents(mine_name)
        if normalized != mine_name:
            terms.append(f"{mine_word} {normalized}")
    
    return terms

def generate_name_variants(mine_name: str) -> List[str]:
    """Generiere Suchvarianten für Minennamen"""
    variants = set()
    
    # Original Name
    variants.add(mine_name)
    
    # Normalisierte Version (ohne Akzente)
    normalized = normalize_accents(mine_name)
    if normalized != mine_name:
        variants.add(normalized)
    
    # Mit/ohne "Mine" Präfix
    if "Mine " in mine_name:
        without_mine = mine_name.replace("Mine ", "").strip()
        variants.add(without_mine)
        variants.add(normalize_accents(without_mine))
    elif "mine " in mine_name.lower():
        # Case-insensitive Entfernung
        import re
        without_mine = re.sub(r'\bmine\s+', '', mine_name, flags=re.IGNORECASE).strip()
        variants.add(without_mine)
    else:
        # Füge "Mine" hinzu
        with_mine = f"Mine {mine_name}"
        variants.add(with_mine)
        variants.add(f"mine {mine_name}")
    
    # Entferne Klammern und deren Inhalt (z.B. "Mine Name (Gold)")
    if "(" in mine_name and ")" in mine_name:
        without_brackets = re.sub(r'\s*\([^)]*\)', '', mine_name).strip()
        variants.add(without_brackets)
        variants.add(normalize_accents(without_brackets))
    
    return list(variants)

def extract_sources_from_content(content: str) -> List[Dict[str, str]]:
    """Extrahiere alle Quellen aus dem Content"""
    sources = []
    seen_values = set()
    
    # 1. Inline-Quellen im Format [Quelle: ...] oder [Source: ...]
    inline_patterns = [
        r'\[Quelle:\s*([^\]]+)\]',
        r'\[Source:\s*([^\]]+)\]',
        r'\(Quelle:\s*([^\)]+)\)',
        r'\(Source:\s*([^\)]+)\)'
    ]
    
    for pattern in inline_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            value = match.strip()
            if value and value not in seen_values:
                seen_values.add(value)
                # Prüfe ob es eine URL ist
                if 'http' in value.lower() or 'www.' in value.lower():
                    sources.append({'type': 'url', 'value': value})
                else:
                    sources.append({'type': 'document', 'value': value})
    
    # 2. Nummerierte Quellen am Ende [1], [2], etc.
    # ÄNDERUNG 28.06.2025: Verbesserte Extraktion nummerierter Quellen
    numbered_sources = re.findall(r'\[(\d+)\]\s*([^\n\[]+)', content)
    for num, source in numbered_sources:
        value = source.strip()
        # Entferne trailing Sonderzeichen
        value = value.rstrip('.,;:)]')
        # Filtere ungültige Einträge
        invalid_entries = ['', ' ', '...', 'k.A.', '[', ']', 'Perplexity Search']
        if value and value not in invalid_entries and value not in seen_values and len(value) > 10:
            seen_values.add(value)
            if 'http' in value.lower() or 'www.' in value.lower():
                # Validiere URL
                if re.match(r'https?://[^\s]+\.[^\s]+', value):
                    sources.append({'type': 'url', 'value': value})
            else:
                sources.append({'type': 'document', 'value': value})
    
    # 3. URL-Pattern (verbessert für verschiedene URL-Formate)
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    urls = re.findall(url_pattern, content)
    
    for url in urls:
        # Bereinige URL von trailing characters
        url = url.rstrip('.,;:)')
        if url not in seen_values:
            seen_values.add(url)
            sources.append({
                'type': 'url',
                'value': url,
                'context': _extract_context(content, url)
            })
    
    # 4. Dokument-Referenzen (NI 43-101, Annual Reports, etc.)
    doc_patterns = [
        r'(NI\s*43-101\s*(?:Technical\s+)?Report[^,\n]*)',
        r'(Annual\s+Report\s+\d{4}[^,\n]*)',
        r'((?:Environmental|Closure|Feasibility)\s+(?:Impact\s+)?(?:Assessment|Study|Report)[^,\n]*)',
        r'(SEDAR\s+(?:filing|document)[^,\n]*)',
        r'((?:Q\d|Year-end)\s+\d{4}\s+(?:Report|Results)[^,\n]*)',
        r'(Jahresbericht\s+\d{4}[^,\n]*)',
        r'(Umweltbericht[^,\n]*)',
        r'(Machbarkeitsstudie[^,\n]*)'
    ]
    
    for pattern in doc_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            value = match.strip()
            if value and len(value) > 5 and value not in seen_values:
                seen_values.add(value)
                sources.append({
                    'type': 'document',
                    'value': value,
                    'context': _extract_context(content, match)
                })
    
    # 5. Organisationen und Datenbanken
    org_patterns = [
        r'(?:according to|per|from|source:|quelle:|laut)\s+([A-Z][^,\n]{3,50})',
        r'((?:SEDAR|EDGAR|InfoMine|Mining\.com|S&P Global|Natural Resources Canada|USGS)[^,\n]*)'
    ]
    
    for pattern in org_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            value = match.strip()
            if value and len(value) > 3 and value not in seen_values:
                seen_values.add(value)
                sources.append({
                    'type': 'organization',
                    'value': value,
                    'context': _extract_context(content, match)
                })
    
    # 6. Quellen-Sektion am Ende des Contents
    # ÄNDERUNG 28.06.2025: Robustere Extraktion der QUELLEN-SEKTION
    quellen_patterns = [
        r'\*\*QUELLEN-SEKTION:\*\*(.*?)(?:\*\*|$)',
        r'QUELLEN[:\-\s]*\n(.*?)(?:\n\n|$)'
    ]
    
    for pattern in quellen_patterns:
        quellen_section = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if quellen_section:
            quellen_text = quellen_section.group(1)
            # Extrahiere nummerierte Quellen
            quellen_items = re.findall(r'\[(\d+)\]\s*([^\[\n]+)', quellen_text)
            for num, item in quellen_items:
                value = item.strip().rstrip('.,;:)]')
                if value and value not in seen_values and len(value) > 10:
                    # Überspringe ungültige Einträge
                    if any(invalid in value.lower() for invalid in ['k.a.', '...', 'keine ', 'nicht gefunden']):
                        continue
                    seen_values.add(value)
                    if value.startswith('http'):
                        if re.match(r'https?://[^\s]+\.[^\s]+', value):
                            sources.append({'type': 'url', 'value': value})
                    else:
                        sources.append({'type': 'document', 'value': value})
            break
    
    return sources

def _extract_context(content: str, target: str, context_length: int = 100) -> str:
    """Extrahiere Kontext um einen gefundenen Begriff"""
    index = content.find(target)
    if index == -1:
        return ""
    
    start = max(0, index - context_length)
    end = min(len(content), index + len(target) + context_length)
    
    context = content[start:end]
    # Bereinige Kontext
    context = ' '.join(context.split())
    
    return f"...{context}..."

def extract_source_numbers(text: str) -> List[int]:
    """Extrahiere Quellennummern aus Text wie [1], [2,3], [Quelle: 1]"""
    numbers = []
    
    # Pattern für [1], [2], [1,2,3] etc.
    matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', text)
    for match in matches:
        # Splitte bei Komma für multiple Quellen
        for num in match.split(','):
            try:
                numbers.append(int(num.strip()))
            except:
                pass
    
    # Pattern für [Quelle: 1], [Source: 2] etc.
    matches = re.findall(r'\[(?:Quelle|Source):\s*(\d+)\]', text, re.IGNORECASE)
    for match in matches:
        try:
            numbers.append(int(match))
        except:
            pass
    
    return sorted(list(set(numbers)))  # Entferne Duplikate und sortiere

def clean_extracted_value(value: str) -> str:
    """Bereinige extrahierte Werte von Markup und Quellen-Referenzen"""
    if not value:
        return value
    
    # Entferne ** Markierungen
    value = value.replace('**', '').strip()
    
    # Entferne [Quelle: ...] Referenzen
    value = re.sub(r'\[Quelle:[^\]]+\]', '', value).strip()
    
    # Entferne inline Quellen-Nummern wie [1], [2][3] etc.
    value = re.sub(r'\[\d+\](?:\[\d+\])*', '', value).strip()
    
    # ÄNDERUNG 28.06.2025: Entferne einzelne eckige Klammern und andere Reste
    value = re.sub(r'[\[\]]', '', value).strip()
    
    # Entferne führende/nachfolgende Sonderzeichen
    value = value.strip(' -.,;:')
    
    # Entferne mehrfache Leerzeichen
    value = ' '.join(value.split())
    
    return value

def extract_structured_data(content: str, mine_name: str, country: str = None) -> Dict[str, str]:
    """Extrahiere strukturierte Daten aus dem Perplexity-Response"""
    data = {col: '' for col in CSV_COLUMNS}
    data['Name'] = mine_name
    
    # Hole länderspezifische Währung
    country_config = get_country_config(country) if country else {}
    currency = country_config.get('currency', 'USD')
    
    # Patterns für verschiedene Datenfelder
    patterns = {
        'ID': [
            r'ID:\s*([^\n]+)',
            r'Kennziffer:\s*([^\n]+)',
            r'Nummer:\s*([^\n]+)',
            r'Reference:\s*([^\n]+)'
        ],
        'Country': [r'Land:\s*([^\n]+)', r'Country:\s*([^\n]+)', r'in\s+(\w+(?:\s+\w+)?)\s*(?:gelegen|liegt)'],
        'Region': [
            r'Region:\s*([^\n]+)', 
            r'Provinz:\s*([^\n]+)', 
            r'Province:\s*([^\n]+)', 
            r'in\s+(?:der\s+)?(?:Region|Provinz)\s+([^\n,]+)',
            r'in\s+(Quebec|Québec|Ontario|British Columbia|Alberta|Manitoba|Saskatchewan)[\s,]',
            r'(?:located\s+in|liegt\s+in)\s+(Quebec|Québec|Ontario|British Columbia|Alberta)[\s,]'
        ],
        'Betreiber': [
            r'Betreiber:\s*([^\n]+)', 
            r'Operator:\s*([^\n]+)', 
            r'betrieben\s+von\s+([^\n,]+)', 
            r'Eigentümer:\s*([^\n]+)',
            r'Owner:\s*([^\n]+)',
            r'(?:gehört|owned\s+by)\s+([^\n,]+)'
        ],
        'x-Koordinate': [r'Latitude:\s*([-\d.]+)', r'Lat:\s*([-\d.]+)', r'Breitengrad:\s*([-\d.]+)'],
        'y-Koordinate': [r'Longitude:\s*([-\d.]+)', r'Long?:\s*([-\d.]+)', r'Längengrad:\s*([-\d.]+)'],
        'Aktivitätsstatus': [
            r'Status:\s*([^\n]+)', 
            r'Aktivitätsstatus:\s*([^\n]+)', 
            r'(?:ist\s+)?(?:derzeit\s+)?(aktiv|geschlossen|stillgelegt|in Betrieb|geplant)',
            r'(Geplant[^,\n]*)',
            r'(Akquisition\s+abgeschlossen[^,\n]*)',
            r'(In\s+Entwicklung[^,\n]*)',
            r'(Explorationsphase[^,\n]*)',
            r'(Produktion\s+eingestellt[^,\n]*)',
            r'(Temporär\s+stillgelegt[^,\n]*)'
        ],
        'Restaurationskosten': [
            # Existierende Patterns für bereits bezahlte Kosten
            r'Restaurationskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'Sanierungskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'(?:Environmental\s+)?liabilities?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            r'Closure\s+costs?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            # Neue Patterns für geplante/zukünftige Kosten
            r'(?:geplante|geschätzte|estimated|planned|future)\s+(?:Restaurations|Sanierungs|restoration|remediation|closure)kosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
            r'(?:Restaurations|Sanierungs)kosten\s+(?:werden|sind)\s+(?:auf|geschätzt)\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'Rückstellungen?\s+(?:für\s+)?(?:Rekultivierung|Sanierung|Stilllegung):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'(?:Asset\s+)?(?:Retirement|Decommissioning)\s+Obligations?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            r'(?:provision|reserve)\s+for\s+(?:site\s+)?(?:restoration|remediation|closure):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?\s*(?:CAD|CDN)?',
            # Patterns für "budgetiert" oder "veranschlagt"
            r'(?:budgetiert|veranschlagt|budgeted|allocated)\s+für\s+(?:Restauration|Sanierung|restoration):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
            # Zusätzliche flexible Patterns
            r'(?:Umwelt|Environmental).*?(?:Kosten|costs|liabilities).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?',
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:für|for)\s+(?:Restauration|Sanierung|restoration|closure)',
            r'(?:Schätzung|estimate).*?(?:Restauration|Sanierung|closure).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?'
        ],
        'Jahr der Aufnahme der Kosten': [
            r'(?:Kosten|costs?)\s+(?:von|from|Stand)\s+(\d{4})', 
            r'(?:per|as\s+of)\s+(\d{4})',
            r'(?:Stand|status|as\s+of):\s*(?:\w+\s+)?(\d{4})',
            r'(\d{4})\s+(?:Kosten|costs|liabilities)'
        ],
        'Jahr der Erstellung des Dokumentes': [
            # ÄNDERUNG 28.06.2025: Strengere Jahr-Validierung (1900-2030)
            r'(?:Dokument|Report|Bericht)\s+(?:vom|von|dated|from)\s+(\b(?:19|20)\d{2}\b)',
            r'(?:Stand|Date|Datum):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
            r'(?:erstellt|created|prepared|published)\s+(?:im|in)?\s*(\b(?:19|20)\d{2}\b)',
            r'(\b(?:19|20)\d{2}\b)\s+(?:Report|Bericht|Document|Study)',
            r'(?:Veröffentlicht|Published|Released):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
            r'(?:Technical\s+Report|NI\s*43-101).*?(\b(?:19|20)\d{2}\b)',
            # Fallback für Jahr in Klammern
            r'(?:Report|Document|Bericht).*?\((\b(?:19|20)\d{2}\b)\)'
        ],
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': [
            r'Rohstoffe?:\s*([^\n]+)', 
            r'(?:produziert|fördert|abbaut)\s+([^\n]+(?:Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)[^\n]*)',
            r'Commodity:\s*([^\n]+)',
            r'Commodities:\s*([^\n]+)',
            r'Mineral(?:s|ien)?:\s*([^\n]+)',
            r'(?:haupt|main)\s*(?:rohstoff|commodity):\s*([^\n]+)'
        ],
        'Minentyp (Untertage/ Open-Pit/ usw.)': [
            r'Minentyp:\s*([^\n]+)', 
            r'Type:\s*([^\n]+)',
            r'((?:Open[- ]?Pit|Untertage|Underground|Tagebau)[^\n,]*)'
        ],
        'Produktionsstart': [r'Produktionsstart:\s*(\d{4})', r'Start:\s*(\d{4})', r'(?:in\s+Betrieb\s+seit|eröffnet)\s+(\d{4})'],
        'Produktionsende': [r'Produktionsende:\s*(\d{4})', r'Ende:\s*(\d{4})', r'geschlossen\s+(?:seit\s+)?(\d{4})'],
        'Fördermenge/Jahr': [
            r'Fördermenge:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
            r'Produktion:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
            r'produziert\s+(?:jährlich\s+)?([\d,]+(?:\.\d+)?)\s*([^\n]+)'
        ],
        'Fläche der Mine in qkm': [r'Fläche:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)', r'Area:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)']
    }
    
    # Extrahiere Daten mit Patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1)
                # Debug-Logging für wichtige Felder
                if field in ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']:
                    logger.debug(f"Pattern match für {field}: '{value}' (Pattern: {pattern[:50]}...)")
                # Spezielle Verarbeitung für Restaurationskosten
                if field == 'Restaurationskosten':
                    # Konvertiere zu CAD und formatiere
                    value = value.replace(',', '')
                    try:
                        amount = float(value)
                        # Wenn "Million" erwähnt wurde, multipliziere
                        if 'million' in match.group(0).lower() or 'mio' in match.group(0).lower():
                            amount *= 1_000_000
                        
                        # Prüfe ob es geplante/zukünftige Kosten sind
                        full_match = match.group(0).lower()
                        if any(word in full_match for word in ['geplant', 'geschätzt', 'estimated', 'planned', 
                                                               'future', 'budgetiert', 'veranschlagt', 
                                                               'rückstellung', 'provision', 'reserve']):
                            data[field] = f"${amount:,.0f} {currency} (geplant)"
                        else:
                            data[field] = f"${amount:,.0f} {currency}"
                    except:
                        data[field] = clean_extracted_value(value)
                else:
                    # Bereinige alle extrahierten Werte
                    data[field] = clean_extracted_value(value)
                break
    
    # Intelligentes Status-Mapping - nutze die detaillierte Beschreibung
    if data['Aktivitätsstatus']:
        status_text = data['Aktivitätsstatus']
        status_lower = status_text.lower()
        
        # Bestimme die Kategorie basierend auf dem Text
        if any(word in status_lower for word in ['aktiv', 'in betrieb', 'produziert', 'operating', 'active']):
            category = 'aktiv'
        elif any(word in status_lower for word in ['geplant', 'akquisition', 'entwicklung', 'exploration', 'planned', 'proposed']):
            category = 'geplant'
        elif any(word in status_lower for word in ['geschlossen', 'stillgelegt', 'eingestellt', 'closed', 'ceased']):
            category = 'geschlossen'
        elif any(word in status_lower for word in ['temporär', 'suspended', 'care and maintenance']):
            category = 'sonstiges'
        else:
            category = 'sonstiges'
        
        # Behalte die detaillierte Beschreibung, füge nur die Kategorie hinzu
        if len(status_text) > 20 and category != status_text.lower():
            data['Aktivitätsstatus'] = f"{status_text} ({category})"
        else:
            data['Aktivitätsstatus'] = category
    
    # Lösche die redundante Spalte - wir nutzen nur noch eine
    data.pop('Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)', None)
    
    # Intelligente Land/Region Trennung
    if data['Country'] and '(' in data['Country']:
        # Beispiel: "Kanada (Quebec)" → Country: Kanada, Region: Quebec
        match = re.match(r'^([^(]+)\s*\(([^)]+)\)', data['Country'])
        if match:
            country = match.group(1).strip()
            region = match.group(2).strip()
            data['Country'] = country
            # Nur setzen wenn Region noch leer ist
            if not data['Region']:
                data['Region'] = region
    
    # Bekannte Provinzen/Regionen zuordnen basierend auf Länderkonfiguration
    if data['Country'] and not data['Region']:
        country_lower = data['Country'].lower()
        content_lower = content.lower()
        
        # Suche passende Länderkonfiguration
        country_config = None
        for country_key in config.COUNTRY_CONFIGS:
            if country_key.lower() in country_lower or country_lower in country_key.lower():
                country_config = config.COUNTRY_CONFIGS[country_key]
                break
        
        # Wenn Länderkonfiguration gefunden, suche nach Regionen
        if country_config and 'regions' in country_config:
            for region in country_config['regions']:
                if region.lower() in content_lower:
                    data['Region'] = region
                    break
    
    # Extrahiere alle Quellen aus dem Content
    sources = extract_sources_from_content(content)
    
    # Sammle alle Quellen-Werte
    all_source_values = []
    
    # URLs zuerst
    source_urls = [s['value'] for s in sources if s['type'] == 'url']
    all_source_values.extend(source_urls)
    
    # Dann Dokumente
    source_docs = [s['value'] for s in sources if s['type'] == 'document']
    all_source_values.extend(source_docs)
    
    # Dann Organisationen
    source_orgs = [s['value'] for s in sources if s['type'] == 'organization']
    all_source_values.extend(source_orgs)
    
    # ÄNDERUNG 28.06.2025: Formatiere Quellen mit Nummerierung - aber filtere ungültige Einträge
    valid_source_values = []
    for source_value in all_source_values:
        # Filtere k.A., leere und ungültige Quellen aus
        if (source_value and 
            not any(skip in source_value.lower() for skip in 
                    ['k.a.', 'k.a', 'keine', 'nicht gefunden', 'nicht verfügbar', 
                     'perplexity search', '[quelle:', 'no specific'])):
            valid_source_values.append(source_value)
    
    if valid_source_values:
        # Erstelle nummerierte Liste nur mit validen Quellen
        numbered_sources = []
        for i, source_value in enumerate(valid_source_values, 1):
            numbered_sources.append(f"[{i}] {source_value}")
        data['Quellenangaben'] = '+++'.join(numbered_sources)
    else:
        data['Quellenangaben'] = 'Keine spezifischen Quellen dokumentiert'
    
    return data

def find_value_in_context(value: str, content: str, context_size: int = 200) -> List[Dict[str, Any]]:
    """
    Finde alle Vorkommen eines Wertes im Content mit Kontext
    """
    contexts = []
    value_lower = value.lower()
    content_lower = content.lower()
    
    # Finde alle Positionen des Wertes
    start = 0
    while True:
        pos = content_lower.find(value_lower, start)
        if pos == -1:
            break
        
        # Extrahiere Kontext
        context_start = max(0, pos - context_size)
        context_end = min(len(content), pos + len(value) + context_size)
        context = content[context_start:context_end]
        
        contexts.append({
            'position': pos,
            'context': context,
            'before': content[context_start:pos],
            'after': content[pos + len(value):context_end]
        })
        
        start = pos + 1
    
    return contexts

def find_sources_in_context(context: str, all_sources: List[Dict[str, Any]]) -> List[int]:
    """
    Finde Quellen-Referenzen in einem Kontext-String
    """
    found_sources = []
    context_lower = context.lower()
    
    # Suche nach Quellen-Keywords
    source_keywords = [
        'according to', 'per ', 'from ', 'source:', 'quelle:', 'laut ', 'gemäß ',
        'based on', 'as reported', 'states that', 'indicates', 'shows'
    ]
    
    # Prüfe jede Quelle
    for idx, source in enumerate(all_sources, 1):
        source_value = source['value'].lower()
        
        # Direkte Erwähnung der Quelle
        if source_value in context_lower:
            found_sources.append(idx)
            continue
        
        # Teilweise Übereinstimmung (für lange Quellennamen)
        if len(source_value) > 20:
            # Nimm die ersten bedeutsamen Wörter
            key_parts = source_value.split()[:3]
            if all(part in context_lower for part in key_parts):
                found_sources.append(idx)
                continue
        
        # Spezielle Patterns für Dokumente
        if source['type'] == 'document':
            # NI 43-101 Varianten
            if 'ni 43-101' in source_value and 'ni 43-101' in context_lower:
                found_sources.append(idx)
            # Annual Report Varianten
            elif 'annual report' in source_value and 'annual report' in context_lower:
                found_sources.append(idx)
            # Technical Report Varianten
            elif 'technical report' in source_value and 'technical report' in context_lower:
                found_sources.append(idx)
    
    # Prüfe auf Quellen-Keywords mit nachfolgenden Referenzen
    for keyword in source_keywords:
        if keyword in context_lower:
            # Extrahiere Text nach dem Keyword
            keyword_pos = context_lower.find(keyword)
            after_keyword = context_lower[keyword_pos + len(keyword):keyword_pos + len(keyword) + 100]
            
            # Suche nach Quellen in diesem Bereich
            for idx, source in enumerate(all_sources, 1):
                if idx not in found_sources:
                    source_short = source['value'][:30].lower()
                    if source_short in after_keyword:
                        found_sources.append(idx)
    
    return sorted(list(set(found_sources)))

def split_content_into_sections(content: str) -> List[Dict[str, Any]]:
    """
    Teile Content in logische Abschnitte basierend auf Struktur
    """
    sections = []
    
    # Erkenne Abschnittsgrenzen
    section_markers = [
        r'\n\n',  # Doppelte Zeilenumbrüche
        r'\n(?=According to)',  # Neue Quelle
        r'\n(?=Based on)',  # Neue Quelle
        r'\n(?=The [\w\s]+ report)',  # Report-Referenz
        r'\n(?=\d+\.)',  # Nummerierte Liste
        r'\n(?=[A-Z][^.!?]*:)',  # Überschriften mit Doppelpunkt
    ]
    
    # Kombiniere alle Marker
    combined_pattern = '|'.join(section_markers)
    
    # Splitte Content
    parts = re.split(combined_pattern, content)
    
    current_pos = 0
    for part in parts:
        if part.strip():
            sections.append({
                'content': part,
                'start': current_pos,
                'end': current_pos + len(part)
            })
        current_pos += len(part) + 2  # +2 für Trenner
    
    return sections

def extract_structured_data_with_sources(content: str, mine_name: str, country: str = None) -> Dict[str, Any]:
    """
    Extrahiere strukturierte Daten mit Quellenverfolgung
    Gibt zurück: {
        'data': {field: value},  # Bereinigte Werte für Anzeige
        'data_with_sources': {field: {'value': value, 'sources': [1,2,3]}},  # Mit Quellenreferenzen
        'source_index': {1: 'URL oder Dokumentname', 2: '...'}  # Quellen-Mapping
    }
    """
    # Hole normale strukturierte Daten
    data = extract_structured_data(content, mine_name, country)
    
    # Initialisiere erweiterte Datenstruktur
    data_with_sources = {}
    
    # Erstelle Quellen-Index mit gleicher Reihenfolge wie in extract_structured_data
    all_sources = extract_sources_from_content(content)
    source_index = {}
    
    # Sortiere Quellen nach Typ für konsistente Nummerierung
    # URLs zuerst
    source_urls = [s for s in all_sources if s['type'] == 'url']
    # Dann Dokumente
    source_docs = [s for s in all_sources if s['type'] == 'document']
    # Dann Organisationen
    source_orgs = [s for s in all_sources if s['type'] == 'organization']
    
    # Erstelle Index mit konsistenter Nummerierung
    idx = 1
    for source in source_urls + source_docs + source_orgs:
        source_index[idx] = source['value']
        idx += 1
    
    # ÄNDERUNG 28.06.2025: Debug-Logging
    logger.debug(f"Extrahiere Quellen für {mine_name}: {len(all_sources)} Quellen gefunden")
    
    # Prüfe ob Content nummerierte Quellen enthält
    has_numbered_sources = bool(re.search(r'\[\d+\]', content))
    
    # ÄNDERUNG 28.06.2025: Erstelle sortierte Quellenliste für Kontext-Analyse
    sorted_sources = source_urls + source_docs + source_orgs
    
    # Für jedes Feld: Finde zugehörige Quellennummern
    for field, value in data.items():
        # ÄNDERUNG 28.06.2025: Prüfe ob Feld Quellen braucht und ob echter Wert vorhanden
        needs_sources = (
            value and 
            value != '-' and
            field not in FIELDS_WITHOUT_SOURCES and
            value.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden', 'nicht verfügbar']
        )
        
        if needs_sources:
            source_numbers = []
            
            # STUFE 1: Explizite nummerierte Quellen
            if has_numbered_sources:
                # Escape special regex characters im Wert
                escaped_value = re.escape(value)
                
                # Verschiedene Pattern-Varianten für mehr Flexibilität
                patterns = []
                
                if re.match(r'[\d,.$]+', value):
                    # Für Zahlen: erlaube verschiedene Formatierungen
                    base_number = re.sub(r'[,$]', '', value)
                    patterns.extend([
                        rf'{re.escape(base_number)}[^\n]*?\[(\d+(?:,\s*\d+)*)\]',
                        rf'\[(\d+(?:,\s*\d+)*)\][^\n]*?{re.escape(base_number)}'
                    ])
                else:
                    # Für Text: verschiedene Muster
                    # Verkürze lange Werte für besseres Matching
                    search_value = escaped_value[:50] if len(escaped_value) > 50 else escaped_value
                    patterns.extend([
                        rf'{search_value}[^\n]*?\[(\d+(?:,\s*\d+)*)\]',
                        rf'\[(\d+(?:,\s*\d+)*)\][^\n]*?{search_value}'
                    ])
                    
                    # ÄNDERUNG 28.06.2025: Fix für Regex-Fehler - erst splitten, dann escapen
                    if ' ' in value:
                        try:
                            first_word = value.split()[0]
                            escaped_first_word = re.escape(first_word)
                            patterns.append(rf'{escaped_first_word}[^\n]*?\[(\d+(?:,\s*\d+)*)\]')
                        except Exception as e:
                            logger.debug(f"Konnte ersten Teil von '{value}' nicht extrahieren: {e}")
                
                # Versuche alle Patterns mit Fehlerbehandlung
                for pattern in patterns:
                    if pattern:
                        try:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Extrahiere alle Nummern aus dem Match
                                for num in match.split(','):
                                    try:
                                        source_num = int(num.strip())
                                        if source_num not in source_numbers and source_num <= len(all_sources):
                                            source_numbers.append(source_num)
                                    except ValueError:
                                        continue
                        except re.error as e:
                            logger.debug(f"Regex-Fehler für Pattern '{pattern[:50]}...': {e}")
                
                # Debug wenn keine Quellen gefunden
                if not source_numbers and field in ['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)', 'Betreiber', 'Restaurationskosten']:
                    logger.debug(f"Keine Quellennummern gefunden für {field}: '{value[:50]}...'")
            
            # STUFE 2: Kontext-basierte Zuordnung (wenn keine expliziten Quellen gefunden)
            if not source_numbers:
                contexts = find_value_in_context(value, content)
                for ctx in contexts[:3]:  # Analysiere max 3 Vorkommen
                    ctx_sources = find_sources_in_context(ctx['context'], sorted_sources)
                    source_numbers.extend(ctx_sources)
                
                # Entferne Duplikate
                source_numbers = sorted(list(set(source_numbers)))
            
            # STUFE 3: Abschnitts-basierte Zuordnung (wenn immer noch keine Quellen)
            if not source_numbers:
                sections = split_content_into_sections(content)
                for section in sections:
                    if value.lower() in section['content'].lower():
                        # Finde Quellen in diesem Abschnitt
                        section_sources = find_sources_in_context(section['content'], sorted_sources)
                        if section_sources:
                            source_numbers.extend(section_sources[:2])  # Max 2 pro Abschnitt
                            break
                
                # Entferne Duplikate
                source_numbers = sorted(list(set(source_numbers)))
            
            # STUFE 4: Intelligente Fallback-Strategie für wichtige Felder
            if not source_numbers:
                # Kritische Felder die Quellen brauchen
                critical_fields = [
                    'Restaurationskosten',
                    'Jahr der Aufnahme der Kosten',
                    'Jahr der Erstellung des Dokumentes',
                    'Betreiber',
                    'Aktivitätsstatus'
                ]
                
                if field in critical_fields and sorted_sources:
                    # Priorisiere relevante Quellen basierend auf Feldtyp
                    if 'kosten' in field.lower() or 'jahr' in field.lower():
                        # Für Finanzdaten: Priorisiere Reports und offizielle Dokumente
                        relevant_sources = []
                        for idx, src in enumerate(sorted_sources, 1):
                            if any(keyword in src['value'].lower() for keyword in 
                                   ['report', 'sedar', 'annual', 'financial', 'ni 43-101']):
                                relevant_sources.append(idx)
                        
                        if relevant_sources:
                            source_numbers = relevant_sources[:2]  # Top 2 relevante Quellen
                        else:
                            source_numbers = [1]  # Fallback auf erste Quelle
                    else:
                        # Für andere kritische Felder: Nimm erste Quelle
                        source_numbers = [1]
            
            # ÄNDERUNG 28.06.2025: Debug-Logging für finale Quellenzuordnung
            if source_numbers:
                logger.debug(f"Quellen für {field} '{value[:30]}...': {source_numbers}")
            
            # Speichere Wert mit Quellen
            data_with_sources[field] = {
                'value': value,
                'sources': sorted(list(set(source_numbers)))  # Entferne finale Duplikate
            }
        else:
            data_with_sources[field] = {
                'value': value or '',
                'sources': []
            }
    
    return {
        'data': data,
        'data_with_sources': data_with_sources,
        'source_index': source_index
    }

# Haupt-Such-Endpoint
@app.post("/api/search", response_model=MineSearchResponse)
async def search_mine(request: MineSearchRequest, model: str = "sonar-pro"):
    """
    Sucht nach Mining-Informationen �ber Perplexity API.
    Keine 33 Agenten, keine Event Loops, nur ein API Call.
    """
    if not PERPLEXITY_API_KEY:
        logger.error("Perplexity API Key nicht konfiguriert")
        raise HTTPException(status_code=500, detail="API Key nicht konfiguriert")
    
    # Generiere Namensvarianten für bessere Suchergebnisse
    name_variants = generate_name_variants(request.mine_name)
    logger.info(f"Suche mit Namensvarianten: {name_variants}")
    
    # Konstruiere erweiterte Suchanfrage
    primary_name = request.mine_name
    additional_names = [v for v in name_variants if v != primary_name]
    
    # Generiere mehrsprachige Suchbegriffe
    multilingual_terms = generate_multilingual_search_terms(request.mine_name, request.country)
    
    # Basis-Suchanfrage
    search_query = f"Finde Informationen über die Mine: {primary_name}"
    if additional_names:
        search_query += f" (auch bekannt als: {', '.join(additional_names[:2])})"
    
    # Füge mehrsprachige Begriffe hinzu wenn relevant
    if len(multilingual_terms) > 1:
        search_query += f" (Suchbegriffe: {', '.join(multilingual_terms[:3])})"
    
    if request.country:
        search_query += f" in {request.country}"
    
    if request.commodity:
        # Hole länderspezifische Rohstoff-Begriffe
        country_config = get_country_config(request.country)
        commodity_terms = country_config.get('mining_terms', {}).get('commodity', ['commodity'])
        search_query += f", die {request.commodity} abbaut ({'/'.join(commodity_terms)}: {request.commodity})"
    
    # Fokussierte Suche mit Schwerpunkt auf Finanzdaten und Quellen
    if model == "sonar-deep-research":
        # Bei Deep Research: Umfassende Suche mit Finanzfokus und Quellen
        # Hole länderspezifische Währung
        country_config = get_country_config(request.country)
        currency = country_config.get('currency', 'USD')
        search_query += f". WICHTIG: Suche NUR nach der spezifischen Mine '{primary_name}'! Ich benötige BESONDERS: 1) Restaurationskosten/Sanierungskosten in {currency}, 2) Umwelthaftung/Environmental liabilities, 3) Stilllegungskosten/Closure costs, 4) Rückstellungen für Rekultivierung. Außerdem: Betreiber, exakte Koordinaten, Rohstoffe, Produktionsdaten, Aktivitätsstatus, Fläche in km². KRITISCH: Finde und liste ALLE verfügbaren Quellen auf - Websites, Reports (besonders NI 43-101), Regierungsdatenbanken, SEDAR-Einträge, Umweltberichte, akademische Studien. Gib für JEDE Information die genaue Quelle mit URL an!"
    else:
        # Standard: Fokussierte Suche mit expliziter Quellenanfrage
        # Hole länderspezifische Währung
        country_config = get_country_config(request.country)
        currency = country_config.get('currency', 'USD')
        search_query += f". Ich benötige für die Mine '{primary_name}': 1) Betreiber, 2) Koordinaten, 3) Rohstoffe, 4) Status (aktiv/geschlossen), 5) WICHTIG: Restaurationskosten/Sanierungskosten in {currency} falls verfügbar, 6) Produktionsdaten. ZUSÄTZLICH: Sammle ALLE verfügbaren Quellen und URLs - offizielle Websites, Regierungsdatenbanken, Mining-Portale, technische Reports. Strukturiere die Antwort klar mit Überschriften und gib für jede Information die Quelle an."
    
    logger.info(f"Starte Suche: {request.mine_name} mit Modell: {model}")
    
    # Hole Modell-Konfiguration
    model_config = config.PERPLEXITY_MODELS.get(model, config.PERPLEXITY_MODELS[config.DEFAULT_MODEL])
    model_id = model_config["id"]
    timeout = model_config["timeout"]
    max_tokens = model_config["max_tokens"]
    
    try:
        # Ein einziger, sauberer API Call mit modell-spezifischem Timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                PERPLEXITY_API_URL,
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{
                        "role": "system",
                        "content": "Du bist ein Mining-Recherche-Experte. Antworte auf Deutsch mit STRUKTURIERTEN DATEN im folgenden Format:\n\n**GEFUNDENE DATEN FÜR [MINENNAME]:**\n- Name: [exakter Name] [Quelle: URL/Dokument]\n- Land: [Land] [Quelle: URL/Dokument]\n- Region: [Region/Provinz] [Quelle: URL/Dokument]\n- Betreiber: [Betreiber/Eigentümer] [Quelle: URL/Dokument]\n- Koordinaten: [Latitude, Longitude] [Quelle: URL/Dokument]\n- Status: [aktiv/geschlossen/geplant] [Quelle: URL/Dokument]\n- Rohstoffe: [Liste der Rohstoffe] [Quelle: URL/Dokument]\n- Minentyp: [Untertage/Open-Pit/etc] [Quelle: URL/Dokument]\n- Produktionsstart: [Jahr] [Quelle: URL/Dokument]\n- Produktionsende: [Jahr oder 'aktiv'] [Quelle: URL/Dokument]\n- Fördermenge: [Menge/Jahr mit Einheit] [Quelle: URL/Dokument]\n- Fläche: [in km²] [Quelle: URL/Dokument]\n- Restaurationskosten: [Betrag in CAD$ mit Jahr] [Quelle: URL/Dokument]\n\n**QUELLEN-SEKTION:**\n[Liste ALLE verwendeten Quellen nummeriert auf]\n[1] URL oder Dokumentname\n[2] URL oder Dokumentname\n[3] URL oder Dokumentname\n... etc.\n\n**KRITISCHE QUELLEN-REGELN:**\n1. JEDE einzelne Information MUSS mit [Quelle: ...] gekennzeichnet werden!\n2. Verwende [Quelle: Perplexity Search] wenn keine spezifische URL verfügbar ist\n3. Sammle ALLE verfügbaren Quellen:\n   • Offizielle Betreiber-Websites\n   • Regierungsdatenbanken (SEDAR, EDGAR, InfoMine)\n   • Mining-Fachportale (mining.com, mining-technology.com)\n   • Umweltberichte und Environmental Impact Assessments\n   • NI 43-101 Technical Reports\n   • Jahresberichte und Financial Statements\n   • Lokale Nachrichten und Pressemitteilungen\n4. KEINE Information ohne Quellenangabe!\n5. Liste am Ende ALLE gefundenen URLs und Dokumente nummeriert auf\n\nNutze 'k.A.' für nicht gefundene Daten. Gib NUR Informationen über die spezifisch angefragte Mine."
                    }, {
                        "role": "user",
                        "content": search_query
                    }],
                    "temperature": config.PERPLEXITY_TEMPERATURE,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Perplexity API Fehler: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"API Fehler: {response.text}"
                )
            
            result = response.json()
            
            # Extrahiere die Antwort
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                # Validiere die Antwort - prüfe ob es wirklich um die gesuchte Mine geht
                content_lower = content.lower()
                mine_name_lower = request.mine_name.lower()
                mine_name_normalized = normalize_accents(request.mine_name).lower()
                
                # Prüfe ob die gesuchte Mine im Inhalt erwähnt wird
                is_valid_result = (
                    mine_name_lower in content_lower or
                    mine_name_normalized in content_lower or
                    any(variant.lower() in content_lower for variant in name_variants[:3])
                )
                
                # Prüfe auf typische "nicht gefunden" Phrasen - aber nur wenn EXPLIZIT gesagt wird
                not_found_phrases = [
                    "keine mine mit diesem namen",
                    "konnte keine informationen finden",
                    "existiert nicht",
                    "wurde nicht gefunden"
                ]
                
                # Nur als "nicht gefunden" markieren wenn explizit gesagt UND Mine nicht erwähnt
                is_not_found = any(phrase in content_lower for phrase in not_found_phrases) and not is_valid_result
                
                # Wenn Mine nicht gefunden oder falsches Ergebnis
                if is_not_found or not is_valid_result:
                    logger.warning(f"Mine '{request.mine_name}' nicht gefunden oder falsches Ergebnis")
                    content = f"Keine spezifischen Informationen über die Mine '{request.mine_name}' gefunden. Die Suche lieferte keine eindeutigen Ergebnisse für diese spezifische Mine."
                
                # ÄNDERUNG 28.06.2025: Debug-Logging für Content-Analyse
                logger.debug(f"Content-Länge für {request.mine_name}: {len(content)} Zeichen")
                logger.debug(f"Erste 300 Zeichen: {content[:300]}...")
                
                # ÄNDERUNG 28.06.2025: Nutze erweiterte Datenextraktion mit Quellentracking
                extended_data = extract_structured_data_with_sources(content, request.mine_name, request.country)
                structured_data = extended_data['data']
                data_with_sources = extended_data['data_with_sources']
                source_index = extended_data['source_index']
                
                # Debug: Zähle gefüllte Felder
                filled_count = sum(1 for v in structured_data.values() if v and v != '-' and v != 'Keine spezifischen Quellen dokumentiert')
                logger.info(f"Strukturierte Daten für {request.mine_name}: {filled_count} von {len(structured_data)} Feldern gefüllt")
                
                # Extrahiere Quellen separat für weitere Verarbeitung
                extracted_sources = extract_sources_from_content(content)
                
                # Berechne Datenqualitäts-Metriken
                filled_fields = sum(1 for col in CSV_COLUMNS if structured_data.get(col) and col != 'Name')
                total_fields = len(CSV_COLUMNS) - 1  # Minus Name-Feld
                data_completeness = filled_fields / total_fields if total_fields > 0 else 0
                
                # Bestimme Qualitätsstufe
                if data_completeness >= 0.7:
                    quality_level = "Hoch"
                elif data_completeness >= 0.4:
                    quality_level = "Mittel"
                else:
                    quality_level = "Niedrig"
                
                return MineSearchResponse(
                    success=True,
                    data={
                        "content": content,
                        "mine_name": request.mine_name,
                        "structured_data": structured_data,
                        "structured_data_with_sources": data_with_sources,  # NEU: Daten mit Quellenreferenzen
                        "source_index": source_index,  # NEU: Quellen-Nummerierung
                        "sources": extracted_sources,  # Neu: Separate Quellenliste
                        "source_summary": {
                            "urls": len([s for s in extracted_sources if s['type'] == 'url']),
                            "documents": len([s for s in extracted_sources if s['type'] == 'document']),
                            "organizations": len([s for s in extracted_sources if s['type'] == 'organization']),
                            "total": len(extracted_sources)
                        },
                        "data_quality": {
                            "filled_fields": filled_fields,
                            "total_fields": total_fields,
                            "completeness_percentage": round(data_completeness * 100),
                            "quality_level": quality_level,
                            "missing_critical_fields": [col for col in ['Betreiber', 'Restaurationskosten in $ CAD', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'] 
                                                       if not structured_data.get(col)]
                        },
                        "search_metadata": {
                            "model_used": model,
                            "search_timestamp": datetime.now().isoformat()
                        },
                        "api_response": result,
                        "validated": is_valid_result and not is_not_found
                    },
                    search_query=search_query
                )
            else:
                raise ValueError("Keine Antwort von Perplexity API")
                
    except httpx.TimeoutException:
        logger.error(f"Timeout bei Perplexity API nach {timeout}s")
        return MineSearchResponse(
            success=False,
            error=f"Zeitüberschreitung bei der Suche nach {timeout} Sekunden. Bei Deep Research kann die Suche bis zu 30 Minuten dauern.",
            search_query=search_query
        )
    except Exception as e:
        logger.error(f"Fehler bei der Suche: {str(e)}")
        return MineSearchResponse(
            success=False,
            error=f"Fehler bei der Suche: {str(e)}",
            search_query=search_query
        )

# CSV Upload Endpoint
@app.post("/api/upload-csv")
async def upload_csv(csv_file: UploadFile = File(...)):
    """
    CSV Datei hochladen und analysieren.
    Erwartet Spalten: mine_name (Pflicht), country, commodity (optional)
    """
    if not csv_file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Nur CSV Dateien erlaubt")
    
    try:
        # Lese CSV Inhalt
        contents = await csv_file.read()
        text_content = contents.decode('utf-8-sig')  # Handle BOM
        
        # Erkenne Delimiter (Komma oder Semikolon)
        first_line = text_content.split('\n')[0]
        delimiter = ';' if ';' in first_line else ','
        logger.info(f"CSV Delimiter erkannt: '{delimiter}'")
        
        # Parse CSV mit erkanntem Delimiter
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        mines = []
        
        # Erkenne mögliche Spaltennamen
        first_row = next(csv_reader, None)
        if not first_row:
            raise ValueError("CSV ist leer")
            
        # Zurück zum Anfang
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        
        # Finde relevante Spalten (case-insensitive)
        columns = {k.lower(): k for k in first_row.keys()}
        
        # Mögliche Namen für die Mine-Spalte
        mine_column = None
        mine_possibilities = ['name', 'mine', 'mine_name', 'site', 'mine site', 'nom', 'nom de la mine', 'site minier', 'minenname']
        for possible in mine_possibilities:
            if possible.lower() in columns:
                mine_column = columns[possible.lower()]
                break
                
        # Mögliche Namen für Land
        country_column = None
        country_possibilities = ['country', 'land', 'pays', 'staat', 'país', 'negara']
        for possible in country_possibilities:
            if possible.lower() in columns:
                country_column = columns[possible.lower()]
                break
        
        # Mögliche Namen für Region - separat von Land
        region_column = None
        region_possibilities = ['region', 'province', 'provinz', 'état', 'bundesland', 
                               'territorio', 'wilayah', 'departamento', 'región']
        for possible in region_possibilities:
            if possible.lower() in columns:
                region_column = columns[possible.lower()]
                break
                
        # Mögliche Namen für Rohstoff
        commodity_column = None
        commodity_possibilities = ['commodity', 'rohstoff', 'rohstoffabbau', 'material', 'substance', 'mineral', 'produit', 'minerai', 'ressource']
        for possible in commodity_possibilities:
            if possible.lower() in columns:
                commodity_column = columns[possible.lower()]
                break
        
        if not mine_column:
            # Zeige verfügbare Spalten
            available = list(first_row.keys())
            raise ValueError(f"Keine Spalte für Minennamen gefunden. Verfügbare Spalten: {', '.join(available)}")
        
        logger.info(f"CSV Spalten gefunden - Mine: {mine_column}, Land: {country_column}, Region: {region_column}, Rohstoff: {commodity_column}")
        
        for row in csv_reader:
            # Hole Minennamen
            mine_name = row.get(mine_column, '').strip()
            if not mine_name:
                continue
                
            mine = {
                'mine_name': mine_name,
                'country': row.get(country_column, '').strip() if country_column else '',
                'region': row.get(region_column, '').strip() if region_column else '',
                'commodity': row.get(commodity_column, '').strip() if commodity_column else '',
                'all_data': row  # Speichere alle CSV-Daten für späteren Zugriff
            }
            mines.append(mine)
        
        if not mines:
            raise ValueError("Keine gültigen Minen in der CSV gefunden")
        
        # Generiere eine Session-ID und speichere die Minen mit Spalteninfo
        import uuid
        session_id = str(uuid.uuid4())
        uploaded_mines_cache[session_id] = {
            'mines': mines,
            'columns': list(first_row.keys()),
            'mine_column': mine_column,
            'country_column': country_column,
            'region_column': region_column,
            'commodity_column': commodity_column
        }
        logger.info(f"CSV mit {len(mines)} Minen in Session {session_id} gespeichert")
        
        # Erstelle Response mit Batch-Suche Formular
        html_response = f"""
        <div class="csv-info-card">
            <h3>✓ CSV erfolgreich geladen</h3>
            <p><strong>{len(mines)}</strong> Minen gefunden</p>
            
            <form id="batch-form" 
                  hx-post="/api/batch-search" 
                  hx-target="#results"
                  hx-indicator="#batch-loading">
                
                <input type="hidden" name="session_id" value="{session_id}">
                
                <div class="form-group">
                    <label>Anzahl zu suchender Minen:</label>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="number" 
                               name="count" 
                               min="1" 
                               max="{len(mines)}"
                               value="{min(5, len(mines))}"
                               style="width: 100px;">
                        <span>von {len(mines)} Minen</span>
                        <button type="submit" name="search_all" value="false" class="batch-search-button">
                            Suche starten
                        </button>
                        <button type="submit" name="search_all" value="true" class="batch-search-button">
                            Alle suchen
                        </button>
                    </div>
                </div>
            </form>
            
            <div id="batch-loading" class="htmx-indicator">
                <div class="spinner"></div>
                <p>Batch-Suche läuft...</p>
            </div>
            
            <details style="margin-top: 20px;">
                <summary>Erste 5 Minen anzeigen</summary>
                <ul>
                    {"".join([f"<li>{m['mine_name']} ({m['country'] or 'Kein Land'}) - {m['commodity'] or 'Kein Rohstoff'}</li>" for m in mines[:5]])}
                </ul>
            </details>
        </div>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        logger.error(f"Fehler beim CSV Upload: {e}")
        return HTMLResponse(
            content=f'<div class="result-card error"><h3>❌ Fehler beim Laden der CSV</h3><p>{str(e)}</p></div>'
        )

# Batch Search Endpoint
@app.post("/api/batch-search")
async def batch_search(
    session_id: str = Form(...),
    model: str = Form("sonar-pro"),
    search_type: str = Form("standard"),  # Neu: standard oder enhanced
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false")
):
    """
    Batch-Suche für mehrere Minen aus CSV.
    """
    try:
        # Hole Minen-Daten aus dem Cache
        if session_id not in uploaded_mines_cache:
            raise ValueError("Session abgelaufen. Bitte CSV erneut hochladen.")
        
        session_data = uploaded_mines_cache[session_id]
        mines = session_data['mines']
        columns = session_data['columns']
        logger.info(f"Batch-Suche für Session {session_id} mit {len(mines)} Minen")
        
        # Bestimme wie viele Minen gesucht werden
        if search_all == "true":
            mines_to_search = mines
        else:
            mines_to_search = mines[:count] if count else mines[:5]
        
        # Führe Suchen durch
        results = []
        errors = []
        
        for i, mine in enumerate(mines_to_search):
            logger.info(f"Batch-Suche {i+1}/{len(mines_to_search)}: {mine['mine_name']}")
            
            try:
                # Nutze existierende search_mine Funktion mit gewähltem Modell
                request = MineSearchRequest(**mine)
                
                # ÄNDERUNG 28.06.2025: Unterstützung für erweiterte Suche
                # Verwende IMMER das gewählte Modell
                if search_type == "enhanced" and model != "sonar-deep-research":
                    # 2-Phasen-Suche mit dem gewählten Modell
                    result = await enhanced_search(request, model=model)
                else:
                    # Normale Suche mit gewähltem Modell (auch für Deep Research)
                    result = await search_mine(request, model=model)
                
                if result.success:
                    results.append({
                        'mine': mine,
                        'data': result.data
                    })
                else:
                    errors.append({
                        'mine': mine,
                        'error': result.error
                    })
                    
                # Kleine Pause zwischen Requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                errors.append({
                    'mine': mine,
                    'error': str(e)
                })
        
        # ÄNDERUNG 28.06.2025: Speichere Ergebnisse im Cache für Download
        batch_results_cache[session_id] = {
            'results': results,
            'errors': errors,
            'timestamp': datetime.now(),
            'model': model,
            'columns': columns
        }
        
        # Erstelle CSV-Export aller Ergebnisse MIT Quellenreferenzen
        csv_export = ""
        csv_export_with_sources = ""
        if results:
            # Standard CSV ohne Quellen
            csv_lines = [";".join(CSV_COLUMNS)]  # Header
            
            # Erweiterte CSV mit Quellen
            extended_columns = []
            for col in CSV_COLUMNS:
                extended_columns.append(col)
                if col != 'Quellenangaben':  # Keine Quellen für Quellenangaben selbst
                    extended_columns.append(f"{col}_Quellen")
            csv_lines_with_sources = [";".join(extended_columns)]  # Erweiterter Header
            
            for r in results:
                if 'structured_data' in r['data']:
                    # Standard CSV Zeile
                    csv_line = ";".join([r['data']['structured_data'].get(col, '') for col in CSV_COLUMNS])
                    csv_lines.append(csv_line)
                    
                    # Erweiterte CSV Zeile mit Quellen
                    extended_values = []
                    for col in CSV_COLUMNS:
                        value = r['data']['structured_data'].get(col, '')
                        extended_values.append(value)
                        
                        # Füge Quellenreferenzen hinzu wenn vorhanden (außer für Quellenangaben selbst)
                        if col != 'Quellenangaben' and 'structured_data_with_sources' in r['data']:
                            source_data = r['data']['structured_data_with_sources'].get(col, {})
                            if source_data.get('sources'):
                                extended_values.append(f"[{','.join(map(str, source_data['sources']))}]")
                            else:
                                extended_values.append('')
                    
                    csv_lines_with_sources.append(";".join(extended_values))
            
            csv_export = f"""
            <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-radius: 5px;">
                <h4>📊 CSV-Export Standard (ohne Quellenreferenzen)</h4>
                <p>Kopieren Sie die folgenden Daten und fügen Sie sie in Excel ein:</p>
                <textarea style="width: 100%; height: 200px; font-family: monospace; font-size: 12px;" readonly>{chr(10).join(csv_lines)}</textarea>
            </div>
            """
            
            csv_export_with_sources = f"""
            <div style="margin: 20px 0; padding: 15px; background: #f0fff4; border-radius: 5px;">
                <h4>📊 CSV-Export Erweitert (mit Quellenreferenzen)</h4>
                <p>Diese Version enthält für jedes Feld die zugehörigen Quellennummern [1,2,3]:</p>
                <textarea style="width: 100%; height: 200px; font-family: monospace; font-size: 12px;" readonly>{chr(10).join(csv_lines_with_sources)}</textarea>
                <button onclick="navigator.clipboard.writeText(this.previousElementSibling.value)" style="margin-top: 10px; padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    📋 In Zwischenablage kopieren
                </button>
            </div>
            """
        
        # Erstelle HTML Response
        html_response = f"""
        <div class="batch-results">
            <h3>Batch-Suche abgeschlossen</h3>
            <p>✓ {len(results)} erfolgreich | ❌ {len(errors)} Fehler</p>
            
            <!-- ÄNDERUNG 28.06.2025: Download-Button hinzufügen -->
            <div style="margin: 20px 0;">
                <button onclick="downloadResults('{session_id}')" 
                        style="background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                    📥 Ergebnisse als CSV herunterladen
                </button>
                <script>
                    function downloadResults(sessionId) {{
                        window.location.href = '/api/download-results?session_id=' + sessionId;
                    }}
                </script>
            </div>
            
            {csv_export}
            {csv_export_with_sources}
            
            <div class="results-container">
                {"".join([create_result_card(r) for r in results])}
                {"".join([create_error_card(e) for e in errors])}
            </div>
        </div>
        """
        
        return HTMLResponse(content=html_response)
        
    except ValueError as e:
        logger.error(f"Wert-Fehler bei Batch-Suche: {e}")
        return HTMLResponse(
            content=f'<div class="result-card error"><h3>❌ Fehler bei Batch-Suche</h3><p>{str(e)}</p><p><small>Tipp: Laden Sie die CSV-Datei erneut hoch.</small></p></div>'
        )
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Batch-Suche: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<div class="result-card error"><h3>❌ Fehler bei Batch-Suche</h3><p>Ein unerwarteter Fehler ist aufgetreten: {str(e)}</p></div>'
        )

def create_result_card(result: Dict) -> str:
    """Erstelle HTML für ein Suchergebnis"""
    mine = result['mine']
    data = result['data']
    
    # Erstelle strukturierte Tabelle
    structured_html = ""
    if 'structured_data' in data:
        structured = data['structured_data']
        structured_html = """
        <h5>Extrahierte Daten:</h5>
        <table class="data-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Feld</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Wert</th>
            </tr>
        """
        
        # Definiere Finanzspalten für Hervorhebung
        finanz_spalten = ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']
        
        # ÄNDERUNG 28.06.2025: Verwende structured_data_with_sources für Quellennummern
        data_with_sources = data.get('structured_data_with_sources', {})
        
        # Zeige ALLE CSV-Spalten
        for field in CSV_COLUMNS:
            if field == 'ID':
                continue  # ID wird separat behandelt oder übersprungen
                
            value = structured.get(field, '-')
            sources_refs = ''
            
            # ÄNDERUNG 28.06.2025: Hole Quellennummern nur bei echten Infos und erlaubten Feldern
            if (field not in FIELDS_WITHOUT_SOURCES and 
                field in data_with_sources and
                value and 
                value != '-' and
                value.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden']):
                sources = data_with_sources[field].get('sources', [])
                if sources:
                    sources_refs = f' <span style="color: #6b7280; font-size: 0.85em;">[{",".join(map(str, sources))}]</span>'
            
            # Spezielle Formatierung für verschiedene Spaltentypen
            row_style = ''
            display_value = value
            
            # Finanzspalten gelb hinterlegen
            if field in finanz_spalten:
                row_style = 'style="background-color: #fef3c7;"'
                
                # Restaurationskosten rot hervorheben wenn vorhanden
                if field == 'Restaurationskosten' and value != '-' and value:
                    display_value = f'<span style="color: #dc2626; font-weight: bold;">{value}</span>'
                elif value == '-':
                    display_value = '<span style="color: #9ca3af; font-style: italic;">Keine Daten gefunden</span>'
            
            # Status farbig darstellen
            elif field == 'Aktivitätsstatus' and value != '-':
                if 'aktiv' in value.lower():
                    display_value = f'<span style="color: #10b981; font-weight: 500;">{value}</span>'
                elif 'geplant' in value.lower():
                    display_value = f'<span style="color: #f59e0b; font-weight: 500;">{value}</span>'
                elif 'geschlossen' in value.lower():
                    display_value = f'<span style="color: #ef4444; font-weight: 500;">{value}</span>'
            
            # Füge Quellennummern an (bereits in sources_refs vorbereitet)
            display_value += sources_refs
            
            structured_html += f"""
            <tr {row_style}>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>{field}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{display_value}</td>
            </tr>
            """
        
        structured_html += "</table>"
    
    # Quellen-Anzeige
    sources_html = ""
    if 'sources' in data and data['sources']:
        sources = data['sources']
        source_summary = data.get('source_summary', {})
        
        sources_html = f"""
        <h5 style="margin-top: 20px;">📚 Gefundene Quellen ({source_summary.get('total', 0)} insgesamt):</h5>
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px;">
        """
        
        # URLs
        url_sources = [s for s in sources if s['type'] == 'url']
        if url_sources:
            sources_html += "<strong>🌐 Websites:</strong><ul style='margin: 5px 0;'>"
            for source in url_sources[:5]:  # Max 5 URLs anzeigen
                sources_html += f"<li><a href='{source['value']}' target='_blank' style='color: #0066cc;'>{source['value']}</a></li>"
            if len(url_sources) > 5:
                sources_html += f"<li><em>... und {len(url_sources) - 5} weitere URLs</em></li>"
            sources_html += "</ul>"
        
        # Dokumente
        doc_sources = [s for s in sources if s['type'] == 'document']
        if doc_sources:
            sources_html += "<strong>📄 Dokumente:</strong><ul style='margin: 5px 0;'>"
            for source in doc_sources[:5]:
                sources_html += f"<li>{source['value']}</li>"
            if len(doc_sources) > 5:
                sources_html += f"<li><em>... und {len(doc_sources) - 5} weitere Dokumente</em></li>"
            sources_html += "</ul>"
        
        # Organisationen
        org_sources = [s for s in sources if s['type'] == 'organization']
        if org_sources:
            sources_html += "<strong>🏢 Organisationen/Datenbanken:</strong><ul style='margin: 5px 0;'>"
            for source in org_sources[:3]:
                sources_html += f"<li>{source['value']}</li>"
            if len(org_sources) > 3:
                sources_html += f"<li><em>... und {len(org_sources) - 3} weitere Organisationen</em></li>"
            sources_html += "</ul>"
        
        sources_html += "</div>"
    
    # CSV Download-Link
    csv_download = ""
    if 'structured_data' in data:
        # ÄNDERUNG 28.06.2025: Verwende | als Trennzeichen und füge Quellennummern hinzu
        csv_values = []
        data_with_sources = data.get('structured_data_with_sources', {})
        
        for col in CSV_COLUMNS:
            val = data['structured_data'].get(col, '')
            # Füge Quellennummern hinzu wenn vorhanden
            if col in data_with_sources and data_with_sources[col].get('sources'):
                sources = data_with_sources[col]['sources']
                val += f" [{','.join(map(str, sources))}]"
            csv_values.append(val)
        
        csv_line = "|".join(csv_values)
        csv_download = f"""
        <details style="margin-top: 10px;">
            <summary>CSV-Format (zum Kopieren)</summary>
            <pre style="font-size: 0.8em; background: #f5f5f5; padding: 10px; overflow-x: auto;">{csv_line}</pre>
        </details>
        """
    
    # Original-Antwort als Details
    original_content = f"""
    <details style="margin-top: 10px;">
        <summary>Vollständige Antwort anzeigen</summary>
        <pre style="font-size: 0.9em; max-height: 300px; overflow-y: auto;">{data.get('content', 'Keine Daten')}</pre>
    </details>
    """
    
    return f"""
    <div class="result-card success">
        <h4>✓ {mine['mine_name']}</h4>
        <div class="result-content">
            {structured_html}
            {sources_html}
            {csv_download}
            {original_content}
        </div>
    </div>
    """

def create_error_card(error: Dict) -> str:
    """Erstelle HTML für einen Fehler"""
    mine = error['mine']
    err = error['error']
    return f"""
    <div class="result-card error">
        <h4>❌ {mine['mine_name']}</h4>
        <p>Fehler: {err}</p>
    </div>
    """

# Zwei-Phasen-Suche Endpoint
@app.post("/api/enhanced-search")
async def enhanced_search(request: MineSearchRequest, model: str = Query("sonar-pro")):
    """
    Erweiterte Zwei-Phasen-Suche für umfangreichere Ergebnisse
    
    Phase 1: Basis-Suche mit Quellenfokus
    Phase 2: Vertiefung basierend auf gefundenen Quellen
    
    ÄNDERUNG 28.06.2025: Akzeptiert jetzt model Parameter für flexible Nutzung
    """
    logger.info(f"Starte erweiterte Zwei-Phasen-Suche für: {request.mine_name} mit Modell: {model}")
    
    # Phase 1: Initiale Suche mit Fokus auf Quellensammlung
    phase1_query = MineSearchRequest(
        mine_name=request.mine_name,
        country=request.country,
        commodity=request.commodity
    )
    
    phase1_result = await search_mine(phase1_query, model=model)
    
    if not phase1_result.success or not phase1_result.data:
        return phase1_result
    
    # Extrahiere gefundene Quellen
    sources = phase1_result.data.get('sources', [])
    
    # ÄNDERUNG 28.06.2025: Debug-Logging für Quellen
    logger.info(f"Phase 1 Quellen gefunden: {len(sources)}")
    for idx, src in enumerate(sources[:5]):  # Zeige erste 5 Quellen
        logger.debug(f"Quelle {idx+1}: {src['type']} - {src['value'][:50] if len(src['value']) > 50 else src['value']}")
    
    # Filtere valide Quellen - ÄNDERUNG 28.06.2025: Weniger restriktiv
    # Akzeptiere alle URLs und Dokumente mit mehr als 5 Zeichen
    valid_sources = [s for s in sources if 
        s['type'] == 'url' or 
        (s['type'] == 'document' and len(s['value']) > 5 and 
         not any(skip in s['value'].lower() for skip in ['k.a.', 'keine', 'nicht gefunden']))]
    
    if not valid_sources:
        logger.info(f"Keine validen Quellen für Phase 2 gefunden (von {len(sources)} total) - beende Suche")
        return phase1_result
    
    logger.info(f"Phase 1 abgeschlossen: {len(valid_sources)} valide Quellen für Phase 2")
    
    # Phase 2: Vertiefende Suche für Top-Quellen
    phase2_results = []
    
    # Priorisiere Quellen (arbeite mit validen Quellen)
    priority_sources = []
    
    # Priorisiere offizielle Dokumente
    doc_sources = [s for s in valid_sources if s['type'] == 'document' and any(
        keyword in s['value'].lower() for keyword in ['ni 43-101', 'annual report', 'environmental', 'closure']
    )]
    priority_sources.extend(doc_sources[:2])
    
    # Priorisiere Regierungsseiten
    gov_urls = [s for s in valid_sources if s['type'] == 'url' and any(
        domain in s['value'] for domain in ['sedar.com', '.gov', '.gc.ca', '.gov.au']
    )]
    priority_sources.extend(gov_urls[:2])
    
    # Priorisiere Mining-Portale
    mining_urls = [s for s in valid_sources if s['type'] == 'url' and any(
        domain in s['value'] for domain in ['mining.com', 'mining-technology.com', 'infomine.com']
    )]
    priority_sources.extend(mining_urls[:1])
    
    # Falls keine priorisierten gefunden, nimm die ersten validen
    if not priority_sources and valid_sources:
        priority_sources = valid_sources[:3]
    
    # Führe Phase 2 Suchen durch
    for i, source in enumerate(priority_sources[:3]):  # Max 3 vertiefte Suchen
        logger.info(f"Phase 2 - Suche {i+1}/3: {source['type']} - {source['value'][:50]}...")
        
        # Konstruiere spezifische Suchanfrage
        if source['type'] == 'document':
            phase2_query = f"Analysiere das Dokument '{source['value']}' für die Mine {request.mine_name}. Extrahiere besonders: Restaurationskosten, Umweltverbindlichkeiten, Produktionsdaten, technische Details."
        elif source['type'] == 'url':
            phase2_query = f"Besuche {source['value']} und finde spezifische Informationen über die Mine {request.mine_name}. Fokus auf: Finanzdaten, Umweltkosten, aktuelle Updates, technische Reports."
        else:
            phase2_query = f"Suche bei {source['value']} nach detaillierten Informationen über {request.mine_name}."
        
        try:
            # ÄNDERUNG 28.06.2025: Nutze das gleiche Modell wie Phase 1 (außer bei Deep Research)
            # Bei Deep Research nutze Standard-Modell für Phase 2 um Zeit zu sparen
            phase2_model = "sonar-pro" if model == "sonar-deep-research" else model
            model_config = config.PERPLEXITY_MODELS.get(phase2_model, config.PERPLEXITY_MODELS["sonar-pro"])
            
            async with httpx.AsyncClient(timeout=model_config["timeout"]) as client:
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers={
                        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_config["id"],
                        "messages": [{
                            "role": "system",
                            "content": "Du bist ein Mining-Recherche-Experte. Extrahiere spezifische Daten aus der angegebenen Quelle. WICHTIG: Gib JEDE Information mit [Quelle: ...] an! Verwende [Quelle: Perplexity Search] wenn keine spezifische URL verfügbar ist."
                        }, {
                            "role": "user",
                            "content": phase2_query
                        }],
                        "temperature": 0.1,
                        "max_tokens": model_config["max_tokens"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        content = result["choices"][0]["message"]["content"]
                        phase2_results.append({
                            "source": source,
                            "content": content
                        })
                
        except Exception as e:
            logger.error(f"Fehler in Phase 2 für Quelle {source['value'][:30]}: {e}")
        
        # Kleine Pause zwischen Requests
        await asyncio.sleep(0.5)
    
    # Kombiniere Ergebnisse
    combined_content = phase1_result.data['content']
    
    if phase2_results:
        combined_content += "\n\n**ERWEITERTE INFORMATIONEN AUS VERTIEFTER RECHERCHE:**\n\n"
        for i, result in enumerate(phase2_results):
            combined_content += f"\n### Quelle {i+1}: {result['source']['value'][:80]}...\n"
            combined_content += result['content'] + "\n"
    
    # Aktualisiere strukturierte Daten mit neuen Informationen
    enhanced_structured_data = extract_structured_data(combined_content, request.mine_name)
    
    # Extrahiere alle Quellen aus kombiniertem Content
    all_sources = extract_sources_from_content(combined_content)
    
    return MineSearchResponse(
        success=True,
        data={
            "content": combined_content,
            "mine_name": request.mine_name,
            "structured_data": enhanced_structured_data,
            "sources": all_sources,
            "source_summary": {
                "urls": len([s for s in all_sources if s['type'] == 'url']),
                "documents": len([s for s in all_sources if s['type'] == 'document']),
                "organizations": len([s for s in all_sources if s['type'] == 'organization']),
                "total": len(all_sources)
            },
            "search_phases": {
                "phase1_sources": len(sources),
                "phase2_searches": len(phase2_results),
                "total_content_length": len(combined_content)
            },
            "validated": True
        },
        search_query=f"Erweiterte Suche: {request.mine_name}"
    )

# ÄNDERUNG 28.06.2025: Download-Endpoint für CSV-Export
@app.get("/api/download-results")
async def download_results(session_id: str):
    """Download alle Suchergebnisse einer Session als CSV"""
    if session_id not in batch_results_cache:
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden. Bitte führen Sie zuerst eine Suche durch.")
    
    cache_data = batch_results_cache[session_id]
    results = cache_data['results']
    
    # CSV erstellen mit | als Trennzeichen
    output = io.StringIO()
    writer = csv.writer(output, delimiter='|', quoting=csv.QUOTE_MINIMAL)
    
    # Header schreiben
    writer.writerow(CSV_COLUMNS)
    
    # Für jedes Ergebnis eine Zeile
    for result in results:
        if result['data'].get('success', True) and 'structured_data' in result['data']:
            row = []
            structured_data = result['data']['structured_data']
            data_with_sources = result['data'].get('structured_data_with_sources', {})
            
            for col in CSV_COLUMNS:
                val = structured_data.get(col, '')
                
                # ÄNDERUNG 28.06.2025: Füge Quellennummern nur bei echten Infos und erlaubten Feldern
                if (col not in FIELDS_WITHOUT_SOURCES and 
                    col in data_with_sources and
                    val and 
                    val != '-' and
                    val.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden']):
                    sources = data_with_sources[col].get('sources', [])
                    if sources:
                        val += f" [{','.join(map(str, sources))}]"
                
                row.append(val)
            
            writer.writerow(row)
    
    # CSV-String holen
    csv_content = output.getvalue()
    output.close()
    
    # Als Download zurückgeben
    filename = f"minesearch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

# Favicon Route (verhindert 404 Fehler)
@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors"""
    return Response(status_code=204)  # No Content

# Chrome DevTools Route (verhindert 404 Fehler)
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    """Return empty JSON for Chrome DevTools"""
    return {"configVersion": 1.0, "configurations": []}

# Health Check
@app.get("/health")
async def health_check():
    """System Status Check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api_key_configured": bool(PERPLEXITY_API_KEY),
        "timestamp": datetime.now()
    }

# Lifespan Context Manager für moderne FastAPI Version
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisierung beim Start"""
    logger.info("MineSearch 2.0 gestartet")
    logger.info(f"Konfiguration: {config.get_summary()}")
    
    try:
        config.validate()
        logger.info("Konfiguration validiert - alle Systeme bereit")
    except ValueError as e:
        logger.error(f"Konfigurationsfehler: {e}")
        logger.warning("System startet trotzdem - bitte Konfiguration prüfen!")
    
    yield
    
    # Cleanup beim Shutdown
    logger.info("MineSearch 2.0 beendet")

# App mit Lifespan erstellen
app.router.lifespan_context = lifespan

# Smart-Search Endpoint mit automatischem Fallback
@app.post("/api/smart-search")
async def smart_search(request: MineSearchRequest, auto_upgrade: bool = True):
    """
    Intelligente Suche mit automatischem Modell-Upgrade bei schlechten Ergebnissen
    
    1. Startet mit schnellem Modell (sonar)
    2. Wenn Datenqualität < 40%: Automatisch Standard-Modell (sonar-pro)
    3. Transparente Rückmeldung über Suchverlauf
    """
    search_history = []
    
    # Phase 1: Schnelle Suche
    logger.info(f"Smart-Search Phase 1: Schnelle Suche für {request.mine_name}")
    phase1_result = await search_mine(request, model="sonar")
    search_history.append({
        "phase": 1,
        "model": "sonar",
        "model_name": "Schnell",
        "duration": "30 Sekunden"
    })
    
    if not phase1_result.success or not phase1_result.data:
        return phase1_result
    
    # Prüfe Datenqualität
    data_quality = phase1_result.data.get('data_quality', {})
    completeness = data_quality.get('completeness_percentage', 0)
    
    # Phase 2: Automatisches Upgrade wenn nötig und erlaubt
    if auto_upgrade and completeness < 40:
        logger.info(f"Smart-Search Phase 2: Datenqualität nur {completeness}% - Upgrade auf Standard-Modell")
        
        # Informiere Frontend über Upgrade
        phase1_result.data['search_status'] = {
            "upgrading": True,
            "reason": f"Nur {completeness}% der Daten gefunden",
            "next_model": "Standard (60 Sekunden)"
        }
        
        # Führe erweiterte Suche durch
        phase2_result = await search_mine(request, model="sonar-pro")
        search_history.append({
            "phase": 2,
            "model": "sonar-pro",
            "model_name": "Standard",
            "duration": "60 Sekunden",
            "reason": "Automatisches Upgrade wegen niedriger Datenqualität"
        })
        
        if phase2_result.success and phase2_result.data:
            # Füge Suchverlauf hinzu
            phase2_result.data['search_history'] = search_history
            phase2_result.data['search_summary'] = f"Suche automatisch erweitert: Schnell → Standard (Datenqualität verbessert von {completeness}% auf {phase2_result.data.get('data_quality', {}).get('completeness_percentage', 0)}%)"
            return phase2_result
    
    # Füge Suchverlauf zur ursprünglichen Antwort hinzu
    phase1_result.data['search_history'] = search_history
    if completeness < 40:
        phase1_result.data['recommendation'] = "Empfehlung: Verwenden Sie die erweiterte Suche oder Deep Research für bessere Ergebnisse"
    
    return phase1_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=config.DEBUG)