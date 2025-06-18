#!/usr/bin/env python3
"""
Script to fix SearchResult creation in all agent files
"""

import re
import os

def fix_search_result_in_file(filepath):
    """Fix SearchResult creation in a single file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find SearchResult creation
    pattern = r'SearchResult\(([\s\S]*?)\)'
    
    def fix_search_result(match):
        """Fix a single SearchResult creation"""
        params = match.group(1)
        
        # Add mine_name if missing
        if 'mine_name=' not in params:
            params = f'\n                            mine_name=query.mine_name,{params}'
        
        # Replace confidence with confidence_score
        params = re.sub(r'confidence\s*=', 'confidence_score=', params)
        
        # Replace search_language and found_at with proper metadata
        if 'search_language=' in params or 'found_at=' in params:
            # Extract search_language value
            lang_match = re.search(r'search_language\s*=\s*["\'](\w+)["\']', params)
            language = lang_match.group(1) if lang_match else 'en'
            
            # Remove search_language and found_at
            params = re.sub(r',?\s*search_language\s*=\s*["\']?\w+["\']?', '', params)
            params = re.sub(r',?\s*found_at\s*=\s*[^,\n)]+', '', params)
        else:
            language = 'en'
        
        # Add timestamp if missing
        if 'timestamp=' not in params:
            params = re.sub(r'\)$', ',\n                            timestamp=datetime.now()', params)
        
        # Add metadata if missing
        if 'metadata=' not in params:
            params = re.sub(r'\)$', f',\n                            metadata={{"language": "{language}"}}', params)
        
        # Convert confidence values to float
        params = re.sub(r'confidence_score\s*=\s*["\'](\w+)["\']', 
                       lambda m: f'confidence_score={{"high": 0.9, "medium": 0.7, "low": 0.5}}.get("{m.group(1)}", 0.7)', 
                       params)
        
        return f'SearchResult({params})'
    
    # Apply fixes
    fixed_content = re.sub(pattern, fix_search_result, content)
    
    # Save the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed: {filepath}")

# List of agent files to fix
agent_files = [
    '/app/src/agents/tavily_agent.py',
    '/app/src/agents/exa_agent.py',
    '/app/src/agents/apify_agent.py',
    '/app/src/agents/scrapingbee_agent.py',
    '/app/src/agents/firecrawl_agent.py',
    '/app/src/agents/brightdata_agent.py'
]

for agent_file in agent_files:
    if os.path.exists(agent_file):
        fix_search_result_in_file(agent_file)
    else:
        print(f"File not found: {agent_file}")

print("All agents fixed!")