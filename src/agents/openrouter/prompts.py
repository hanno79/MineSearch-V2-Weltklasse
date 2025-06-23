"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Prompt-Templates für OpenRouter Agent
"""

from typing import List
from ..base_agent import MineQuery
from ..enhanced_search import get_mining_domains


class OpenRouterPromptGenerator:
    """Generiert spezialisierte Prompts für OpenRouter"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """System-Prompt für Mining-Expertise"""
        return """You are an expert mining research specialist with deep knowledge of:
- Mining operations and mineral extraction
- Environmental remediation and closure costs
- Mining regulations and compliance
- Geological surveys and resource estimates
- Mining company structures and ownership
- Technical mining reports (NI 43-101, JORC)
- Mining databases and government registries

Provide accurate, detailed information with specific sources."""
    
    @staticmethod
    def build_comprehensive_prompt(query: MineQuery, search_queries: List[str]) -> str:
        """Build comprehensive mining search prompt"""
        fields_str = ", ".join(query.required_fields)
        queries_str = "\n".join([f"- {q}" for q in search_queries[:5]])
        domains_str = ", ".join(get_mining_domains()[:10])
        
        return f"""You are conducting a comprehensive search for detailed information about a mine.

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
    
    @staticmethod
    def build_technical_prompt(query: MineQuery) -> str:
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
    
    @staticmethod
    def build_environmental_prompt(query: MineQuery) -> str:
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
- Provincial/state mining ministries

Provide specific amounts with currency and year.
Format as JSON with sources."""
    
    @staticmethod
    def build_ownership_prompt(query: MineQuery) -> str:
        """Build ownership and operator prompt"""
        return f"""Search for current ownership and operational control of {query.mine_name} mine in {query.region}, {query.country}:

Find:
1. Current operating company
2. Parent company (if different)
3. Ownership percentages
4. Joint venture partners
5. Recent ownership changes
6. Corporate structure

Search in:
- SEDAR filings
- Company websites
- Mining registries
- Recent news and press releases
- Corporate databases

Provide the most current information with dates.
Format as JSON with sources."""
    
    @staticmethod
    def build_status_prompt(query: MineQuery) -> str:
        """Build operational status prompt"""
        return f"""Determine the current operational status of {query.mine_name} mine in {query.region}, {query.country}:

Identify:
1. Current operational status (active, suspended, closed, care & maintenance)
2. Date of last status change
3. Reason for status change
4. Production levels (if active)
5. Number of employees
6. Recent developments

Search in:
- Recent news articles
- Company updates
- Government mining reports
- Local news sources
- Industry publications

Provide the most recent status with date and source.
Format as JSON."""
