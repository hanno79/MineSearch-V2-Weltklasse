"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Import-Wrapper für refaktoriertes dynamic_source_discovery Modul
"""

# Re-exportiere alle Klassen vom refaktorierten Modul
from .dynamic_source_discovery import DynamicSourceDiscovery, DiscoveredSource, SourceType

__all__ = ['DynamicSourceDiscovery', 'DiscoveredSource', 'SourceType']