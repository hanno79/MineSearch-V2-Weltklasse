"""
Source Discovery Package
Erweiterte Quellensuche für MineSearch

Author: MineSearch Development Team
Date: 2025-01-11
"""

from .core import EnhancedSourceDiscovery
from .active_discovery import ActiveDiscovery

# Import aus der source_discovery.py Datei mit absoluten Pfad
import importlib.util
import os
spec = importlib.util.spec_from_file_location("source_discovery_legacy",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "source_discovery.py"))
source_discovery_legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_discovery_legacy)

# Exportiere die Funktionen
extract_sources_from_content = source_discovery_legacy.extract_sources_from_content
SourceDiscovery = source_discovery_legacy.SourceDiscovery

__all__ = ["EnhancedSourceDiscovery", "ActiveDiscovery", "extract_sources_from_content", "SourceDiscovery"]
