"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Zentrale Konfiguration fuer MineSearch 2.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ÄNDERUNG 01.07.2025: CSV_COLUMNS zentral definiert zur Vermeidung von Duplikaten
CSV_COLUMNS = [
    'ID', 'Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus',
    'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
]

# Felder die KEINE Quellennummern brauchen
FIELDS_WITHOUT_SOURCES = [
    'ID', 'Name', 'Country', 'Region', 'Eigentümer', 'Quellenangaben'
]

# Lade Umgebungsvariablen
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Zentrale Konfigurationsklasse - KISS Prinzip"""
    
    # API Keys
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    
    # Server Einstellungen
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Datenbank
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mines.db')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Einstellungen
    API_TIMEOUT = 30  # Sekunden
    MAX_RETRIES = 3
    
    # Perplexity Modelle
    PERPLEXITY_MODELS = {
        "sonar": {
            "id": "llama-3.1-sonar-small-128k-online",
            "name": "Schnelle Suche",
            "timeout": 30,
            "max_tokens": 1000,
            "description": "Günstig und schnell für einfache Anfragen"
        },
        "sonar-pro": {
            "id": "llama-3.1-sonar-large-128k-online", 
            "name": "Erweiterte Suche (Empfohlen)",
            "timeout": 60,
            "max_tokens": 2000,
            "description": "Beste Balance zwischen Qualität und Geschwindigkeit"
        },
        "sonar-deep-research": {
            "id": "sonar-deep-research",
            "name": "Tiefenrecherche",
            "timeout": 2000,  # 33 Minuten
            "max_tokens": 10000,
            "description": "Umfassende Recherche (kann 30+ Minuten dauern)"
        },
        "sonar-reasoning-pro": {
            "id": "sonar-reasoning-pro",
            "name": "Analyse mit Reasoning",
            "timeout": 120,
            "max_tokens": 3000,
            "description": "Für komplexe Analysen mit logischem Denken"
        }
    }
    
    # Default Modell
    DEFAULT_MODEL = "sonar-pro"
    PERPLEXITY_TEMPERATURE = 0.2
    
    # Länderspezifische Konfigurationen
    COUNTRY_CONFIGS = {
        'kanada': {
            'languages': ['en', 'fr'],
            'currency': 'CAD',
            'regions': ['Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                       'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick', 
                       'Newfoundland and Labrador', 'Prince Edward Island',
                       'Northwest Territories', 'Yukon', 'Nunavut'],
            'mining_terms': {
                'mine': ['mine', 'site minier', 'project', 'projet', 'property', 'propriété'],
                'operator': ['operator', 'opérateur', 'exploitant', 'betreiber', 'operador'],
                'owner': ['owner', 'propriétaire', 'eigentümer', 'propietario', 'belongs to', 'gehört', 'property of'],
                'commodity': ['commodity', 'produit', 'minerai', 'mineral', 'minéral'],
                'restoration_costs': ['restoration costs', 'closure costs', 'reclamation costs', 
                                    'coûts de restauration', 'coûts de fermeture', 'coûts de réhabilitation',
                                    'asset retirement obligation', 'ARO', 'obligation de mise hors service',
                                    'environmental liability', 'passif environnemental', 
                                    'closure bond', 'garantie financière', 'financial assurance',
                                    'provision for closure', 'provision pour fermeture']
            },
            'priority_domains': ['mern.gouv.qc.ca', 'nrcan.gc.ca', 'gestim.quebec',
                               'mining.ca', 'sedar.com', 'tse.ca', 'gov.bc.ca']
        },
        'canada': {  # Englische Variante
            'languages': ['en', 'fr'],
            'currency': 'CAD',
            'regions': ['Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                       'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick', 
                       'Newfoundland and Labrador', 'Prince Edward Island',
                       'Northwest Territories', 'Yukon', 'Nunavut'],
            'mining_terms': {
                'mine': ['mine', 'site minier', 'project', 'projet', 'property', 'propriété'],
                'operator': ['operator', 'opérateur', 'exploitant', 'betreiber', 'operador'],
                'owner': ['owner', 'propriétaire', 'eigentümer', 'propietario', 'belongs to', 'gehört', 'property of'],
                'commodity': ['commodity', 'produit', 'minerai', 'mineral', 'minéral'],
                'restoration_costs': ['restoration costs', 'closure costs', 'reclamation costs', 
                                    'coûts de restauration', 'coûts de fermeture', 'coûts de réhabilitation',
                                    'asset retirement obligation', 'ARO', 'obligation de mise hors service',
                                    'environmental liability', 'passif environnemental', 
                                    'closure bond', 'garantie financière', 'financial assurance',
                                    'provision for closure', 'provision pour fermeture']
            },
            'priority_domains': ['mern.gouv.qc.ca', 'nrcan.gc.ca', 'gestim.quebec',
                               'mining.ca', 'sedar.com', 'tse.ca', 'gov.bc.ca']
        },
        'australien': {
            'languages': ['en'],
            'currency': 'AUD',
            'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                       'Victoria', 'South Australia', 'Tasmania', 
                       'Northern Territory'],
            'mining_terms': {
                'mine': ['mine', 'mining operation', 'project', 'property', 'deposit'],
                'operator': ['operator', 'company', 'joint venture', 'JV', 'operates', 'operating company'],
                'owner': ['owner', 'owns', 'ownership', 'property of', 'belongs to', 'held by'],
                'commodity': ['commodity', 'mineral', 'ore', 'resource'],
                'restoration_costs': ['restoration costs', 'closure costs', 'reclamation costs',
                                    'rehabilitation costs', 'asset retirement obligation', 'ARO',
                                    'environmental liability', 'closure bond', 'financial assurance',
                                    'provision for closure', 'mine closure provision']
            },
            'priority_domains': ['ga.gov.au', 'dmp.wa.gov.au', 'sarig.sa.gov.au', 
                               'minedex.dmirs.wa.gov.au', 'asx.com.au']
        },
        'australia': {  # Englische Variante
            'languages': ['en'],
            'currency': 'AUD',
            'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                       'Victoria', 'South Australia', 'Tasmania', 
                       'Northern Territory'],
            'mining_terms': {
                'mine': ['mine', 'mining operation', 'project', 'property', 'deposit'],
                'operator': ['operator', 'company', 'joint venture', 'JV', 'operates', 'operating company'],
                'owner': ['owner', 'owns', 'ownership', 'property of', 'belongs to', 'held by'],
                'commodity': ['commodity', 'mineral', 'ore', 'resource'],
                'restoration_costs': ['restoration costs', 'closure costs', 'reclamation costs',
                                    'rehabilitation costs', 'asset retirement obligation', 'ARO',
                                    'environmental liability', 'closure bond', 'financial assurance',
                                    'provision for closure', 'mine closure provision']
            },
            'priority_domains': ['ga.gov.au', 'dmp.wa.gov.au', 'sarig.sa.gov.au', 
                               'minedex.dmirs.wa.gov.au', 'asx.com.au']
        },
        'indonesien': {
            'languages': ['id', 'en'],
            'currency': 'IDR',
            'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                       'Java', 'Nusa Tenggara', 'Maluku'],
            'mining_terms': {
                'mine': ['tambang', 'mine', 'proyek', 'project', 'lokasi penambangan'],
                'operator': ['PT', 'operator', 'perusahaan', 'kontraktor', 'pemegang IUP', 'dioperasikan oleh'],
                'owner': ['pemilik', 'owner', 'dimiliki oleh', 'milik', 'kepemilikan'],
                'commodity': ['komoditas', 'mineral', 'bahan galian', 'sumber daya'],
                'restoration_costs': ['biaya reklamasi', 'biaya penutupan tambang', 'restoration costs',
                                    'jaminan reklamasi', 'dana jaminan', 'closure costs',
                                    'kewajiban lingkungan', 'environmental liability',
                                    'provisi penutupan tambang', 'closure provision']
            },
            'priority_domains': ['esdm.go.id', 'minerba.esdm.go.id', 'modi.esdm.go.id',
                               'idx.co.id', 'ptba.co.id', 'antam.com']
        },
        'indonesia': {  # Englische Variante
            'languages': ['id', 'en'],
            'currency': 'IDR',
            'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                       'Java', 'Nusa Tenggara', 'Maluku'],
            'mining_terms': {
                'mine': ['tambang', 'mine', 'proyek', 'project', 'lokasi penambangan'],
                'operator': ['PT', 'operator', 'perusahaan', 'kontraktor', 'pemegang IUP', 'dioperasikan oleh'],
                'owner': ['pemilik', 'owner', 'dimiliki oleh', 'milik', 'kepemilikan'],
                'commodity': ['komoditas', 'mineral', 'bahan galian', 'sumber daya'],
                'restoration_costs': ['biaya reklamasi', 'biaya penutupan tambang', 'restoration costs',
                                    'jaminan reklamasi', 'dana jaminan', 'closure costs',
                                    'kewajiban lingkungan', 'environmental liability',
                                    'provisi penutupan tambang', 'closure provision']
            },
            'priority_domains': ['esdm.go.id', 'minerba.esdm.go.id', 'modi.esdm.go.id',
                               'idx.co.id', 'ptba.co.id', 'antam.com']
        },
        'peru': {
            'languages': ['es', 'en'],
            'currency': 'PEN',
            'regions': ['Arequipa', 'Cajamarca', 'Cusco', 'Junín', 
                       'La Libertad', 'Pasco', 'Áncash', 'Apurímac'],
            'mining_terms': {
                'mine': ['mina', 'mine', 'proyecto', 'project', 'yacimiento', 'operación minera'],
                'operator': ['operador', 'empresa minera', 'titular', 'compañía', 'concesionario', 'opera'],
                'owner': ['propietario', 'dueño', 'owner', 'propiedad de', 'pertenece a'],
                'commodity': ['mineral', 'commodity', 'recurso', 'metal', 'concentrado'],
                'restoration_costs': ['costos de cierre', 'costos de restauración', 'closure costs',
                                    'pasivos ambientales', 'provisión de cierre', 'garantías financieras',
                                    'plan de cierre de minas', 'obligaciones de cierre',
                                    'fondos de garantía', 'environmental liability']
            },
            'priority_domains': ['ingemmet.gob.pe', 'minem.gob.pe', 'osinergmin.gob.pe',
                               'smv.gob.pe', 'bvl.com.pe']
        },
        'chile': {
            'languages': ['es', 'en'],
            'currency': 'CLP',
            'regions': ['Antofagasta', 'Atacama', 'Coquimbo', 'Valparaíso',
                       'O\'Higgins', 'Maule', 'Tarapacá'],
            'mining_terms': {
                'mine': ['mina', 'faena minera', 'proyecto', 'yacimiento', 'operación'],
                'operator': ['operador', 'compañía minera', 'titular', 'empresa', 'sociedad minera', 'operada por'],
                'owner': ['propietario', 'dueño', 'owner', 'propiedad de', 'pertenece a', 'de propiedad de'],
                'commodity': ['mineral', 'commodity', 'recurso', 'metal', 'concentrado'],
                'restoration_costs': ['costos de cierre', 'costos de restauración', 'closure costs',
                                    'pasivos ambientales', 'provisión de cierre', 'garantías financieras',
                                    'plan de cierre de faena', 'obligaciones ambientales',
                                    'fondos de garantía', 'environmental liability']
            },
            'priority_domains': ['sernageomin.cl', 'cochilco.cl', 'sonami.cl',
                               'cmfchile.cl', 'bolsadesantiago.com']
        }
    }
    
    # ÄNDERUNG 29.06.2025: Globale Mining-Begriffe und Abkürzungen
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
    
    # ÄNDERUNG 29.06.2025: Priorisierte Domains für Mining-Daten
    PRIORITY_MINING_DOMAINS = {
        'tier1': [  # Regierungsseiten und offizielle Datenbanken - keine Bevorzugung
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
    
    # ÄNDERUNG 29.06.2025: PDF-Suchmuster für technische Dokumente
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
        
        if not cls.PERPLEXITY_API_KEY:
            errors.append("PERPLEXITY_API_KEY nicht gesetzt")
            
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

# Exportiere Konfiguration
config = Config()