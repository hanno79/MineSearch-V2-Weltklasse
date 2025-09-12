"""
Zentraler Ort für Feld-bezogene Konstanten.

Hinweis: Diese Konstanten werden u. a. genutzt, um die Tabelle
`prohibited_field_patterns` in SQLite zu befüllen und Trigger-Checks
gegen Feldnamen-als-Werte durchzuführen.

Author: MineSearch Development Team
Date: 2025-01-11
"""

from typing import List

__all__ = ["PROHIBITED_FIELD_NAMES"]

# Kritische Feldnamen, die nicht als Werte in JSON erscheinen dürfen.
# Wartung an einer Stelle, um Konsistenz über Code und DB-Seeds zu sichern.
PROHIBITED_FIELD_NAMES: List[str] = [
    "x-koordinate", "y-koordinate", "x-Koordinate", "y-Koordinate",
    "restaurationskosten", "Restaurationskosten", "kostenjahr", "Kostenjahr",
    "dokumentenjahr", "Dokumentenjahr", "produktionsstart", "Produktionsstart",
    "produktionsende", "Produktionsende", "betreiber", "Betreiber",
    "eigentümer", "Eigentümer", "rohstoffe", "Rohstoffe",
    "minentyp", "Minentyp", "aktivitätsstatus", "Aktivitätsstatus",
    "region", "Region", "country", "Country", "land", "Land",
]


