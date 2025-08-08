"""
Offizieller Entrypoint für Uvicorn: `uvicorn minesearch.main:app`

Leitet auf die eigentliche App unter `backend.minesearch.main:app` weiter.
"""

from backend.minesearch.main import app  # noqa: F401

__all__ = ["app"]


