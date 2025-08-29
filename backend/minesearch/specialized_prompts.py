"""Adapter-Modul: Stellt SpecializedPrompts unter `minesearch.specialized_prompts` bereit."""

# Bevorzugt v2-Implementation, faellt ansonsten auf lokale Implementation zurueck.
try:
    from minesearch_v2.backend.specialized_prompts import SpecializedPrompts as _V2SpecializedPrompts  # type: ignore
    _HAS_V2 = True
except Exception:
    _V2SpecializedPrompts = None  # type: ignore
    _HAS_V2 = False

try:
    from minesearch.specialized_prompts_impl import SpecializedPrompts as _ImplSpecializedPrompts  # type: ignore
    _HAS_IMPL = True
except Exception:
    _ImplSpecializedPrompts = None  # type: ignore
    _HAS_IMPL = False


class SpecializedPrompts:  # type: ignore
    @staticmethod
    def get_enhanced_query(**kwargs: object) -> str:
        if _HAS_V2 and hasattr(_V2SpecializedPrompts, "get_enhanced_query"):
            return _V2SpecializedPrompts.get_enhanced_query(**kwargs)  # type: ignore
        if _HAS_IMPL and hasattr(_ImplSpecializedPrompts, "get_enhanced_query"):
            return _ImplSpecializedPrompts.get_enhanced_query(**kwargs)  # type: ignore
        return ""

    @staticmethod
    def get_restoration_costs_prompt(*args: object, **kwargs: object) -> str:
        if _HAS_V2 and hasattr(_V2SpecializedPrompts, "get_restoration_costs_prompt"):
            return _V2SpecializedPrompts.get_restoration_costs_prompt(*args, **kwargs)  # type: ignore
        if _HAS_IMPL and hasattr(_ImplSpecializedPrompts, "get_restoration_costs_prompt"):
            return _ImplSpecializedPrompts.get_restoration_costs_prompt(*args, **kwargs)  # type: ignore
        return ""

    @staticmethod
    def get_universal_anti_template_instructions() -> str:
        # Sorgt dafuer, dass die Methode immer verfuegbar ist
        if _HAS_V2 and hasattr(_V2SpecializedPrompts, "get_universal_anti_template_instructions"):
            return _V2SpecializedPrompts.get_universal_anti_template_instructions()  # type: ignore
        if _HAS_IMPL and hasattr(_ImplSpecializedPrompts, "get_universal_anti_template_instructions"):
            return _ImplSpecializedPrompts.get_universal_anti_template_instructions()  # type: ignore
        return ""


__all__ = ["SpecializedPrompts"]


