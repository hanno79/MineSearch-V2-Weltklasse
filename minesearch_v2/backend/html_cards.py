"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: HTML-Karten-Generierung für MineSearch Frontend
"""

from typing import Dict, List, Any, Optional
from config import CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
import re


def create_result_card(result: Dict) -> str:
    """Erstelle HTML für ein Suchergebnis"""
    mine = result['mine']
    data = result['data']
    
    # Erstelle strukturierte Tabelle
    structured_html = ""
    if 'structured_data' in data:
        structured = data['structured_data']
        structured_html = """
        <h5>Extrahierte Daten:</h5>
        <table class="data-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Feld</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Wert</th>
            </tr>
        """
        
        # Definiere Finanzspalten für Hervorhebung
        finanz_spalten = ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']
        
        # Verwende structured_data_with_sources für Quellennummern
        data_with_sources = data.get('structured_data_with_sources', {})
        
        # Zeige ALLE CSV-Spalten
        for field in CSV_COLUMNS:
            if field == 'ID':
                continue  # ID wird separat behandelt oder übersprungen
                
            value = structured.get(field, '')
            sources_refs = ''
            
            # Hole Quellennummern nur bei echten Infos und erlaubten Feldern
            if (field not in FIELDS_WITHOUT_SOURCES and 
                field in data_with_sources and
                value and 
                value.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden']):
                sources = data_with_sources[field].get('sources', [])
                if sources:
                    # Entferne Duplikate in den Quellennummern
                    unique_sources = list(set(sources))
                    sources_refs = f" <small><strong>[{', '.join(map(str, unique_sources))}]</strong></small>"
            
            # Hervorhebung für Finanzfelder
            row_style = ""
            if field in finanz_spalten:
                row_style = ' style="background-color: #fff3cd;"'  # Gelber Hintergrund
            
            # Formatiere Wert für Anzeige
            display_value = value if value else '<span style="color: #999;">Keine Daten verfügbar</span>'
            
            structured_html += f"""
            <tr{row_style}>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{field}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{display_value}{sources_refs}</td>
            </tr>
            """
        
        structured_html += "</table>"
    
    # Quellen-HTML generieren
    sources_html = ""
    if 'sources' in data and data['sources']:
        sources_html = "<h5>Quellen:</h5><ol style='margin-left: 20px; padding-left: 0;'>"
        for i, source in enumerate(data['sources'], 1):
            if isinstance(source, dict):
                url = source.get('url', source.get('value', ''))
                title = source.get('title', f'Quelle {i}')
                desc = source.get('description', '')
                
                # Kürze zu lange Titel
                if len(title) > 80:
                    title = title[:77] + "..."
                
                if url:
                    if url.startswith('http'):
                        sources_html += f"""<li style='margin-bottom: 8px;'>
                            <strong>{i}.</strong> <a href="{url}" target="_blank" style="color: #007bff; text-decoration: none;">{title}</a>
                            {f'<br><small style="color: #666;">{desc[:100]}...</small>' if desc else ''}
                        </li>"""
                    else:
                        sources_html += f"""<li style='margin-bottom: 8px;'>
                            <strong>{i}.</strong> {title}
                            <br><small style="color: #666;">{url[:200]}{'...' if len(url) > 200 else ''}</small>
                        </li>"""
                else:
                    sources_html += f"<li style='margin-bottom: 8px;'><strong>{i}.</strong> {title}</li>"
        sources_html += "</ol>"
    
    # Raw Data HTML
    raw_data_html = ""
    if 'raw_content' in data and data['raw_content']:
        raw_content = data['raw_content'][:2000]  # Kürze sehr lange Inhalte
        if len(data['raw_content']) > 2000:
            raw_content += "...\n[Inhalt gekürzt]"
        
        raw_data_html = f"""
        <details style="margin-top: 15px;">
            <summary style="cursor: pointer; font-weight: bold; color: #007bff;">
                🔍 Raw Content anzeigen
            </summary>
            <div style="background-color: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; border-radius: 4px; margin-top: 10px; max-height: 300px; overflow-y: auto;">
                <pre style="white-space: pre-wrap; font-size: 12px; margin: 0;">{raw_content}</pre>
            </div>
        </details>
        """
    
    # Qualitäts-Indikator
    quality_html = ""
    if 'quality_metrics' in data:
        quality = data['quality_metrics']
        score = quality.get('quality_score', 0)
        completion = quality.get('completion_rate', 0)
        
        # Bestimme Farbe basierend auf Qualität
        if score >= 0.7:
            color = "#28a745"  # Grün
            icon = "✅"
        elif score >= 0.4:
            color = "#ffc107"  # Gelb
            icon = "⚠️"
        else:
            color = "#dc3545"  # Rot
            icon = "❌"
        
        quality_html = f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-left: 4px solid {color}; margin: 15px 0;">
            <strong>{icon} Datenqualität:</strong> {score:.1%} 
            ({quality.get('filled_fields', 0)}/{quality.get('total_fields', len(CSV_COLUMNS))} Felder ausgefüllt)
        </div>
        """
    
    # Modell-Info
    model_info = ""
    if 'model_used' in data:
        model_info = f"""
        <small style="color: #666; font-style: italic;">
            Generiert mit: {data['model_used']} | 
            Suchtyp: {data.get('search_type', 'Standard')} |
            {data.get('timestamp', 'Unbekannte Zeit')}
        </small>
        """
    
    return f"""
    <div class="result-card" style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="color: #333; margin-top: 0;">
            🏔️ {mine.get('name', 'Unbekannte Mine')}
            {f" - {mine.get('country', '')}" if mine.get('country') else ""}
        </h4>
        
        {quality_html}
        {structured_html}
        {sources_html}
        {raw_data_html}
        
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
            {model_info}
        </div>
    </div>
    """


def create_error_card(error: Dict) -> str:
    """Erstelle HTML für eine Fehlermeldung"""
    mine = error.get('mine', {})
    error_msg = error.get('error', 'Unbekannter Fehler')
    model = error.get('model_used', 'Unbekanntes Modell')
    timestamp = error.get('timestamp', 'Unbekannte Zeit')
    
    # Bestimme Icon basierend auf Fehlertyp
    icon = "❌"
    if "timeout" in error_msg.lower():
        icon = "⏱️"
    elif "api" in error_msg.lower():
        icon = "🔌"
    elif "not found" in error_msg.lower():
        icon = "🔍"
    
    return f"""
    <div class="error-card" style="border: 1px solid #dc3545; border-radius: 8px; padding: 20px; margin-bottom: 20px; background-color: #f8d7da; color: #721c24;">
        <h4 style="color: #721c24; margin-top: 0;">
            {icon} Fehler bei {mine.get('name', 'Unbekannte Mine')}
            {f" - {mine.get('country', '')}" if mine.get('country') else ""}
        </h4>
        
        <div style="background-color: #fff; padding: 15px; border: 1px solid #f5c6cb; border-radius: 4px; margin: 10px 0;">
            <strong>Fehlermeldung:</strong><br>
            {error_msg}
        </div>
        
        <small style="color: #856404;">
            Modell: {model} | {timestamp}
        </small>
    </div>
    """