"""
Extraction Package
Datenextraktion und -verarbeitung für MineSearch

Author: MineSearch Development Team
Date: 2025-01-11
"""

from .processors import is_template_or_dummy_value, clean_extracted_value

__all__ = ["is_template_or_dummy_value", "clean_extracted_value"]
