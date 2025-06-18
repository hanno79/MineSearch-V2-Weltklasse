#!/usr/bin/env python3
"""Test OpenRouter configuration"""
import os
from dotenv import load_dotenv
from src.core.config import Config

# Load environment variables
load_dotenv()

# Create config
config = Config()

print("OpenRouter API Key configured:", bool(config.api.openrouter_key))
print("OpenRouter API Key value:", config.api.openrouter_key[:10] + "..." if config.api.openrouter_key else "NOT SET")

# Test available agents
from src.agents.factory import AgentFactory
available = AgentFactory.get_available_agents(config)

print("\nAvailable agents:")
for agent, is_available in available.items():
    if is_available:
        print(f"  ✓ {agent}")
    else:
        print(f"  ✗ {agent}")

# Count OpenRouter models
openrouter_models = [k for k in available.keys() if k.startswith("openrouter_")]
print(f"\nOpenRouter models found: {len(openrouter_models)}")
for model in openrouter_models:
    print(f"  - {model}")