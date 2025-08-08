"""
Übergangs-Paket für offiziellen Entrypoint `minesearch.main:app`.

Adapter mappt `minesearch.*` auf `backend.minesearch.*`, damit absolute
Imports sofort funktionieren (vor dem Import der App!).
"""

import importlib
import sys
from types import ModuleType

# Adapter: mappe häufig genutzte Submodule/Packages auf backend.minesearch.*
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
    "search_utils",
    "source_manager",
    "source_discovery",
    "enhanced_source_discovery",
    "data_extraction",
    "extraction_patterns",
    "extraction_processors",
    "extraction_validators",
    "html_utils",
    "specialized_prompts",
    "validation_service",
    "cache_service",
    "api_fix_wrapper",
    "model_tier_strategy",
    "model_id_parser",
    "service_manager",
]

backend_pkg: ModuleType
try:
    backend_pkg = importlib.import_module("backend.minesearch")
    # Richte den Suchpfad dieses Pakets auf den des Backend-Pakets aus,
    # damit Untermodule wie `minesearch.config` normal gefunden werden.
    try:
        __path__ = backend_pkg.__path__  # type: ignore[attr-defined]
    except Exception:
        pass
except Exception:
    backend_pkg = None  # type: ignore

for _name in _ADAPTER_SUBMODULES:
    try:
        _backend_mod = importlib.import_module(f"backend.minesearch.{_name}")
        sys.modules[f"minesearch.{_name}"] = _backend_mod
        # Exporte als Attribute für bequemen Zugriff (nur letztes Segment)
        setattr(sys.modules[__name__], _name.split(".")[-1], _backend_mod)
    except Exception:
        # Adapter ist best-effort; fehlende Submodule sind für SAFE_MODE ok
        pass

# Jetzt, nach eingerichtetem Mapping, App importieren
try:
    from backend.minesearch.main import app  # type: ignore  # noqa: F401
except Exception as _e:
    # Wenn App-Import fehlschlägt, expose kein app-Attribut (Import-Check kann reagieren)
    app = None  # type: ignore

__all__ = ["app"]


