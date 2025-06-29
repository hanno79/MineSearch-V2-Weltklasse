"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Zentrale Konfiguration fuer MineSearch 2.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv

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
                'mine': ['mine', 'site minier'],
                'operator': ['operator', 'opérateur', 'exploitant'],
                'commodity': ['commodity', 'produit', 'minerai']
            }
        },
        'canada': {  # Englische Variante
            'languages': ['en', 'fr'],
            'currency': 'CAD',
            'regions': ['Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                       'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick', 
                       'Newfoundland and Labrador', 'Prince Edward Island',
                       'Northwest Territories', 'Yukon', 'Nunavut']
        },
        'australien': {
            'languages': ['en'],
            'currency': 'AUD',
            'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                       'Victoria', 'South Australia', 'Tasmania', 
                       'Northern Territory'],
            'mining_terms': {
                'mine': ['mine', 'mining operation'],
                'operator': ['operator', 'owner'],
                'commodity': ['commodity', 'mineral']
            }
        },
        'australia': {  # Englische Variante
            'languages': ['en'],
            'currency': 'AUD',
            'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                       'Victoria', 'South Australia', 'Tasmania', 
                       'Northern Territory']
        },
        'indonesien': {
            'languages': ['id', 'en'],
            'currency': 'IDR',
            'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                       'Java', 'Nusa Tenggara', 'Maluku'],
            'mining_terms': {
                'mine': ['tambang', 'mine'],
                'operator': ['PT', 'operator', 'perusahaan'],
                'commodity': ['komoditas', 'mineral', 'bahan galian']
            }
        },
        'indonesia': {  # Englische Variante
            'languages': ['id', 'en'],
            'currency': 'IDR',
            'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                       'Java', 'Nusa Tenggara', 'Maluku']
        },
        'peru': {
            'languages': ['es', 'en'],
            'currency': 'PEN',
            'regions': ['Arequipa', 'Cajamarca', 'Cusco', 'Junín', 
                       'La Libertad', 'Pasco', 'Áncash', 'Apurímac'],
            'mining_terms': {
                'mine': ['mina', 'mine'],
                'operator': ['operador', 'empresa minera'],
                'commodity': ['mineral', 'commodity']
            }
        },
        'chile': {
            'languages': ['es', 'en'],
            'currency': 'CLP',
            'regions': ['Antofagasta', 'Atacama', 'Coquimbo', 'Valparaíso',
                       'O\'Higgins', 'Maule', 'Tarapacá'],
            'mining_terms': {
                'mine': ['mina', 'faena minera'],
                'operator': ['operador', 'compañía minera'],
                'commodity': ['mineral', 'commodity']
            }
        }
    }
    
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