"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: MineSearch 2.0 - Radikal vereinfachtes Mining-Recherche-System
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Temporärer Speicher für CSV-Daten (in Production würde man Redis/DB nutzen)
uploaded_mines_cache = {}

# CSV Spaltendefinition für strukturierte Ausgabe
CSV_COLUMNS = [
    'ID', 'Name', 'Country', 'Region', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus', 
    'Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)',
    'Restaurationskosten in $ CAD', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
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
    seen_urls = set()
    
    # URL-Pattern (verbessert für verschiedene URL-Formate)
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    urls = re.findall(url_pattern, content)
    
    for url in urls:
        # Bereinige URL von trailing characters
        url = url.rstrip('.,;:)')
        if url not in seen_urls:
            seen_urls.add(url)
            sources.append({
                'type': 'url',
                'value': url,
                'context': _extract_context(content, url)
            })
    
    # Dokument-Referenzen (NI 43-101, Annual Reports, etc.)
    doc_patterns = [
        r'(NI\s*43-101\s*(?:Technical\s+)?Report[^,\n]*)',
        r'(Annual\s+Report\s+\d{4}[^,\n]*)',
        r'((?:Environmental|Closure|Feasibility)\s+(?:Impact\s+)?(?:Assessment|Study|Report)[^,\n]*)',
        r'(SEDAR\s+(?:filing|document)[^,\n]*)',
        r'((?:Q\d|Year-end)\s+\d{4}\s+(?:Report|Results)[^,\n]*)'
    ]
    
    for pattern in doc_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match.strip() and len(match) > 5:
                sources.append({
                    'type': 'document',
                    'value': match.strip(),
                    'context': _extract_context(content, match)
                })
    
    # Organisationen und Datenbanken
    org_patterns = [
        r'(?:according to|per|from|source:|quelle:)\s+([A-Z][^,\n]{3,50})',
        r'((?:SEDAR|EDGAR|InfoMine|Mining\.com|S&P Global)[^,\n]*)',
        r'((?:Natural Resources Canada|USGS|Mining Association)[^,\n]*)'
    ]
    
    for pattern in org_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match.strip() and len(match) > 3:
                sources.append({
                    'type': 'organization',
                    'value': match.strip(),
                    'context': _extract_context(content, match)
                })
    
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

def extract_structured_data(content: str, mine_name: str) -> Dict[str, str]:
    """Extrahiere strukturierte Daten aus dem Perplexity-Response"""
    data = {col: '' for col in CSV_COLUMNS}
    data['Name'] = mine_name
    
    # Patterns für verschiedene Datenfelder
    patterns = {
        'Country': [r'Land:\s*([^\n]+)', r'Country:\s*([^\n]+)', r'in\s+(\w+(?:\s+\w+)?)\s*(?:gelegen|liegt)'],
        'Region': [r'Region:\s*([^\n]+)', r'Provinz:\s*([^\n]+)', r'Province:\s*([^\n]+)', r'in\s+(?:der\s+)?(?:Region|Provinz)\s+([^\n,]+)'],
        'Betreiber': [r'Betreiber:\s*([^\n]+)', r'Operator:\s*([^\n]+)', r'betrieben\s+von\s+([^\n,]+)', r'Eigentümer:\s*([^\n]+)'],
        'x-Koordinate': [r'Latitude:\s*([-\d.]+)', r'Lat:\s*([-\d.]+)', r'Breitengrad:\s*([-\d.]+)'],
        'y-Koordinate': [r'Longitude:\s*([-\d.]+)', r'Long?:\s*([-\d.]+)', r'Längengrad:\s*([-\d.]+)'],
        'Aktivitätsstatus': [r'Status:\s*([^\n]+)', r'Aktivitätsstatus:\s*([^\n]+)', r'(?:ist\s+)?(?:derzeit\s+)?(aktiv|geschlossen|stillgelegt|in Betrieb)'],
        'Restaurationskosten in $ CAD': [
            r'Restaurationskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'Sanierungskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
            r'(?:Environmental\s+)?liabilities?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
            r'Closure\s+costs?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?'
        ],
        'Jahr der Aufnahme der Kosten': [r'(?:Kosten|costs?)\s+(?:von|from|Stand)\s+(\d{4})', r'(?:per|as\s+of)\s+(\d{4})'],
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': [
            r'Rohstoffe?:\s*([^\n]+)', 
            r'(?:produziert|fördert|abbaut)\s+([^\n]+(?:Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)[^\n]*)',
            r'Commodity:\s*([^\n]+)'
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
                # Spezielle Verarbeitung für Restaurationskosten
                if field == 'Restaurationskosten in $ CAD':
                    # Konvertiere zu CAD und formatiere
                    value = value.replace(',', '')
                    try:
                        amount = float(value)
                        # Wenn "Million" erwähnt wurde, multipliziere
                        if 'million' in match.group(0).lower() or 'mio' in match.group(0).lower():
                            amount *= 1_000_000
                        data[field] = f"${amount:,.0f} CAD"
                    except:
                        data[field] = value
                else:
                    data[field] = value.strip()
                break
    
    # Status-Mapping
    if data['Aktivitätsstatus']:
        status_lower = data['Aktivitätsstatus'].lower()
        if 'aktiv' in status_lower or 'in betrieb' in status_lower:
            data['Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)'] = 'aktiv'
        elif 'geschlossen' in status_lower or 'stillgelegt' in status_lower:
            data['Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)'] = 'geschlossen'
        elif 'geplant' in status_lower:
            data['Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)'] = 'geplant'
        else:
            data['Aktivitätsstatus (aktiv/ geplant/ geschlossen/ sonstiges)'] = 'sonstiges'
    
    # Extrahiere alle Quellen aus dem Content
    sources = extract_sources_from_content(content)
    
    # Formatiere Quellen für CSV
    source_urls = [s['value'] for s in sources if s['type'] == 'url']
    source_docs = [s['value'] for s in sources if s['type'] == 'document']
    source_orgs = [s['value'] for s in sources if s['type'] == 'organization']
    
    # Kombiniere alle Quellen
    all_sources = []
    if source_urls:
        all_sources.append(f"URLs: {'; '.join(source_urls[:5])}")  # Max 5 URLs
    if source_docs:
        all_sources.append(f"Dokumente: {'; '.join(source_docs[:3])}")  # Max 3 Docs
    if source_orgs:
        all_sources.append(f"Organisationen: {'; '.join(source_orgs[:3])}")  # Max 3 Orgs
    
    data['Quellenangaben'] = ' | '.join(all_sources) if all_sources else 'Keine spezifischen Quellen gefunden'
    
    return data

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
    
    search_query = f"Finde Informationen über die Mine: {primary_name}"
    if additional_names:
        search_query += f" (auch bekannt als: {', '.join(additional_names[:2])})"
    
    if request.country:
        search_query += f" in {request.country}"
        # Füge Quebec/Kanada hinzu wenn relevant
        if request.country.lower() in ['canada', 'kanada', 'quebec', 'québec']:
            search_query += " (Quebec, Kanada)"
    
    if request.commodity:
        search_query += f", die {request.commodity} abbaut"
    
    # Fokussierte Suche mit Schwerpunkt auf Finanzdaten und Quellen
    if model == "sonar-deep-research":
        # Bei Deep Research: Umfassende Suche mit Finanzfokus und Quellen
        search_query += f". WICHTIG: Suche NUR nach der spezifischen Mine '{primary_name}'! Ich benötige BESONDERS: 1) Restaurationskosten/Sanierungskosten in CAD$, 2) Umwelthaftung/Environmental liabilities, 3) Stilllegungskosten/Closure costs, 4) Rückstellungen für Rekultivierung. Außerdem: Betreiber, exakte Koordinaten, Rohstoffe, Produktionsdaten, Aktivitätsstatus, Fläche in km². KRITISCH: Finde und liste ALLE verfügbaren Quellen auf - Websites, Reports (besonders NI 43-101), Regierungsdatenbanken, SEDAR-Einträge, Umweltberichte, akademische Studien. Gib für JEDE Information die genaue Quelle mit URL an!"
    else:
        # Standard: Fokussierte Suche mit expliziter Quellenanfrage
        search_query += f". Ich benötige für die Mine '{primary_name}': 1) Betreiber, 2) Koordinaten, 3) Rohstoffe, 4) Status (aktiv/geschlossen), 5) WICHTIG: Restaurationskosten/Sanierungskosten in CAD$ falls verfügbar, 6) Produktionsdaten. ZUSÄTZLICH: Sammle ALLE verfügbaren Quellen und URLs - offizielle Websites, Regierungsdatenbanken, Mining-Portale, technische Reports. Strukturiere die Antwort klar mit Überschriften und gib für jede Information die Quelle an."
    
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
                        "content": "Du bist ein Mining-Recherche-Experte. Antworte auf Deutsch mit STRUKTURIERTEN DATEN im folgenden Format:\n\n**GEFUNDENE DATEN FÜR [MINENNAME]:**\n- Name: [exakter Name]\n- Land: [Land]\n- Region: [Region/Provinz]\n- Betreiber: [Betreiber/Eigentümer]\n- Koordinaten: [Latitude, Longitude]\n- Status: [aktiv/geschlossen/geplant]\n- Rohstoffe: [Liste der Rohstoffe]\n- Minentyp: [Untertage/Open-Pit/etc]\n- Produktionsstart: [Jahr]\n- Produktionsende: [Jahr oder 'aktiv']\n- Fördermenge: [Menge/Jahr mit Einheit]\n- Fläche: [in km²]\n- Restaurationskosten: [Betrag in CAD$ mit Jahr]\n- Quellen: [URLs oder Referenzen]\n\n**WICHTIG FÜR QUELLEN:**\n- Sammle ALLE verfügbaren Quellen und URLs!\n- Suche besonders nach:\n  • Offizielle Betreiber-Websites\n  • Regierungsdatenbanken (SEDAR, EDGAR, InfoMine)\n  • Mining-Fachportale (mining.com, mining-technology.com)\n  • Umweltberichte und Environmental Impact Assessments\n  • NI 43-101 Technical Reports\n  • Jahresberichte und Financial Statements\n  • Lokale Nachrichten und Pressemitteilungen\n  • Akademische Studien und Forschungsberichte\n- Gib für JEDE Information die spezifische Quelle an!\n- Liste am Ende ALLE gefundenen URLs und Dokumente auf\n\nNutze 'k.A.' für nicht gefundene Daten. Gib NUR Informationen über die spezifisch angefragte Mine."
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
                
                # Extrahiere strukturierte Daten
                structured_data = extract_structured_data(content, request.mine_name)
                
                # Extrahiere Quellen separat für weitere Verarbeitung
                extracted_sources = extract_sources_from_content(content)
                
                return MineSearchResponse(
                    success=True,
                    data={
                        "content": content,
                        "mine_name": request.mine_name,
                        "structured_data": structured_data,
                        "sources": extracted_sources,  # Neu: Separate Quellenliste
                        "source_summary": {
                            "urls": len([s for s in extracted_sources if s['type'] == 'url']),
                            "documents": len([s for s in extracted_sources if s['type'] == 'document']),
                            "organizations": len([s for s in extracted_sources if s['type'] == 'organization']),
                            "total": len(extracted_sources)
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
                
        # Mögliche Namen für Land/Region  
        country_column = None
        country_possibilities = ['country', 'land', 'pays', 'region', 'province', 'staat', 'état', 'territoire']
        for possible in country_possibilities:
            if possible.lower() in columns:
                country_column = columns[possible.lower()]
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
        
        logger.info(f"CSV Spalten gefunden - Mine: {mine_column}, Land: {country_column}, Rohstoff: {commodity_column}")
        
        for row in csv_reader:
            # Hole Minennamen
            mine_name = row.get(mine_column, '').strip()
            if not mine_name:
                continue
                
            mine = {
                'mine_name': mine_name,
                'country': row.get(country_column, '').strip() if country_column else '',
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
                    <label for="model">Such-Modell auswählen:</label>
                    <select name="model" id="model" style="width: 100%; padding: 10px; margin-bottom: 15px;">
                        <option value="sonar">Schnelle Suche - für einfache Anfragen</option>
                        <option value="sonar-pro" selected>Erweiterte Suche (Empfohlen) - beste Balance</option>
                        <option value="sonar-deep-research">Tiefenrecherche - umfassend (30+ Min)</option>
                        <option value="sonar-reasoning-pro">Analyse mit Reasoning - für komplexe Fälle</option>
                    </select>
                    <small id="model-warning" style="color: #dc2626; display: none;">
                        ⚠️ Tiefenrecherche kann 30+ Minuten pro Mine dauern!
                    </small>
                </div>
                
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
            
            <script>
                // Zeige Warnung bei Deep Research
                document.getElementById('model').addEventListener('change', function() {{
                    const warning = document.getElementById('model-warning');
                    if (this.value === 'sonar-deep-research') {{
                        warning.style.display = 'block';
                    }} else {{
                        warning.style.display = 'none';
                    }}
                }});
            </script>
            
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
                if search_type == "enhanced":
                    result = await enhanced_search(request)
                else:
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
        
        # Erstelle CSV-Export aller Ergebnisse
        csv_export = ""
        if results:
            csv_lines = [";".join(CSV_COLUMNS)]  # Header
            for r in results:
                if 'structured_data' in r['data']:
                    csv_line = ";".join([r['data']['structured_data'].get(col, '') for col in CSV_COLUMNS])
                    csv_lines.append(csv_line)
            
            csv_export = f"""
            <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-radius: 5px;">
                <h4>📊 CSV-Export aller Ergebnisse</h4>
                <p>Kopieren Sie die folgenden Daten und fügen Sie sie in Excel ein:</p>
                <textarea style="width: 100%; height: 200px; font-family: monospace; font-size: 12px;" readonly>{chr(10).join(csv_lines)}</textarea>
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
            
            {csv_export}
            
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
        
        # Prioritäre Felder zuerst anzeigen
        priority_fields = [
            'Name', 'Country', 'Region', 'Betreiber', 
            'Aktivitätsstatus', 'Restaurationskosten in $ CAD',
            'Jahr der Aufnahme der Kosten', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
            'x-Koordinate', 'y-Koordinate'
        ]
        
        # Zeige prioritäre Felder
        for field in priority_fields:
            if field in structured and structured[field]:
                value = structured[field]
                # Hervorhebung für Restaurationskosten
                style = 'style="background-color: #fffacd;"' if 'Restaurationskosten' in field else ''
                structured_html += f"""
                <tr {style}>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{field}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{value}</td>
                </tr>
                """
        
        # Zeige restliche Felder
        for field, value in structured.items():
            if field not in priority_fields and value:
                structured_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{field}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{value}</td>
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
        csv_line = ";".join([data['structured_data'].get(col, '') for col in CSV_COLUMNS])
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
async def enhanced_search(request: MineSearchRequest, model: str = "sonar-pro"):
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
    
    if not sources:
        logger.info("Keine Quellen in Phase 1 gefunden - beende Suche")
        return phase1_result
    
    logger.info(f"Phase 1 abgeschlossen: {len(sources)} Quellen gefunden")
    
    # Phase 2: Vertiefende Suche für Top-Quellen
    phase2_results = []
    
    # Priorisiere Quellen
    priority_sources = []
    
    # Priorisiere offizielle Dokumente
    doc_sources = [s for s in sources if s['type'] == 'document' and any(
        keyword in s['value'].lower() for keyword in ['ni 43-101', 'annual report', 'environmental', 'closure']
    )]
    priority_sources.extend(doc_sources[:2])
    
    # Priorisiere Regierungsseiten
    gov_urls = [s for s in sources if s['type'] == 'url' and any(
        domain in s['value'] for domain in ['sedar.com', '.gov', '.gc.ca', '.gov.au']
    )]
    priority_sources.extend(gov_urls[:2])
    
    # Priorisiere Mining-Portale
    mining_urls = [s for s in sources if s['type'] == 'url' and any(
        domain in s['value'] for domain in ['mining.com', 'mining-technology.com', 'infomine.com']
    )]
    priority_sources.extend(mining_urls[:1])
    
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
                            "content": "Du bist ein Mining-Recherche-Experte. Extrahiere spezifische Daten aus der angegebenen Quelle."
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=config.DEBUG)