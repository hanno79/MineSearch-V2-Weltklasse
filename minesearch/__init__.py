"""
Übergangs-Paket für offiziellen Entrypoint `minesearch.main:app`.

Stellt zusätzlich Adapter-Submodule bereit, sodass absolute Imports wie
`from minesearch.database import db_manager` funktionieren, indem sie auf
`backend.minesearch.*` gemappt werden.
"""

from backend.minesearch.main import app  # noqa: F401

# Adapter: mappe häufig genutzte Submodule auf backend.minesearch.*
import importlib
import sys

_ADAPTER_SUBMODULES = [
    "api",
    "api.routes",
    "config",
    "database",
    "models",
    "providers",
    "search_service",
    "search_service_multi",
    "search_service_multi_enhanced",
    "services_container",
    "utils",
    "source_manager",
    "data_extraction",
    "extraction_patterns",
    "extraction_processors",
    "extraction_validators",
]

for _name in _ADAPTER_SUBMODULES:
    try:
        _backend_mod = importlib.import_module(f"backend.minesearch.{_name}")
        sys.modules[f"minesearch.{_name}"] = _backend_mod
        setattr(sys.modules[__name__], _name.split(".")[-1], _backend_mod)
    except Exception:
        # Adapter ist best-effort; fehlende Submodule sind für SAFE_MODE ok
        pass

__all__ = ["app"]


