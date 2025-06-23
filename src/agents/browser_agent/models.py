"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Browser Agent
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


@dataclass
class BrowserConfig:
    """Konfiguration für Browser"""
    headless: bool = True
    timeout: int = 30000  # Millisekunden
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = 'MiningResearchBot/1.0 (Compatible with modern browsers)'
    locale: str = 'en-US'
    args: List[str] = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = ['--no-sandbox', '--disable-setuid-sandbox']


@dataclass
class ScrapeResult:
    """Ergebnis eines Browser-Scrapes"""
    url: str
    field_name: str
    value: Any
    source: str
    confidence_score: float
    metadata: Dict[str, Any]
    extraction_method: str = "browser_extraction"
    screenshot_path: Optional[str] = None


@dataclass
class PortalConfig:
    """Konfiguration für Government Portal"""
    country: str
    name: str
    base_url: str
    search_path: str
    selectors: Dict[str, str]
    requires_js: bool = True
    wait_conditions: List[str] = None
    
    def __post_init__(self):
        if self.wait_conditions is None:
            self.wait_conditions = []


class ExtractionStrategy(Enum):
    """Strategie für Datenextraktion"""
    TABLE = "table"
    FORM = "form"
    LIST = "list"
    TEXT = "text"
    STRUCTURED = "structured"


@dataclass
class ExtractionRule:
    """Regel für Datenextraktion"""
    field_name: str
    selector: str
    strategy: ExtractionStrategy
    transform: Optional[str] = None  # JavaScript-Code für Transformation
    multiple: bool = False
    required: bool = False
    
    def apply_transform(self, value: str) -> Any:
        """Wendet Transformation auf extrahierten Wert an"""
        if not self.transform or not value:
            return value
            
        # Einfache Transformationen
        if self.transform == "trim":
            return value.strip()
        elif self.transform == "lowercase":
            return value.lower()
        elif self.transform == "uppercase":
            return value.upper()
        elif self.transform.startswith("replace:"):
            parts = self.transform.split(":", 2)
            if len(parts) == 3:
                return value.replace(parts[1], parts[2])
        
        return value


@dataclass
class NavigationStep:
    """Schritt für Portal-Navigation"""
    action: str  # "click", "fill", "select", "wait"
    selector: str
    value: Optional[str] = None
    wait_after: int = 1000  # Millisekunden


@dataclass
class JavaScriptCheck:
    """Prüfung ob JavaScript benötigt wird"""
    indicator: str  # Element das nur mit JS existiert
    dynamic_content: bool
    ajax_calls: bool
    spa_framework: Optional[str] = None  # React, Angular, Vue etc.