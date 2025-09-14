"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Basis-Konfiguration für MineSearch
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from minesearch.config.api_keys import APIKeysConfig
from minesearch.config.providers import PROVIDERS_CONFIG
from minesearch.config.models import MODELS_CONFIG

# CSV-Spalten Definition
# ÄNDERUNG 13.07.2025: ID-Feld entfernt - wird systemseitig generiert, nicht aus Quellen extrahiert
CSV_COLUMNS = [
    'Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus',
    'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
]

# Felder die KEINE Quellennummern brauchen
# ÄNDERUNG 13.07.2025: ID entfernt da nicht mehr in CSV_COLUMNS
FIELDS_WITHOUT_SOURCES = [
    'Name', 'Country', 'Region', 'Eigentümer', 'Quellenangaben'
]

# Lade Umgebungsvariablen
# Bevorzuge Root-.env, fallback auf package-lokale .env; schließlich Systemumgebung
from dotenv import find_dotenv
root_env = Path(__file__).resolve().parents[3] / '.env'
local_env = Path(__file__).resolve().parents[1] / '.env'
if root_env.exists():
    load_dotenv(root_env)
elif local_env.exists():
    load_dotenv(local_env)
else:
    # Letzter Versuch: automatische Suche im Projekt
    auto_env = find_dotenv(usecwd=True)
    if auto_env:
        load_dotenv(auto_env)

class Config(APIKeysConfig):
    """Zentrale Konfigurationsklasse - KISS Prinzip"""
    
    # Server Einstellungen - configured for Replit environment
    HOST = os.getenv('HOST', '0.0.0.0')  # Frontend on port 5000, bind to all interfaces
    PORT = int(os.getenv('PORT', 5000))  # Use port 5000 for frontend access
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'  # Enable debug for development
    
    # Datenbank: URL bevorzugt; falls nicht vorhanden, aus DATABASE_PATH ableiten
    _ROOT = Path(__file__).resolve().parents[3]
    _db_url_env = os.getenv('DATABASE_URL')
    if _db_url_env and _db_url_env.strip():
        DATABASE_URL = _db_url_env
    else:
        # FIX: Korrigierter DB-Pfad nach Codebase-Bereinigung
        _db_path = os.getenv('DATABASE_PATH', 'backend/minesearch/database/mines.db')
        # Absoluten Pfad bilden, dann als sqlite URL
        _db_path_abs = (_ROOT / _db_path).resolve()
        DATABASE_URL = f"sqlite:///{_db_path_abs}"
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Einstellungen
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))  # Sekunden
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # Default Modell - ENTFERNT: Keine automatische Perplexity-Auswahl mehr
    # ÄNDERUNG 14.07.2025: Kimi K2 als explizites Default-Modell für Kostenkontrolle
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'openrouter:kimi-k2')
    PERPLEXITY_TEMPERATURE = float(os.getenv('PERPLEXITY_TEMPERATURE', 0.2))
    
    # Provider Konfiguration
    PROVIDERS = PROVIDERS_CONFIG
    
    # Modell Konfigurationen
    PERPLEXITY_MODELS = MODELS_CONFIG['perplexity']
    ANTHROPIC_MODELS = MODELS_CONFIG['anthropic']
    GEMINI_MODELS = MODELS_CONFIG['gemini']
    GROK_MODELS = MODELS_CONFIG['grok']
    OPENAI_MODELS = MODELS_CONFIG['openai']
    # DEEPSEEK_MODELS = MODELS_CONFIG['deepseek']  # ENTFERNT 06.08.2025: DeepSeek nur über OpenRouter
    OPENROUTER_MODELS = MODELS_CONFIG['openrouter']
    EXA_MODELS = MODELS_CONFIG['exa']
    TAVILY_MODELS = MODELS_CONFIG['tavily']
    
    # Globale Mining-Begriffe und Abkürzungen
    MINING_ABBREVIATIONS = {
        'technical_reports': ['NI 43-101', 'JORC', 'SAMREC', 'PERC', 'SME', 'CRIRSCO'],
        'study_types': ['PEA', 'PFS', 'DFS', 'FS', 'Feasibility Study', 'Pre-Feasibility',
                       'Preliminary Economic Assessment', 'Scoping Study'],
        'resource_categories': ['Measured', 'Indicated', 'Inferred', 'Reserve', 'Resource',
                              'Proven', 'Probable', 'M&I', 'P&P'],
        'commodity_symbols': {
            'Au': 'Gold', 'Ag': 'Silver', 'Cu': 'Copper', 'Pb': 'Lead', 'Zn': 'Zinc',
            'Ni': 'Nickel', 'Co': 'Cobalt', 'Li': 'Lithium', 'Fe': 'Iron', 'U': 'Uranium',
            'Mo': 'Molybdenum', 'Pt': 'Platinum', 'Pd': 'Palladium', 'REE': 'Rare Earth'
        }
    }
    
    # Priorisierte Domains für Mining-Daten
    PRIORITY_MINING_DOMAINS = {
        'tier1': [  # Regierungsseiten und offizielle Datenbanken
            'mern.gouv.qc.ca', 'nrcan.gc.ca', 'blm.gov', 'usgs.gov',
            'ga.gov.au', 'sarig.sa.gov.au', 'sernageomin.cl', 'gestim.quebec',
            'ingemmet.gob.pe', 'esdm.go.id', 'dmr.gov.za'
        ],
        'tier2': [  # Börsen und Finanzdokumente
            'sedar.com', 'sec.gov', 'asx.com.au', 'tsx.com', 'jse.co.za',
            'bolsadesantiago.com', 'bvl.com.pe', 'idx.co.id'
        ],
        'tier3': [  # Mining-Portale und Industrie-Seiten
            'mining.com', 'mining-technology.com', 'infomine.com',
            'northernminer.com', 'miningweekly.com', 'minexploration.com'
        ]
    }
    
    # PDF-Suchmuster für technische Dokumente
    PDF_SEARCH_PATTERNS = [
        '*technical-report*.pdf', '*NI-43-101*.pdf', '*feasibility*.pdf',
        '*closure-plan*.pdf', '*environmental-assessment*.pdf', '*restoration*.pdf',
        '*reclamation*.pdf', '*rehabilitation*.pdf', '*annual-report*.pdf',
        '*sustainability-report*.pdf', '*resource-estimate*.pdf'
    ]
    
    @classmethod
    def validate(cls):
        """Validiere kritische Konfiguration beim Start"""
        errors = []
        warnings = []
        
        # Multi-Provider Validierung
        providers_configured = False
        
        if cls.PROVIDERS.get('perplexity', {}).get('enabled'):
            if not cls.PERPLEXITY_API_KEY:
                warnings.append("PERPLEXITY_API_KEY nicht gesetzt - Perplexity Provider deaktiviert")
                cls.PROVIDERS['perplexity']['enabled'] = False
            else:
                providers_configured = True
        
        if cls.PROVIDERS.get('openrouter', {}).get('enabled'):
            if not cls.OPENROUTER_API_KEY:
                warnings.append("OPENROUTER_API_KEY nicht gesetzt - OpenRouter Provider deaktiviert")
                cls.PROVIDERS['openrouter']['enabled'] = False
            else:
                providers_configured = True
        
        if not providers_configured:
            errors.append("Kein Provider konfiguriert - mindestens ein API-Key muss gesetzt sein")
        
        # Zeige Warnungen
        for warning in warnings:
            print(f"⚠️  WARNUNG: {warning}")
            
        if errors:
            raise ValueError(f"Konfigurationsfehler: {', '.join(errors)}")
    
    @classmethod
    def get_summary(cls):
        """Gibt Konfigurations-Zusammenfassung zurueck"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG,
            "api_key_configured": bool(cls.PERPLEXITY_API_KEY),
            "database": cls.DATABASE_URL,
            "log_level": cls.LOG_LEVEL
        }

# Erstelle globale Config-Instanz
config = Config()