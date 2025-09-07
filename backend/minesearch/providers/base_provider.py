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
    
    async def search_single_field(
        self,
        field_name: str,
        mine_name: str,
        model_id: str,
        sources: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> SearchResult:
        """
        ÄNDERUNG 27.08.2025: Erweiterte Methode für Sequential Field Orchestrator
        Sucht fokussiert nach einem einzelnen Feld mit allen verfügbaren Quellen
        
        Diese Methode implementiert eine optimierte Suche, die sich auf ein spezifisches
        Datenfeld konzentriert und alle verfügbaren Quellen systematisch durchsucht.
        
        Args:
            field_name: Name des spezifischen Feldes (z.B. "Restaurationskosten")
            mine_name: Name der Mine
            model_id: ID des zu verwendenden Modells
            sources: Liste aller verfügbaren Quellen die durchsucht werden sollen
            options: Erweiterte Optionen mit field-spezifischen Parametern
            
        Returns:
            SearchResult mit fokussiertem Ergebnis für das spezifische Feld
        """
        # Erstelle field-fokussierte Query
        focused_query = self._build_single_field_query(field_name, mine_name, sources, options)
        
        # Erweitere Optionen für field-fokussierte Suche
        field_options = options.copy()
        field_options.update({
            'focus_field': field_name,
            'search_mode': 'single_field',
            'discovered_sources': sources,
            'skip_source_discovery': True,
            'field_specific_optimization': True
        })
        
        # Führe fokussierte Suche durch
        result = await self.search(focused_query, model_id, field_options)
        
        # Post-processing: Extrahiere nur das relevante Feld
        if result.success and result.structured_data:
            filtered_data = {}
            
            # Suche das spezifische Feld in verschiedenen Varianten
            field_variants = self._get_field_variants(field_name)
            
            for variant in field_variants:
                if variant in result.structured_data:
                    value = result.structured_data[variant]
                    if value and str(value).strip() and str(value) not in ['None', 'null', '', '-']:
                        filtered_data[field_name] = str(value).strip()
                        break
            
            # Update structured_data to contain only the focused field
            result.structured_data = filtered_data
            
            # Add field-specific metadata
            if not result.metadata:
                result.metadata = {}
            result.metadata.update({
                'focused_field': field_name,
                'sources_searched': len(sources),
                'search_mode': 'single_field',
                'field_found': field_name in filtered_data
            })
        
        return result
    
    def _build_single_field_query(
        self,
        field_name: str,
        mine_name: str,
        sources: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Erstellt eine fokussierte Query für ein einzelnes Feld
        """
        opts = options or {}
        country = opts.get('country', '')
        commodity = opts.get('commodity', '')
        
        # Basis Query
        query = f"Suche AUSSCHLIESSLICH nach '{field_name}' für die Mine '{mine_name}'"
        
        if country:
            query += f" in {country}"
        if commodity:
            query += f" ({commodity} Mine)"
        
        # Field-spezifische Suchstrategie
        field_strategies = {
            'Restaurationskosten': """
Konzentriere dich NUR auf Kosten für:
- Mine Closure / Decommissioning 
- Environmental Restoration
- Rehabilitation Costs
- Site Remediation
- Reclamation Expenses
Gib den EXAKTEN Betrag zurück wenn gefunden.""",
            
            'Eigentümer': """
Suche NUR nach dem aktuellen Eigentümer/Owner:
- Company Name
- Corporation
- Mining Company
- Parent Company
Gib den EXAKTEN Firmennamen zurück.""",
            
            'Betreiber': """
Suche NUR nach dem aktuellen Betreiber/Operator:
- Operating Company
- Mine Operator
- Management Company
Gib den EXAKTEN Betreiber-Namen zurück.""",
            
            'Aktivitätsstatus': """
Suche NUR nach dem aktuellen Status:
- Active/Operational
- Inactive/Closed
- Under Development
- Suspended
- Care & Maintenance
Gib den EXAKTEN Status zurück.""",
            
            'Rohstoff': """
Suche NUR nach den abgebauten Rohstoffen:
- Gold, Kupfer, Silber, etc.
- Primary/Secondary Commodities
- Resource Type
Gib die EXAKTEN Rohstoffe zurück.""",
            
            'Fördermenge/Jahr Rohstoff': """
Suche NUR nach spezifischer Rohstoffproduktion:
- Gold: in Unzen (oz), Tonnen (t)
- Kupfer: in Tonnen (t), Pfund (lbs)
- Kohle: in Tonnen (t)
- Annual Commodity Production
- Refined Output
Gib die EXAKTE Menge mit Einheit zurück.""",
            
            'Fördermenge/Jahr Abraum': """
Suche NUR nach der gesamten Materialextraktion:
- Total Material Mined
- Waste Rock + Ore
- Overburden Removal
- Total Mining Volume
- in Millionen Tonnen (Mt)
Gib die EXAKTE Gesamtmenge inkl. Abraum zurück."""
        }
        
        # Füge field-spezifische Strategie hinzu
        for key, strategy in field_strategies.items():
            if key.lower() in field_name.lower():
                query += f"\n\n{strategy}"
                break
        
        # Quellenkontext
        if sources:
            high_priority_sources = [s for s in sources[:10] if s.get('priority', 3) <= 2]
            if high_priority_sources:
                query += f"\n\nPRIORITÄT auf diese {len(high_priority_sources)} vertrauenswürdigen Quellen:"
                for source in high_priority_sources:
                    query += f"\n• {source.get('domain', 'Unknown')} - {source.get('description', 'Specialized source')}"
        
        query += f"\n\n⚠️ WICHTIG: Gib AUSSCHLIESSLICH Informationen zu '{field_name}' zurück!"
        query += f"\nAlle anderen Datenfelder sind für diese Suche IRRELEVANT."
        query += f"\nWenn '{field_name}' nicht gefunden wird, gib explizit 'Nicht gefunden' zurück."
        
        return query
    
    def _get_field_variants(self, field_name: str) -> List[str]:
        """
        Gibt verschiedene Varianten eines Feldnamens zurück
        """
        variants = [field_name]
        
        # Standard-Varianten
        field_mapping = {
            'Restaurationskosten': ['Restaurationskosten', 'Mine Closure Cost', 'Decommissioning Cost', 'Restoration Cost'],
            'Eigentümer': ['Eigentümer', 'Owner', 'Company', 'Corporation'],
            'Betreiber': ['Betreiber', 'Operator', 'Operating Company', 'Manager'],
            'Aktivitätsstatus': ['Aktivitätsstatus', 'Status', 'Operational Status', 'Mine Status'],
            'Rohstoff': ['Rohstoff', 'Commodity', 'Resource', 'Mineral'],
            'Fördermenge/Jahr Rohstoff': ['Fördermenge/Jahr Rohstoff', 'Annual Commodity Production', 'Refined Production', 'Metal Production', 'Gold Production', 'Copper Production'],
            'Fördermenge/Jahr Abraum': ['Fördermenge/Jahr Abraum', 'Total Material Mined', 'Mining Volume', 'Waste Rock', 'Overburden', 'Total Extraction'],
            'x-Koordinate': ['x-Koordinate', 'Latitude', 'Lat', 'X-Coordinate'],
            'y-Koordinate': ['y-Koordinate', 'Longitude', 'Lon', 'Long', 'Y-Coordinate'],
            'Country': ['Country', 'Land', 'Nation'],
            'Region': ['Region', 'Province', 'State', 'Territory']
        }
        
        for key, mapped_variants in field_mapping.items():
            if key.lower() in field_name.lower() or field_name.lower() in key.lower():
                variants.extend(mapped_variants)
                break
        
        return list(set(variants))  # Remove duplicates
    
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