"""
Author: rahn
Datum: 27.08.2025  
Version: 1.0
Beschreibung: Datenbank-Viewer API für Read-Only Zugriff auf alle Tabellen
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text, inspect
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from minesearch.database import db_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# NORMALISIERTE DATENBANK-STRUKTUR (06.09.2025)
# Nach Bereinigung: Nur 12 relevante Tabellen
NORMALIZED_STRUCTURE = {
    "🗂️ Stammdaten (Lookups)": [
        'countries',     # Länder mit ISO-Codes
        'regions',       # Regionen/Provinzen
        'commodities',   # Rohstoffe (Gold, Kupfer, etc.)
        'companies',     # Unternehmen (Owner/Operator)
        'ai_models',     # AI-Modelle für Suchen
        'sources'        # Datenquellen
    ],
    "⛏️ Kerndaten": [
        'mines'          # Minen mit Foreign Keys zu Lookups
    ],
    "🔗 Beziehungen (N:M)": [
        'mine_commodities',  # Mine ↔ Rohstoffe
        'mine_owners',       # Mine ↔ Eigentümer
        'mine_operators'     # Mine ↔ Betreiber
    ],
    "🔍 Such-Ergebnisse": [
        'search_results',    # Gespeicherte Suchergebnisse
        'search_sessions'    # Such-Sessions für Gruppierung
    ]
}

def categorize_table(table_name: str, row_count: int) -> str:
    """Kategorisiert Tabellen basierend auf normalisierter Struktur"""
    
    # Durchsuche die normalisierte Struktur
    for category, tables in NORMALIZED_STRUCTURE.items():
        if table_name in tables:
            return category
    
    # Fallback für unbekannte Tabellen (sollte nicht vorkommen)
    return "❓ Unbekannt"

# Wichtige Tabellen für Quick-Access
IMPORTANT_TABLES = ['mines', 'search_results', 'sources', 'countries', 'commodities', 'companies']

@router.get("/tables")
async def get_all_tables():
    """Gibt eine Liste aller verfügbaren Tabellen zurück"""
    try:
        with db_manager.get_session() as session:
            preparer = session.bind.dialect.identifier_preparer
            # Alle Tabellen aus sqlite_master
            result = session.execute(text("""
                SELECT name, type FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))
            all_tables = result.fetchall()
            
            # Zähle Einträge für jede Tabelle und kategorisiere dynamisch
            table_info = []
            categories_found = {}
            
            for table_name, table_type in all_tables:
                try:
                    quoted_table = preparer.quote(table_name)
                    count_result = session.execute(text(f"SELECT COUNT(*) FROM {quoted_table}"))
                    count = count_result.fetchone()[0]
                    
                    # Dynamische Kategorisierung
                    category = categorize_table(table_name, count)
                    
                    # Sammle gefundene Kategorien für Statistik
                    if category not in categories_found:
                        categories_found[category] = []
                    categories_found[category].append(table_name)
                    
                    table_info.append({
                        "name": table_name,
                        "type": table_type,
                        "row_count": count,
                        "category": category,
                        "is_important": table_name in IMPORTANT_TABLES
                    })
                except Exception as e:
                    logger.warning(f"Fehler beim Zählen von Tabelle {table_name}: {e}")
                    table_info.append({
                        "name": table_name,
                        "type": table_type, 
                        "row_count": 0,
                        "category": "Error",
                        "is_important": False
                    })
            
            return {
                "success": True,
                "tables": table_info,
                "categories": categories_found,  # Dynamisch gefundene Kategorien
                "normalized_structure": NORMALIZED_STRUCTURE,  # Struktur-Definition
                "important_tables": IMPORTANT_TABLES,
                "total_tables": len(table_info),
                "normalized": True,  # Flag für normalisierte DB
                "category_count": len(categories_found)
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Laden der Tabellen: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@router.get("/table/{table_name}")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    filter_column: Optional[str] = Query(None),
    filter_value: Optional[str] = Query(None)
):
    """Gibt Daten einer spezifischen Tabelle zurück"""
    try:
        with db_manager.get_session() as session:
            # Validiere Tabelle existiert
            check_table = session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name = :table_name
            """), {"table_name": table_name})
            
            if not check_table.fetchone():
                raise HTTPException(status_code=404, detail=f"Tabelle '{table_name}' nicht gefunden")
            
            # Hole Spalten-Info (mit sicherem Quoting des Tabellennamens)
            preparer = session.bind.dialect.identifier_preparer
            quoted_table = preparer.quote(table_name)
            column_result = session.execute(text(f"PRAGMA table_info({quoted_table})"))
            columns_info = column_result.fetchall()
            columns = [col[1] for col in columns_info]  # col[1] ist der Name
            column_types = {col[1]: col[2] for col in columns_info}  # col[2] ist der Typ

            # Baue Mapping der sicher gequoteten Spaltennamen
            quoted_columns = {name: preparer.quote(name) for name in columns}

            # Validierung der übergebenen Identifier
            if filter_column is not None and filter_column not in columns:
                raise HTTPException(status_code=400, detail=f"Ungültige Spalte für Filter: '{filter_column}'")
            if sort_by is not None and sort_by not in columns:
                raise HTTPException(status_code=400, detail=f"Ungültige Spalte für Sortierung: '{sort_by}'")

            # Sortierreihenfolge normalisieren/validieren
            sort_order_value = (sort_order or "asc").lower()
            if sort_order_value not in ("asc", "desc"):
                raise HTTPException(status_code=400, detail="Ungültige Sortierreihenfolge. Erlaubt: 'asc' oder 'desc'")
            sort_order_sql = "ASC" if sort_order_value == "asc" else "DESC"

            # Baue Basis-Queries mit sicher gequoteten Identifiern
            base_query = f"SELECT * FROM {quoted_table}"
            count_query = f"SELECT COUNT(*) FROM {quoted_table}"

            # Filter hinzufügen (gebundener Parameter nur für Werte)
            where_clause = ""
            filter_params = {}
            if filter_column and filter_value is not None:
                quoted_filter_col = quoted_columns[filter_column]
                where_clause = f" WHERE {quoted_filter_col} LIKE :filter_value"
                filter_params["filter_value"] = f"%{filter_value}%"
                base_query += where_clause
                count_query += where_clause

            # Sortierung hinzufügen (nur gültige/whitelistete Spalten, sicher gequotet)
            if sort_by:
                quoted_sort_col = quoted_columns[sort_by]
                base_query += f" ORDER BY {quoted_sort_col} {sort_order_sql}"
            else:
                if "id" in columns:
                    base_query += f" ORDER BY {quoted_columns['id']} {sort_order_sql}"
                elif "created_at" in columns:
                    base_query += f" ORDER BY {quoted_columns['created_at']} {sort_order_sql}"

            # Pagination mittels gebundener Parameter (sichere Integers)
            offset = (page - 1) * limit
            base_query += " LIMIT :limit OFFSET :offset"
            
            # Führe Queries aus
            total_result = session.execute(text(count_query), filter_params)
            total_count = total_result.fetchone()[0]
            
            data_params = {**filter_params, "limit": int(limit), "offset": int(offset)}
            data_result = session.execute(text(base_query), data_params)
            rows = data_result.fetchall()
            
            # Konvertiere zu Dictionary und formatiere Daten
            formatted_rows = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i] if i < len(row) else None
                    
                    # Formatiere spezielle Datentypen
                    if value is None:
                        formatted_value = None
                    elif column_types.get(column, '').lower() in ['json', 'text'] and isinstance(value, str):
                        # Versuche JSON zu parsen
                        try:
                            json_data = json.loads(value)
                            formatted_value = {
                                "type": "json",
                                "raw": value,
                                "parsed": json_data
                            }
                        except:
                            formatted_value = value
                    elif isinstance(value, datetime):
                        formatted_value = value.isoformat()
                    else:
                        formatted_value = value
                    
                    row_dict[column] = formatted_value
                
                formatted_rows.append(row_dict)
            
            return {
                "success": True,
                "data": {
                    "table_name": table_name,
                    "columns": columns,
                    "column_types": column_types,
                    "rows": formatted_rows,
                    "pagination": {
                        "total_count": total_count,
                        "page": page,
                        "limit": limit,
                        "total_pages": (total_count + limit - 1) // limit,
                        "has_next": page * limit < total_count,
                        "has_prev": page > 1
                    },
                    "filters": {
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "filter_column": filter_column,
                        "filter_value": filter_value
                    }
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden von Tabelle {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@router.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """Gibt das Schema einer Tabelle zurück"""
    try:
        with db_manager.get_session() as session:
            # Table Info
            result = session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()
            
            if not columns:
                raise HTTPException(status_code=404, detail=f"Tabelle '{table_name}' nicht gefunden")
            
            # Foreign Keys
            fk_result = session.execute(text(f"PRAGMA foreign_key_list({table_name})"))
            foreign_keys = fk_result.fetchall()
            
            # Indices
            idx_result = session.execute(text(f"PRAGMA index_list({table_name})"))
            indices = idx_result.fetchall()
            
            schema_info = {
                "table_name": table_name,
                "columns": [
                    {
                        "id": col[0],
                        "name": col[1], 
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    } for col in columns
                ],
                "foreign_keys": [
                    {
                        "id": fk[0],
                        "seq": fk[1], 
                        "table": fk[2],
                        "from": fk[3],
                        "to": fk[4]
                    } for fk in foreign_keys
                ],
                "indices": [
                    {
                        "seq": idx[0],
                        "name": idx[1],
                        "unique": bool(idx[2])
                    } for idx in indices
                ]
            }
            
            return {
                "success": True,
                "schema": schema_info
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden des Schemas für {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@router.get("/export/{table_name}/csv")
async def export_table_csv(
    table_name: str,
    filter_column: Optional[str] = Query(None),
    filter_value: Optional[str] = Query(None)
):
    """Exportiert Tabellen-Daten als CSV"""
    try:
        from io import StringIO
        import csv
        
        with db_manager.get_session() as session:
            preparer = session.bind.dialect.identifier_preparer
            # Validiere Tabelle
            check_table = session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name = :table_name
            """), {"table_name": table_name})
            
            if not check_table.fetchone():
                raise HTTPException(status_code=404, detail=f"Tabelle '{table_name}' nicht gefunden")
            
            # Hole Spalten
            quoted_table = preparer.quote(table_name)
            column_result = session.execute(text(f"PRAGMA table_info({quoted_table})"))
            columns = [col[1] for col in column_result.fetchall()]
            quoted_columns = {name: preparer.quote(name) for name in columns}
            
            # Validiere Filterspalte
            if filter_column is not None and filter_column not in columns:
                raise HTTPException(status_code=400, detail=f"Ungültige Spalte für Filter: '{filter_column}'")
            
            # Baue Query mit optionalem Filter
            query = f"SELECT * FROM {quoted_table}"
            params = {}
            if filter_column and filter_value is not None:
                quoted_filter_col = quoted_columns[filter_column]
                query += f" WHERE {quoted_filter_col} LIKE :filter_value"
                params["filter_value"] = f"%{filter_value}%"
            
            # Daten laden (max 10000 Einträge für CSV)
            query += " LIMIT 10000"
            result = session.execute(text(query), params)
            rows = result.fetchall()
            
            # CSV generieren
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(columns)
            
            # Daten
            for row in rows:
                # Konvertiere alle Werte zu Strings
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append("")
                    elif isinstance(value, datetime):
                        formatted_row.append(value.isoformat())
                    else:
                        formatted_row.append(str(value))
                writer.writerow(formatted_row)
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={table_name}_export.csv"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim CSV-Export von {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")