"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored Multi-Provider Search Service für MineSearch (CLAUDE.md konform)
"""

from search_service_advanced import SearchServiceAdvanced

# Hauptklasse für Multi-Provider Search Service
class MultiProviderSearchService(SearchServiceAdvanced):
    """
    Hauptklasse für Multi-Provider Mining-Suchen
    
    Erbt alle Funktionen von:
    - SearchServiceCore: Basis-Funktionen und Format-Konvertierung
    - SearchServiceOperations: Standard Such-Operationen
    - SearchServiceAdvanced: Erweiterte Such-Strategien
    """
    
    def __init__(self):
        """Initialisiert den Multi-Provider Search Service"""
        super().__init__()

# Service-Instanz für Kompatibilität (DEPRECATED - use services_container)
from services_container import services
multi_search_service = services.multi_search_service