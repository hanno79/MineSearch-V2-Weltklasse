#!/usr/bin/env python3
"""
Simuliert Template-Ersetzung für das clear_db Command
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

# Simuliere Template-Ersetzung
raw_args = 'stat'  # Simuliert: {{args}} wird durch 'stat' ersetzt

print('=== TEMPLATE REPLACEMENT TEST ===')
print(f'Template args: {repr(raw_args)}')
print(f'sys.argv: {sys.argv}')

# ROBUST: Use sys.argv as primary source, template as fallback
if len(sys.argv) > 1:
    # Direct Python execution - use sys.argv
    arg = ' '.join(sys.argv[1:]).strip().lower()
    print(f'Using sys.argv: {arg}')
elif raw_args != '{{args}}' and raw_args.strip():
    # Template replaced successfully
    arg = raw_args.strip().lower()
    print(f'Using template: {arg}')
else:
    # Template not replaced or empty - use default
    arg = 'all'
    print('Using default: all')

print(f'Final argument: {arg}')