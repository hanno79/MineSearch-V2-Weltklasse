"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für DeepSeek Research Agent
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class DeepSeekModel(Enum):
    """Verfügbare DeepSeek Modelle"""
    CHAT = "chat"
    REASONER = "reasoner"
    CODER = "coder"


@dataclass
class ModelConfig:
    """Konfiguration für ein DeepSeek Modell"""
    id: str
    name: str
    capabilities: List[str]
    cost_per_1k: float
    
    @classmethod
    def get_models(cls) -> Dict[str, 'ModelConfig']:
        """Gibt alle verfügbaren Modelle zurück"""
        return {
            "chat": ModelConfig(
                id="deepseek-chat",
                name="DeepSeek Chat",
                capabilities=["general", "fast", "multilingual"],
                cost_per_1k=0.0001
            ),
            "reasoner": ModelConfig(
                id="deepseek-reasoner", 
                name="DeepSeek Reasoner",
                capabilities=["reasoning", "analysis", "complex_queries"],
                cost_per_1k=0.0005
            ),
            "coder": ModelConfig(
                id="deepseek-coder",
                name="DeepSeek Coder",
                capabilities=["code", "technical", "data_extraction"],
                cost_per_1k=0.0001
            )
        }


@dataclass
class ResearchStep:
    """Ein Schritt im Research-Plan"""
    objective: str
    strategy: str
    sources: List[str]
    keywords: List[str]
    expected_data: List[str]
    priority: str = "medium"
    completed: bool = False


@dataclass
class AdaptationStrategy:
    """Strategie zur Anpassung des Research-Plans"""
    missing_fields: List[str]
    found_fields: List[str]
    confidence_threshold: float
    max_retries: int
    adaptation_type: str  # "refine", "expand", "pivot"


@dataclass
class ResearchContext:
    """Kontext für die aktuelle Research-Session"""
    mine_name: str
    country: str
    region: str
    languages: List[str]
    required_fields: List[str]
    search_domains: List[str]
    time_budget: int  # Sekunden
    current_step: int = 0
    total_findings: int = 0
    
    def to_prompt_context(self) -> str:
        """Konvertiert zu Prompt-Kontext"""
        return f"""Mine: {self.mine_name}
Location: {self.region}, {self.country}
Languages: {', '.join(self.languages)}
Required fields: {', '.join(self.required_fields)}
Preferred sources: {', '.join(self.search_domains[:5])}"""


@dataclass
class ExtractionResult:
    """Ergebnis einer Datenextraktion"""
    field_name: str
    value: Any
    source: str
    confidence: float
    metadata: Dict[str, Any]
    extraction_method: str = "ai_extraction"
    
    def to_search_result(self) -> Dict[str, Any]:
        """Konvertiert zu SearchResult Format"""
        return {
            "field_name": self.field_name,
            "value": self.value,
            "source": self.source,
            "confidence_score": self.confidence,
            "metadata": self.metadata
        }