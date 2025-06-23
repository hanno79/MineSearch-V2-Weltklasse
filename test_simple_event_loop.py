"""
Quick test of event loop manager
"""

import asyncio
from src.core.event_loop_manager import run_async, get_event_loop_manager


async def simple_test():
    print("Test läuft...")
    await asyncio.sleep(0.1)
    return "Erfolgreich!"


def main():
    print("Starte Test...")
    
    # Test 1: Einfacher async Aufruf
    result = run_async(simple_test())
    print(f"Ergebnis: {result}")
    
    # Cleanup
    manager = get_event_loop_manager()
    manager.shutdown()
    print("Fertig!")


if __name__ == "__main__":
    main()