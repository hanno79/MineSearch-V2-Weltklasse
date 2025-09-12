"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: REGEL 10 Enforcement - Detektor für Fallback-Werte
ZWECK: Verhindert versteckte 0.5 Fallback-Werte in Produktion
"""

import logging
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class FallbackDetector:
    """
    REGEL 10 Enforcement: Erkennt und verhindert Fallback-Werte

    Funktionen:
    - Erkennt 0.5 Fallback-Werte in verschiedenen Formaten
    - Warnt bei verdächtigen Patterns
    - Blockiert Speicherung von Fallback-Daten
    """

    # Verbotene Fallback-Werte (REGEL 10)
    FORBIDDEN_FALLBACK_VALUES = [
        0.5,        # Häufigster Fallback
        '0.5',      # String-Version
        0.50,       # Mit Dezimalen
        '0.50',     # String mit Dezimalen
    ]

    # Verdächtige Patterns
    SUSPICIOUS_PATTERNS = [
        'fallback',
        'default',
        'unknown',
        'placeholder',
        'dummy',
        'template'
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode: Bei True werden Fallback-Werte blockiert, bei False nur gewarnt
        """
        self.strict_mode = strict_mode
        self.warnings_count = 0
        self.blocked_count = 0

    def scan_data_structure(self, data: Any, path: str = "root") -> Dict[str, List[str]]:
        """
        Scannt eine Datenstruktur nach Fallback-Werten

        Returns:
            Dict mit gefundenen Problemen: {"warnings": [...], "errors": [...]}
        """
        results = {"warnings": [], "errors": []}

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}"

                # Prüfe spezifische Felder
                if key.lower() in ['confidence', 'reliability', 'score']:
                    if value in self.FORBIDDEN_FALLBACK_VALUES:
                        error_msg = f"🚨 REGEL 10 VERLETZUNG: {current_path} = {value} (verbotener Fallback-Wert)"
                        results["errors"].append(error_msg)
                        self.blocked_count += 1

                # Rekursive Suche
                nested_results = self.scan_data_structure(value, current_path)
                results["warnings"].extend(nested_results["warnings"])
                results["errors"].extend(nested_results["errors"])

        elif isinstance(data, list):
            for i, item in enumerate(data):
                nested_results = self.scan_data_structure(item, f"{path}[{i}]")
                results["warnings"].extend(nested_results["warnings"])
                results["errors"].extend(nested_results["errors"])

        elif isinstance(data, str):
            # Prüfe auf verdächtige Patterns in Strings
            data_lower = data.lower()
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern in data_lower and len(data.strip()) < 20:  # Kurze Strings verdächtiger
                    warning_msg = f"⚠️ Verdächtiges Pattern '{pattern}' in {path}: '{data}'"
                    results["warnings"].append(warning_msg)
                    self.warnings_count += 1

        return results

    def validate_search_result(self, search_result: Dict[str, Any]) -> bool:
        """
        Validiert ein Suchergebnis vor der Speicherung

        Returns:
            True wenn sauber, False wenn Fallback-Werte entdeckt wurden
        """
        logger.debug("[FALLBACK-DETECTOR] Validiere Suchergebnis...")

        scan_results = self.scan_data_structure(search_result)

        # Log Warnungen
        for warning in scan_results["warnings"]:
            logger.warning(f"[FALLBACK-DETECTOR] {warning}")

        # Log und handle Fehler
        for error in scan_results["errors"]:
            logger.error(f"[FALLBACK-DETECTOR] {error}")

        # Entscheide basierend auf strict_mode
        has_errors = len(scan_results["errors"]) > 0

        if has_errors and self.strict_mode:
            logger.error(f"[FALLBACK-DETECTOR] REGEL 10: Suchergebnis BLOCKIERT wegen
{len(scan_results['errors'])} Fallback-Werten")
            return False
        elif has_errors and not self.strict_mode:
            logger.warning(f"[FALLBACK-DETECTOR] REGEL 10: {len(scan_results['errors'])}
Fallback-Werte gefunden, aber durchgelassen (strict_mode=False)")

        return True

    def get_statistics(self) -> Dict[str, int]:
        """Gibt Statistiken über gefundene Probleme zurück"""
        return {
            "warnings_count": self.warnings_count,
            "blocked_count": self.blocked_count,
            "strict_mode": self.strict_mode
        }

    def create_clean_alternative(self, value: Any) -> Any:
        """
        Erstellt eine saubere Alternative für einen Fallback-Wert

        REGEL 10: Statt 0.5 → None/null
        """
        if value in self.FORBIDDEN_FALLBACK_VALUES:
            logger.info(f"[FALLBACK-DETECTOR] REGEL 10: Ersetze {value} mit None")
            return None
        return value

# Globale Instanz
fallback_detector = FallbackDetector(strict_mode=True)

def validate_data(data: Any) -> bool:
    """
    Globale Validierungsfunktion

    Returns:
        True wenn Daten sauber sind, False bei Fallback-Werten
    """
    return fallback_detector.validate_search_result(data)

def clean_fallback_values(data: Any) -> Any:
    """
    Bereinigt Fallback-Werte aus Datenstruktur

    REGEL 10: 0.5 → None
    """
    if isinstance(data, dict):
        return {key: clean_fallback_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_fallback_values(item) for item in data]
    else:
        return fallback_detector.create_clean_alternative(data)
