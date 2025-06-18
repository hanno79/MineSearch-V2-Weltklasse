"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: Research Orchestrator for intelligent multi-agent coordination
"""

import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

from .base_agent import BaseAgent, MineQuery, SearchResult
from .deepseek_research_agent import DeepSeekResearchAgent
from .factory import AgentFactory
from ..core.config import Config
from ..core.logger import get_logger


class TaskType(Enum):
    """Different types of research tasks"""
    DISCOVERY = "discovery"  # Find new sources
    EXTRACTION = "extraction"  # Extract specific data
    VALIDATION = "validation"  # Validate findings
    SYNTHESIS = "synthesis"  # Combine and analyze
    DEEP_DIVE = "deep_dive"  # Detailed investigation


class AgentCapability(Enum):
    """Agent capabilities for task assignment"""
    WEB_SEARCH = "web_search"
    DEEP_RESEARCH = "deep_research"
    SCRAPING = "scraping"
    REASONING = "reasoning"
    MULTILINGUAL = "multilingual"
    TECHNICAL = "technical"
    FINANCIAL = "financial"


@dataclass
class ResearchTask:
    """A research task with dependencies"""
    id: str
    type: TaskType
    objective: str
    fields: List[str]
    dependencies: List[str]  # Task IDs this depends on
    assigned_agents: List[str]
    priority: int
    status: str = "pending"
    results: List[SearchResult] = None
    

class ResearchOrchestrator:
    """Orchestrates complex research across multiple agents"""
    
    # Agent capability mapping
    AGENT_CAPABILITIES = {
        "tavily": [AgentCapability.WEB_SEARCH, AgentCapability.MULTILINGUAL],
        "perplexity": [AgentCapability.WEB_SEARCH, AgentCapability.DEEP_RESEARCH],
        "exa": [AgentCapability.WEB_SEARCH, AgentCapability.TECHNICAL],
        "claude": [AgentCapability.REASONING, AgentCapability.DEEP_RESEARCH, AgentCapability.MULTILINGUAL],
        "gpt4": [AgentCapability.REASONING, AgentCapability.TECHNICAL, AgentCapability.FINANCIAL],
        "deepseek": [AgentCapability.DEEP_RESEARCH, AgentCapability.REASONING],
        "deepseek_reasoner": [AgentCapability.REASONING, AgentCapability.DEEP_RESEARCH],
        "firecrawl": [AgentCapability.SCRAPING, AgentCapability.TECHNICAL],
        "brightdata": [AgentCapability.SCRAPING, AgentCapability.MULTILINGUAL],
        "scraper": [AgentCapability.SCRAPING],
        "scrapingbee": [AgentCapability.SCRAPING],
        "apify": [AgentCapability.SCRAPING, AgentCapability.TECHNICAL]
    }
    
    def __init__(self, config: Config, available_agents: List[str]):
        self.config = config
        self.available_agents = available_agents
        self.logger = get_logger("research_orchestrator")
        self.agent_instances = {}
        self.task_results = {}
        
    async def execute_research(self, query: MineQuery) -> List[SearchResult]:
        """Execute comprehensive research with intelligent orchestration"""
        self.logger.info(f"Starting orchestrated research for {query.mine_name}")
        
        # Phase 1: Create research plan
        research_plan = self._create_research_plan(query)
        self.logger.info(f"Created research plan with {len(research_plan)} tasks")
        
        # Phase 2: Initialize required agents
        await self._initialize_agents(research_plan)
        
        # Phase 3: Execute tasks with dependency management
        all_results = await self._execute_research_plan(research_plan, query)
        
        # Phase 4: Cross-validate results
        validated_results = await self._cross_validate_results(all_results, query)
        
        # Phase 5: Final synthesis
        final_results = await self._synthesize_final_results(validated_results, query)
        
        self.logger.info(f"Research completed with {len(final_results)} results")
        return final_results
    
    def _create_research_plan(self, query: MineQuery) -> List[ResearchTask]:
        """Create intelligent research plan with task dependencies"""
        tasks = []
        task_counter = 0
        
        # Task 1: Source Discovery
        discovery_task = ResearchTask(
            id=f"task_{task_counter}",
            type=TaskType.DISCOVERY,
            objective="Discover relevant sources and databases",
            fields=[],  # All fields
            dependencies=[],
            assigned_agents=self._select_agents_for_capability(
                [AgentCapability.WEB_SEARCH], 
                max_agents=5
            ),
            priority=1
        )
        tasks.append(discovery_task)
        task_counter += 1
        
        # Task 2-4: Field-specific extraction (depends on discovery)
        field_groups = self._group_fields_by_type(query.required_fields)
        
        for group_name, fields in field_groups.items():
            extraction_task = ResearchTask(
                id=f"task_{task_counter}",
                type=TaskType.EXTRACTION,
                objective=f"Extract {group_name} information",
                fields=fields,
                dependencies=[discovery_task.id],
                assigned_agents=self._select_agents_for_field_group(group_name),
                priority=2
            )
            tasks.append(extraction_task)
            task_counter += 1
        
        # Task 5: Deep research for missing/complex fields
        deep_task = ResearchTask(
            id=f"task_{task_counter}",
            type=TaskType.DEEP_DIVE,
            objective="Deep research for complex or missing data",
            fields=query.required_fields,
            dependencies=[t.id for t in tasks if t.type == TaskType.EXTRACTION],
            assigned_agents=self._select_agents_for_capability(
                [AgentCapability.DEEP_RESEARCH, AgentCapability.REASONING],
                max_agents=3
            ),
            priority=3
        )
        tasks.append(deep_task)
        task_counter += 1
        
        # Task 6: Validation
        validation_task = ResearchTask(
            id=f"task_{task_counter}",
            type=TaskType.VALIDATION,
            objective="Validate and cross-reference findings",
            fields=query.required_fields,
            dependencies=[deep_task.id],
            assigned_agents=self._select_agents_for_capability(
                [AgentCapability.REASONING],
                max_agents=2
            ),
            priority=4
        )
        tasks.append(validation_task)
        task_counter += 1
        
        # Task 7: Final synthesis
        synthesis_task = ResearchTask(
            id=f"task_{task_counter}",
            type=TaskType.SYNTHESIS,
            objective="Synthesize all findings into final results",
            fields=query.required_fields,
            dependencies=[validation_task.id],
            assigned_agents=self._select_best_synthesis_agents(),
            priority=5
        )
        tasks.append(synthesis_task)
        
        return tasks
    
    def _group_fields_by_type(self, fields: List[str]) -> Dict[str, List[str]]:
        """Group fields by their type for specialized extraction"""
        groups = {
            "operational": [],
            "financial": [],
            "environmental": [],
            "technical": []
        }
        
        for field in fields:
            field_lower = field.lower()
            if any(term in field_lower for term in ["operator", "betreiber", "status", "production"]):
                groups["operational"].append(field)
            elif any(term in field_lower for term in ["cost", "kosten", "financial", "investment"]):
                groups["financial"].append(field)
            elif any(term in field_lower for term in ["environmental", "umwelt", "restoration"]):
                groups["environmental"].append(field)
            else:
                groups["technical"].append(field)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _select_agents_for_capability(self, capabilities: List[AgentCapability], 
                                    max_agents: int = 5) -> List[str]:
        """Select best agents for given capabilities"""
        scored_agents = {}
        
        for agent in self.available_agents:
            if agent in self.AGENT_CAPABILITIES:
                agent_caps = self.AGENT_CAPABILITIES[agent]
                # Score based on capability match
                score = sum(1 for cap in capabilities if cap in agent_caps)
                if score > 0:
                    scored_agents[agent] = score
        
        # Sort by score and return top agents
        sorted_agents = sorted(scored_agents.items(), key=lambda x: x[1], reverse=True)
        return [agent for agent, _ in sorted_agents[:max_agents]]
    
    def _select_agents_for_field_group(self, group_name: str) -> List[str]:
        """Select agents based on field group"""
        if group_name == "financial":
            return self._select_agents_for_capability(
                [AgentCapability.FINANCIAL, AgentCapability.REASONING]
            )
        elif group_name == "environmental":
            return self._select_agents_for_capability(
                [AgentCapability.WEB_SEARCH, AgentCapability.MULTILINGUAL]
            )
        elif group_name == "technical":
            return self._select_agents_for_capability(
                [AgentCapability.TECHNICAL, AgentCapability.SCRAPING]
            )
        else:  # operational
            return self._select_agents_for_capability(
                [AgentCapability.WEB_SEARCH, AgentCapability.SCRAPING]
            )
    
    def _select_best_synthesis_agents(self) -> List[str]:
        """Select best agents for synthesis"""
        # Prefer reasoning agents for synthesis
        reasoning_agents = self._select_agents_for_capability(
            [AgentCapability.REASONING, AgentCapability.DEEP_RESEARCH],
            max_agents=3
        )
        
        # Ensure we have at least one agent
        if not reasoning_agents and self.available_agents:
            reasoning_agents = [self.available_agents[0]]
        
        return reasoning_agents
    
    async def _initialize_agents(self, tasks: List[ResearchTask]):
        """Initialize all required agents"""
        required_agents = set()
        for task in tasks:
            required_agents.update(task.assigned_agents)
        
        self.logger.info(f"Initializing {len(required_agents)} agents")
        
        for agent_name in required_agents:
            if agent_name not in self.agent_instances:
                try:
                    agent = AgentFactory.create_agent(agent_name, self.config)
                    if agent:
                        success = await agent.initialize()
                        if success:
                            self.agent_instances[agent_name] = agent
                            self.logger.info(f"Initialized agent: {agent_name}")
                        else:
                            self.logger.warning(f"Failed to initialize agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Error creating agent {agent_name}: {e}")
    
    async def _execute_research_plan(self, tasks: List[ResearchTask], 
                                   query: MineQuery) -> List[SearchResult]:
        """Execute research plan with dependency management"""
        all_results = []
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = [
                task for task in tasks
                if task.status == "pending" and
                all(dep in completed_tasks for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                self.logger.warning("No tasks ready, possible circular dependency")
                break
            
            # Execute ready tasks in parallel
            task_results = await asyncio.gather(*[
                self._execute_task(task, query) for task in ready_tasks
            ])
            
            # Update task status and collect results
            for task, results in zip(ready_tasks, task_results):
                task.status = "completed"
                task.results = results
                completed_tasks.add(task.id)
                self.task_results[task.id] = results
                all_results.extend(results)
                
                self.logger.info(
                    f"Completed task {task.id}: {task.objective} "
                    f"({len(results)} results)"
                )
        
        return all_results
    
    async def _execute_task(self, task: ResearchTask, query: MineQuery) -> List[SearchResult]:
        """Execute a single research task"""
        results = []
        
        # Get previous results for context
        context_results = []
        for dep_id in task.dependencies:
            if dep_id in self.task_results:
                context_results.extend(self.task_results[dep_id])
        
        # Create specialized query for this task
        task_query = MineQuery(
            mine_name=query.mine_name,
            region=query.region,
            country=query.country,
            languages=query.languages,
            required_fields=task.fields if task.fields else query.required_fields
        )
        
        # Execute with each assigned agent
        agent_tasks = []
        for agent_name in task.assigned_agents:
            if agent_name in self.agent_instances:
                agent = self.agent_instances[agent_name]
                
                # Add context to agent if supported
                if hasattr(agent, 'set_context'):
                    agent.set_context(context_results)
                
                agent_tasks.append(agent.execute_search(task_query))
        
        # Execute all agent searches in parallel
        if agent_tasks:
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            for agent_result in agent_results:
                if isinstance(agent_result, list):
                    results.extend(agent_result)
                elif isinstance(agent_result, Exception):
                    self.logger.error(f"Agent error in task {task.id}: {agent_result}")
        
        return results
    
    async def _cross_validate_results(self, results: List[SearchResult], 
                                    query: MineQuery) -> List[SearchResult]:
        """Cross-validate results between different sources"""
        validated = []
        
        # Group results by field
        field_groups = {}
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        # Validate each field
        for field, field_results in field_groups.items():
            if len(field_results) == 1:
                # Single source - pass through with adjusted confidence
                result = field_results[0]
                result.confidence_score *= 0.8  # Lower confidence for single source
                validated.append(result)
            else:
                # Multiple sources - validate
                validated_result = self._validate_field_results(field_results)
                if validated_result:
                    validated.append(validated_result)
        
        return validated
    
    def _validate_field_results(self, results: List[SearchResult]) -> Optional[SearchResult]:
        """Validate multiple results for the same field"""
        if not results:
            return None
        
        # Group by value
        value_groups = {}
        for result in results:
            value_str = str(result.value)
            if value_str not in value_groups:
                value_groups[value_str] = []
            value_groups[value_str].append(result)
        
        # Find consensus value
        if len(value_groups) == 1:
            # All sources agree
            best_result = max(results, key=lambda r: r.confidence_score)
            best_result.confidence_score = min(0.95, best_result.confidence_score * 1.2)
            best_result.metadata['validation'] = f"Confirmed by {len(results)} sources"
            return best_result
        else:
            # Sources disagree - pick most common or highest confidence
            most_common = max(value_groups.items(), key=lambda x: len(x[1]))
            if len(most_common[1]) >= len(results) / 2:
                # Majority agreement
                best_result = max(most_common[1], key=lambda r: r.confidence_score)
                best_result.confidence_score = min(0.85, best_result.confidence_score * 1.1)
                best_result.metadata['validation'] = f"Majority agreement ({len(most_common[1])}/{len(results)} sources)"
                return best_result
            else:
                # No clear consensus - pick highest confidence
                best_result = max(results, key=lambda r: r.confidence_score)
                best_result.confidence_score *= 0.9  # Lower confidence due to disagreement
                best_result.metadata['validation'] = "No consensus - highest confidence selected"
                return best_result
    
    async def _synthesize_final_results(self, results: List[SearchResult], 
                                      query: MineQuery) -> List[SearchResult]:
        """Final synthesis of all results"""
        # If we have synthesis agents, use them
        synthesis_agents = [
            agent for agent_name, agent in self.agent_instances.items()
            if agent_name in ["deepseek_reasoner", "claude", "gpt4"]
        ]
        
        if synthesis_agents:
            # Use first available synthesis agent
            agent = synthesis_agents[0]
            
            # Create synthesis prompt
            synthesis_data = self._prepare_synthesis_data(results, query)
            
            # If agent supports synthesis method
            if hasattr(agent, 'synthesize_results'):
                synthesized = await agent.synthesize_results(synthesis_data, query)
                if synthesized:
                    return synthesized
        
        # Fallback: return validated results as-is
        return results
    
    def _prepare_synthesis_data(self, results: List[SearchResult], 
                              query: MineQuery) -> Dict[str, Any]:
        """Prepare data for synthesis"""
        # Group by field
        field_data = {}
        for result in results:
            field = result.field_name
            if field not in field_data:
                field_data[field] = {
                    'values': [],
                    'sources': [],
                    'dates': [],
                    'confidence_scores': []
                }
            
            field_data[field]['values'].append(result.value)
            field_data[field]['sources'].append(result.source)
            field_data[field]['dates'].append(result.source_date)
            field_data[field]['confidence_scores'].append(result.confidence_score)
        
        return {
            'mine_name': query.mine_name,
            'location': f"{query.region}, {query.country}",
            'field_data': field_data,
            'total_sources': len(set(r.source for r in results)),
            'total_results': len(results)
        }
    
    async def cleanup(self):
        """Clean up all agent instances"""
        cleanup_tasks = []
        for agent in self.agent_instances.values():
            cleanup_tasks.append(agent.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.agent_instances.clear()
        self.task_results.clear()