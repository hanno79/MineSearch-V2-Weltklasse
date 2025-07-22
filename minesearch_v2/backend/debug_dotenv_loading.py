#!/usr/bin/env python3
"""
Debug: .env File Loading Test
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("🔧 DEBUG: .env File Loading")
print("=" * 50)

# Test current working directory
print(f"Current working directory: {os.getcwd()}")

# Test the path calculation used in base.py
current_file = Path(__file__)
print(f"Current file: {current_file}")
print(f"Current file parent: {current_file.parent}")
print(f"Current file parent.parent: {current_file.parent.parent}")
print(f"Current file parent.parent.parent: {current_file.parent.parent.parent}")

env_path = Path(__file__).parent.parent.parent / '.env'
print(f"Calculated env_path: {env_path}")
print(f"env_path exists: {env_path.exists()}")

if env_path.exists():
    print(f"env_path is file: {env_path.is_file()}")
    
    # Read .env file content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    print(f"env_path has {len(lines)} lines")
    
    # Look for ABACUS_API_KEY
    for i, line in enumerate(lines, 1):
        if 'ABACUS_API_KEY' in line:
            print(f"Line {i}: {line.strip()}")
else:
    print("❌ .env file not found!")

# Test different possible paths
possible_paths = [
    Path('/app/minesearch_v2/.env'),
    Path('/app/.env'),
    Path('./minesearch_v2/.env'),
    Path('./.env'),
    Path('../../.env'),
    Path('../.env')
]

print("\n🔍 Testing different .env paths:")
for path in possible_paths:
    resolved = path.resolve()
    print(f"  {path} -> {resolved} (exists: {resolved.exists()})")

print("\n🧪 Testing dotenv loading:")

# Test loading from the calculated path
print("1. Loading from calculated path...")
load_result = load_dotenv(env_path)
print(f"   load_dotenv result: {load_result}")
print(f"   ABACUS_API_KEY after load: {os.getenv('ABACUS_API_KEY')}")

# Test loading from correct path
correct_path = Path('/app/minesearch_v2/.env')
if correct_path.exists():
    print("2. Loading from /app/minesearch_v2/.env...")
    load_result2 = load_dotenv(correct_path)
    print(f"   load_dotenv result: {load_result2}")
    print(f"   ABACUS_API_KEY after load: {os.getenv('ABACUS_API_KEY')}")

print("=" * 50)