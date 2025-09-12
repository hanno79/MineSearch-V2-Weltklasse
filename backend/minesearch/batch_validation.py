"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Batch-Results Validierung - verhindert Regressionen bei Template-Pattern-Filtering
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Ergebnis einer Batch-Validierung"""
    is_valid: bool
    issues_found: List[str]
    warning_count: int
    critical_count: int
    success_metrics: Dict[str, Any]

class BatchResultsValidator:
    """
    REGRESSION-PREVENTION: Validiert Batch-Ergebnisse auf häufige Probleme
    """

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.known_template_indicators = [
            'k.A.', 'N/A', 'unknown', 'LEER', 'TEMPLATE:',
            'nichts gefunden', 'keine Angaben', 'not found'
        ]

    def validate_batch_results(self, results: List[Dict[str, Any]]) -> ValidationResult:
        """
        HAUPTFUNKTION: Validiert komplette Batch-Ergebnisse

        Args:
            results: Liste der Batch-Suchergebnisse

        Returns:
            ValidationResult mit detaillierter Analyse
        """
        issues = []
        warnings = 0
        criticals = 0

        if not results:
            return ValidationResult(
                is_valid=False,
                issues_found=["Keine Batch-Ergebnisse zum Validieren erhalten"],
                warning_count=0,
                critical_count=1,
                success_metrics={}
            )

        # Validierung 1: Template-Pattern-Regression-Check
        template_issues = self._check_template_pattern_regression(results)
        if template_issues:
            issues.extend(template_issues)
            criticals += len(template_issues)

        # Validierung 2: Datenqualität-Check
        quality_issues = self._check_data_quality(results)
        if quality_issues:
            issues.extend(quality_issues)
            warnings += len(quality_issues)

        # Validierung 3: Structured-Data-Pipeline-Check
        pipeline_issues = self._check_structured_data_pipeline(results)
        if pipeline_issues:
            issues.extend(pipeline_issues)
            criticals += len(pipeline_issues)

        # Success-Metriken berechnen
        success_metrics = self._calculate_success_metrics(results)

        is_valid = criticals == 0

        logger.info(f"[BATCH-VALIDATION] Validated {len(results)} results: "
                   f"{warnings} warnings, {criticals} critical issues")

        return ValidationResult(
            is_valid=is_valid,
            issues_found=issues,
            warning_count=warnings,
            critical_count=criticals,
            success_metrics=success_metrics
        )

    def _check_template_pattern_regression(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        KRITISCHE VALIDIERUNG: Prüft auf Template-Pattern-Regressions
        """
        issues = []
        total_fields = 0
        template_fields = 0

        for result in results:
            if result.get('success') and result.get("data", {}).get('structured_data'):
                structured_data = result['data']['structured_data']

                for field_name, field_value in structured_data.items():
                    total_fields += 1

                    # Prüfe auf Template-Pattern
                    if field_value and str(field_value).strip():
                        value_str = str(field_value).strip()

                        # KRITISCH: Prüfe auf aggressive Template-Konvertierung
                        if any(template in value_str for template in self.known_template_indicators):
                            template_fields += 1

                            # Besonders verdächtig: echte Daten die zu Template wurden
                            if len(value_str) > 20 and any(template in value_str for template in ['k.A.', 'LEER']):
                                issues.append(f"KRITISCH: Mögliche Template-Regression -
'{value_str}' in Feld '{field_name}' sieht aus wie konvertierte echte Daten")

        # Threshold-basierte Validierung
        if total_fields > 0:
            template_ratio = template_fields / total_fields
            if template_ratio > 0.8:  # Mehr als 80% Template-Werte
                issues.append(f"KRITISCH: Template-Pattern-Regression erkannt -
{template_ratio*100:.1f}% aller Felder enthalten Template-Werte")
            elif template_ratio > 0.6:  # Mehr als 60% Template-Werte
                issues.append(f"WARNUNG: Hoher Template-Anteil - {template_ratio*100:.1f}% der
Felder enthalten Template-Werte")

        return issues

    def _check_data_quality(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Prüft Datenqualität der Batch-Ergebnisse
        """
        issues = []
        successful_results = [r for r in results if r.get("success", False)]

        if not successful_results:
            issues.append("KRITISCH: Alle Batch-Suchen sind fehlgeschlagen")
            return issues

        # Prüfe Feld-Abdeckung
        total_fields_found = 0
        for result in successful_results:
            structured_data = result.get("data", {}).get('structured_data', {})
            for value in structured_data.values():
                if (value and
                    str(value).strip() and
                    str(value).strip() not in self.known_template_indicators):
                    total_fields_found += 1

        avg_fields_per_mine = total_fields_found / len(successful_results) if successful_results else 0

        if avg_fields_per_mine < 2:
            issues.append(f"WARNUNG: Niedrige Datenqualität - nur {avg_fields_per_mine:.1f} Felder
pro Mine im Durchschnitt")

        return issues

    def _check_structured_data_pipeline(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Prüft ob Structured-Data-Pipeline korrekt funktioniert
        """
        issues = []

        for idx, result in enumerate(results):
            mine_name = result.get("mine_name", f'Mine {idx+1}')

            if result.get('success'):
                # Erfolgreich, aber keine structured_data
                if not result.get("data", {}).get('structured_data'):
                    issues.append(f"KRITISCH: Mine '{mine_name}' als erfolgreich markiert aber
structured_data ist leer")

                # Structured_data vorhanden aber komplett leer
                elif result.get("data", {}).get('structured_data'):
                    structured_data = result['data']['structured_data']
                    non_empty_values = [v for v in structured_data.values()
                                      if v and str(v).strip() and str(v).strip() not in self.known_template_indicators]

                    if len(non_empty_values) == 0:
                        issues.append(f"KRITISCH: Mine '{mine_name}' hat structured_data aber alle
Werte sind leer oder Templates")

        return issues

    def _calculate_success_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Berechnet Success-Metriken für die Validierung
        """
        total_results = len(results)
        successful_results = [r for r in results if r.get("success", False)]

        # Feld-Statistiken
        total_fields = 0
        filled_fields = 0
        template_fields = 0

        for result in successful_results:
            structured_data = result.get("data", {}).get('structured_data', {})
            for field_value in structured_data.values():
                total_fields += 1
                if field_value and str(field_value).strip():
                    value_str = str(field_value).strip()
                    if value_str not in self.known_template_indicators:
                        filled_fields += 1
                    else:
                        template_fields += 1

        return {
            'total_mines': total_results,
            'successful_mines': len(successful_results),
            'success_rate': len(successful_results) / total_results if total_results > 0 else 0,
            'total_fields_analyzed': total_fields,
            'fields_with_data': filled_fields,
            'template_fields': template_fields,
            'data_quality_ratio': filled_fields / total_fields if total_fields > 0 else 0,
            'avg_fields_per_mine': filled_fields / len(successful_results) if successful_results else 0
        }

# Globale Validator-Instanz
batch_validator = BatchResultsValidator()

def validate_batch_results(results: List[Dict[str, Any]]) -> ValidationResult:
    """
    CONVENIENCE FUNCTION: Validiert Batch-Ergebnisse

    Args:
        results: Batch-Suchergebnisse

    Returns:
        ValidationResult mit detaillierter Analyse
    """
    return batch_validator.validate_batch_results(results)

def log_validation_summary(validation_result: ValidationResult):
    """
    UTILITY FUNCTION: Loggt Validierungs-Zusammenfassung
    """
    if validation_result.is_valid:
        logger.info(f"[BATCH-VALIDATION] ✅ Batch-Ergebnisse sind VALIDE - {validation_result.warning_count} Warnungen")
    else:
        logger.error(f"[BATCH-VALIDATION] ❌ Batch-Ergebnisse sind INVALIDE -
{validation_result.critical_count} kritische Probleme")

    for issue in validation_result.issues_found:
        if "KRITISCH" in issue:
            logger.error(f"[BATCH-VALIDATION] {issue}")
        else:
            logger.warning(f"[BATCH-VALIDATION] {issue}")

    metrics = validation_result.success_metrics
    logger.info(f"[BATCH-VALIDATION] Metriken: {metrics.get("data_quality_ratio", 0)*100:.1f}% Datenqualität, "
               f"{metrics.get("avg_fields_per_mine", 0):.1f} Felder/Mine")
