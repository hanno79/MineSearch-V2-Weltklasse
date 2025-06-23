"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Sprachmuster und Übersetzungsfunktionen
"""

from typing import Dict, List, Optional, Any

class LanguagePatternManager:
    """Verwaltet Sprachmuster für Keyword-Generierung"""
    
    def __init__(self):
        self.patterns = self._initialize_language_patterns()
        self.generic_mining_terms = self._initialize_mining_terms()
        
    def _initialize_language_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialisiert Sprachmuster für Keyword-Generierung"""
        return {
            "word_formation": {
                "en": {
                    "compound_separator": " ",
                    "adjective_position": "before",
                    "common_suffixes": ["ing", "tion", "ment", "ity", "ness"],
                    "common_prefixes": ["re", "un", "pre", "post", "ex"]
                },
                "es": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["ción", "miento", "dad", "eza"],
                    "common_prefixes": ["re", "des", "pre", "post", "ex"]
                },
                "fr": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["tion", "ment", "té", "ance"],
                    "common_prefixes": ["re", "dé", "pré", "post", "ex"]
                },
                "de": {
                    "compound_separator": "",  # Zusammengesetzte Wörter
                    "adjective_position": "before",
                    "common_suffixes": ["ung", "heit", "keit", "schaft"],
                    "common_prefixes": ["ver", "ent", "be", "ge", "un"]
                },
                "pt": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["ção", "mento", "dade", "eza"],
                    "common_prefixes": ["re", "des", "pre", "pós", "ex"]
                }
            }
        }
    
    def _initialize_mining_terms(self) -> Dict[str, Dict[str, str]]:
        """Initialisiert generische Mining-Begriffe"""
        return {
            "mineral": {"es": "mineral", "fr": "minéral", "pt": "mineral", "de": "Mineral"},
            "ore": {"es": "mena", "fr": "minerai", "pt": "minério", "de": "Erz"},
            "resource": {"es": "recurso", "fr": "ressource", "pt": "recurso", "de": "Ressource"},
            "commodity": {"es": "materia prima", "fr": "matière première", "pt": "commodity", "de": "Rohstoff"},
            "metal": {"es": "metal", "fr": "métal", "pt": "metal", "de": "Metall"},
            "deposit": {"es": "yacimiento", "fr": "gisement", "pt": "jazida", "de": "Lagerstätte"}
        }
    
    def get_context_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Gibt kontextuelle Muster zurück"""
        return {
            "ministry_patterns": {
                "en": ["ministry of {}", "department of {}", "{} authority"],
                "es": ["ministerio de {}", "departamento de {}", "autoridad de {}"],
                "fr": ["ministère de {}", "département de {}", "autorité de {}"],
                "pt": ["ministério de {}", "departamento de {}", "autoridade de {}"],
                "de": ["ministerium für {}", "amt für {}", "{} behörde"]
            },
            "association_patterns": {
                "en": ["{} mining association", "{} mining chamber", "{} miners federation"],
                "es": ["asociación minera de {}", "cámara minera de {}", "federación de mineros de {}"],
                "fr": ["association minière de {}", "chambre minière de {}", "fédération des mineurs de {}"],
                "pt": ["associação mineira de {}", "câmara mineira de {}", "federação de mineiros de {}"],
                "de": ["bergbauverband {}", "bergbaukammer {}", "bergarbeiterverband {}"]
            }
        }
    
    def get_time_modifiers(self, language: str) -> List[str]:
        """Gibt zeitliche Modifikatoren für eine Sprache zurück"""
        time_modifiers = {
            "en": ["current", "latest", "recent", "historical", "2024", "2023"],
            "es": ["actual", "último", "reciente", "histórico", "2024", "2023"],
            "fr": ["actuel", "dernier", "récent", "historique", "2024", "2023"],
            "pt": ["atual", "último", "recente", "histórico", "2024", "2023"],
            "de": ["aktuell", "neueste", "kürzlich", "historisch", "2024", "2023"]
        }
        return time_modifiers.get(language, [])
    
    def get_abbreviations(self) -> Dict[str, List[str]]:
        """Gibt gängige Abkürzungen zurück"""
        return {
            "environmental": ["env", "enviro"],
            "production": ["prod", "prd"],
            "ministry": ["min", "minist"],
            "department": ["dept", "dep"],
            "corporation": ["corp", "co"],
            "limited": ["ltd", "ltda"]
        }