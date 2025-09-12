"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: API Module für MineSearch v2
"""

# Hinweis: Dieses Paket-Init lädt bewusst KEINE Submodule, um
# Zirkularimporte und schwere Initialisierungen beim Paketimport zu vermeiden.
# Submodule wie `routes`, `middleware`, `handlers` sollen explizit dort
# importiert werden, wo sie gebraucht werden.

__all__: list[str] = []
