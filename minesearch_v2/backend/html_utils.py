"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored HTML-Utility-Funktionen für MineSearch Frontend (CLAUDE.md konform)
"""

from typing import Dict, List, Any, Optional

# Import aller refactoriserten Module
from html_cards import create_result_card, create_error_card
from html_batch import create_batch_results_table, _create_batch_source_summary
from html_sources import create_source_discovery_tab, _create_sources_section, create_sources_overview

# Re-exportiere alle Funktionen für Kompatibilität
__all__ = [
    'create_result_card',
    'create_error_card', 
    'create_batch_results_table',
    'create_source_discovery_tab',
    'create_sources_overview'
]


def create_comprehensive_results_page(results: List[Dict], sources_data: Optional[Dict] = None,
                                    title: str = "MineSearch Ergebnisse") -> str:
    """
    Erstellt eine umfassende HTML-Seite mit allen Ergebnissen
    
    Args:
        results: Liste der Suchergebnisse
        sources_data: Optional - Source Discovery Daten
        title: Titel der Seite
        
    Returns:
        Vollständige HTML-Seite
    """
    if not results:
        return f"""
        <div style="text-align: center; padding: 50px; color: #666;">
            <h3>{title}</h3>
            <p>Keine Ergebnisse verfügbar.</p>
        </div>
        """
    
    # Kategorisiere Ergebnisse
    successful_results = [r for r in results if r.get('success', False)]
    failed_results = [r for r in results if not r.get('success', False)]
    
    # Erstelle Statistiken
    total_mines = len(results)
    successful_mines = len(successful_results)
    success_rate = (successful_mines / total_mines * 100) if total_mines > 0 else 0
    
    # Kopfbereich mit Statistiken
    header_html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
        <h2 style="margin: 0; font-size: 2.5em;">🏔️ {title}</h2>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px;">
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{total_mines}</div>
                <div>Minen untersucht</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{successful_mines}</div>
                <div>Erfolgreich analysiert</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{success_rate:.1f}%</div>
                <div>Erfolgsquote</div>
            </div>
        </div>
    </div>
    """
    
    # Hauptinhalt
    content_html = ""
    
    # Source Discovery Tab (falls verfügbar)
    if sources_data:
        content_html += create_source_discovery_tab(sources_data)
    
    # Batch-Tabelle (falls mehrere Ergebnisse)
    if len(successful_results) > 1:
        content_html += create_batch_results_table(successful_results)
    
    # Einzelne Ergebniskarten
    content_html += '<div style="margin-top: 30px;">'
    
    if successful_results:
        content_html += '<h3>✅ Erfolgreiche Analysen</h3>'
        for result in successful_results:
            content_html += create_result_card(result)
    
    if failed_results:
        content_html += '<h3 style="margin-top: 40px;">❌ Fehlgeschlagene Analysen</h3>'
        for result in failed_results:
            content_html += create_error_card(result)
    
    content_html += '</div>'
    
    # Fußbereich
    footer_html = f"""
    <div style="margin-top: 50px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; color: #666;">
        <p>
            📊 Generiert am {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')} | 
            🔍 MineSearch v2.0 | 
            ⚡ Powered by Multiple AI Models
        </p>
    </div>
    """
    
    return header_html + content_html + footer_html


def create_quick_summary(results: List[Dict]) -> str:
    """
    Erstellt eine schnelle Zusammenfassung der Ergebnisse
    
    Args:
        results: Liste der Suchergebnisse
        
    Returns:
        HTML-String mit Zusammenfassung
    """
    if not results:
        return ""
    
    # Berechne Statistiken
    total_results = len(results)
    successful_results = [r for r in results if r.get('success', False)]
    total_fields_found = 0
    mines_with_coordinates = 0
    mines_with_operators = 0
    mines_with_costs = 0
    
    for result in successful_results:
        data = result.get('data', {})
        structured_data = data.get('structured_data', {})
        
        # Zähle gefüllte Felder
        filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
        total_fields_found += filled_fields
        
        # Prüfe spezifische Felder
        if structured_data.get('x-Koordinate') or structured_data.get('y-Koordinate'):
            mines_with_coordinates += 1
        
        if structured_data.get('Betreiber') or structured_data.get('Eigentümer'):
            mines_with_operators += 1
        
        if structured_data.get('Restaurationskosten'):
            mines_with_costs += 1
    
    avg_fields = total_fields_found / len(successful_results) if successful_results else 0
    
    return f"""
    <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 5px solid #4caf50; margin: 20px 0;">
        <h4 style="color: #2e7d32; margin-top: 0;">📋 Schnelle Zusammenfassung</h4>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
            <div>
                <strong>Erfolgreiche Analysen:</strong> {len(successful_results)}/{total_results}<br>
                <strong>Durchschnittliche Felder:</strong> {avg_fields:.1f} pro Mine<br>
                <strong>Minen mit Koordinaten:</strong> {mines_with_coordinates}
            </div>
            <div>
                <strong>Minen mit Betreiber:</strong> {mines_with_operators}<br>
                <strong>Minen mit Kosten:</strong> {mines_with_costs}<br>
                <strong>Gesamt gefundene Daten:</strong> {total_fields_found} Felder
            </div>
        </div>
    </div>
    """


# Legacy-Kompatibilität: Importiere datetime für Footer
from datetime import datetime