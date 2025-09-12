"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: CSV-Export-Funktionalität für konsolidierte Ergebnis-Verarbeitung (Refactoring aus
consolidated_results.py)
"""

import logging
import csv
import io
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

# Import field mappings
from .consolidated_field_utils import FIELD_ORDER
from .consolidated_utils import _normalize_placeholder_value

logger = logging.getLogger(__name__)
router = APIRouter()


class CSVFieldProcessor:
    """Prozessiert Felder für CSV-Export mit atomischen Werten und Quellenreferenzen"""

    @staticmethod
    def process_field(field: str, result: Dict[str, Any]) -> str:
        """
        Hauptfunktion zur Feldverarbeitung für CSV-Export

        Args:
            field: Feldname
            result: Result-Dictionary mit allen Daten

        Returns:
            Verarbeiteter und für CSV optimierter Feldwert
        """
        # Get raw value (atomic lookup with DB session; fallback to best_values)
        value = CSVFieldProcessor._get_field_value(field, result)

        # Normalize according to Rule 10 semantics (empty -> empty string)
        normalized_value = CSVFieldProcessor._normalize_value(value)

        # Resolve source ids via layered fallbacks
        source_ids = CSVFieldProcessor._resolve_source_ids(field, result)

        # Append source references only when appropriate
        value_with_refs = CSVFieldProcessor._add_source_references(normalized_value, source_ids)

        # Escape for CSV and enforce final empty-string on whitespace-only
        final_value = CSVFieldProcessor._escape_for_csv(value_with_refs)
        return final_value

    @staticmethod
    def _get_field_value(field: str, result: Dict[str, Any]) -> Any:
        """Holt Feldwert mit Priorität auf atomische Werte"""
        atomic_value = None
        try:
            from minesearch.atomic_value_service import calculate_best_atomic_value
            from minesearch.database import db_manager

            with db_manager.get_session() as session:
                atomic_result = calculate_best_atomic_value(
                    session, result["mine_name"], field, fallback_to_json=False
                )

                if (
                    atomic_result.get('method') == 'atomic_normalized'
                    and atomic_result.get("confidence_score", 0.0) >= 30.0
                ):
                    atomic_value = atomic_result.get('display_value')
                    logger.debug(f"[CSV-ATOMIC] Verwende atomischen Wert für
{result['mine_name']}.{field}: {atomic_value}")

        except Exception as e:
            # Handle DB/session and atomic lookup errors internally; fall back to best_values
            logger.debug(f"[CSV-ATOMIC] Fehler bei atomischen Werten für {field}: {e}")

        if atomic_value:
            return atomic_value

        best_values = result.get("best_values", {})
        return best_values.get(field, "")

    @staticmethod
    def _normalize_value(value: Any) -> str:
        """Normalisiert Wert gemäß REGEL 10"""
        return _normalize_placeholder_value(value) or ""

    @staticmethod
    def _resolve_source_ids(field: str, result: Dict[str, Any]) -> List[int]:
        """Löst Quellenreferenz-IDs mit mehrstufigem Fallback auf"""
        detailed_breakdown = result.get("detailed_breakdown", {})
        if field not in detailed_breakdown:
            return []

        field_data = detailed_breakdown.get(field, {}) or {}
        source_ids = field_data.get("global_source_numbers", []) or []

        # Fallback 1: structured_fields
        if not source_ids:
            structured_fields = result.get("structured_fields", {}) or {}
            if field in structured_fields:
                source_ids = structured_fields[field].get('global_source_numbers', []) or []

        # Fallback 2: source_mapping (extract first 10 numeric source ids)
        if not source_ids:
            source_mapping = result.get("source_mapping", {})
            if source_mapping and isinstance(source_mapping, dict):
                available_sources = source_mapping.get("sources", {}) or {}
                if available_sources:
                    try:
                        numeric_keys = [int(k) for k in available_sources.keys() if str(k).isdigit()]
                        source_ids = sorted(numeric_keys)[:10]
                    except Exception:
                        source_ids = []

        # Deduplicate while preserving order
        seen: set[int] = set()
        deduped_ids: List[int] = []
        for sid in source_ids:
            if sid not in seen:
                deduped_ids.append(sid)
                seen.add(sid)
        return deduped_ids

    @staticmethod
    def _add_source_references(normalized_value: str, source_ids: List[int]) -> str:
        """Fügt Quellenreferenzen hinzu wenn angemessen"""
        # Only add references for non-empty values and when not already present
        if not normalized_value or not normalized_value.strip():
            return normalized_value

        if not source_ids or len(source_ids) < 3:
            return normalized_value

        # Check if bracketed references already exist
        if re.search(r'\[\d+(?:,\d+)*\]', normalized_value):
            return normalized_value

        refs = f"[{','.join(map(str, source_ids))}]"
        return f"{normalized_value} {refs}"

    @staticmethod
    def _escape_for_csv(value: str) -> str:
        """Escapt Wert für CSV und ersetzt problematische Zeichen"""
        # CSV-FIX 29.08.2025: Ersetze Pipe-Zeichen mit Schrägstrich gemäß User-Anforderung
        escaped_value = str(value).replace("|", "/")
        return escaped_value.strip() and escaped_value or ""


def create_csv_headers_and_fields(all_fields: set) -> tuple[List[str], List[str]]:
    """
    Erstellt CSV-Header und Datenfeld-Mapping basierend auf FIELD_ORDER

    Returns:
        tuple: (header_list, data_fields_list)
    """
    # FIX: Verwende FIELD_ORDER für CSV wie in UI, nicht alphabetische Sortierung
    ordered_fields = []
    unordered_fields = []

    # Separate fields into ordered and unordered (exclude meta fields)
    for field in all_fields:
        if field.startswith('_'):  # Skip meta fields like _source_mapping
            continue
        elif field in FIELD_ORDER:
            ordered_fields.append(field)
        else:
            unordered_fields.append(field)

    # Sort ordered fields by their position in FIELD_ORDER
    ordered_fields.sort(key=lambda x: FIELD_ORDER.index(x))

    # Sort unordered fields alphabetically
    unordered_fields.sort()

    # Combine for final field order (same as UI)
    sorted_fields = ordered_fields + unordered_fields

    # USER REQUIREMENTS 30.07.2025: Header exakt nach gewünschter Reihenfolge
    # Mine | Land | Region | Zuverlässigkeit | Modelle | Letzte Aktualisierung | ...

    header = []
    data_fields = []

    # Metadaten-Felder zuerst (entsprechend FIELD_ORDER)
    metadata_mapping = {
        "Mine": ("Mine", "mine_name"),
        "Land": ("Land", "country"),
        "Region": ("Region", "region"),
        "Zuverlässigkeit": ("Zuverlässigkeit", "overall_confidence"),
        "Modelle": ("Modelle", "model_count"),
        "Letzte Aktualisierung": ("Letzte Aktualisierung", "last_updated")
    }

    # Füge Metadaten-Felder in FIELD_ORDER Reihenfolge hinzu
    for field_name in FIELD_ORDER:
        if field_name in metadata_mapping:
            display_name, data_field = metadata_mapping[field_name]
            header.append(display_name)
            data_fields.append(data_field)

    # Dann alle anderen Felder aus FIELD_ORDER (außer Metadaten, Details und redundantes Quellenangaben)
    excluded_field_keys = set(metadata_mapping.keys()) | {"Details", "Quellenangaben"}
    remaining_fields = [f for f in FIELD_ORDER if f not in excluded_field_keys and f in all_fields]

    # Füge verbleibende Datenfelder hinzu
    for field_name in remaining_fields:
        header.append(field_name)
        data_fields.append(field_name)

    # Ungeordnete Felder am Ende hinzufügen
    for field_name in unordered_fields:
        if field_name not in excluded_field_keys:
            header.append(field_name)
            data_fields.append(field_name)

    return header, data_fields


def process_csv_data_row(result: Dict, data_fields: List[str]) -> List[str]:
    """
    Verarbeitet eine Datenzeile für CSV-Export

    Args:
        result: Result-Dictionary
        data_fields: Liste der Datenfelder

    Returns:
        Liste der verarbeiteten Feldwerte
    """
    csv_row = []

    for field in data_fields:
        if field == "mine_name":
            csv_row.append(result.get("mine_name", ""))
        elif field == "country":
            csv_row.append(result.get("country", ""))
        elif field == "region":
            csv_row.append(result.get("region", ""))
        elif field == "overall_confidence":
            confidence = result.get("overall_confidence", 0)
            csv_row.append(f"{confidence}%" if confidence > 0 else "")
        elif field == "model_count":
            csv_row.append(str(result.get("model_count", 0)))
        elif field == "last_updated":
            last_updated = result.get("last_updated", "")
            if last_updated:
                try:
                    # Convert ISO format to readable format
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    csv_row.append(dt.strftime("%d.%m.%Y %H:%M"))
                except:
                    csv_row.append(last_updated)
            else:
                csv_row.append("")
        else:
            # Reguläre Datenfelder mit CSVFieldProcessor verarbeiten
            processed_value = CSVFieldProcessor.process_field(field, result)
            csv_row.append(processed_value)

    return csv_row


def generate_csv_content(results: List[Dict], header: List[str], data_fields: List[str]) -> str:
    """
    Generiert CSV-Content aus Ergebnissen

    Args:
        results: Liste der Ergebnis-Dictionaries
        header: CSV-Header
        data_fields: Entsprechende Datenfelder

    Returns:
        CSV-Content als String
    """
    csv_lines = []

    # Header hinzufügen
    csv_lines.append("|".join(header))

    # Datenzeilen verarbeiten
    for result in results:
        csv_row = process_csv_data_row(result, data_fields)
        csv_lines.append("|".join(csv_row))

    return "\n".join(csv_lines)


def create_csv_metadata_footer(results: List[Dict], source_index: Dict) -> List[str]:
    """
    Erstellt Metadaten-Footer für CSV mit Quellenverzeichnis

    Args:
        results: Liste der Ergebnisse
        source_index: Globaler Quellenindex

    Returns:
        Liste der Footer-Zeilen
    """
    footer_lines = []

    # Statistiken
    footer_lines.append("")  # Leerzeile
    footer_lines.append("# CSV-EXPORT STATISTIKEN")
    footer_lines.append(f"# Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    footer_lines.append(f"# Anzahl Minen: {len(results)}")

    if source_index:
        footer_lines.append(f"# Anzahl Quellen: {len(source_index)}")
        footer_lines.append("")
        footer_lines.append("# QUELLENVERZEICHNIS")

        # Sortiere Quellen nach Nummer
        sorted_sources = sorted(source_index.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)

        for source_num, source_data in sorted_sources:
            if isinstance(source_data, dict):
                url = source_data.get("url", 'Unbekannte Quelle')
                title = source_data.get("title", '')
                if title:
                    footer_lines.append(f"# [{source_num}] {title} - {url}")
                else:
                    footer_lines.append(f"# [{source_num}] {url}")
            else:
                footer_lines.append(f"# [{source_num}] {source_data}")

    return footer_lines


@router.get("/results/export/csv")
async def export_consolidated_csv(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("mine_name"),
    order: str = Query("asc"),
    exclude_exa: bool = Query(True)
):
    """
    Exportiere konsolidierte Ergebnisse als CSV mit | Trennzeichen

    CSV-Format entspricht der UI-Darstellung mit:
    - Pipe-Trennzeichen (|)
    - Quellenreferenzen [1,2,3]
    - Metadaten-Footer
    - REGEL 10 konforme Werte (keine Fallbacks)
    """
    try:
        # Import hier um zirkuläre Abhängigkeiten zu vermeiden
        from .consolidated_results import get_consolidated_results

        # Hole konsolidierte Daten (wiederverwendung der get_consolidated_results Logik)
        consolidated_data = await get_consolidated_results(
            country=country,
            region=region,
            days_back=days_back,
            sort_by=sort_by,
            order=order,
            exclude_exa=exclude_exa
        )

        if not consolidated_data["success"]:
            raise HTTPException(status_code=500, detail="Fehler beim Laden der Daten")

        results = consolidated_data["data"]["consolidated_results"]
        source_index = consolidated_data["data"].get("global_source_index", {})

        if not results:
            raise HTTPException(status_code=404, detail="Keine Daten für Export verfügbar")

        # CSV-Header erstellen (alle möglichen Felder sammeln)
        all_fields = set()
        for result in results:
            all_fields.update(result["best_values"].keys())

        # Header und Datenfelder erstellen
        header, data_fields = create_csv_headers_and_fields(all_fields)

        # CSV-Content generieren
        csv_content = generate_csv_content(results, header, data_fields)

        # Metadaten-Footer hinzufügen
        footer_lines = create_csv_metadata_footer(results, source_index)
        final_content = csv_content + "\n" + "\n".join(footer_lines)

        # Create streaming response
        def generate():
    """generate - TODO: Dokumentation hinzufügen"""
            yield final_content.encode('utf-8-sig')  # BOM für Excel-Kompatibilität

        # Dateiname mit Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"minesearch_export_{timestamp}.csv"

        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CSV-EXPORT] Fehler beim CSV-Export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV-Export Fehler: {str(e)}")


def create_csv_test_data() -> Dict:
    """
    Erstellt Test-Daten für CSV-Export-Validierung
    Kann für Unit-Tests verwendet werden
    """
    return {
        "success": True,
        "data": {
            "consolidated_results": [
                {
                    "mine_name": "Test Mine",
                    "country": "Deutschland",
                    "region": "Bayern",
                    "overall_confidence": 85.5,
                    "model_count": 3,
                    "last_updated": "2025-09-11T12:00:00",
                    "best_values": {
                        "Betreiber": "Test Corporation",
                        "Rohstoffe": "Gold, Kupfer",
                        "Minentyp": "Untertage"
                    },
                    "detailed_breakdown": {
                        "Betreiber": {
                            "global_source_numbers": [1, 2, 3]
                        }
                    }
                }
            ],
            "global_source_index": {
                "1": {"url": "https://example.com/source1", "title": "Test Source 1"},
                "2": {"url": "https://example.com/source2", "title": "Test Source 2"},
                "3": {"url": "https://example.com/source3", "title": "Test Source 3"}
            }
        }
    }
