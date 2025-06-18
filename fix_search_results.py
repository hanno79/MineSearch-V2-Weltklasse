#!/usr/bin/env python3
"""
Manually fix SearchResult creation issues
"""

import fileinput
import sys
import re

files_to_fix = [
    '/app/src/agents/tavily_agent.py',
    '/app/src/agents/exa_agent.py', 
    '/app/src/agents/apify_agent.py',
    '/app/src/agents/scrapingbee_agent.py',
    '/app/src/agents/firecrawl_agent.py',
    '/app/src/agents/brightdata_agent.py'
]

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix confidence parameter name
    content = re.sub(r'confidence\s*=\s*"(\w+)"', 
                    lambda m: f'confidence_score={{"high": 0.9, "medium": 0.7, "low": 0.5}}.get("{m.group(1)}", 0.7)',
                    content)
    
    # Remove search_language parameter
    content = re.sub(r',\s*search_language\s*=\s*"[^"]*"', '', content)
    
    # Remove found_at parameter  
    content = re.sub(r',\s*found_at\s*=\s*datetime\.now\(\)', '', content)
    
    # Add timestamp parameter where missing
    if 'timestamp=' not in content:
        # Find SearchResult creations without timestamp
        def add_timestamp(match):
            result_content = match.group(0)
            if 'timestamp=' not in result_content:
                # Insert before the closing parenthesis
                result_content = result_content.rstrip(')')
                result_content += ',\n                            timestamp=datetime.now()'
                result_content += ')'
            return result_content
        
        content = re.sub(r'SearchResult\([^)]+\)', add_timestamp, content, flags=re.DOTALL)
    
    # Add metadata parameter where missing
    def add_metadata(match):
        result_content = match.group(0)
        if 'metadata=' not in result_content:
            # Insert before the closing parenthesis
            result_content = result_content.rstrip(')')
            result_content += ',\n                            metadata={}'
            result_content += ')'
        return result_content
    
    content = re.sub(r'SearchResult\([^)]+\)', add_metadata, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

for filepath in files_to_fix:
    fix_file(filepath)