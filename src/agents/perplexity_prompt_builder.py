"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Prompt Builder für Perplexity Agent
"""

from typing import Dict, List
from .base_agent import MineQuery


class PerplexityPromptBuilder:
    """Erstellt optimierte Prompts für Perplexity API"""
    
    @staticmethod
    def create_enhanced_prompt(query: MineQuery, search_query: str, priority_domains: List[str]) -> str:
        """Creates enhanced prompt using specific search queries and domains"""
        # ÄNDERUNG 27.06.2025: Extrahiert aus perplexity_agent.py für bessere Modularität
        domains_str = ", ".join(priority_domains)
        
        prompt = f"""Search for information about the {query.mine_name} mine in {query.region}, {query.country}.

IMPORTANT: Provide ONLY factual information found in your search results. Do not repeat the search query or instructions.

Focus on these sources: {domains_str}

Find and report these specific data points:
- Owner/Operator: [Company name that operates the mine]
- Location: [GPS coordinates or precise location]
- Status: [Current operational status]
- Commodities: [What minerals/metals are mined]
- Production: [Annual production volumes]
- Workforce: [Number of employees]
- Environmental costs: [Closure/remediation costs]
- Recent updates: [News from 2020-2025]

Format: Provide direct answers with source citations. Start with "Based on my search..." and list the findings."""
        
        return prompt
    
    @staticmethod
    def create_prompts(query: MineQuery) -> Dict[str, str]:
        """Create optimized prompts for Perplexity's online search capabilities"""
        # ÄNDERUNG 27.06.2025: Extrahiert aus perplexity_agent.py für bessere Modularität
        prompts = {}
        
        # Allgemeine Informationen - ERWEITERT
        general_prompt = f"""COMPREHENSIVE SEARCH REQUIRED: Find ALL available information about the {query.mine_name} mine in {query.region}, {query.country}.

SEARCH INSTRUCTIONS:
- Use ALL name variations and spellings
- Search in multiple languages relevant to {query.country}
- Look for official documents, PDFs, technical reports
- Check government databases, company filings, NGO reports
- Include historical and archived information

REQUIRED DATA:
1. OWNERSHIP:
   - Current operator/owner (full legal name)
   - Parent company and ownership structure
   - Historical ownership changes
   - Joint venture partners

2. LOCATION:
   - Exact GPS coordinates (latitude, longitude)
   - Physical address
   - Distance from nearest city/town
   - Access routes

3. OPERATIONAL:
   - Current status (active/suspended/closed/care & maintenance)
   - Status change dates and reasons
   - Mine type (open pit/underground/both)
   - Mining method details

4. PRODUCTION:
   - All commodities produced (primary and by-products)
   - Annual production volumes (with units)
   - Historical production data
   - Processing capacity

5. FINANCIAL:
   - Environmental bonds/financial assurance amounts
   - Closure cost estimates
   - Asset value
   - Recent investments

6. TECHNICAL:
   - Reserve/resource estimates
   - Mine life
   - Processing methods
   - Infrastructure

Provide EXACT values with SPECIFIC sources and dates. Include direct URLs."""

        prompts['general'] = general_prompt
        
        # Umwelt- und Finanzdaten
        environmental_prompt = f"""Search for environmental and financial information about the {query.mine_name} mine in {query.region}, {query.country}.

Specifically look for:
1. Rehabilitation/restoration costs (closure bonds, financial assurance)
2. Environmental liabilities
3. Water usage/consumption data
4. Energy consumption
5. Environmental certifications (ISO 14001, etc.)
6. Recent environmental incidents or violations
7. Community impact assessments
8. Sustainability reports

Focus on recent data (2020-2025) from official sources, government databases, and company reports.
Include specific numbers with currency and units."""

        prompts['environmental'] = environmental_prompt
        
        # Regierungsdatenbanken für Kanada
        if query.country.lower() == 'canada':
            gov_prompt = f"""Search Canadian government databases for {query.mine_name} in {query.region}:

Check these specific sources:
- Natural Resources Canada (NRCan) mine database
- Provincial mining registries (MERN for Quebec, Ontario Mining Registry, etc.)
- GESTIM database for Quebec mines
- Environmental assessment registries
- Securities commission filings (SEDAR)

Find official data on:
- Mining claims and permits
- Environmental bonds and financial assurances
- Production statistics
- Compliance reports
- Corporate registration details"""

            prompts['government'] = gov_prompt
        
        return prompts
    
    @staticmethod
    def get_system_prompt() -> str:
        """Returns the system prompt for the API"""
        # ÄNDERUNG 27.06.2025: Zentralisierter System-Prompt
        return """You are a mining industry research specialist. Your responses must:

1. Provide ONLY factual data from your search results
2. Use this exact format for answers:
   - Owner: [company name only]
   - Status: [active/closed/suspended only]
   - Coordinates: [numbers only]
   - Production: [numbers with units]
   - Costs: [numbers with currency]

3. NEVER include:
   - The search query in your response
   - Phrases like "or owner company" or "extracted"
   - Incomplete sentences
   - Speculative information

4. If data is not found, say "Not found" - do not guess"""