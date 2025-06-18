"""
Author: rahn
Datum: 18.06.2025
Version: 1.1
Beschreibung: Factory für Agent-Erstellung
"""
from typing import Dict, Type, Optional
from src.agents.base_agent import BaseAgent
from src.agents.claude_agent import ClaudeAgent
from src.agents.gpt_agent import GPTAgent
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.scraper_agent import ScraperAgent
from src.agents.tavily_agent import TavilyAgent
from src.agents.exa_agent import ExaAgent
from src.agents.apify_agent import ApifyAgent
from src.agents.scrapingbee_agent import ScrapingBeeAgent
from src.agents.firecrawl_agent import FirecrawlAgent
from src.agents.brightdata_agent import BrightDataAgent
from src.agents.openrouter_agent import OpenRouterAgent
from src.agents.deepseek_research_agent import DeepSeekResearchAgent
from src.core.config import Config


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
        "deepseek_coder": DeepSeekResearchAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, config: Config, **kwargs) -> Optional[BaseAgent]:
        """Erstellt einen Agenten basierend auf Typ"""
        
        # Handle OpenRouter model types
        if agent_type.startswith("openrouter_"):
            model_id = kwargs.get('model_id')
            if model_id and config.api.openrouter_key:
                return OpenRouterAgent(api_key=config.api.openrouter_key, model_id=model_id)
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
            from src.agents.openrouter_agent import OpenRouterAgent
            # Include both free and premium models
            all_models = {**OpenRouterAgent.FREE_MODELS, **OpenRouterAgent.PREMIUM_MODELS}
            for model_id in all_models:
                # Handle models with :free suffix
                model_key = f"openrouter_{model_id.split('/')[-1].split(':')[0]}"
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
        
        return available