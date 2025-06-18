"""
OpenRouter Agent for accessing multiple free LLMs
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import json
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains
import asyncio

logger = get_logger(__name__)


@dataclass
class OpenRouterModel:
    """OpenRouter model configuration"""
    id: str
    name: str
    provider: str
    is_free: bool
    context_length: int
    description: str


class OpenRouterAgent(BaseAgent):
    """Agent that uses OpenRouter API to access multiple LLMs"""
    
    # Premium models for best performance (Updated 2025)
    PREMIUM_MODELS = {
        "anthropic/claude-3.5-sonnet-20241022": OpenRouterModel(
            id="anthropic/claude-3.5-sonnet-20241022",
            name="Claude 3.5 Sonnet (Latest)",
            provider="Anthropic",
            is_free=False,
            context_length=200000,
            description="Latest Claude 3.5 Sonnet with improved performance"
        ),
        "anthropic/claude-3-opus": OpenRouterModel(
            id="anthropic/claude-3-opus",
            name="Claude 3 Opus",
            provider="Anthropic",
            is_free=False,
            context_length=200000,
            description="Claude's most powerful model for complex tasks"
        ),
        "google/gemini-2.0-flash-exp:free": OpenRouterModel(
            id="google/gemini-2.0-flash-exp:free",
            name="Gemini 2.0 Flash (Free)",
            provider="Google",
            is_free=True,
            context_length=1048576,
            description="Google's latest Gemini 2.0 Flash with 1M context"
        ),
        "google/gemini-pro-1.5": OpenRouterModel(
            id="google/gemini-pro-1.5",
            name="Gemini 1.5 Pro",
            provider="Google",
            is_free=False,
            context_length=2097152,
            description="Google's Gemini Pro with 2M context window"
        ),
        "google/gemini-2.0-flash-thinking-exp-1219:free": OpenRouterModel(
            id="google/gemini-2.0-flash-thinking-exp-1219:free",
            name="Gemini 2.0 Flash Thinking (Free)",
            provider="Google",
            is_free=True,
            context_length=65536,
            description="Reasoning model for complex problem solving"
        ),
        "x-ai/grok-2-1212": OpenRouterModel(
            id="x-ai/grok-2-1212",
            name="Grok 2 (Latest)",
            provider="xAI",
            is_free=False,
            context_length=131072,
            description="Latest Grok with real-time search capabilities"
        ),
        "openai/gpt-4o": OpenRouterModel(
            id="openai/gpt-4o",
            name="GPT-4o",
            provider="OpenAI",
            is_free=False,
            context_length=128000,
            description="OpenAI's GPT-4 Omni model"
        ),
        "openai/gpt-4o-2024-11-20": OpenRouterModel(
            id="openai/gpt-4o-2024-11-20",
            name="GPT-4o (Latest)",
            provider="OpenAI",
            is_free=False,
            context_length=128000,
            description="Latest GPT-4o with improved capabilities"
        ),
        "openai/o1": OpenRouterModel(
            id="openai/o1",
            name="OpenAI o1",
            provider="OpenAI",
            is_free=False,
            context_length=200000,
            description="Advanced reasoning model for complex tasks"
        ),
        "openai/o1-preview": OpenRouterModel(
            id="openai/o1-preview",
            name="OpenAI o1 Preview",
            provider="OpenAI",
            is_free=False,
            context_length=128000,
            description="Preview of OpenAI's reasoning model"
        ),
        "meta-llama/llama-3.1-405b-instruct": OpenRouterModel(
            id="meta-llama/llama-3.1-405b-instruct",
            name="Llama 3.1 405B",
            provider="Meta",
            is_free=False,
            context_length=128000,
            description="Meta's largest open model with 405B parameters"
        )
    }
    
    # Free tier models with strong performance
    FREE_MODELS = {
        "deepseek/deepseek-chat": OpenRouterModel(
            id="deepseek/deepseek-chat",
            name="DeepSeek Chat",
            provider="DeepSeek",
            is_free=True,
            context_length=32768,
            description="DeepSeek's latest chat model with strong reasoning"
        ),
        "qwen/qwen-2.5-72b-instruct": OpenRouterModel(
            id="qwen/qwen-2.5-72b-instruct",
            name="Qwen 2.5 72B",
            provider="Alibaba",
            is_free=True,
            context_length=32768,
            description="Alibaba's powerful 72B parameter model"
        ),
        "mistralai/mistral-7b-instruct": OpenRouterModel(
            id="mistralai/mistral-7b-instruct",
            name="Mistral 7B Instruct",
            provider="Mistral AI",
            is_free=True,
            context_length=32768,
            description="Mistral's efficient 7B instruction model"
        ),
        "meta-llama/llama-3.2-90b-instruct": OpenRouterModel(
            id="meta-llama/llama-3.2-90b-instruct",
            name="Llama 3.2 90B",
            provider="Meta",
            is_free=True,
            context_length=128000,
            description="Meta's latest 90B Llama model"
        ),
        "google/gemma-2-27b-it": OpenRouterModel(
            id="google/gemma-2-27b-it",
            name="Gemma 2 27B",
            provider="Google",
            is_free=True,
            context_length=8192,
            description="Google's Gemma 2 instruction-tuned model"
        ),
        "nousresearch/hermes-3-llama-3.1-70b": OpenRouterModel(
            id="nousresearch/hermes-3-llama-3.1-70b",
            name="Hermes 3 Llama 70B",
            provider="Nous Research",
            is_free=True,
            context_length=128000,
            description="Fine-tuned Llama for complex tasks"
        )
    }
    
    def __init__(self, api_key: str, model_id: str = "deepseek/deepseek-chat"):
        """Initialize OpenRouter agent"""
        super().__init__(name=f"openrouter_{model_id.split('/')[-1].split(':')[0]}")
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Set model - check both free and premium
        if model_id in self.FREE_MODELS:
            self.model = self.FREE_MODELS[model_id]
        elif model_id in self.PREMIUM_MODELS:
            self.model = self.PREMIUM_MODELS[model_id]
        else:
            # Default to DeepSeek if invalid model
            logger.warning(f"Unknown model {model_id}, using DeepSeek")
            self.model = self.FREE_MODELS["deepseek/deepseek-chat"]
        
        self.model_id = self.model.id
        logger.info(f"Initialized OpenRouter agent with model: {self.model.name} ({'Free' if self.model.is_free else 'Premium'})")
        self.perf_logger = PerformanceLogger(logger)
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Enhanced mining search using OpenRouter LLM with multiple queries"""
        all_results = []
        
        self.perf_logger.start_timer("openrouter_search")
        
        try:
            # Get enhanced mining queries
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Create multiple specialized prompts
            prompts = [
                self._build_comprehensive_prompt(query, mining_queries[:5]),
                self._build_technical_prompt(query),
                self._build_environmental_prompt(query),
                self._build_financial_prompt(query),
                self._build_operational_prompt(query)
            ]
            
            # Status update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"OpenRouter: Starting {len(prompts)} specialized mining searches")
            
            # Execute searches with different prompts
            for idx, prompt in enumerate(prompts):
                try:
                    # Status update
                    if hasattr(self, 'status_callback') and self.status_callback:
                        prompt_type = ['comprehensive', 'technical', 'environmental', 'financial', 'operational'][idx]
                        await self.status_callback(f"OpenRouter: {prompt_type} search ({idx+1}/{len(prompts)})")
                    
                    results = await self._execute_search(query, prompt)
                    all_results.extend(results)
                    
                    # Respect rate limits
                    await asyncio.sleep(2.0)
                    
                except Exception as e:
                    logger.error(f"OpenRouter prompt {idx} error: {str(e)}")
            
            logger.info(f"OpenRouter ({self.model.name}) found {len(all_results)} total results")
            self.perf_logger.end_timer("openrouter_search", results_found=len(all_results))
            return all_results
                    
        except Exception as e:
            logger.error(f"OpenRouter search error: {str(e)}")
            self.perf_logger.end_timer("openrouter_search", error=str(e))
            return all_results
    
    async def _execute_search(self, query: MineQuery, prompt: str) -> List[SearchResult]:
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
                        "content": """You are an expert mining research specialist with deep knowledge of:
- Mining operations and mineral extraction
- Environmental remediation and closure costs
- Mining regulations and compliance
- Geological surveys and resource estimates
- Mining company structures and ownership
- Technical mining reports (NI 43-101, JORC)
- Mining databases and government registries

Provide accurate, detailed information with specific sources."""
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
                        logger.error(f"OpenRouter API error: {error_text}")
                        return []
                    
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Parse response
                    results = self._parse_response(content, query)
                    
                    logger.info(f"OpenRouter ({self.model.name}) found {len(results)} results")
                    return results
                    
        except Exception as e:
            logger.error(f"OpenRouter search error: {str(e)}")
            return []
    
    def _build_comprehensive_prompt(self, query: MineQuery, search_queries: List[str]) -> str:
        """Build comprehensive mining search prompt"""
        fields_str = ", ".join(query.required_fields)
        queries_str = "\n".join([f"- {q}" for q in search_queries[:5]])
        domains_str = ", ".join(get_mining_domains()[:10])
        
        prompt = f"""You are conducting a comprehensive search for detailed information about a mine.

Mine Name: {query.mine_name}
Region: {query.region}
Country: {query.country}

Use these search strategies:
{queries_str}

Prioritize information from these mining-specific sources:
{domains_str}

Required fields to find:
{fields_str}

For each field, provide:
1. Field name (exactly as listed)
2. The precise value/information
3. The specific source (website, report, database)
4. Date of information (if available)
5. Confidence level (0-1)

Important mining-specific details to look for:
- NI 43-101 or JORC technical reports
- Government mining registries and databases
- Environmental bonds and closure costs
- Production data and reserves
- Exact GPS coordinates
- Current operational status
- Ownership structure and operators

Format as JSON array:
[
  {{
    "field": "betreiber",
    "value": "Company Name Inc.",
    "source": "SEDAR NI 43-101 Report 2024",
    "date": "2024",
    "confidence": 0.95
  }}
]

Be specific and accurate. Include units for all measurements."""
        return prompt
    
    def _build_technical_prompt(self, query: MineQuery) -> str:
        """Build technical mining data prompt"""
        return f"""Search for technical mining data for {query.mine_name} mine in {query.region}, {query.country}:

Focus on:
1. Resource estimates and reserves (proven, probable, measured, indicated)
2. Production capacity and annual output
3. Mine type (open-pit, underground, heap leach, etc.)
4. Processing methods and recovery rates
5. Mine life and expansion plans
6. Infrastructure (power, water, transportation)
7. Exact coordinates (latitude, longitude)

Search in:
- NI 43-101 technical reports
- JORC reports
- Company technical disclosures
- Government mining databases
- Geological surveys

Provide data in JSON format with sources and confidence scores."""
    
    def _build_environmental_prompt(self, query: MineQuery) -> str:
        """Build environmental and closure cost prompt"""
        return f"""Search for environmental and closure information for {query.mine_name} mine in {query.region}, {query.country}:

Specific focus on:
1. Environmental remediation costs
2. Closure bonds and financial assurance
3. Rehabilitation obligations
4. Tailings management costs
5. Water treatment requirements
6. Environmental liabilities
7. Government-mandated cleanup costs

Search in:
- Environmental impact assessments
- Government environmental databases
- Company annual reports (environmental liabilities section)
- Securities filings (asset retirement obligations)
- Environmental agency reports
- Mining regulatory body publications

Provide specific dollar amounts, currencies, and dates in JSON format."""
    
    def _build_financial_prompt(self, query: MineQuery) -> str:
        """Build financial and ownership prompt"""
        return f"""Search for financial and ownership data for {query.mine_name} mine in {query.region}, {query.country}:

Focus on:
1. Current owner/operator company
2. Ownership percentage and joint ventures
3. Parent company structure
4. Historical ownership changes
5. Market capitalization of owner
6. Recent transactions or acquisitions
7. Royalty agreements

Search in:
- SEDAR filings
- SEC EDGAR database
- Stock exchange announcements
- Company investor presentations
- M&A databases
- Mining industry news

Provide current ownership structure in JSON format."""
    
    def _build_operational_prompt(self, query: MineQuery) -> str:
        """Build operational status prompt"""
        return f"""Search for current operational status of {query.mine_name} mine in {query.region}, {query.country}:

Determine:
1. Current operational status (operating, suspended, closed, care & maintenance)
2. Production start date
3. Closure or suspension dates
4. Reasons for status changes
5. Number of employees
6. Recent operational updates
7. Planned restart dates (if applicable)

Search in:
- Recent company press releases
- Mining news websites
- Government mining reports
- Industry publications
- Local news sources

Provide current status with dates in JSON format."""
    
    def _parse_response(self, content: str, query: MineQuery) -> List[SearchResult]:
        """Parse LLM response into SearchResults"""
        results = []
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                for item in data:
                    if all(k in item for k in ['field', 'value', 'confidence']):
                        # Map field names to German if needed
                        field_mapping = {
                            'operator': 'betreiber',
                            'owner': 'betreiber',
                            'coordinates': 'koordinaten',
                            'location': 'koordinaten',
                            'remediation_cost': 'sanierungskosten',
                            'closure_cost': 'sanierungskosten',
                            'environmental_bond': 'sanierungskosten',
                            'commodity': 'rohstofftyp',
                            'mineral': 'rohstofftyp',
                            'status': 'aktivitaetsstatus',
                            'operational_status': 'aktivitaetsstatus',
                            'production': 'jahresproduktion',
                            'annual_production': 'jahresproduktion'
                        }
                        
                        field_name = item['field'].lower().replace(' ', '_')
                        field_name = field_mapping.get(field_name, field_name)
                        
                        result = SearchResult(
                            field_name=field_name,
                            value=str(item['value']),
                            source=item.get('source', f'OpenRouter {self.model.name}'),
                            confidence_score=float(item['confidence']),
                            agent_name=self.name,
                            found_at=datetime.now(),
                            mine_id=None,  # Will be set by orchestrator
                            metadata={
                                'model': self.model.name,
                                'date': item.get('date', ''),
                                'search_type': 'llm_mining_search'
                            }
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Failed to parse OpenRouter response: {str(e)}")
            
            # Fallback: try to extract any useful information
            try:
                for field in query.required_fields:
                    if field.lower() in content.lower():
                        # Try to extract value near field mention
                        lines = content.split('\n')
                        for line in lines:
                            if field.lower() in line.lower():
                                result = SearchResult(
                                    field_name=field,
                                    value=line.strip(),
                                    source=f"OpenRouter {self.model.name}",
                                    confidence_score=0.5,
                                    agent_name=self.name,
                                    found_at=datetime.now(),
                                    mine_id=None
                                )
                                results.append(result)
                                break
            except:
                pass
        
        return results
    
    async def initialize(self) -> bool:
        """Initialize the agent"""
        return await self.validate()
    
    async def validate_credentials(self) -> bool:
        """Validate API credentials"""
        return await self.validate()
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Main search method for base agent compatibility"""
        return await self.search(query)
    
    async def validate(self) -> bool:
        """Validate OpenRouter credentials"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Simple test query
            payload = {
                "model": self.model_id,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"OpenRouter validation error: {str(e)}")
            return False
    
    @classmethod
    def get_available_models(cls) -> Dict[str, OpenRouterModel]:
        """Get all available models"""
        all_models = {}
        all_models.update(cls.FREE_MODELS)
        all_models.update(cls.PREMIUM_MODELS)
        return all_models