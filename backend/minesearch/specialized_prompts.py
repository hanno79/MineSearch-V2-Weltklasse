"""Adapter-Modul: Stellt SpecializedPrompts unter `minesearch.specialized_prompts` bereit."""

try:
    from minesearch_v2.backend.specialized_prompts import SpecializedPrompts  # type: ignore
except Exception as e:  # Fallback: Minimaler Stub für SAFE_MODE
    class SpecializedPrompts:  # type: ignore
        @staticmethod
        def get_enhanced_query(**_: object) -> str:
            return ""

        @staticmethod
        def get_restoration_costs_prompt(*_: object, **__: object) -> str:
            return ""

__all__ = ["SpecializedPrompts"]


