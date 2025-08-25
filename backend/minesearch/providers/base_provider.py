"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Abstrakte Basis-Klasse für alle Search-Provider
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Konfiguration für ein Modell"""
    id: str
    name: str
    timeout: int
    max_tokens: int
    description: str
    provider: str
    supports_web_search: bool = True
    supports_deep_research: bool = False
    is_free: bool = False
    # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung hinzugefügt
    provider_category: str = None


@dataclass
class SearchResult:
    """Einheitliches Ergebnis-Format für alle Provider"""
    success: bool
    content: str
    structured_data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    search_duration: Optional[float] = None


class AbstractProvider(ABC):
    """Abstrakte Basis-Klasse für alle Search-Provider"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.api_key = api_key
        self.config = config
        self.name = self.__class__.__name__.replace('Provider', '').lower()
        
    @abstractmethod
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        Führe eine Suche mit dem spezifizierten Modell durch
        
        Args:
            query: Die Suchanfrage
            model_id: ID des zu verwendenden Modells
            options: Zusätzliche Optionen (z.B. temperature, max_tokens)
            
        Returns:
            SearchResult mit einheitlicher Struktur
        """
        pass
    
    @abstractmethod
    def get_models(self) -> Dict[str, ModelConfig]:
        """
        Gibt alle verfügbaren Modelle dieses Providers zurück
        
        Returns:
            Dict mit model_id als Key und ModelConfig als Value
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validiert die Provider-Konfiguration (API-Key, etc.)
        
        Returns:
            True wenn konfiguration gültig, False sonst
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        Gibt den System-Prompt für diesen Provider zurück
        
        Args:
            options: Optionen die den Prompt beeinflussen können
            
        Returns:
            System-Prompt als String
        """
        pass
    
    def format_search_query(self, mine_name: str, country: Optional[str], 
                          commodity: Optional[str], options: Dict[str, Any]) -> str:
        """
        Formatiert die Suchanfrage für diesen Provider
        Kann von Subklassen überschrieben werden für provider-spezifische Formatierung
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            options: Zusätzliche Optionen
            
        Returns:
            Formatierte Suchanfrage
        """
        query = f"Finde detaillierte Informationen über die Mine: {mine_name}"
        
        if country:
            query += f" in {country}"
            
        if commodity:
            query += f", die {commodity} abbaut"
            
        return query
    
    def parse_response(self, raw_response: Any) -> SearchResult:
        """
        Parst die Provider-spezifische Antwort in das einheitliche Format
        Muss von Subklassen implementiert werden wenn nötig
        
        Args:
            raw_response: Rohe Antwort vom Provider
            
        Returns:
            SearchResult im einheitlichen Format
        """
        # Standard-Implementierung - kann überschrieben werden
        return SearchResult(
            success=True,
            content=str(raw_response),
            structured_data={},
            sources=[],
            metadata={}
        )
    
    async def health_check(self) -> bool:
        """
        Prüft ob der Provider erreichbar ist
        
        Returns:
            True wenn erreichbar, False sonst
        """
        try:
            # Einfacher Test mit minimalem Request
            return self.validate_config()
        except Exception as e:
            logger.error(f"[{self.name}] Health check failed: {e}")
            return False