"""Adapter: Stellt BatchService unter `minesearch.batch_service` bereit."""

try:
    from minesearch_v2.backend.batch_service import BatchService  # type: ignore
except Exception as e:
    # Minimaler Stub, falls in SAFE_MODE nicht verfügbar
    class BatchService:  # type: ignore
        def __init__(self, *_, **__):
            raise ImportError("BatchService ist in dieser Umgebung nicht verfügbar")

__all__ = ["BatchService"]


