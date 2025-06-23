"""
Abstrakte Basis-Klasse für alle Mining Research Agenten
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import logging
from enum import Enum
import hashlib
import json
from .extraction_patterns import ExtractionPatterns
from src.core.cancellation import CancellationToken, CancellationException


class AgentStatus(Enum):
    """Status eines Agenten"""
    READY = "ready"
    RUNNING = "running"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class MineQuery:
    """Struktur für eine Minen-Suchanfrage"""
    mine_name: str
    region: str
    country: str
    languages: List[str]
    required_fields: List[str]
    
    def get_cache_key(self) -> str:
        """Generiert eindeutigen Cache-Key"""
        data = f"{self.mine_name}_{self.region}_{self.country}"
        return hashlib.md5(data.encode()).hexdigest()


@dataclass
class SearchResult:
    """Struktur für ein Suchergebnis"""
    mine_name: str
    field_name: str
    value: Any
    source: str
    source_url: Optional[str]
    source_date: Optional[int]  # Jahr
    confidence_score: float
    agent_name: str
    timestamp: datetime
    metadata: Dict[str, Any]
    found_at: Optional[str] = None  # Optional field for OpenRouter compatibility
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            "mine_name": self.mine_name,
            "field_name": self.field_name,
            "value": self.value,
            "source": self.source,
            "source_url": self.source_url,
            "source_date": self.source_date,
            "confidence_score": self.confidence_score,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "found_at": self.found_at
        }


class BaseAgent(ABC):
    """Abstrakte Basis-Klasse für alle Agenten"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"agent.{name}")
        self.status = AgentStatus.READY
        self.stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_fields_found": 0,
            "start_time": datetime.now()
        }
        self._rate_limiter = None
        self._session = None
        self.status_callback = None
        self.extractor = ExtractionPatterns()
        self._cancellation_token: Optional[CancellationToken] = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        pass
    
    @abstractmethod
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt die eigentliche Suche durch"""
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validiert API-Credentials"""
        pass
    
    async def _send_status(self, message: str) -> None:
        """Sendet Status-Update wenn Callback vorhanden"""
        if self.status_callback:
            try:
                await self.status_callback(f"{self.name}: {message}")
            except Exception as e:
                self.logger.warning(f"Status callback failed: {e}")
    
    async def execute_search(self, query: MineQuery) -> List[SearchResult]:
        """Wrapper für Suche mit Error-Handling"""
        self.stats["total_requests"] += 1
        
        try:
            # Status prüfen
            if self.status == AgentStatus.DISABLED:
                self.logger.warning(f"Agent {self.name} ist deaktiviert")
                return []
            
            # Rate Limiting
            await self._check_rate_limit()
            
            # Status setzen
            self.status = AgentStatus.RUNNING
            
            # Eigentliche Suche
            self.logger.info(f"Starte Suche für {query.mine_name}")
            results = await self.search_mine(query)
            
            # Statistik aktualisieren
            self.stats["successful_requests"] += 1
            self.stats["total_fields_found"] += len(results)
            
            # Status zurücksetzen
            self.status = AgentStatus.READY
            
            return results
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.status = AgentStatus.ERROR
            self.logger.error(f"Fehler bei Suche: {str(e)}")
            return []
    
    async def _check_rate_limit(self) -> None:
        """Implementiert Rate-Limiting"""
        if self._rate_limiter:
            await self._rate_limiter.acquire()
    
    async def cleanup(self) -> None:
        """Räumt Ressourcen auf - muss von Subklassen überschrieben werden"""
        # Basis-Cleanup
        if hasattr(self, '_session') and self._session:
            try:
                await self._session.close()
                self._session = None
            except Exception as e:
                self.logger.warning(f"Fehler beim Schließen der Session: {e}")
        
        # Weitere Ressourcen können von Subklassen aufgeräumt werden
        self.logger.debug(f"Agent {self.name} aufgeräumt")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        runtime = (datetime.now() - self.stats["start_time"]).total_seconds()
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / 
                          self.stats["total_requests"]) * 100
        
        return {
            "name": self.name,
            "status": self.status.value,
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": round(success_rate, 2),
            "total_fields_found": self.stats["total_fields_found"],
            "runtime_seconds": round(runtime, 2),
            "requests_per_minute": round(
                self.stats["total_requests"] / (runtime / 60) if runtime > 0 else 0, 
                2
            )
        }
    
    
    def _parse_language_response(self, text: str, language: str) -> str:
        """Hilfs-Methode für Sprachverarbeitung"""
        # Basis-Implementation, kann von Subklassen überschrieben werden
        return text
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extrahiert Jahr aus Text"""
        import re
        
        # Suche nach 4-stelligen Jahreszahlen
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Neueste Jahr zurückgeben
            years = [int(match) for match in matches]
            return max(years)
        
        return None
    
    async def _handle_api_error(self, error: Exception, context: str = "") -> None:
        """Einheitliche API-Fehlerbehandlung"""
        error_msg = f"{self.name} API error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        self.logger.error(error_msg)
        self.stats["failed_requests"] += 1
        
        # Status-Update senden
        await self._send_status(f"Error: {str(error)[:100]}")
        
        # Spezifische Fehlerbehandlung
        if "rate limit" in str(error).lower():
            self.logger.warning(f"{self.name}: Rate limit erreicht")
            await asyncio.sleep(5)  # Kurze Pause bei Rate Limit
        elif "unauthorized" in str(error).lower() or "forbidden" in str(error).lower():
            self.logger.error(f"{self.name}: API-Key ungültig oder keine Berechtigung")
            self.status = AgentStatus.ERROR
        elif "timeout" in str(error).lower():
            self.logger.warning(f"{self.name}: Request timeout")
    
    def _safe_extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Sicheres Extrahieren von JSON aus Text"""
        import json
        import re
        
        # Versuche direktes JSON-Parsing
        try:
            result: Dict[str, Any] = json.loads(text)
            return result
        except:
            pass
        
        # Suche nach JSON-Blöcken im Text
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                parsed_result: Dict[str, Any] = json.loads(match)
                return parsed_result
            except:
                continue
        
        return None
    
    def _normalize_field_name(self, field: str) -> str:
        """Normalisiert Feldnamen für konsistente Ergebnisse"""
        # Entferne Whitespace und konvertiere zu lowercase
        normalized = field.strip().lower()
        
        # Ersetze Sonderzeichen
        normalized = normalized.replace(" ", "_")
        normalized = normalized.replace("-", "_")
        normalized = normalized.replace("/", "_")
        
        # Mapping für häufige Varianten
        field_mappings = {
            "operator": "betreiber",
            "owner": "betreiber",
            "company": "betreiber",
            "coordinates": "koordinaten",
            "location": "koordinaten",
            "gps": "koordinaten",
            "commodity": "rohstofftyp",
            "mineral": "rohstofftyp",
            "resource": "rohstofftyp",
            "status": "aktivitaetsstatus",
            "operational_status": "aktivitaetsstatus",
            "remediation_costs": "sanierungskosten",
            "closure_costs": "sanierungskosten",
            "rehabilitation": "sanierungskosten"
        }
        
        return field_mappings.get(normalized, normalized)
    
    def set_cancellation_token(self, token: Optional[CancellationToken]) -> None:
        """
        ÄNDERUNG 19.06.2025: Setzt das Cancellation Token für diesen Agenten
        
        Args:
            token: CancellationToken oder None
        """
        self._cancellation_token = token
    
    async def check_cancellation(self) -> None:
        """
        ÄNDERUNG 19.06.2025: Prüft ob Abbruch angefordert wurde
        
        Raises:
            CancellationException: Wenn Abbruch angefordert wurde
        """
        if self._cancellation_token and self._cancellation_token.is_cancelled():
            self.logger.info(f"Agent {self.name} wird wegen Abbruch beendet")
            raise CancellationException(f"Agent {self.name} abgebrochen")
    
    def _extract_with_context(self, text: str, field: str) -> List[Tuple[Any, float]]:
        """
        Nutzt kontextbasierte Extraktion für bessere Ergebnisse
        
        Returns:
            Liste von Tupeln (extrahierter_wert, konfidenz)
        """
        # Normalisiere Feldname
        normalized_field = self._normalize_field_name(field)
        
        # Nutze kontextbasierten Extraktor
        # ÄNDERUNG 19.06.2025: Korrigiere Methodenname - verwende extract_field statt extract_with_confidence
        from ..agents.extraction_patterns import FieldType
        
        # Map field name to FieldType
        field_type_map = {
            "betreiber": FieldType.OPERATOR,
            "koordinaten": FieldType.COORDINATES,
            "rohstofftyp": FieldType.COMMODITY,
            "aktivitaetsstatus": FieldType.STATUS,
            "sanierungskosten": FieldType.COSTS,
            "jahresproduktion": FieldType.PRODUCTION
        }
        
        field_type = field_type_map.get(normalized_field)
        if field_type:
            results = self.extractor.extract_field(text, field_type)
        else:
            results = []
        
        # Log für Debugging
        if results:
            self.logger.debug(f"Extrahiert für {normalized_field}: {results[:3]}")  # Top 3
        
        return results
    
    def _normalize_currency(self, value: str, from_currency: str, 
                          to_currency: str) -> Optional[float]:
        """Normalisiert Währungsangaben"""
        # Vereinfachte Implementation
        # In Produktion: Externe API für Wechselkurse
        
        try:
            # Entferne Währungssymbole und Formatierung
            import re
            
            # Extrahiere numerischen Wert
            value_clean = re.sub(r'[^\d.,]', '', value)
            value_clean = value_clean.replace(',', '.')
            amount = float(value_clean)
            
            # Vereinfachte Umrechnung (feste Kurse)
            conversion_rates = {
                ('USD', 'CAD'): 1.35,
                ('EUR', 'CAD'): 1.45,
                ('CAD', 'CAD'): 1.0,
            }
            
            rate = conversion_rates.get((from_currency, to_currency), 1.0)
            return amount * rate
            
        except:
            return None
    
    def _add_geographic_constraints(self, query: str, region: str, country: str) -> str:
        """
        ÄNDERUNG 19.06.2025: Fügt geografische Einschränkungen zu einer Suchanfrage hinzu
        
        Args:
            query: Die Basis-Suchanfrage
            region: Die Region (z.B. "Quebec")
            country: Das Land (z.B. "Canada")
            
        Returns:
            Die erweiterte Suchanfrage mit geografischen Einschränkungen
        """
        # Füge Region und Land zur Query hinzu
        if region and country:
            query += f' "{region}" "{country}"'
        elif country:
            query += f' "{country}"'
        elif region:
            query += f' "{region}"'
        
        # Füge Ausschlüsse hinzu
        exclusions = self._get_geographic_exclusions(region, country)
        if exclusions:
            query += " " + " ".join(exclusions)
        
        return query
    
    def _get_geographic_exclusions(self, region: str, country: str) -> List[str]:
        """
        ÄNDERUNG 19.06.2025: Gibt eine Liste von geografischen Ausschlüssen zurück
        
        Returns:
            Liste von Ausschlüssen im Format "-Location"
        """
        exclusions = []
        
        # Länder-basierte Ausschlüsse
        country_exclusions = {
            "canada": ["-Greenland", "-Grönland", "-Iceland", "-Alaska"],
            "usa": ["-Canada", "-Mexico", "-Greenland"],
            "australia": ["-New Zealand", "-Indonesia", "-Papua New Guinea"],
            "chile": ["-Argentina", "-Peru", "-Bolivia"],
            "peru": ["-Chile", "-Brazil", "-Bolivia"],
            "brazil": ["-Venezuela", "-Colombia", "-Peru", "-Argentina"],
            "south africa": ["-Namibia", "-Botswana", "-Zimbabwe"],
            "mexico": ["-USA", "-Guatemala", "-Belize"],
            "germany": ["-Poland", "-Czech Republic", "-Austria"],
            "china": ["-Mongolia", "-Russia", "-India"]
        }
        
        # Regions-basierte Ausschlüsse
        region_exclusions = {
            "quebec": ["-Greenland", "-Grönland", "-Nunavut", "-Iceland"],
            "ontario": ["-Michigan", "-Minnesota", "-Wisconsin"],
            "british columbia": ["-Alaska", "-Washington"],
            "yukon": ["-Alaska", "-Northwest Territories"],
            "northwest territories": ["-Nunavut", "-Yukon"]
        }
        
        if country and country.lower() in country_exclusions:
            exclusions.extend(country_exclusions[country.lower()])
        
        if region and region.lower() in region_exclusions:
            exclusions.extend(region_exclusions[region.lower()])
        
        # Entferne Duplikate
        return list(set(exclusions))
    
    def _validate_geographic_result(self, result: SearchResult, query: MineQuery) -> bool:
        """
        ÄNDERUNG 19.06.2025: Validiert ob ein Suchergebnis geografisch korrekt ist
        
        Args:
            result: Das zu validierende Suchergebnis
            query: Die ursprüngliche Suchanfrage
            
        Returns:
            True wenn das Ergebnis geografisch korrekt ist, False sonst
        """
        # Prüfe ob das Ergebnis Text enthält, der auf falsche geografische Zuordnung hinweist
        if not result.value:
            return True
        
        text_to_check = str(result.value).lower()
        
        # Liste von falschen geografischen Zuordnungen
        false_positives = {
            "canada": ["greenland", "grönland", "iceland", "alaska", "russia"],
            "quebec": ["greenland", "grönland", "nunavut", "iceland"],
            "usa": ["canada", "mexico", "greenland"],
            "australia": ["new zealand", "indonesia", "papua new guinea"]
        }
        
        # Prüfe Land
        if query.country and query.country.lower() in false_positives:
            for false_location in false_positives[query.country.lower()]:
                if false_location in text_to_check:
                    self.logger.warning(
                        f"Geografisch falsches Ergebnis gefunden: {false_location} in Ergebnis für {query.country}"
                    )
                    return False
        
        # Prüfe Region
        if query.region and query.region.lower() in false_positives:
            for false_location in false_positives[query.region.lower()]:
                if false_location in text_to_check:
                    self.logger.warning(
                        f"Geografisch falsches Ergebnis gefunden: {false_location} in Ergebnis für {query.region}"
                    )
                    return False
        
        return True