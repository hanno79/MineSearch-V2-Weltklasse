"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: DeepSeek Research Agent with advanced research capabilities
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from .enhanced_search import get_mining_search_queries, get_mining_domains, get_country_specific_domains
from ..core.logger import get_logger, PerformanceLogger


class DeepSeekResearchAgent(BaseAgent):
    """DeepSeek Agent with advanced research capabilities"""
    
    # Available models with their capabilities
    MODELS = {
        "chat": {
            "id": "deepseek-chat",
            "name": "DeepSeek Chat",
            "capabilities": ["general", "fast", "multilingual"],
            "cost_per_1k": 0.0001
        },
        "reasoner": {
            "id": "deepseek-reasoner", 
            "name": "DeepSeek Reasoner",
            "capabilities": ["reasoning", "analysis", "complex_queries"],
            "cost_per_1k": 0.0005
        },
        "coder": {
            "id": "deepseek-coder",
            "name": "DeepSeek Coder",
            "capabilities": ["code", "technical", "data_extraction"],
            "cost_per_1k": 0.0001
        }
    }
    
    def __init__(self, name: str, config: Dict[str, Any], model_type: str = "chat"):
        super().__init__(name, config)
        
        # Check if using direct API or OpenRouter
        self.use_openrouter = config.get('use_openrouter', True)
        
        if self.use_openrouter:
            self.api_key = config['api_config'].openrouter_key
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = f"deepseek/{self.MODELS[model_type]['id']}"
        else:
            # Direct DeepSeek API (wenn verfügbar)
            self.api_key = config['api_config'].get('deepseek_key')
            self.base_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = self.MODELS[model_type]['id']
        
        self.model_type = model_type
        self._rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 requests per minute
        self.logger = get_logger(f"agent.{name}", agent_type="deepseek")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes for complex research
        
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
                headers.update({
                    "HTTP-Referer": "https://minesearch.app",
                    "X-Title": "MineSearch"
                })
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
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
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Execute advanced mining research with DeepSeek"""
        results = []
        
        self.perf_logger.start_timer(f"deepseek_research_{query.mine_name}")
        
        try:
            # Phase 1: Research Planning
            research_plan = await self._create_research_plan(query)
            self.logger.info(f"Created research plan with {len(research_plan)} steps")
            
            # Phase 2: Execute Research Steps
            for step_idx, step in enumerate(research_plan):
                self.logger.info(f"Executing research step {step_idx + 1}/{len(research_plan)}: {step['objective']}")
                
                step_results = await self._execute_research_step(query, step)
                results.extend(step_results)
                
                # Adaptive research - adjust plan based on findings
                if step_idx < len(research_plan) - 1:
                    research_plan = await self._adapt_research_plan(
                        research_plan[step_idx + 1:], 
                        step_results,
                        query
                    )
            
            # Phase 3: Deep Analysis & Synthesis
            if results:
                synthesized_results = await self._synthesize_findings(results, query)
                results.extend(synthesized_results)
            
            self.perf_logger.end_timer(
                f"deepseek_research_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during research: {e}")
            self.stats['failed_requests'] += 1
            return results
    
    async def _create_research_plan(self, query: MineQuery) -> List[Dict[str, Any]]:
        """Create multi-step research plan"""
        
        # Get comprehensive search queries
        search_queries = get_mining_search_queries(
            query.mine_name,
            query.region, 
            query.country,
            query.required_fields
        )
        
        # Get relevant domains
        domains = get_mining_domains()
        if query.country:
            domains.extend(get_country_specific_domains(query.country))
        
        prompt = f"""Create a comprehensive research plan to find detailed information about the {query.mine_name} mine.

Location: {query.region}, {query.country}
Required Information: {', '.join(query.required_fields)}
Available Languages: {', '.join(query.languages)}

Based on these search patterns:
{json.dumps(search_queries[:10], indent=2)}

And these priority domains:
{json.dumps(domains[:15], indent=2)}

Create a step-by-step research plan with specific objectives and search strategies.
Each step should focus on different aspects or sources.

Return a JSON array with research steps, each containing:
- objective: What to find
- strategy: How to search
- sources: Where to look
- keywords: Specific search terms
- expected_data: What fields might be found"""

        response = await self._make_api_call(prompt, temperature=0.3)
        
        if response:
            # Extract JSON from response
            try:
                if isinstance(response, str):
                    # Find JSON in response
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        plan = json.loads(json_match.group())
                    else:
                        # Fallback plan
                        plan = self._create_fallback_plan(query)
                else:
                    plan = response
                    
                return plan[:5]  # Limit to 5 steps
            except:
                return self._create_fallback_plan(query)
        
        return self._create_fallback_plan(query)
    
    def _create_fallback_plan(self, query: MineQuery) -> List[Dict[str, Any]]:
        """Create fallback research plan"""
        return [
            {
                "objective": "Find basic mine information and operator",
                "strategy": "Search government databases and company websites",
                "sources": ["government", "company"],
                "keywords": [f'"{query.mine_name}" operator owner company'],
                "expected_data": ["betreiber", "operator", "status"]
            },
            {
                "objective": "Locate technical and production data",
                "strategy": "Search technical reports and industry publications",
                "sources": ["technical", "industry"],
                "keywords": [f'"{query.mine_name}" production capacity technical report'],
                "expected_data": ["koordinaten", "produktion", "rohstofftyp"]
            },
            {
                "objective": "Find environmental and financial information",
                "strategy": "Search environmental assessments and financial reports",
                "sources": ["environmental", "financial"],
                "keywords": [f'"{query.mine_name}" environmental impact remediation costs'],
                "expected_data": ["sanierungskosten", "umweltauswirkungen"]
            }
        ]
    
    async def _execute_research_step(self, query: MineQuery, step: Dict[str, Any]) -> List[SearchResult]:
        """Execute a single research step"""
        results = []
        
        # Create focused prompt for this step
        prompt = f"""Research Task: {step['objective']}

Mine: {query.mine_name}
Location: {query.region}, {query.country}
Strategy: {step['strategy']}

Search using these keywords: {', '.join(step['keywords'])}
Focus on these sources: {', '.join(step['sources'])}
Extract data for: {', '.join(step['expected_data'])}

Provide detailed findings with:
1. Specific data values found
2. Source of information
3. Confidence level
4. Date/year of information
5. Any contradictions or uncertainties

Format findings as structured data."""

        response = await self._make_api_call(prompt, temperature=0.1)
        
        if response:
            # Parse and extract results
            extracted = self._extract_structured_data(response, query, step)
            results.extend(extracted)
        
        return results
    
    async def _adapt_research_plan(self, remaining_steps: List[Dict[str, Any]], 
                                  recent_findings: List[SearchResult],
                                  query: MineQuery) -> List[Dict[str, Any]]:
        """Adapt research plan based on findings"""
        
        # Check what fields were found
        found_fields = set(r.field_name for r in recent_findings)
        missing_fields = set(query.required_fields) - found_fields
        
        if not missing_fields:
            return remaining_steps  # Continue as planned
        
        # Create prompt to adapt plan
        prompt = f"""Based on recent findings, adapt the research plan.

Missing fields: {', '.join(missing_fields)}
Found fields: {', '.join(found_fields)}

Recent findings summary:
{self._summarize_findings(recent_findings[:5])}

Remaining research steps:
{json.dumps(remaining_steps, indent=2)}

Should we:
1. Continue with the existing plan?
2. Add new search strategies for missing fields?
3. Try alternative sources?

Provide adapted research steps focusing on missing information."""

        response = await self._make_api_call(prompt, temperature=0.5)
        
        # Return original plan if adaptation fails
        return remaining_steps
    
    async def _synthesize_findings(self, results: List[SearchResult], 
                                 query: MineQuery) -> List[SearchResult]:
        """Synthesize and validate findings"""
        synthesized = []
        
        # Group results by field
        field_groups = {}
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        # Synthesize each field
        for field, field_results in field_groups.items():
            if len(field_results) > 1:
                # Multiple values found - need synthesis
                synthesis_prompt = f"""Analyze these findings for {field} of {query.mine_name}:

{self._format_field_results(field_results)}

Tasks:
1. Identify the most reliable/recent value
2. Explain any discrepancies
3. Provide confidence assessment
4. Suggest the best value to use

Return structured analysis."""

                response = await self._make_api_call(synthesis_prompt, temperature=0.1)
                
                if response:
                    # Create synthesized result
                    best_value = self._extract_best_value(response, field_results)
                    if best_value:
                        synthesized.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=best_value['value'],
                            source="DeepSeek Research Synthesis",
                            source_url="",
                            source_date=best_value.get('year'),
                            confidence_score=best_value.get('confidence', 0.8),
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                "synthesis": True,
                                "sources_analyzed": len(field_results),
                                "reasoning": best_value.get('reasoning', '')
                            }
                        ))
        
        return synthesized
    
    def _summarize_findings(self, findings: List[SearchResult]) -> str:
        """Summarize findings for prompt"""
        summary = []
        for f in findings:
            summary.append(f"- {f.field_name}: {f.value} (confidence: {f.confidence_score:.2f})")
        return "\n".join(summary)
    
    def _format_field_results(self, results: List[SearchResult]) -> str:
        """Format field results for analysis"""
        formatted = []
        for r in results:
            formatted.append(
                f"Value: {r.value}\n"
                f"Source: {r.source}\n"
                f"Date: {r.source_date or 'Unknown'}\n"
                f"Confidence: {r.confidence_score:.2f}\n"
            )
        return "\n---\n".join(formatted)
    
    def _extract_structured_data(self, response: str, query: MineQuery, 
                               step: Dict[str, Any]) -> List[SearchResult]:
        """Extract structured data from response"""
        results = []
        
        # Use parent's extraction methods with enhancements
        for field in query.required_fields:
            if field in step.get('expected_data', []):
                extracted_values = self._extract_with_context(response, field)
                
                for value, confidence in extracted_values:
                    if confidence >= 0.4:  # Lower threshold for research
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=value,
                            source=f"DeepSeek Research: {step['objective']}",
                            source_url="",
                            source_date=self._extract_year_from_text(response),
                            confidence_score=confidence,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                "research_step": step['objective'],
                                "model": self.model_type,
                                "strategy": step['strategy']
                            }
                        )
                        results.append(result)
        
        return results
    
    def _extract_best_value(self, analysis: str, candidates: List[SearchResult]) -> Optional[Dict[str, Any]]:
        """Extract best value from synthesis analysis"""
        # Simple extraction - can be enhanced
        if candidates:
            # Sort by confidence and recency
            sorted_candidates = sorted(
                candidates,
                key=lambda x: (x.confidence_score, x.source_date or 0),
                reverse=True
            )
            
            best = sorted_candidates[0]
            return {
                'value': best.value,
                'confidence': min(0.95, best.confidence_score * 1.1),  # Boost confidence
                'year': best.source_date,
                'reasoning': f"Selected from {len(candidates)} sources"
            }
        
        return None
    
    async def _make_api_call(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Make API call to DeepSeek"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.use_openrouter:
            headers.update({
                "HTTP-Referer": "https://minesearch.app",
                "X-Title": "MineSearch Research"
            })
        
        # Enhanced system prompt for research
        system_prompt = """You are an expert mining industry researcher with access to comprehensive databases.
Your task is to find accurate, detailed information about mines worldwide.
Always provide specific values, dates, and sources when available.
Be precise with technical details and financial figures.
Cross-reference information for accuracy."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
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
                    self.logger.error(f"API error: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API request timeout")
            return None
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info(f"DeepSeek Research Agent ({self.model_type}) terminated")