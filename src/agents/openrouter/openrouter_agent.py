"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: OpenRouter Agent for accessing multiple free LLMs
"""

from typing import List, Dict, Any, Optional
import aiohttp
import json
from datetime import datetime
import asyncio

from ..base_agent import BaseAgent, MineQuery, SearchResult
from src.core.logger import get_logger, PerformanceLogger
from ..enhanced_search import get_mining_search_queries

from .models import ModelRegistry
from .prompts import OpenRouterPromptGenerator
from .response_parser import OpenRouterResponseParser


class OpenRouterAgent(BaseAgent):
    """Agent that uses OpenRouter API to access multiple LLMs"""
    
    def __init__(self, api_key: str, model_id: str = "deepseek/deepseek-chat", 
                 config: Optional[Dict[str, Any]] = None):
        """Initialize OpenRouter agent"""
        # ÄNDERUNG 18.06.2025: Fix für BaseAgent config requirement
        agent_name = f"openrouter_{model_id.split('/')[-1].split(':')[0]}"
        super().__init__(name=agent_name, config=config or {})
        
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Set model
        self.model = ModelRegistry.get_model(model_id)
        self.model_id = self.model.id
        
        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized OpenRouter agent with model: {self.model.name} ({'Free' if self.model.is_free else 'Premium'})")
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Components
        self.prompt_generator = OpenRouterPromptGenerator()
        self.response_parser = OpenRouterResponseParser(self.name, self.model.name, self.logger)
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Enhanced mining search using OpenRouter LLM with multiple queries"""
        self.perf_logger.start_timer(f"openrouter_search_{query.mine_name}")
        
        # Get mining search queries
        search_queries = get_mining_search_queries(
            query.mine_name,
            query.region,
            query.country
        )
        
        all_results = []
        
        # Run multiple targeted searches
        prompts = [
            ("comprehensive", self.prompt_generator.build_comprehensive_prompt(query, search_queries)),
            ("technical", self.prompt_generator.build_technical_prompt(query)),
            ("environmental", self.prompt_generator.build_environmental_prompt(query)),
            ("ownership", self.prompt_generator.build_ownership_prompt(query)),
            ("status", self.prompt_generator.build_status_prompt(query))
        ]
        
        for prompt_type, prompt in prompts:
            results = await self._search_with_prompt(prompt, query)
            if results:
                self.logger.info(f"OpenRouter {prompt_type} search found {len(results)} results")
                all_results.extend(results)
            
            # Small delay between searches
            await asyncio.sleep(1)
        
        self.perf_logger.end_timer(
            f"openrouter_search_{query.mine_name}",
            results_found=len(all_results)
        )
        
        return all_results
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Implementation of base agent search_mine method"""
        return await self.search(query)
    
    async def validate_credentials(self) -> bool:
        """Validate API credentials"""
        if not self.api_key:
            self.logger.warning("No OpenRouter API key provided")
            return False
        
        # Test with a simple request
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/minesearch",
                "X-Title": "MineSearch"
            }
            
            payload = {
                "model": self.model_id,
                "messages": [
                    {"role": "user", "content": "Say 'OK' if you can read this."}
                ],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        self.logger.info("OpenRouter API credentials validated successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenRouter API validation failed: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"OpenRouter credential validation error: {str(e)}")
            return False
    
    async def _search_with_prompt(self, prompt: str, query: MineQuery) -> List[SearchResult]:
        """Execute a single search with given prompt"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/minesearch",
                "X-Title": "MineSearch"
            }
            
            payload = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": self.prompt_generator.get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 8000  # Increased for comprehensive mining data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)  # Longer timeout for mining searches
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"OpenRouter API error: {error_text}")
                        return []
                    
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Parse response
                    results = self.response_parser.parse_response(content, query)
                    
                    self.logger.info(f"OpenRouter ({self.model.name}) found {len(results)} results")
                    return results
                    
        except Exception as e:
            self.logger.error(f"OpenRouter search error: {str(e)}")
            return []
    
    async def initialize(self) -> bool:
        """Initialize the agent"""
        # Validate credentials during initialization
        return await self.validate_credentials()
    
    def list_available_models(self):
        """List all available models"""
        print("\n=== Premium Models ===")
        for model_id, model in ModelRegistry.get_premium_models().items():
            print(f"{model_id}: {model.name} - {model.description}")
            print(f"  Context: {model.context_length:,} tokens\n")
        
        print("\n=== Free Models ===")
        for model_id, model in ModelRegistry.get_free_models().items():
            print(f"{model_id}: {model.name} - {model.description}")
            print(f"  Context: {model.context_length:,} tokens\n")
