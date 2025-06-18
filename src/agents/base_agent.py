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
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """Abstrakte Basis-Klasse für alle Agenten"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"agent.{name}")
        self.status = AgentStatus.READY
        self.stats = {
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
    
    async def _send_status(self, message: str):
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
    
    async def _check_rate_limit(self):
        """Implementiert Rate-Limiting"""
        if self._rate_limiter:
            await self._rate_limiter.acquire()
    
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
    
    async def cleanup(self):
        """Cleanup-Methode für Ressourcen"""
        if self._session:
            await self._session.close()
        self.logger.info(f"Agent {self.name} beendet")
    
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
            self.status = AgentStatus.FAILED
        elif "timeout" in str(error).lower():
            self.logger.warning(f"{self.name}: Request timeout")
    
    def _safe_extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Sicheres Extrahieren von JSON aus Text"""
        import json
        import re
        
        # Versuche direktes JSON-Parsing
        try:
            return json.loads(text)
        except:
            pass
        
        # Suche nach JSON-Blöcken im Text
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
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
    
    def _extract_with_context(self, text: str, field: str) -> List[Tuple[Any, float]]:
        """
        Nutzt kontextbasierte Extraktion für bessere Ergebnisse
        
        Returns:
            Liste von Tupeln (extrahierter_wert, konfidenz)
        """
        # Normalisiere Feldname
        normalized_field = self._normalize_field_name(field)
        
        # Nutze kontextbasierten Extraktor
        results = self.extractor.extract_with_confidence(text, normalized_field)
        
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