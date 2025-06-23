"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Agent Coordinator - Refactored Import
"""

# ÄNDERUNG 22.06.2025: Import aus modularisierter Struktur
from .coordinator import AgentCoordinator, AgentStrength, AgentCapability

__all__ = ['AgentCoordinator', 'AgentStrength', 'AgentCapability']