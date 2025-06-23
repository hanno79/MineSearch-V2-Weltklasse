"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für DeepSeek Research Agent
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from ..enhanced_search import get_mining_search_queries, get_mining_domains, get_country_specific_domains
from src.core.logger import get_logger
from .models import DeepSeekModel, ModelConfig, ResearchContext, ResearchStep
from .research_processor import ResearchProcessor


class DeepSeekResearchAgent(BaseAgent):
    """DeepSeek Agent with advanced research capabilities"""
    
    def __init__(self, name: str, config: Dict[str, Any], model_type: str = "chat"):
        super().__init__(name, config)
        
        # Model configuration
        self.model_type = model_type
        self.model_config = ModelConfig.get_models()[model_type]
        
        # Check if using direct API or OpenRouter
        self.use_openrouter = config.get('use_openrouter', True)
        
        if self.use_openrouter:
            self.api_key = config['api_config'].openrouter_key
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = f"deepseek/{self.model_config.id}"
        else:
            # Direct DeepSeek API (wenn verfügbar)
            self.api_key = config['api_config'].get('deepseek_key')
            self.base_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = self.model_config.id
        
        self._rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 requests per minute
        self.logger = get_logger(f"agent.{name}", agent_type="deepseek")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes for complex research
        
        # Research processor
        self.processor = ResearchProcessor(self.logger)
        
    async def initialize(self) -> bool:
        """Initialize the agent"""
        try:
            self._session = aiohttp.ClientSession()
            
            # Skip validation if no API key
            if not self.api_key:
                self.logger.warning(f"No API key configured for DeepSeek ({self.model_type})")
                self.status = AgentStatus.DISABLED
                return False
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info(f"DeepSeek Research Agent ({self.model_type}) successfully initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validate API key with test request"""
        if not self.api_key:
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if self.use_openrouter:
                headers["HTTP-Referer"] = "https://mining-research.local"
                headers["X-Title"] = "Mining Research System"
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            async with self._session.post(
                self.base_url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Execute advanced research for mining data"""
        async with self.perf_logger.track_operation("deepseek_research"):
            self.status = AgentStatus.BUSY
            
            try:
                if self.model_type == "reasoner":
                    # Use reasoning model for complex research
                    return await self._research_with_reasoning(query)
                else:
                    # Standard search
                    return await self._standard_search(query)
                    
            except Exception as e:
                self.logger.error(f"Search error: {e}")
                self.status = AgentStatus.ERROR
                return []
            finally:
                self.status = AgentStatus.IDLE
    
    async def _research_with_reasoning(self, query: MineQuery) -> List[SearchResult]:
        """Advanced research using reasoning capabilities"""
        results = []
        
        # Create research context
        context = ResearchContext(
            mine_name=query.mine_name,
            country=query.country,
            region=query.region,
            languages=query.languages,
            required_fields=query.required_fields,
            search_domains=get_mining_domains() + get_country_specific_domains(query.country),
            time_budget=120  # 2 minutes
        )
        
        # Phase 1: Create research plan
        self.logger.info("Creating research plan...")
        research_plan = await self._create_research_plan(query)
        
        # Phase 2: Execute research steps
        for i, step in enumerate(research_plan):
            self.logger.info(f"Executing step {i+1}: {step.objective}")
            
            step_results = await self._execute_research_step(query, step, context)
            results.extend(step_results)
            
            # Check if we need to adapt
            if i < len(research_plan) - 1:
                remaining_steps = research_plan[i+1:]
                adapted_steps, strategy = self.processor.adapt_research_plan(
                    remaining_steps, results, query
                )
                
                if strategy.adaptation_type != "complete":
                    self.logger.info(f"Adapting research plan: {strategy.adaptation_type}")
                    research_plan[i+1:] = adapted_steps
        
        return results
    
    async def _standard_search(self, query: MineQuery) -> List[SearchResult]:
        """Standard search without advanced reasoning"""
        results = []
        
        # Get search queries
        search_queries = get_mining_search_queries(
            query.mine_name, query.country, query.region, query.required_fields
        )
        
        # Execute searches
        for search_query in search_queries[:3]:  # Limit queries
            prompt = self._create_search_prompt(query, search_query)
            response = await self._make_api_call(prompt)
            
            if response:
                # Extract results
                extracted = self.processor.extract_structured_data(
                    response, query, 
                    ResearchStep(
                        objective="Standard search",
                        strategy="Direct search",
                        sources=["general"],
                        keywords=[search_query],
                        expected_data=query.required_fields
                    )
                )
                results.extend(extracted)
        
        return results
    
    async def _create_research_plan(self, query: MineQuery) -> List[ResearchStep]:
        """Create dynamic research plan"""
        prompt = f"""Create a research plan to find mining data for:
Mine: {query.mine_name}
Location: {query.region}, {query.country}
Required fields: {', '.join(query.required_fields)}

Consider:
1. Government databases and official sources
2. Technical reports and industry publications  
3. Environmental assessments
4. Financial documents
5. News and media coverage

Return a JSON array with research steps, each containing:
- objective: What to find
- strategy: How to search
- sources: Where to look
- keywords: Specific search terms
- expected_data: What fields might be found"""

        response = await self._make_api_call(prompt, temperature=0.3)
        
        if response:
            return await self.processor.create_research_plan(query, response)
        else:
            return self.processor.create_fallback_plan(query)
    
    async def _execute_research_step(self, query: MineQuery, step: ResearchStep,
                                   context: ResearchContext) -> List[SearchResult]:
        """Execute a single research step"""
        results = []
        
        # Create focused prompt
        prompt = self.processor.create_step_prompt(step, context)
        response = await self._make_api_call(prompt, temperature=0.1)
        
        if response:
            # Parse and extract results
            extracted = self.processor.extract_structured_data(response, query, step)
            results.extend(extracted)
        
        return results
    
    async def _make_api_call(self, prompt: str, temperature: float = 0.1) -> Optional[str]:
        """Make API call to DeepSeek"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.use_openrouter:
            headers["HTTP-Referer"] = "https://mining-research.local"
            headers["X-Title"] = "Mining Research System"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert mining research analyst. Extract accurate, specific data with sources."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }
        
        try:
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    self.logger.error(f"API error {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("Request timeout")
            return None
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            return None
    
    def _create_search_prompt(self, query: MineQuery, search_query: str) -> str:
        """Create search prompt for standard search"""
        return f"""Search for information about {query.mine_name} mine in {query.region}, {query.country}.

Search query: {search_query}

Extract specific data for these fields:
{', '.join(query.required_fields)}

Provide:
- Exact values found
- Source of information
- Confidence level
- Any relevant context

Format as structured data."""
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()