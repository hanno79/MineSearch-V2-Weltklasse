"""
Author: rahn
Datum: 16.06.2025
Version: 2.0
Beschreibung: Zentrale Validierungsfunktionen für Minendaten

ÄNDERUNG 27.06.2025: Refactoring zur Einhaltung der 500-Zeilen-Regel
# Validierungslogik in separate Module aufgeteilt:
# - validators/base.py: Basis-Klassen
# - validators/mine_validators.py: Minen-spezifische Validierungen
# - validators/currency_validators.py: Währungsvalidierungen
# - validators/coordinate_validators.py: Koordinatenvalidierungen
# - validators/api_validators.py: API-Validierungen
"""

# Re-export der wichtigsten Klassen und Funktionen für Abwärtskompatibilität
from .validators import (
    ValidationError,
    DataValidator,
    get_validator
)

# Für direkten Import der spezialisierten Validatoren
from .validators import (
    MineValidator,
    APIValidator,
    CurrencyValidator,
    CoordinateValidator
)

# Expliziter Export für bessere IDE-Unterstützung
__all__ = [
    'ValidationError',
    'DataValidator',
    'get_validator',
    'MineValidator',
    'APIValidator', 
    'CurrencyValidator',
    'CoordinateValidator'
]

# ÄNDERUNG 27.06.2025: Backward Compatibility
# Die alte validators.py fungiert jetzt als Wrapper für die neuen Module
# Alle bestehenden Importe sollten weiterhin funktionieren