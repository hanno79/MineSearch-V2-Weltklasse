"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: HTML-Batch-Ergebnisse für MineSearch Frontend
"""

from typing import Dict, List, Any, Optional
from config import CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
import re
import logging

logger = logging.getLogger(__name__)


def create_batch_results_table(results: List[Dict]) -> str:
    """Erstelle HTML-Tabelle für Batch-Ergebnisse"""
    if not results:
        return ""
    
    logger.info(f"create_batch_results_table: Verarbeite {len(results)} Ergebnisse")
    
    # CSV-Daten für Export vorbereiten
    csv_lines_with_sources = [";".join(CSV_COLUMNS)]  # Header
    
    # HTML-Tabelle vorbereiten
    csv_table_html = f"""
    <div style="margin: 0; padding: 10px 0; background: #f0fff4; width: 100%;">
        <div style="max-width: 1400px; margin: 0 auto; padding: 0 15px;">
            <h4>📊 Ergebnistabelle mit Quellenreferenzen</h4>
            <p style="margin-bottom: 10px;">Die Tabelle zeigt alle gefundenen Daten. Zahlen in eckigen Klammern [1,2,3] verweisen auf die Quellen unten.</p>
        </div>
        
        <div style="overflow-x: auto; padding: 0 10px;">
            <table id="results-table" style="width: 100%; border-collapse: collapse; font-size: 13px; background: white; table-layout: fixed;">
                <thead>
                    <tr style="background: #4CAF50; color: white;">
    """
    
    # Tabellen-Header mit optimierten Breiten
    column_widths = {
        'ID': '40px',
        'Name': '150px',
        'Country': '80px',
        'Region': '100px',
        'Eigentümer': '120px',
        'Betreiber': '120px',
        'x-Koordinate': '90px',
        'y-Koordinate': '90px',
        'Aktivitätsstatus': '100px',
        'Restaurationskosten': '130px',
        'Jahr der Aufnahme der Kosten': '80px',
        'Jahr der Erstellung des Dokumentes': '80px',
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': '100px',
        'Minentyp (Untertage/ Open-Pit/ usw.)': '100px',
        'Produktionsstart': '80px',
        'Produktionsende': '80px',
        'Fördermenge/Jahr': '100px',
        'Fläche der Mine in qkm': '80px',
        'Quellenangaben': '120px'
    }
    
    for col in CSV_COLUMNS:
        width = column_widths.get(col, 'auto')
        csv_table_html += f'<th style="padding: 8px 6px; border: 1px solid #ddd; text-align: left; position: sticky; top: 0; background: #4CAF50; width: {width}; min-width: {width}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{col}</th>'
    csv_table_html += '</tr></thead><tbody>'
    
    # Tabellen-Zeilen
    rows_added = 0
    for idx, r in enumerate(results):
        logger.info(f"[TABLE-DEBUG] Result {idx}: keys={list(r.keys())}")
        logger.info(f"[TABLE-DEBUG] Result {idx} - Mine: {r.get('mine_name', 'Unknown')}, Success: {r.get('success', False)}")
        
        # Prüfe ob structured_data vorhanden ist
        has_structured_data = False
        if 'data' in r and isinstance(r['data'], dict):
            data_keys = list(r['data'].keys())
            logger.info(f"[TABLE-DEBUG] Result {idx} data keys: {data_keys}")
            
            has_structured_data = 'structured_data' in r['data'] and r['data']['structured_data']
            if has_structured_data:
                sd_keys = list(r['data']['structured_data'].keys())
                logger.info(f"[TABLE-DEBUG] Result {idx} structured_data keys (first 5): {sd_keys[:5]}")
                logger.info(f"[TABLE-DEBUG] Result {idx} structured_data sample: {dict(list(r['data']['structured_data'].items())[:3])}")
            else:
                logger.warning(f"[TABLE-DEBUG] Result {idx} has no structured_data or it's empty")
        else:
            logger.warning(f"[TABLE-DEBUG] Result {idx} has no 'data' key or data is not dict")
        
        if has_structured_data:
            rows_added += 1
            row_style = 'style="background: #f9f9f9;"' if idx % 2 == 0 else ''
            csv_table_html += f'<tr {row_style}>'
            
            # CSV-Zeile für Export vorbereiten
            csv_values = []
            
            for col in CSV_COLUMNS:
                value = r['data']['structured_data'].get(col, '')
                display_value = value if value else ''
                
                # Spezialbehandlung für Quellenangaben im CSV - KEINE Dummy-Werte
                if col == 'Quellenangaben' and value and value != 'Keine spezifischen Quellen dokumentiert':
                    # Für CSV: Entferne Nummerierung aus Quellen
                    clean_sources = []
                    if '+++' in value:
                        for source in value.split('+++'):
                            # Entferne [X] Präfix mit regex
                            clean_source = re.sub(r'^\[\d+\]\s*', '', source.strip())
                            if clean_source and not clean_source.startswith('Keine'):
                                clean_sources.append(clean_source)
                    
                    if clean_sources:
                        display_value = ' | '.join(clean_sources)
                    else:
                        display_value = ''
                elif col == 'Quellenangaben' and (not value or value == 'Keine spezifischen Quellen dokumentiert'):
                    display_value = ''
                
                # Für CSV: Escape Semikolons
                csv_value = str(display_value).replace(';', ',') if display_value else ''
                csv_values.append(csv_value)
                
                # Formatiere für HTML-Tabelle
                if col in ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']:
                    cell_style = 'style="background: #fff3cd; padding: 6px 4px; border: 1px solid #ddd; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"'
                else:
                    cell_style = 'style="padding: 6px 4px; border: 1px solid #ddd; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"'
                
                csv_table_html += f'<td {cell_style} title="{display_value}">{display_value[:100]}{"..." if len(str(display_value)) > 100 else ""}</td>'
            
            csv_table_html += '</tr>'
            csv_lines_with_sources.append(";".join(csv_values))
    
    csv_table_html += '</tbody></table></div></div>'
    
    # Batch-Quellen-Zusammenfassung
    source_summary = _create_batch_source_summary(results)
    
    logger.info(f"[TABLE] Batch-Tabelle erstellt: {rows_added} Zeilen mit Daten")
    
    return csv_table_html + source_summary


def _create_batch_source_summary(results: List[Dict]) -> str:
    """Erstelle Zusammenfassung aller Quellen für Batch-Ergebnisse"""
    all_sources = {}
    source_counter = 1
    
    # Sammle alle Quellen
    for result in results:
        if 'data' in result and 'sources' in result['data']:
            sources = result['data']['sources']
            mine_name = result.get('mine_name', f"Mine {source_counter}")
            
            for source in sources:
                if isinstance(source, dict):
                    url = source.get('url', source.get('value', ''))
                    title = source.get('title', f'Quelle {source_counter}')
                    
                    if url and url not in all_sources:
                        all_sources[url] = {
                            'number': source_counter,
                            'title': title,
                            'url': url,
                            'mines': [mine_name]
                        }
                        source_counter += 1
                    elif url in all_sources:
                        if mine_name not in all_sources[url]['mines']:
                            all_sources[url]['mines'].append(mine_name)
    
    if not all_sources:
        return ""
    
    # Erstelle HTML für Quellen-Zusammenfassung
    sources_html = """
    <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
        <h4>📚 Quellenverzeichnis für alle Batch-Ergebnisse</h4>
        <p>Die folgenden Quellen wurden für die Recherche verwendet:</p>
        <ol style="margin-left: 20px;">
    """
    
    for source_data in sorted(all_sources.values(), key=lambda x: x['number']):
        mines_list = ', '.join(source_data['mines'][:3])  # Zeige max. 3 Minen
        if len(source_data['mines']) > 3:
            mines_list += f" und {len(source_data['mines']) - 3} weitere"
        
        sources_html += f"""
        <li style="margin-bottom: 10px;">
            <strong>[{source_data['number']}]</strong> 
            <a href="{source_data['url']}" target="_blank" style="color: #007bff;">{source_data['title']}</a>
            <br><small style="color: #666;">Verwendet für: {mines_list}</small>
        </li>
        """
    
    sources_html += "</ol></div>"
    
    return sources_html