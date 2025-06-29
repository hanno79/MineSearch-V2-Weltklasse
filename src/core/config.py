"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Konfigurationsmanagement für Multi-Agent Mining Research System
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml


@dataclass
class APIConfig:
    """API-Konfiguration"""
    openrouter_key: Optional[str] = None
    perplexity_key: Optional[str] = None
    tavily_key: Optional[str] = None
    exa_key: Optional[str] = None
    apify_key: Optional[str] = None
    scrapingbee_key: Optional[str] = None
    firecrawl_key: Optional[str] = None
    brightdata_key: Optional[str] = None
    deepseek_key: Optional[str] = None
    gemini_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    custom_key: Optional[str] = None
    custom_endpoint: Optional[str] = None
    
    def validate(self) -> Dict[str, bool]:
        """Validiert API-Keys und gibt Status zurück"""
        return {
            "openrouter": bool(self.openrouter_key),
            "perplexity": bool(self.perplexity_key),
            "tavily": bool(self.tavily_key),
            "exa": bool(self.exa_key),
            "apify": bool(self.apify_key),
            "scrapingbee": bool(self.scrapingbee_key),
            "firecrawl": bool(self.firecrawl_key),
            "brightdata": bool(self.brightdata_key),
            "deepseek": bool(self.deepseek_key),
            "gemini": bool(self.gemini_key),
            "anthropic": bool(self.anthropic_key),
            "custom": bool(self.custom_key and self.custom_endpoint)
        }


@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration"""
    path: Path
    
    def __post_init__(self):
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """Logging-Konfiguration"""
    level: str = "INFO"
    file_path: Path = Path("./logs/minesearch.log")
    max_size_mb: int = 10
    backup_count: int = 5
    
    def __post_init__(self):
        self.file_path = Path(self.file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class ScrapingConfig:
    """Web-Scraping-Konfiguration"""
    user_agent: str
    respect_robots: bool = True
    delay_seconds: float = 1.0
    timeout_seconds: int = 30
    retry_attempts: int = 3


@dataclass
class ExportConfig:
    """Export-Konfiguration"""
    default_path: Path
    column_separator: str = "|"
    cell_separator: str = "+++"
    encoding: str = "utf-8"
    
    def __post_init__(self):
        self.default_path = Path(self.default_path)
        self.default_path.mkdir(parents=True, exist_ok=True)


class Config:
    """Haupt-Konfigurationsklasse"""
    
    def __init__(self, env_file: Optional[str] = None):
        # Lade .env Datei
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv()
        
        # Initialisiere Konfigurationen
        self.api = APIConfig(
            openrouter_key=os.getenv("OPENROUTER_API_KEY"),
            perplexity_key=os.getenv("PERPLEXITY_API_KEY"),
            tavily_key=os.getenv("TAVILY_API_KEY"),
            exa_key=os.getenv("EXA_API_KEY"),
            apify_key=os.getenv("APIFY_API_KEY"),
            scrapingbee_key=os.getenv("SCRAPINGBEE_API_KEY"),
            firecrawl_key=os.getenv("FIRECRAWL_API_KEY"),
            brightdata_key=os.getenv("BRIGHTDATA_API_KEY"),
            deepseek_key=os.getenv("DEEPSEEK_API_KEY"),
            gemini_key=os.getenv("GEMINI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            custom_key=os.getenv("CUSTOM_API_KEY"),
            custom_endpoint=os.getenv("CUSTOM_API_ENDPOINT")
        )
        
        self.database = DatabaseConfig(
            path=Path(os.getenv("DATABASE_PATH", "./data/minesearch.db"))
        )
        
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=Path(os.getenv("LOG_FILE_PATH", "./logs/minesearch.log")),
            max_size_mb=int(os.getenv("LOG_MAX_SIZE_MB", 10)),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", 5))
        )
        
        self.scraping = ScrapingConfig(
            user_agent=os.getenv("USER_AGENT", "MineSearch/1.0"),
            respect_robots=os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true",
            delay_seconds=float(os.getenv("SCRAPING_DELAY_SECONDS", 1)),
            timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", 30)),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", 3))
        )
        
        self.export = ExportConfig(
            default_path=Path(os.getenv("DEFAULT_EXPORT_PATH", "./data/output/")),
            column_separator=os.getenv("DEFAULT_COLUMN_SEPARATOR", "|"),
            cell_separator=os.getenv("DEFAULT_CELL_SEPARATOR", "+++"),
            encoding=os.getenv("DEFAULT_ENCODING", "utf-8")
        )
        
        # Parallelisierung
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", 10))
        
        # ÄNDERUNG 17.06.2025: Neue Konfiguration für Agenten-Limits
        # Agenten-Koordination
        self.max_agents_per_field = int(os.getenv("MAX_AGENTS_PER_FIELD", 10))
        self.max_agents_per_stage = int(os.getenv("MAX_AGENTS_PER_STAGE", 50))
        
        # Feature Flags
        self.debug_mode = os.getenv("ENABLE_DEBUG_MODE", "false").lower() == "true"
        self.performance_monitoring = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
        
    def validate(self) -> Dict[str, Any]:
        """Validiert die gesamte Konfiguration"""
        validation_result: Dict[str, Any] = {
            "api_status": self.api.validate(),
            "database_exists": self.database.path.parent.exists(),
            "log_writable": self.logging.file_path.parent.exists(),
            "export_writable": self.export.default_path.exists(),
            "warnings": []
        }
        
        # Warnungen bei fehlenden API-Keys
        if not any(self.api.validate().values()):
            validation_result["warnings"].append(
                "Keine API-Keys konfiguriert. Bitte .env Datei prüfen."
            )
        
        return validation_result
    
    def get_active_agents(self) -> list[str]:
        """Gibt Liste der verfügbaren Agenten zurück"""
        agents = []
        if self.api.openrouter_key:
            agents.extend(["claude", "gpt4"])
        if self.api.perplexity_key:
            agents.append("perplexity")
        agents.append("scraper")  # Immer verfügbar
        return agents
    
    def save_to_yaml(self, path: str):
        """Speichert Konfiguration als YAML"""
        config_dict = {
            "api": {
                "available": self.api.validate()
            },
            "database": {
                "path": str(self.database.path)
            },
            "logging": {
                "level": self.logging.level,
                "file_path": str(self.logging.file_path)
            },
            "scraping": {
                "user_agent": self.scraping.user_agent,
                "respect_robots": self.scraping.respect_robots
            },
            "export": {
                "path": str(self.export.default_path),
                "separators": {
                    "column": self.export.column_separator,
                    "cell": self.export.cell_separator
                }
            }
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False)


# Singleton-Instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Gibt die globale Config-Instanz zurück"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance