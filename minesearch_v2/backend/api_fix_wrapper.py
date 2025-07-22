"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Defensive API Wrapper für robuste Suchfunktionalität
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DefensiveSearchWrapper:
    """Defensive Wrapper für Search-Funktionalität mit Fallback-Mechanismen"""
    
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialisiere Search Service mit Fallback"""
        try:
            from search_service import MineSearchService
            self.service = MineSearchService()
            logger.info("✅ MineSearchService erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"❌ MineSearchService Initialisierung fehlgeschlagen: {e}")
            self.service = None
    
    async def safe_search(self, mine_name: str, country: str = "Canada", 
                         provider: str = "perplexity", model: str = "perplexity:sonar") -> Dict[str, Any]:
        """
        Sichere Suche mit Fallback-Mechanismen
        
        Args:
            mine_name: Name der Mine
            country: Land
            provider: Provider-Name
            model: Modell-Name
            
        Returns:
            Suchergebnis-Dictionary
        """
        search_start = datetime.now()
        
        # Defensive Validierung
        if not mine_name or not mine_name.strip():
            return {
                "success": False,
                "error": "Mine-Name ist erforderlich",
                "data": None
            }
        
        if not self.service:
            self._initialize_service()
            if not self.service:
                return {
                    "success": False,
                    "error": "Search Service nicht verfügbar",
                    "data": None
                }
        
        try:
            # BUGFIX 20.07.2025: Verwende await für asynchrone Calls
            # Versuche verschiedene Methoden-Namen
            if hasattr(self.service, 'search_mine'):
                logger.info(f"[SAFE SEARCH] Verwende search_mine für {mine_name} mit Model: {model}")
                result = await self.service.search_mine(
                    mine_name=mine_name,
                    country=country,
                    model=model
                )
            elif hasattr(self.service, 'search'):
                logger.info(f"[SAFE SEARCH] Verwende search für {mine_name} mit Model: {model}")
                result = await self.service.search(
                    mine_name=mine_name,
                    country=country,
                    provider=provider,
                    model=model
                )
            elif hasattr(self.service, 'enhanced_search'):
                logger.info(f"[SAFE SEARCH] Verwende enhanced_search für {mine_name} mit Model: {model}")
                result = await self.service.enhanced_search(
                    mine_name=mine_name,
                    country=country,
                    model=model
                )
            else:
                raise AttributeError("Keine bekannte Search-Methode gefunden")
            
            # Validiere Ergebnis
            if not isinstance(result, dict):
                raise ValueError(f"Unerwarteter Ergebnis-Typ: {type(result)}")
            
            # Stelle sicher, dass required fields vorhanden sind
            if 'success' not in result:
                result['success'] = bool(result.get('data'))
            
            if 'data' not in result:
                result['data'] = {}
            
            # Timing hinzufügen
            search_duration = (datetime.now() - search_start).total_seconds()
            result['search_duration'] = search_duration
            
            logger.info(f"✅ Suche erfolgreich für {mine_name} in {search_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Search Fehler für {mine_name}: {e}")
            
            # Fallback: Erstelle Mock-Ergebnis für Stabilität
            return self._create_fallback_result(mine_name, country, str(e))
    
    def _create_fallback_result(self, mine_name: str, country: str, error: str) -> Dict[str, Any]:
        """Erstelle Fallback-Ergebnis bei Fehlern"""
        logger.warning(f"[FALLBACK] Erstelle Fallback-Ergebnis für {mine_name}")
        
        # Minimale strukturierte Daten für Stabilität
        fallback_data = {
            "Name": mine_name,
            "Country": country,
            "Region": "X",
            "Eigentümer": "X",
            "Betreiber": "X",
            "x-Koordinate": "X",
            "y-Koordinate": "X",
            "Aktivitätsstatus": "X",
            "Restaurationskosten": "X",
            "Jahr der Aufnahme der Kosten": "X",
            "Jahr der Erstellung des Dokumentes": "X",
            "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "X",
            "Minentyp (Untertage/ Open-Pit/ usw.)": "X",
            "Produktionsstart": "X",
            "Produktionsende": "X",
            "Fördermenge/Jahr": "X",
            "Fläche der Mine in qkm": "X",
            "Quellenangaben": "Service-Fehler: Daten nicht verfügbar"
        }
        
        return {
            "success": False,
            "error": f"Search Service Fehler: {error}",
            "data": {
                "structured_data": fallback_data,
                "source_mapping": {},
                "mine_name": mine_name,
                "country": country,
                "model_used": "fallback",
                "search_timestamp": datetime.now().isoformat(),
                "search_duration": 0.0,
                "fallback_mode": True
            }
        }

# Global instance
defensive_search = DefensiveSearchWrapper()