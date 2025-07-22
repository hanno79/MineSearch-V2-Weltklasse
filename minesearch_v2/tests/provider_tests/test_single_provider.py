#!/usr/bin/env python3
"""
Quick test for single provider to verify format fix
"""

import asyncio
import logging
from provider_test_framework import ProviderTestFramework

logging.basicConfig(level=logging.INFO)

async def test_single():
    framework = ProviderTestFramework()
    result = await framework._test_single_run(
        "perplexity:sonar", 
        framework.QUEBEC_MINES[0], 
        1
    )
    print(f"Test successful: {result.success}")
    print(f"Fields found: {result.fields_found}")
    print(f"Error: {result.error}")
    return result

if __name__ == "__main__":
    asyncio.run(test_single())