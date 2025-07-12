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
    
    async def search(self, strategy: str = "direct", **kwargs):
        """
        Universelle Such-Methode mit verschiedenen Strategien
        
        Args:
            strategy: Such-Strategie ("direct", "multiple", "two_phase", "source_sharing")
            **kwargs: Parameter abhängig von der Strategie
            
        Returns:
            Suchergebnis entsprechend der gewählten Strategie
        """
        if strategy == "direct":
            return await self.search_direct(**kwargs)
        elif strategy == "multiple":
            return await self.search_with_multiple_models(**kwargs)
        elif strategy == "two_phase":
            return await self.search_two_phase(**kwargs)
        elif strategy == "source_sharing":
            return await self.search_with_source_sharing(**kwargs)
        elif strategy == "single_model":
            return await self.search_with_model(**kwargs)
        else:
            raise ValueError(f"Unbekannte Such-Strategie: {strategy}")


# Globale Service-Instanz
multi_search_service = MultiProviderSearchService()