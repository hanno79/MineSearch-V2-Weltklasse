"""
Enhanced Source Discovery - Wrapper Module
Stellt erweiterte Quellensuche bereit

Author: MineSearch Development Team
Date: 2025-01-11
"""

# Importiere die neue modulare Implementierung aus Submodulen
from minesearch.source_discovery.core import EnhancedSourceDiscovery
from minesearch.source_discovery.active_discovery import ActiveDiscovery

# Für Rückwärtskompatibilität
__all__ = ["EnhancedSourceDiscovery", "ActiveDiscovery"]
