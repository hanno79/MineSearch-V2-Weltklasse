"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Dynamic Keyword Generator
"""

from dataclasses import dataclass
from typing import List

@dataclass
class KeywordSet:
    """Eine Sammlung von Keywords für ein bestimmtes Konzept"""
    concept: str
    language: str
    primary_terms: List[str]
    related_terms: List[str]
    variations: List[str]
    context_modifiers: List[str]