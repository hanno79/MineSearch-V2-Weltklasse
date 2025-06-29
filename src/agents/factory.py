"""
Author: rahn
Datum: 18.06.2025
Version: 1.1
Beschreibung: Factory für Agent-Erstellung
"""
from typing import Dict, Type, Optional, Any
from src.agents.base_agent import BaseAgent
from src.agents.claude_agent import ClaudeAgent
from src.agents.gpt_agent import GPTAgent
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.scraper_agent import ScraperAgent
from src.agents.tavily_agent import TavilyAgent
from src.agents.exa_agent import ExaAgent
from src.agents.apify_agent import ApifyAgent
from src.agents.scrapingbee import ScrapingBeeAgent
from src.agents.firecrawl_agent import FirecrawlAgent
from src.agents.brightdata_agent import BrightDataAgent
from src.agents.openrouter_agent import OpenRouterAgent
from src.agents.openrouter.models import ModelRegistry
from src.agents.openrouter.utils import parse_model_id, extract_model_key_from_agent_type, find_model_by_key
from src.agents.deepseek_research import DeepSeekResearchAgent
from src.agents.perplexity_deep_agent import PerplexityDeepAgent
from src.agents.deep_web_crawler_agent import DeepWebCrawlerAgent
from src.agents.browser_agent import BrowserAgent
from src.agents.document_finder import DocumentFinder
from src.agents.premium_mining_research import PremiumMiningResearch
from src.core.config import Config
from src.core.logger import get_logger


class AgentFactory:
    """Factory für Agent-Erstellung"""
    
    _agent_classes: Dict[str, Type[BaseAgent]] = {
        "claude": ClaudeAgent,
        "gpt4": GPTAgent,
        "perplexity": PerplexityAgent,
        "scraper": ScraperAgent,
        "tavily": TavilyAgent,
        "exa": ExaAgent,
        "apify": ApifyAgent,
        "scrapingbee": ScrapingBeeAgent,
        "firecrawl": FirecrawlAgent,
        "brightdata": BrightDataAgent,
        "openrouter": OpenRouterAgent,
        "deepseek": DeepSeekResearchAgent,
        "deepseek_reasoner": DeepSeekResearchAgent,
        "deepseek_coder": DeepSeekResearchAgent,
        "perplexity_deep": PerplexityDeepAgent,
        "deep_web_crawler": DeepWebCrawlerAgent,
        "browser": BrowserAgent,
        "document_finder": DocumentFinder,
        "premium_mining": PremiumMiningResearch
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, config: Config, **kwargs) -> Optional[BaseAgent]:
        """Erstellt einen Agenten basierend auf Typ"""
        
        # ÄNDERUNG 27.06.2025: SessionManager aus kwargs extrahieren
        session_manager = kwargs.pop('session_manager', None)
        
        # Handle OpenRouter model types
        if agent_type.startswith("openrouter_"):
            model_id = kwargs.get('model_id')
            
            # ÄNDERUNG 18.06.2025: Falls keine model_id übergeben, versuche sie aus agent_type zu extrahieren
            if not model_id:
                # Extrahiere Modell-Suffix aus agent_type (z.B. "openrouter_deepseek-chat" -> "deepseek-chat")
                model_suffix = agent_type.replace("openrouter_", "")
                
                # Suche passende model_id mit robustem Parser
                all_models = {**ModelRegistry.get_free_models(), **ModelRegistry.get_premium_models()}
                model_id, _ = find_model_by_key(model_suffix, all_models)
            
            if model_id and config.api.openrouter_key:
                # ÄNDERUNG 19.06.2025: Fix für BaseAgent config requirement
                try:
                    # OpenRouterAgent erwartet api_key, model_id und config
                    agent = OpenRouterAgent(
                        api_key=config.api.openrouter_key,
                        model_id=model_id,
                        config={
                            "api_config": config.api,
                            "scraping_config": config.scraping,
                            "max_concurrent": config.max_concurrent_requests
                        }
                    )
                    return agent
                except Exception as e:
                    # Logging statt print für Produktionsumgebung
                    logger = get_logger("factory")
                    logger.error(f"Error creating OpenRouterAgent: {e}")
                    return None
            return None
        
        # Handle DeepSeek variants
        if agent_type.startswith("deepseek"):
            model_type = "chat"  # default
            if agent_type == "deepseek_reasoner":
                model_type = "reasoner"
            elif agent_type == "deepseek_coder":
                model_type = "coder"
            
            agent_config = {
                "api_config": config.api,
                "scraping_config": config.scraping,
                "max_concurrent": config.max_concurrent_requests,
                "use_openrouter": True  # Use OpenRouter by default
            }
            return DeepSeekResearchAgent(name=agent_type, config=agent_config, model_type=model_type)
        
        if agent_type not in cls._agent_classes:
            raise ValueError(f"Unbekannter Agent-Typ: {agent_type}")
        
        agent_class = cls._agent_classes[agent_type]
        
        # Agent-spezifische Konfiguration
        agent_config = {
            "api_config": config.api,
            "scraping_config": config.scraping,
            "max_concurrent": config.max_concurrent_requests
        }
        
        # ÄNDERUNG 27.06.2025: SessionManager hinzufügen wenn vorhanden
        if session_manager:
            agent_config["session_manager"] = session_manager
        
        # ÄNDERUNG 21.06.2025: Spezielle Konfiguration für Deep Web Crawler
        if agent_type == "deep_web_crawler":
            agent_config["crawler_config"] = {
                "max_depth": 3,
                "max_pages": 100,
                "timeout": 30
            }
        elif agent_type == "browser":
            agent_config["browser_config"] = {
                "headless": True,
                "timeout": 30000,
                "debug": False
            }
        elif agent_type == "document_finder":
            agent_config["document_config"] = {
                "max_documents": 10,
                "process_pdfs": True
            }
        # ÄNDERUNG 22.06.2025: Fix für PerplexityDeepAgent - erwartet andere Parameter
        # ÄNDERUNG 27.06.2025: Verwende übergebenen SessionManager
        elif agent_type == "perplexity_deep":
            # Verwende übergebenen SessionManager oder erstelle neuen
            if not session_manager:
                from src.utils.session_manager import SessionManager
                session_manager = SessionManager()
            return agent_class(
                api_key=config.api.perplexity_key,
                session_manager=session_manager,
                use_deep_research=True
            )
        # ÄNDERUNG 22.06.2025: PremiumMiningResearch benötigt alle verfügbaren Agenten
        elif agent_type == "premium_mining":
            # Premium Mining Research benötigt Zugriff auf andere Agenten
            # Dies wird normalerweise vom Orchestrator verwaltet
            return agent_class(
                name=agent_type,
                config=agent_config,
                agents=kwargs.get('agents', {})
            )
        
        return agent_class(name=agent_type, config=agent_config)
    
    @classmethod
    def get_available_agents(cls, config: Config) -> Dict[str, bool]:
        """Gibt verfügbare Agenten basierend auf Konfiguration zurück"""
        available = {}
        
        # Claude/GPT über OpenRouter
        if config.api.openrouter_key:
            available["claude"] = True
            available["gpt4"] = True
        else:
            available["claude"] = False
            available["gpt4"] = False
        
        # Perplexity
        available["perplexity"] = bool(config.api.perplexity_key)
        
        # Scraper ist immer verfügbar
        available["scraper"] = True
        
        # Neue Scraping Agents
        available["tavily"] = bool(config.api.tavily_key)
        available["exa"] = bool(config.api.exa_key)
        available["apify"] = bool(config.api.apify_key)
        available["scrapingbee"] = bool(config.api.scrapingbee_key)
        available["firecrawl"] = bool(config.api.firecrawl_key)
        available["brightdata"] = bool(config.api.brightdata_key)
        
        # OpenRouter models
        if config.api.openrouter_key:
            # Include both free and premium models
            all_models = {**ModelRegistry.get_free_models(), **ModelRegistry.get_premium_models()}
            for model_id in all_models:
                # Handle models with :free suffix using robust parser
                parsed = parse_model_id(model_id)
                model_key = f"openrouter_{parsed['model_key']}"
                available[model_key] = True
            
            # DeepSeek models via OpenRouter
            available["deepseek"] = True
            available["deepseek_reasoner"] = True
            available["deepseek_coder"] = True
        else:
            # DeepSeek nur mit direktem API Key (falls konfiguriert)
            deepseek_key = getattr(config.api, 'deepseek_key', None)
            available["deepseek"] = bool(deepseek_key)
            available["deepseek_reasoner"] = bool(deepseek_key)
            available["deepseek_coder"] = bool(deepseek_key)
        
        # Neue erweiterte Agenten
        available["deep_web_crawler"] = True  # Immer verfügbar (nutzt andere Agenten intern)
        available["browser"] = True  # Browser Agent (Playwright optional)
        available["document_finder"] = True  # Document Finder (PDF Processor)
        available["perplexity_deep"] = bool(config.api.perplexity_key)  # Benötigt Perplexity
        available["premium_mining"] = bool(config.api.openrouter_key or config.api.perplexity_key)  # Benötigt Premium APIs
        
        return available
    
    @classmethod
    def get_agent_requirements(cls, agent_type: str) -> Dict[str, Any]:
        """Gibt die Anforderungen für einen Agenten zurück"""
        requirements = {
            "claude": {"api_key": "openrouter_key", "description": "Claude AI via OpenRouter"},
            "gpt4": {"api_key": "openrouter_key", "description": "GPT-4 via OpenRouter"},
            "perplexity": {"api_key": "perplexity_key", "description": "Perplexity Web Search"},
            "perplexity_deep": {"api_key": "perplexity_key", "description": "Perplexity Deep Research"},
            "scraper": {"api_key": None, "description": "Basic Web Scraper (no API needed)"},
            "tavily": {"api_key": "tavily_key", "description": "Tavily Search API"},
            "exa": {"api_key": "exa_key", "description": "Exa Semantic Search"},
            "apify": {"api_key": "apify_key", "description": "Apify Web Scraping"},
            "scrapingbee": {"api_key": "scrapingbee_key", "description": "ScrapingBee with JS rendering"},
            "firecrawl": {"api_key": "firecrawl_key", "description": "Firecrawl Intelligent Crawling"},
            "brightdata": {"api_key": "brightdata_key", "description": "Bright Data Enterprise Scraping"},
            "deepseek": {"api_key": "openrouter_key", "description": "DeepSeek Research AI"},
            "deep_web_crawler": {"api_key": None, "description": "Deep Web Crawling Utility"},
            "browser": {"api_key": None, "description": "Browser-based scraping with Playwright"},
            "document_finder": {"api_key": None, "description": "PDF and Document Processing"},
            "premium_mining": {"api_key": "multiple", "description": "Premium Mining Research System"}
        }
        
        if agent_type.startswith("openrouter_"):
            return {"api_key": "openrouter_key", "description": f"OpenRouter Model: {agent_type}"}
        
        return requirements.get(agent_type, {"api_key": "unknown", "description": "Unknown agent"})