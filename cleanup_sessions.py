#!/usr/bin/env python3
"""
Session Cleanup Script
Author: rahn
Datum: 25.06.2025
"""
import asyncio
import gc
import sys
sys.path.append('/app')

from src.utils.session_manager import SessionManager


async def cleanup_all_sessions():
    """Räumt alle Sessions auf"""
    print("Starting session cleanup...")
    
    # Erstelle temporären SessionManager
    session_manager = SessionManager()
    
    # Schließe alle Sessions
    await session_manager.close_all()
    
    # Garbage Collection
    gc.collect()
    
    print("✅ Session cleanup completed")


if __name__ == "__main__":
    asyncio.run(cleanup_all_sessions())