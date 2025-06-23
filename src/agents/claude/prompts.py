"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Prompt-Templates für Claude Agent
"""

from typing import List, Dict
from ..base_agent import MineQuery


class ClaudePromptGenerator:
    """Generiert spezialisierte Prompts für Claude"""
    
    @staticmethod
    def create_mining_prompts(query: MineQuery, mining_queries: List[str], 
                            mining_domains: List[str]) -> Dict[str, str]:
        """Erstellt erweiterte Mining-spezifische Prompts"""
        prompts = {}
        
        # Umfassender Mining-Recherche-Prompt
        prompts['comprehensive'] = ClaudePromptGenerator._create_comprehensive_prompt(
            query, mining_queries, mining_domains
        )
        
        # Kosten-Analyse-Prompt
        prompts['financial'] = ClaudePromptGenerator._create_financial_prompt(query)
        
        # Umwelt-Prompt
        prompts['environmental'] = ClaudePromptGenerator._create_environmental_prompt(query)
        
        # Feldspezifische Prompts
        if query.required_fields:
            prompts['field_specific'] = ClaudePromptGenerator._create_field_specific_prompt(
                query, query.required_fields[0]
            )
        
        return prompts
    
    @staticmethod
    def _create_comprehensive_prompt(query: MineQuery, mining_queries: List[str], 
                                   mining_domains: List[str]) -> str:
        """Erstellt umfassenden Recherche-Prompt"""
        return f"""
You are an expert mining researcher with UNLIMITED access to ALL mining databases, reports, and sources worldwide.

CRITICAL RESEARCH INSTRUCTIONS:
1. Search EXHAUSTIVELY - leave no source unchecked
2. Use ALL name variations and spellings
3. Search in ALL relevant languages for {query.country}
4. Look for PDFs, Excel files, presentations, not just web pages
5. Check historical records and archived documents
6. Cross-reference multiple sources for accuracy

TARGET: Mine "{query.mine_name}" in {query.region}, {query.country}

EXECUTE these search strategies:
{chr(10).join(['- ' + q for q in mining_queries[:20]])}

SEARCH these sources IN ORDER OF PRIORITY:
1. Government (Federal/State/Local):
   - Mining ministries and departments
   - Geological surveys
   - Environmental agencies
   - Mining registries and cadastres
   - Public archives

2. Company Sources:
   - Operator/owner websites
   - Investor presentations
   - Annual reports
   - Sustainability reports
   - Securities filings

3. Third-Party Sources:
   - NGOs and watchdog groups
   - Industry associations
   - News media (local and trade)
   - Academic research
   - Community groups

4. Technical Databases:
{', '.join(mining_domains[:20])}

Find ALL of the following information with EXACT values and sources:

1. OPERATOR/OWNER:
   - Current operating company name
   - Parent company (if applicable)
   - Ownership percentages
   - Joint venture partners

2. EXACT LOCATION:
   - Precise GPS coordinates (latitude, longitude)
   - Distance from nearest town/city
   - Access routes

3. ENVIRONMENTAL COSTS:
   - Environmental bond amount
   - Restoration/remediation costs
   - Closure cost estimates
   - Financial assurance amounts
   - Currency and year of estimates

4. OPERATIONAL STATUS:
   - Current status (operating/suspended/closed/care & maintenance)
   - Status change dates
   - Reasons for status changes

5. PRODUCTION DATA:
   - Annual production volumes
   - Production capacity
   - Historical production
   - Grade/quality of ore

6. MINE CHARACTERISTICS:
   - Commodities mined
   - Mining method (open pit/underground/etc)
   - Total area (hectares/acres)
   - Depth of operations
   - Number of employees

7. TIMELINE:
   - Discovery/founding year
   - Start of operations
   - Major expansion dates
   - Closure date (if applicable)

RETURN FORMAT:
[field_name]: [exact_value]
[source]: [exact URL or document name]
[year]: [year of information]
[confidence]: [high/medium/low]

IMPORTANT:
- Provide ONLY verifiable information from real sources
- If uncertain, mark confidence as low
- Include currency for all financial values
- Use exact coordinates, not approximations
- Date all information
"""
    
    @staticmethod
    def _create_financial_prompt(query: MineQuery) -> str:
        """Erstellt Finanz-fokussierten Prompt"""
        return f"""
You are a financial analyst specializing in mining industry financial obligations and environmental liabilities.

Focus on finding EXACT FINANCIAL DATA for the mine "{query.mine_name}" in {query.region}, {query.country}:

1. ENVIRONMENTAL FINANCIAL OBLIGATIONS:
   - Closure bonds/financial assurance
   - Environmental rehabilitation costs
   - Asset retirement obligations (ARO)
   - Restoration fund requirements
   - Progressive rehabilitation costs

2. SEARCH THESE DOCUMENTS:
   - Annual reports (look for notes on provisions)
   - Securities filings (10-K, AIF, etc.)
   - Environmental impact assessments
   - Closure plans
   - Government regulatory filings
   - Mining permits and licenses

3. KEY TERMS TO SEARCH:
   - "closure cost" "closure bond" "financial assurance"
   - "ARO" "asset retirement obligation"
   - "rehabilitation" "restoration" "remediation"
   - "environmental liability" "provision"
   - Mine name + "million" "cost" "estimate"

4. GOVERNMENT SOURCES:
   - Mining ministry financial security requirements
   - Environmental agency bond postings
   - Public registries of financial guarantees

For EACH financial value found:
- Amount in original currency
- Currency type (CAD, USD, etc.)
- Year of estimate/posting
- Type (bond, cost estimate, provision)
- Source document and page number if available
- Whether amount is posted or just estimated
"""
    
    @staticmethod
    def _create_environmental_prompt(query: MineQuery) -> str:
        """Erstellt Umwelt-fokussierten Prompt"""
        return f"""
You are an environmental specialist researching mining impacts and rehabilitation requirements.

Focus on ENVIRONMENTAL INFORMATION for "{query.mine_name}" in {query.region}, {query.country}:

1. CONTAMINATION AND IMPACTS:
   - Soil contamination levels
   - Water quality issues
   - Air quality impacts
   - Wildlife/habitat disruption
   - Acid mine drainage presence

2. REHABILITATION REQUIREMENTS:
   - Total area requiring rehabilitation
   - Specific rehabilitation methods required
   - Timeline for rehabilitation
   - Success criteria
   - Monitoring requirements

3. REGULATORY COMPLIANCE:
   - Environmental violations/fines
   - Permit conditions
   - Compliance orders
   - Community complaints

4. SEARCH SOURCES:
   - Environmental impact assessments
   - Closure plans
   - Monitoring reports
   - Regulatory inspection reports
   - NGO/watchdog reports
   - Academic studies
   - Community group documentation

Provide specific, quantified impacts where available.
"""
    
    @staticmethod
    def _create_field_specific_prompt(query: MineQuery, field: str) -> str:
        """Erstellt feldspezifische Prompts"""
        field_prompts = {
            "koordinaten": f"""Find the EXACT GPS coordinates for {query.mine_name} mine.
Search: government maps, mining cadastres, Google Earth, technical reports.
Format: decimal degrees (e.g., 45.1234, -73.5678)""",
            
            "betreiber": f"""Find the CURRENT operator/owner of {query.mine_name} mine.
Search: corporate websites, SEDAR, mining registries, recent news.
Include: parent company, ownership %, joint ventures.""",
            
            "sanierungskosten": f"""Find ALL financial obligations for closing/rehabilitating {query.mine_name}.
Search: closure plans, bonds, ARO provisions, government postings.
Include: amount, currency, year, type of obligation.""",
            
            "aktivitaetsstatus": f"""Find the CURRENT operational status of {query.mine_name}.
Search: recent news, company updates, government reports.
Include: status, date of change, reason for status.""",
            
            "jahresproduktion": f"""Find annual production data for {query.mine_name}.
Search: annual reports, statistics agencies, company presentations.
Include: volume, commodity, year, units."""
        }
        
        return field_prompts.get(field, f"Find detailed information about {field} for {query.mine_name} mine.")
