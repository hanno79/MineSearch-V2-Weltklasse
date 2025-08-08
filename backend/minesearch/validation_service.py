"""Adapter-Modul: Stellt validation_service unter `minesearch.validation_service` bereit."""

try:
    from minesearch_v2.backend.validation_service import validation_service  # type: ignore
except Exception:
    # Minimaler Stub für SAFE_MODE
    class _ValidationService:
        def validate_mine_data(self, data):
            return data, {}

    validation_service = _ValidationService()  # type: ignore

__all__ = ["validation_service"]


