"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Basis-Konfiguration für MineSearch
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from .api_keys import APIKeysConfig
from .providers import PROVIDERS_CONFIG
from .models import MODELS_CONFIG

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
# ABACUS-FIX 18.07.2025: Korrigiere Pfad zur richtigen .env Datei
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config(APIKeysConfig):
    """Zentrale Konfigurationsklasse - KISS Prinzip"""
    
    # Server Einstellungen
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Datenbank
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mines.db')
    
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
    DEEPSEEK_MODELS = MODELS_CONFIG['deepseek']
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