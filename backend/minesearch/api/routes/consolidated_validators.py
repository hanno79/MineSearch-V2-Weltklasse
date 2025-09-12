"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Validierungs- und Qualitätsbewertungs-Logic für konsolidierte Ergebnis-Verarbeitung
(Refactoring aus consolidated_results.py)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def validate_and_score_field_values(field_info: Dict, field_name: str) -> Dict:
    """
    Validiert und bewertet Feldwerte mit intelligenter Analyse

    Args:
        field_info: Feldinfo-Dictionary mit value_details
        field_name: Name des Feldes für kontextspezifische Bewertung

    Returns:
        Dict mit Bewertungs- und Validierungsergebnissen
    """
    value_details = field_info.get("value_details", [])

    if not value_details:
        return _create_empty_validation_result()

    # Gruppiere ähnliche Werte
    value_groups = _group_similar_values(value_details, field_name)

    # Bewerte jede Gruppe
    scored_groups = _score_value_groups(value_groups, field_name)

    # Berechne Konsistenz- und Konfidenz-Scores
    consistency_score = _calculate_consistency_score(scored_groups, len(value_details))
    confidence_score = _calculate_confidence_score(scored_groups, value_details)

    # Ermittle besten Wert
    best_value_info = _select_best_value(scored_groups)

    return {
        'best_value_info': best_value_info,
        'confidence_score': confidence_score,
        'consistency_score': consistency_score,
        'value_groups': scored_groups[:3],  # Top 3 Gruppen
        'total_values': len(value_details),
        'unique_values': len(value_groups),
        'validation_passed': confidence_score >= 30.0
    }


def _create_empty_validation_result() -> Dict:
    """Erstellt leeres Validierungsergebnis"""
    return {
        'best_value_info': {
            'display_value': '',
            'confidence_score': 0.0,
            'source_info': 'Keine Daten',
            'method': 'no_data',
            'supporting_sources': []
        },
        'confidence_score': 0.0,
        'consistency_score': 0.0,
        'value_groups': [],
        'total_values': 0,
        'unique_values': 0,
        'validation_passed': False
    }


def _group_similar_values(value_details: List[Dict], field_name: str) -> List[Dict]:
    """
    Gruppiert ähnliche Werte basierend auf semantischer Ähnlichkeit
    """
    from minesearch.value_normalizer import value_normalizer

    groups = []

    for detail in value_details:
        value = detail.get("value", '')
        if not value or str(value).strip() == '':
            continue

        # Finde passende Gruppe oder erstelle neue
        grouped = False
        for group in groups:
            if value_normalizer.are_values_equivalent(value, group['representative_value'], field_name):
                group['details'].append(detail)
                group['support_count'] += 1
                grouped = True
                break

        if not grouped:
            groups.append({
                'representative_value': value,
                'details': [detail],
                'support_count': 1
            })

    return groups


def _score_value_groups(value_groups: List[Dict], field_name: str) -> List[Dict]:
    """
    Bewertet Werte-Gruppen basierend auf verschiedenen Qualitätskriterien
    """
    scored_groups = []

    for group in value_groups:
        value = group['representative_value']
        details = group['details']

        # Basis-Score: Anzahl unterstützender Modelle
        support_score = len(details) * 10

        # Model-Quality-Bonus
        model_bonus = _calculate_model_bonus(details)

        # Value-Quality-Score
        value_quality_score = _calculate_value_quality_score(value, field_name)

        # Numerische Werte bevorzugen für numerische Felder
        numeric_bonus = _calculate_numeric_bonus(value, field_name)

        # Source-Quality-Score
        source_bonus = _calculate_source_bonus(details)

        total_score = support_score + model_bonus + value_quality_score + numeric_bonus + source_bonus

        scored_groups.append({
            'value': value,
            'details': details,
            'support_count': len(details),
            'total_score': total_score,
            'score_breakdown': {
                'support_score': support_score,
                'model_bonus': model_bonus,
                'value_quality': value_quality_score,
                'numeric_bonus': numeric_bonus,
                'source_bonus': source_bonus
            }
        })

    # Sortiere nach Score
    scored_groups.sort(key=lambda x: x['total_score'], reverse=True)
    return scored_groups


def _calculate_model_bonus(details: List[Dict]) -> int:
    """Berechnet Model-Quality-Bonus basierend auf verwendeten Modellen"""
    model_bonus = 0
    premium_models = ['claude-3.5-sonnet', 'gpt-4o', 'gemini-pro']
    search_models = ['tavily', 'exa', 'perplexity']

    for detail in details:
        model_id = detail.get("ai_model", '')
        if any(premium in model_id.lower() for premium in premium_models):
            model_bonus += 15
        elif any(search in model_id.lower() for search in search_models):
            model_bonus += 10
        else:
            model_bonus += 5

    return model_bonus


def _calculate_value_quality_score(value: str, field_name: str) -> int:
    """Bewertet die Qualität eines Wertes"""
    if not value or str(value).strip() == '':
        return 0

    value_str = str(value).strip()

    # Basis-Score basierend auf Länge und Spezifität
    base_score = min(len(value_str), 50)

    # Bonus für strukturierte Werte
    structure_bonus = 0
    if field_name and 'coordinate' in field_name.lower():
        # Koordinaten: Suche nach Zahlen und Grad-Zeichen
        if any(char.isdigit() for char in value_str) and ('°' in value_str or ',' in value_str):
            structure_bonus = 20
    elif field_name and any(word in field_name.lower() for word in ['date', 'jahr', 'year']):
        # Datum/Jahr: Suche nach 4-stelligen Zahlen
        if any(part.isdigit() and len(part) == 4 for part in value_str.split()):
            structure_bonus = 15
    elif field_name and any(word in field_name.lower() for word in ['cost', 'kosten', 'price']):
        # Kosten: Suche nach Währungen und Zahlen
        if any(char in value_str for char in ['$', '€', '£']) and any(char.isdigit() for char in value_str):
            structure_bonus = 15

    return base_score + structure_bonus


def _calculate_numeric_bonus(value: str, field_name: str) -> int:
    """Bonus für numerische Werte in numerischen Feldern"""
    if not field_name:
        return 0

    numeric_fields = ['production_volume', 'area_qkm', 'coordinates', 'year', 'cost', 'kosten']
    if not any(nf in field_name.lower() for nf in numeric_fields):
        return 0

    try:
        # Versuche numerischen Wert zu extrahieren
        clean_value = str(value).replace(',', '.').replace(' ', '')
        # Suche nach Zahlen im String
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', clean_value)
        if numbers:
            return 20
    except (ValueError, AttributeError):
        pass

    return 0


def _calculate_source_bonus(details: List[Dict]) -> int:
    """Berechnet Bonus basierend auf Quellen-Qualität"""
    total_sources = 0
    government_sources = 0

    for detail in details:
        sources = detail.get("real_sources", [])
        total_sources += len(sources)

        # Prüfe auf Regierungs-/Behörden-Quellen
        for source in sources:
            if isinstance(source, str):
                if any(domain in source.lower() for domain in ['.gov', '.ca', '.de', 'government', 'ministry']):
                    government_sources += 1

    source_bonus = min(total_sources * 2, 20)  # Max 20 Punkte
    gov_bonus = government_sources * 5  # 5 Punkte pro Regierungsquelle

    return source_bonus + gov_bonus


def _calculate_consistency_score(scored_groups: List[Dict], total_values: int) -> float:
    """Berechnet Konsistenz-Score basierend auf Werte-Verteilung"""
    if not scored_groups or total_values == 0:
        return 0.0

    if len(scored_groups) == 1:
        return 100.0  # Perfekte Konsistenz

    # Anteil der Modelle die den Top-Value unterstützen
    top_support = scored_groups[0]['support_count']
    consistency_score = (top_support / total_values) * 100

    return min(consistency_score, 100.0)


def _calculate_confidence_score(scored_groups: List[Dict], value_details: List[Dict]) -> float:
    """Berechnet Konfidenz-Score basierend auf Best-Value-Qualität"""
    if not scored_groups or not value_details:
        return 0.0

    max_possible_score = len(value_details) * 25 + 50  # Theoretisches Maximum
    actual_score = scored_groups[0]['total_score']
    confidence_score = min((actual_score / max_possible_score) * 100, 100.0)

    return confidence_score


def _select_best_value(scored_groups: List[Dict]) -> Dict:
    """Wählt besten Wert basierend auf Scoring"""
    if not scored_groups:
        return {
            'display_value': '',
            'confidence_score': 0.0,
            'source_info': 'Keine Daten',
            'method': 'no_data',
            'supporting_sources': []
        }

    best_group = scored_groups[0]
    best_value = best_group['value']

    # Sammle unterstützende Quellen
    supporting_sources = []
    for detail in best_group['details']:
        sources = detail.get("real_sources", [])
        supporting_sources.extend(sources[:2])  # Max 2 Quellen pro Detail

    # Entferne Duplikate und limitiere
    supporting_sources = list(dict.fromkeys(supporting_sources))[:5]  # Max 5 Quellen

    return {
        'display_value': best_value,
        'confidence_score': min((best_group['total_score'] / 100) * 100, 100.0),
        'source_info': f"{best_group['support_count']} Modelle",
        'method': 'intelligent_analysis',
        'supporting_sources': supporting_sources,
        'model_consensus': best_group['support_count'],
        'frequency': best_group['support_count']
    }


def create_result_metadata(mine_data: Dict, best_values: Dict, detailed_breakdown: Dict) -> Dict:
    """
    Erstellt strukturierte Metadaten für API-Response
    """
    # Berechne Overall-Konfidenz
    confidence_scores = [
        details['best_value_info']['confidence_score']
        for details in detailed_breakdown.values()
        if details['best_value_info']['confidence_score'] > 0
    ]
    overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

    # Separiere Metadatenfelder von Datenfeldern
    metadata_fields = {
        'mine_name': mine_data['mine_name'],
        'country': mine_data['country'],
        'region': mine_data['region'],
        'model_count': mine_data['model_count'],
        'last_updated': mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
        'total_sources': mine_data['total_sources']
    }

    return {
        'metadata': metadata_fields,
        'overall_confidence': round(overall_confidence, 1),
        'validation_summary': {
            'total_fields': len(detailed_breakdown),
            'valid_fields': len([d for d in detailed_breakdown.values() if d['validation_passed']]),
            'high_confidence_fields': len([d for d in detailed_breakdown.values() if d['confidence_score'] >= 70]),
            'avg_confidence': round(overall_confidence, 1)
        }
    }


def create_structured_fields_response(detailed_breakdown: Dict, best_values: Dict, mine_data: Dict,
    """create_structured_fields_response - TODO: Dokumentation hinzufügen"""
global_source_index: Dict) -> Dict:
    """
    Erstellt strukturierte Felder für API-Response mit globalen Quellenreferenzen
    """
    structured_fields = {}

    for field_name, field_breakdown in detailed_breakdown.items():
        # Nur echte Datenfelder, keine Metadaten
        metadaten_felder = ['Mine', 'Land', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung', 'Details']
        if field_name in metadaten_felder:
            continue

        best_value_info = field_breakdown['best_value_info']
        supporting_sources = best_value_info.get("supporting_sources", [])

        # PHASE 2.1: Konvertiere URLs zu globalen Referenznummern
        global_source_numbers = []
        if supporting_sources and global_source_index:
            for source_url in supporting_sources[:3]:  # Nur erste 3 URLs
                try:
                    for number, source_data in global_source_index.items():
                        if isinstance(source_data, dict) and source_data.get('url') == source_url:
                            global_source_numbers.append(int(number))
                            break
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error converting source URL {source_url} to global number: {e}")
                    continue

        structured_fields[field_name] = {
            'value': best_values.get(field_name, ''),
            'confidence_score': field_breakdown['confidence_score'],
            'consistency_score': field_breakdown['consistency_score'],
            'source_count': len(supporting_sources),
            'source_references': supporting_sources[:3],  # URLs der unterstützenden Quellen
            'global_source_numbers': sorted(global_source_numbers),  # Globale Nummern für Frontend
            'model_consensus': best_value_info.get("model_consensus", 0),
            'frequency': best_value_info.get("frequency", 1),
            'validation_passed': field_breakdown['validation_passed']
        }

    return structured_fields


def create_quality_metrics(detailed_breakdown: Dict) -> Dict:
    """
    Erstellt Qualitäts-Metriken für die Bewertung der Datenqualität
    """
    if not detailed_breakdown:
        return {
            'fields_with_high_confidence': 0,
            'fields_with_multiple_sources': 0,
            'avg_source_diversity': 0.0,
            'validation_pass_rate': 0.0
        }

    high_confidence_fields = len([
        d for d in detailed_breakdown.values()
        if d['confidence_score'] >= 70
    ])

    fields_with_multiple_sources = len([
        d for d in detailed_breakdown.values()
        if len(d['best_value_info'].get('supporting_sources', [])) > 1
    ])

    avg_source_diversity = sum(
        len(d['best_value_info'].get('supporting_sources', []))
        for d in detailed_breakdown.values()
    ) / len(detailed_breakdown)

    validation_pass_rate = len([
        d for d in detailed_breakdown.values()
        if d['validation_passed']
    ]) / len(detailed_breakdown) * 100

    return {
        'fields_with_high_confidence': high_confidence_fields,
        'fields_with_multiple_sources': fields_with_multiple_sources,
        'avg_source_diversity': round(avg_source_diversity, 1),
        'validation_pass_rate': round(validation_pass_rate, 1)
    }


def filter_best_values_for_legacy_compatibility(best_values: Dict, detailed_breakdown: Dict) -> Dict:
    """
    Filtert und erweitert best_values für Legacy-Kompatibilität
    """
    # FELDFIX 29.08.2025: Meta-Felder filtern und kritische Felder hinzufügen
    filtered_values = {k: v for k, v in best_values.items() if not k.startswith('_')}

    # Kritische Felder aus detailed_breakdown zu best_values kopieren
    for field_name, field_data in detailed_breakdown.items():
        if field_name in ['Land', 'Region']:
            display_value = field_data['best_value_info']['display_value']
            if display_value and display_value != '':
                filtered_values[field_name] = display_value

    return filtered_values
