"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Cleanup Handler für MineSearch
"""

import streamlit as st
import asyncio
import atexit
from src.core.logger import get_logger

logger = get_logger("cleanup_handler")


@st.cache_resource
def get_cleanup_handler():
    """Gibt den globalen Cleanup Handler zurück"""
    return CleanupHandler()


class CleanupHandler:
    """Verwaltet Cleanup von Ressourcen"""
    
    def __init__(self):
        self.resources = []
        self._register_atexit()
        
    def _register_atexit(self):
        """Registriert Cleanup bei Programmende"""
        atexit.register(self.cleanup_all)
        
    def register_resource(self, resource, cleanup_method="close"):
        """Registriert eine Ressource für Cleanup"""
        self.resources.append((resource, cleanup_method))
        
    def cleanup_all(self):
        """Führt Cleanup für alle registrierten Ressourcen durch"""
        logger.info("Starte Cleanup von Ressourcen...")
        
        for resource, method_name in self.resources:
            try:
                cleanup_method = getattr(resource, method_name, None)
                if cleanup_method and callable(cleanup_method):
                    if asyncio.iscoroutinefunction(cleanup_method):
                        # Async cleanup
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                loop.create_task(cleanup_method())
                            else:
                                loop.run_until_complete(cleanup_method())
                        except:
                            pass
                    else:
                        # Sync cleanup
                        cleanup_method()
                    logger.debug(f"Cleanup erfolgreich für {type(resource).__name__}")
            except Exception as e:
                logger.error(f"Fehler beim Cleanup von {type(resource).__name__}: {e}")
                
        self.resources.clear()
        logger.info("Cleanup abgeschlossen")


def cleanup_on_app_start():
    """Führt Cleanup beim App-Start durch"""
    logger.info("App-Start Cleanup...")
    
    # Schließe alte Event Loops
    try:
        loop = asyncio.get_event_loop()
        if loop and not loop.is_closed():
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
    except:
        pass
    
    # Clear Streamlit cache wenn zu groß
    try:
        import gc
        gc.collect()
    except:
        pass
        
    logger.info("App-Start Cleanup abgeschlossen")