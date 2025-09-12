"""
Compact Specialized Prompts Implementation
Kompakte Version der spezialisierten Prompts

Author: MineSearch Development Team
Date: 2025-01-11
"""

from typing import Dict, List, Optional


class SpecializedPrompts:
    """Generiert spezialisierte Prompts für kritische Datenfelder"""

    @staticmethod
    def get_universal_anti_template_instructions() -> str:
        """Universal Anti-Template Instructions für alle CSV_COLUMNS"""
        return """
🚫 UNIVERSAL ANTI-TEMPLATE QUALITY REQUIREMENTS:
==============================================

🎯 KRITISCHE REGEL: GIB NUR FELDER ZURÜCK, FÜR DIE DU ECHTE DATEN HAST!

⚠️ DELIMITER RULE: Replace ALL pipe characters (|) with forward slash (/) in your output
   - Example: "35|1|Mining" → "35/1/Mining"
   - This prevents CSV field misalignment
======================================================================

ABSOLUT VERBOTEN - NIEMALS verwenden:
- TEMPLATE: [beliebiger Text]
- Not specified in available [sources/data/information]
- No specific [field] mentioned in the sources
- Information not available in the provided sources
- [Field] not specified in the available information
- No [field] information found in the sources
- [Field] not mentioned in the available data
- No specific [field] documented in the sources
- [Field] not available in the provided information
- Information about [field] not found in the sources

QUALITÄTSSTANDARDS:
- Nur echte, verifizierbare Daten ausgeben
- Bei Unsicherheit: Feld weglassen
- Quellenreferenzen in eckigen Klammern [1,2,3]
- Keine Platzhalter oder Dummy-Werte
- Präzise, spezifische Angaben
"""

    @staticmethod
    def get_enhanced_query(mine_name: str, country: str = None, commodity: str = None, **kwargs) -> str:
        """Generiere erweiterte Suchanfrage"""
        base_query = f"mining information {mine_name}"
        
        if country:
            base_query += f" {country}"
        
        if commodity:
            base_query += f" {commodity}"
        
        # Erweiterte Suchbegriffe
        enhanced_terms = [
            "production data",
            "operational status", 
            "ownership information",
            "environmental impact",
            "economic data"
        ]
        
        return f"{base_query} {' '.join(enhanced_terms)}"

    @staticmethod
    def get_restoration_costs_prompt(mine_name: str, country: str = None, **kwargs) -> str:
        """Generiere Prompt für Sanierungskosten"""
        base_prompt = f"""
Finde spezifische Informationen über Sanierungskosten für die Mine {mine_name}.
"""
        
        if country:
            base_prompt += f"Fokussiere auf {country} und lokale Regulierungen.\n"
        
        base_prompt += """
WICHTIGE FELDER:
- Geschätzte Sanierungskosten
- Verantwortliche Partei
- Zeitrahmen für Sanierung
- Umweltschutzmaßnahmen
- Finanzielle Sicherheiten

NUR echte, verifizierbare Daten ausgeben!
"""
        
        return base_prompt

    @staticmethod
    def get_field_specific_prompt(field_name: str, mine_name: str, **kwargs) -> str:
        """Generiere feld-spezifischen Prompt"""
        field_prompts = {
            'mine_name': f"Bestätige den offiziellen Namen der Mine: {mine_name}",
            'country': f"In welchem Land befindet sich die Mine {mine_name}?",
            'commodity': f"Welche Rohstoffe werden in der Mine {mine_name} abgebaut?",
            'production_capacity': f"Wie hoch ist die Produktionskapazität der Mine {mine_name}?",
            'ownership': f"Wer ist der Eigentümer der Mine {mine_name}?",
            'operational_status': f"Wie ist der aktuelle Betriebsstatus der Mine {mine_name}?",
            'environmental_impact': f"Welche Umweltauswirkungen hat die Mine {mine_name}?",
            'restoration_costs': f"Wie hoch sind die geschätzten Sanierungskosten für die Mine {mine_name}?"
        }
        
        return field_prompts.get(field_name, f"Finde Informationen über {field_name} für die Mine {mine_name}")

    @staticmethod
    def get_validation_prompt(field_name: str, extracted_value: str, **kwargs) -> str:
        """Generiere Validierungs-Prompt"""
        return f"""
Validiere den extrahierten Wert für {field_name}: "{extracted_value}"

Prüfe:
1. Ist der Wert spezifisch und nicht generisch?
2. Enthält er keine Template-Marker?
3. Ist er verifizierbar aus den Quellen?
4. Ist er im korrekten Format?

Antworte nur mit "VALID" oder "INVALID" und einer kurzen Begründung.
"""

    @staticmethod
    def get_source_verification_prompt(source_url: str, field_name: str, **kwargs) -> str:
        """Generiere Quellen-Verifizierungs-Prompt"""
        return f"""
Verifiziere die Quelle {source_url} für das Feld {field_name}.

Prüfe:
1. Ist die Quelle vertrauenswürdig?
2. Ist sie aktuell und relevant?
3. Enthält sie spezifische Informationen?
4. Ist sie öffentlich zugänglich?

Antworte mit einer Bewertung von 1-10 und einer kurzen Begründung.
"""

    @staticmethod
    def get_consistency_check_prompt(field_name: str, values: List[str], **kwargs) -> str:
        """Generiere Konsistenz-Prüfungs-Prompt"""
        values_str = "\n".join([f"- {v}" for v in values])
        
        return f"""
Prüfe die Konsistenz der Werte für {field_name}:

{values_str}

Identifiziere:
1. Widersprüche zwischen den Werten
2. Offensichtlich falsche Werte
3. Den wahrscheinlichsten korrekten Wert
4. Begründung für die Auswahl

Gib den besten Wert und eine Begründung zurück.
"""

    @staticmethod
    def get_quality_assessment_prompt(extracted_data: Dict[str, Any], **kwargs) -> str:
        """Generiere Qualitätsbewertungs-Prompt"""
        return f"""
Bewerte die Qualität der extrahierten Daten:

{extracted_data}

Bewertungskriterien:
1. Vollständigkeit (0-10)
2. Genauigkeit (0-10)
3. Verifizierbarkeit (0-10)
4. Aktualität (0-10)
5. Konsistenz (0-10)

Gib eine Gesamtbewertung und Verbesserungsvorschläge zurück.
"""

    @staticmethod
    def get_error_handling_prompt(error_type: str, context: str = None, **kwargs) -> str:
        """Generiere Fehlerbehandlungs-Prompt"""
        error_handlers = {
            'template_detected': "Template-Wert erkannt. Verwende nur echte Daten aus den Quellen.",
            'no_data_found': "Keine Daten gefunden. Prüfe alternative Suchbegriffe oder Quellen.",
            'inconsistent_data': "Widersprüchliche Daten gefunden. Wähle den wahrscheinlichsten Wert.",
            'low_confidence': "Niedrige Vertrauenswürdigkeit. Suche nach zusätzlichen Quellen.",
            'format_error': "Formatierungsfehler. Korrigiere das Datenformat."
        }
        
        base_prompt = error_handlers.get(error_type, "Unbekannter Fehler aufgetreten.")
        
        if context:
            base_prompt += f"\nKontext: {context}"
        
        return base_prompt

    @staticmethod
    def get_optimization_prompt(current_performance: Dict[str, Any], **kwargs) -> str:
        """Generiere Optimierungs-Prompt"""
        return f"""
Analysiere die aktuelle Performance:

{current_performance}

Optimierungsvorschläge:
1. Verbesserung der Suchstrategie
2. Erweiterung der Quellenbasis
3. Verfeinerung der Extraktionslogik
4. Verbesserung der Validierung
5. Optimierung der Fehlerbehandlung

Gib konkrete, umsetzbare Verbesserungsvorschläge zurück.
"""


__all__ = ["SpecializedPrompts"]
