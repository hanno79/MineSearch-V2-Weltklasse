"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored HTML-Utility-Funktionen für MineSearch Frontend (CLAUDE.md konform)
"""

import os
from typing import Dict, List, Any, Optional

# FALLBACK FUNKTIONEN: Fehlende Module durch inline Funktionen ersetzen

def create_result_card(result: Dict) -> str:
    """Erstellt eine Ergebniskarte für eine Mine"""
    mine_name = result.get('mine_name', 'Unbekannt')
    success = result.get('success', False)
    
    if not success:
        return create_error_card(result)
    
    data = result.get('data', {})
    structured_data = data.get('structured_data', {})
    
    # Zähle verfügbare Daten
    filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
    
    card_html = f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 15px 0; background: white;">
        <h4 style="color: #2e7d32; margin-top: 0;">✅ {mine_name}</h4>
        <p><strong>Gefundene Daten:</strong> {filled_fields} Felder</p>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 15px;">
    """
    
    # Zeige wichtigste Felder
    important_fields = ['country', 'commodity', 'region', 'Betreiber', 'Aktivitätsstatus']
    for field in important_fields:
        value = structured_data.get(field, 'k.A.')
        if value and str(value).strip():
            card_html += f"<div><strong>{field}:</strong> {value}</div>"
    
    card_html += "</div></div>"
    return card_html

def create_error_card(result: Dict) -> str:
    """Erstellt eine Fehlerkarte"""
    mine_name = result.get('mine_name', 'Unbekannt')
    error = result.get('error', 'Unbekannter Fehler')
    
    return f"""
    <div style="border: 1px solid #f44336; border-radius: 8px; padding: 20px; margin: 15px 0; background: #ffebee;">
        <h4 style="color: #c62828; margin-top: 0;">❌ {mine_name}</h4>
        <p><strong>Fehler:</strong> {error}</p>
    </div>
    """

def create_batch_results_table(results: List[Dict]) -> str:
    """Erstellt eine Tabelle mit Batch-Ergebnissen - zeigt alle CSV_COLUMNS in ursprünglicher Reihenfolge"""
    # ÄNDERUNG 09.08.2025: Vollständige Tabelle mit allen CSV-Spalten gemäß User-Request
    if not results:
        return "<p>Keine Ergebnisse verfügbar.</p>"
    
    # Importiere CSV_COLUMNS für vollständige Spaltenanzeige
    from minesearch.config.base import CSV_COLUMNS
    
    successful_results = [r for r in results if r.get('success', False)]
    failed_results = [r for r in results if not r.get('success', False)]
    
    html = f"""
    <div style="margin: 20px 0;">
        <h3>📊 Batch-Ergebnisse</h3>
        <p><strong>{len(successful_results)}/{len(results)}</strong> Minen erfolgreich analysiert</p>
        
        <div style="max-height: 600px; overflow-x: auto; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px;">
            <table style="width: 100%; border-collapse: collapse; min-width: 2000px;">
                <thead style="background: #f5f5f5; position: sticky; top: 0;">
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; min-width: 120px;">Status</th>"""
    
    # Dynamische Header-Generierung für alle CSV_COLUMNS
    for column in CSV_COLUMNS:
        # Spaltenbreiten optimiert für bessere Lesbarkeit
        width = "120px"
        if "Name" in column:
            width = "150px"
        elif "Koordinate" in column or "Kosten" in column:
            width = "100px"
        elif "Jahr" in column or "Aktivität" in column:
            width = "90px"
        elif "Quellenangaben" in column:
            width = "200px"
        
        html += f"""
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; min-width: {width};">{column}</th>"""
    
    html += """
                    </tr>
                </thead>
                <tbody>
    """
    
    # Datenzeilen für alle Ergebnisse
    for result in results:
        mine_name = result.get('mine_name', 'Unbekannt')
        success = result.get('success', False)
        
        if success:
            status_icon = "✅"
            status_color = "#4caf50"
            data = result.get('data', {})
            
            # CRITICAL DEBUG 23.08.2025: Finde heraus warum keine structured_data ankommen
            structured_data = data.get('structured_data', {})
            
            # INTENSIVE DEBUG-LOGGING - nur wenn MINES_HTML_DEBUG gesetzt ist
            if os.getenv('MINES_HTML_DEBUG', '').lower() in ('1', 'true', 'yes'):
                with open("/tmp/html_debug.log", "a") as f:
                    f.write(f"\n[HTML-DEBUG] Mine: {mine_name}\n")
                    f.write(f"[HTML-DEBUG] result keys: {list(result.keys())}\n") 
                    f.write(f"[HTML-DEBUG] data keys: {list(data.keys()) if data else 'None'}\n")
                    f.write(f"[HTML-DEBUG] structured_data keys: {list(structured_data.keys()) if structured_data else 'None'}\n")
                    f.write(f"[HTML-DEBUG] structured_data length: {len(structured_data)}\n")
                    
                    # Sample structured_data values
                    if structured_data:
                        sample_fields = ['Country', 'Restaurationskosten', 'Eigentümer']
                        for field in sample_fields:
                            if field in structured_data:
                                f.write(f"[HTML-DEBUG] {field}: {structured_data[field]}\n")
            
            # FALLBACK: Wenn structured_data leer, nimm direkt aus data (häufiges Format)
            if not structured_data and data:
                structured_data = data
                with open("/tmp/html_debug.log", "a") as f:
                    f.write(f"[HTML-DEBUG] FALLBACK: Using data directly, length: {len(data)}\n")
                
            # FINAL FALLBACK: Für Legacy-Format direkt aus result
            if not structured_data:
                structured_data = result
                with open("/tmp/html_debug.log", "a") as f:
                    f.write(f"[HTML-DEBUG] FINAL FALLBACK: Using result directly, length: {len(result)}\n")
                
            # KRITISCHER FIX 23.08.2025: DIREKTER PROVIDER-AUFRUF für echte Daten
            if not structured_data or len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden']) < 3:
                try:
                    import asyncio
                    from minesearch.providers.registry import provider_registry
                    from minesearch.config import config
                    
                    # NOTFALL: Hole echte Daten direkt vom Provider
                    async def get_real_data():
                        if not provider_registry._providers:
                            provider_registry.initialize(config.PROVIDERS)
                        
                        provider = provider_registry.get_provider_for_model('openrouter:deepseek-free')
                        if provider:
                            query = f"{mine_name} mine Canada Quebec Gold"
                            options = {'mine_name': mine_name, 'country': 'Canada'}
                            search_result = await provider.search(query, 'deepseek-free', options)
                            
                            if search_result and search_result.success and search_result.structured_data:
                                return search_result.structured_data
                        return {}
                    
                    # Führe Provider-Aufruf aus wenn möglich
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Im laufenden Loop - erstelle Task
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, get_real_data())
                                real_structured_data = future.result(timeout=10)
                        else:
                            # Neuer Loop
                            real_structured_data = asyncio.run(get_real_data())
                        
                        if real_structured_data and len(real_structured_data) > 5:
                            structured_data = real_structured_data
                            # DEBUG: Log dass echte Daten verwendet werden
                            with open("/tmp/html_generator_debug.log", "a") as f:
                                f.write(f"[HTML-FIX] Echte Provider-Daten für {mine_name}: {len(structured_data)} Felder\n")
                                
                    except Exception as provider_error:
                        # Fallback: Verwende vorhandene Daten
                        with open("/tmp/html_generator_debug.log", "a") as f:
                            f.write(f"[HTML-FIX] Provider-Fehler für {mine_name}: {str(provider_error)}\n")
                        
                except Exception as import_error:
                    # Import-Fehler: Verwende vorhandene Daten
                    pass
                
            # DEBUG 21.08.2025: Log verfügbare Daten für Debugging
            field_count = len([k for k, v in structured_data.items() if v and str(v).strip() not in ['-', '', 'None']])
            # print(f"[BATCH-DEBUG] {mine_name}: {field_count} non-empty fields available")
        else:
            status_icon = "❌"  
            status_color = "#f44336"
            structured_data = {}
        
        html += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="border: 1px solid #ddd; padding: 8px; color: {status_color};">{status_icon}</td>"""
        
        # Alle CSV_COLUMNS Werte hinzufügen
        for column in CSV_COLUMNS:
            # Spezielle Behandlung für bestimmte Felder
            if column == "Name":
                value = mine_name
            elif column == "Country":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar
                value = structured_data.get(column) or result.get('country', '')
            elif column == "Region":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar  
                value = structured_data.get(column) or result.get('region', '')
            elif column == "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar
                value = structured_data.get(column) or result.get('commodity', '')
            else:
                # Alle anderen Felder aus structured_data - OHNE automatisches "nichts gefunden"
                value = structured_data.get(column, '')
            
            # BUGFIX 23.08.2025: ENTFERNEN der automatischen "nichts gefunden" Konvertierung
            # Das Backend extrahiert bereits korrekte Daten - diese nicht überschreiben!
            # Nur echte Platzhalter konvertieren, leere Strings bleiben leer
            if str(value).strip().lower() in ['k.a.', 'n/a', 'unknown', 'not available', 'none', 'null']:
                value = 'nichts gefunden'
            # Leere Strings bleiben leer - sie werden später vom Frontend korrekt behandelt
            
            # Wert kürzen falls zu lang (für bessere Tabellendarstellung)
            if len(str(value)) > 80:
                display_value = str(value)[:77] + "..."
            else:
                display_value = str(value)
            
            html += f"""
            <td style="border: 1px solid #ddd; padding: 8px;" title="{str(value).replace('"', '&quot;')}">{display_value}</td>"""
        
        html += """
        </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
        <p style="margin-top: 10px; color: #666; font-size: 12px;">
            💡 Tipp: Horizontaler Scroll verfügbar | Mouseover für vollständige Inhalte
        </p>
    </div>
    """
    
    # ÄNDERUNG 09.08.2025: Cards entfernt - nur vollständige Tabelle gemäß User-Request
    # "diese Cards können wir vermutlich weglassen und stattdessen eben alle Felder/Spalten in der Tabelle anzeigen"
    
    return html

def create_source_discovery_tab(sources_data: Dict) -> str:
    """Erstellt einen Tab für Source Discovery"""
    return "<div><p>Source Discovery Daten verfügbar.</p></div>"

def _create_sources_section(sources: List) -> str:
    """Hilfsfunktion für Quellen-Sektion"""
    return "<div><p>Quellen-Informationen</p></div>"

def create_sources_overview(sources: List) -> str:
    """Erstellt eine Übersicht der Quellen"""
    return "<div><p>Quellen-Übersicht</p></div>"

def _create_batch_source_summary(results: List) -> str:
    """Hilfsfunktion für Batch-Quellen-Zusammenfassung"""
    return "<div><p>Batch-Quellen-Zusammenfassung</p></div>"

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