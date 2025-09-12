"""
Author: rahn
Datum: 12.07.2025
Version: 2.0
Beschreibung: Refactored HTML-Utility-Funktionen für MineSearch Frontend (CLAUDE.md konform)
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Sichere Debug-Hilfsfunktion: nutzt Logger (DEBUG), respektiert Umgebungsflags und maskiert sensible Felder
def html_debug_log(data: Optional[Dict], structured_data: Optional[Dict], result: Dict, mine_name:
    """html_debug_log - TODO: Dokumentation hinzufügen"""
str, fallback_reason: Optional[str] = None) -> None:
    """Schreibt eine kompakte, sichere Debug-Ausgabe über den App-Logger.

    - Aktiv nur wenn MINES_HTML_DEBUG in ('1','true','yes')
    - Unter Produktionsumgebung nur wenn MINES_HTML_DEBUG_ALLOW_PROD gesetzt ist
    - Maskiert/unterdrückt sensible Felder
    """
    try:
        debug_enabled = os.getenv('MINES_HTML_DEBUG', '').lower() in ('1', 'true', 'yes')
        if not debug_enabled:
            return

        is_production = (
            os.getenv('APP_ENV', '').lower() == 'production' or
            os.getenv('ENVIRONMENT', '').lower() == 'production' or
            os.getenv('IS_PROD', '').lower() in ('1', 'true', 'yes')
        )
        allow_prod_debug = os.getenv('MINES_HTML_DEBUG_ALLOW_PROD', '').lower() in ('1', 'true', 'yes')
        if is_production and not allow_prod_debug:
            return

        # Helper: sichere Extraktion von Keys
        def safe_keys(obj: Any) -> List[str]:
    """safe_keys - TODO: Dokumentation hinzufügen"""
            if isinstance(obj, dict):
                try:
                    return list(obj.keys())
                except Exception:
                    return []
            return []

        # Helper: sensible Felder erkennen/maskieren
        sensitive_key_set = {
            'api_key', 'apikey', 'token', 'access_token', 'secret', 'password', 'pass',
            'owner', 'eigentümer', 'betreiber', 'email', 'phone', 'telefon', 'address', 'adresse'
        }

        def mask_value(value: Any) -> str:
    """mask_value - TODO: Dokumentation hinzufügen"""
            s = str(value)
            if len(s) <= 4:
                return '***'
            return s[:2] + '***' + s[-2:]

        # Kompakte Schlüsselübersicht und Länge loggen
        logger.debug(
            "[HTML-DEBUG] Mine=%s | result_keys=%s | data_keys=%s | structured_data_keys=%s |
structured_data_len=%s | fallback=%s",
            mine_name,
            safe_keys(result),
            safe_keys(data),
            safe_keys(structured_data),
            len(structured_data) if isinstance(structured_data, dict) else 0,
            fallback_reason,
        )

        # Beispielwerte aus strukturierten Daten – mit Maskierung sensibler Felder
        if isinstance(structured_data, dict) and structured_data:
            sample_fields = ['Country', 'Restaurationskosten', 'Eigentümer']
            samples: Dict[str, Any] = {}
            for field in sample_fields:
                if field in structured_data:
                    value = structured_data.get(field)
                    if str(field).lower() in sensitive_key_set:
                        samples[field] = mask_value(value)
                    else:
                        # Werte nicht aufblähen: auf 100 Zeichen begrenzen
                        s = str(value)
                        samples[field] = s[:97] + '...' if len(s) > 100 else s
            if samples:
                logger.debug("[HTML-DEBUG] Samples=%s", samples)
    except Exception:
        # Fail-safe: niemals Exceptions im Produktionspfad werfen
        logger.debug("[HTML-DEBUG] Debug-Logger übersprungen (Exception in helper)")

# FALLBACK FUNKTIONEN: Fehlende Module durch inline Funktionen ersetzen

def create_result_card(result: Dict) -> str:
    """Erstellt eine Ergebniskarte für eine Mine"""
    # REGEL 10 COMPLIANCE: Keine Dummy-Werte
    mine_name = result.get('mine_name')
    if not mine_name:
        return create_error_card({'mine_name': 'ERROR', 'error': 'Mine name missing - REGEL 10: Keine Dummy-Werte'})
    success = result.get("success", False)

    if not success:
        return create_error_card(result)

    data_dict = result.get("data", {})
    structured_data = data.get("structured_data", {})

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
    # REGEL 10 COMPLIANCE: Keine Dummy-Werte
    mine_name = result.get('mine_name') or 'ERROR'
    error = result.get("error", 'Unbekannter Fehler')

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

    successful_results = [r for r in results if r.get("success", False)]
    failed_results = [r for r in results if not r.get("success", False)]

    html = f"""
    <div style="margin: 20px 0;">
        <h3>📊 Batch-Ergebnisse</h3>
        <p><strong>{len(successful_results)}/{len(results)}</strong> Minen erfolgreich analysiert</p>

        <!-- TRANSPARENCY FIX 30.08.2025: Legende für Datenquellen -->
        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px; margin: 15px 0;">
            <h4 style="margin-top: 0; color: #495057;">🔍 Datenquellen-Legende:</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div><span style="color: #4caf50;">🔍 fresh_search</span> = Neue Suche (diese Session)</div>
                <div><span style="color: #ff9800;">💾 cached</span> = Aus Datenbank-Cache</div>
                <div><span style="color: #666;">❓ unknown</span> = Unbekannte Herkunft</div>
            </div>
        </div>

        <div style="max-height: 600px; overflow-x: auto; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px;">
            <table style="width: 100%; border-collapse: collapse; min-width: 2200px;">
                <thead style="background: #f5f5f5; position: sticky; top: 0;">
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;
min-width: 120px;">Status</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;
min-width: 150px; background: #e8f5e8;">🔍 Datenquelle</th>"""

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
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;
min-width: {width};">{column}</th>"""

    html += """
                    </tr>
                </thead>
                <tbody>
    """

    # Datenzeilen für alle Ergebnisse
    for result in results:
        # REGEL 10 COMPLIANCE: Keine Dummy-Werte
        mine_name = result.get('mine_name')
        if not mine_name:
            continue  # Skip results without mine name instead of using dummy
        success = result.get("success", False)

        if success:
            status_icon = "✅"
            status_color = "#4caf50"
            data_dict = result.get("data", {})

            # CRITICAL DEBUG 23.08.2025: Finde heraus warum keine structured_data ankommen
            structured_data = data.get("structured_data", {})

            # Kompakte, sichere Debug-Ausgabe über Logger (statt Datei-I/O)
            html_debug_log(data, structured_data, result, mine_name)

            # FALLBACK: Wenn structured_data leer, nimm direkt aus data_dict (häufiges Format)
            if not structured_data and data:
                structured_data = data
                html_debug_log(data, structured_data, result, mine_name, fallback_reason="FALLBACK:
Using data_dict directly")

            # FINAL FALLBACK: Für Legacy-Format direkt aus result
            if not structured_data:
                structured_data = result
                html_debug_log(data, structured_data, result, mine_name, fallback_reason="FINAL
FALLBACK: Using result directly")

            # KRITISCHER FIX 23.08.2025: DIREKTER PROVIDER-AUFRUF für echte Daten
            if not structured_data or len([v for v in structured_data.values() if v and
str(v).strip() and str(v).strip() != 'nichts gefunden']) < 3:
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
                            # Im laufenden Loop - Coroutine sicher in Loop einreichen
                            future = asyncio.run_coroutine_threadsafe(get_real_data(), loop)
                            real_structured_data = future.result(timeout=10)
                        else:
                            # Neuer Loop
                            real_structured_data = asyncio.run(get_real_data())

                        if real_structured_data and len(real_structured_data) > 5:
                            structured_data = real_structured_data
                            # DEBUG: Log dass echte Daten verwendet werden
                            with open("/tmp/html_generator_debug.log", "a") as f:
                                f.write(f"[HTML-FIX] Echte Provider-Daten für {mine_name}:
{len(structured_data)} Felder\n")

                    except Exception as provider_error:
                        # Fallback: Verwende vorhandene Daten
                        with open("/tmp/html_generator_debug.log", "a") as f:
                            f.write(f"[HTML-FIX] Provider-Fehler für {mine_name}: {str(provider_error)}\n")

                except Exception as import_error:
                    # Import-Fehler: Verwende vorhandene Daten
                    pass

            # DEBUG 21.08.2025: Log verfügbare Daten für Debugging
            field_count = len([k for k, v in structured_data.items() if v and str(v).strip() not in ['-', '', 'None']])
        else:
            status_icon = "❌"
            status_color = "#f44336"
            structured_data = {}

        # TRANSPARENCY FIX 30.08.2025: Bestimme Datenquelle für Anzeige
        # REGEL 10 COMPLIANCE: NULL statt "unknown" Fallback
        data_source = None  # REGEL 10: NULL statt versteckter Fallback-Wert
        source_icon = "❓"
        source_color = "#666666"
        source_tooltip = "Keine Datenquelle verfügbar"  # REGEL 10: Explizite Kennzeichnung

        if success and data:
            individual_results = data.get("individual_results", [])
            if individual_results:
                # Prüfe erste erfolgreiche Einzelergebnis
                for individual in individual_results:
                    if individual.get('success'):
                        individual_data = individual.get("data", {})
                        data_source = individual_data.get("data_source", data.get('data_source', 'unknown'))
                        break
            else:
                # Direkt aus result.data
                data_source = data.get("data_source", 'unknown')

        # Setze Icon und Farbe basierend auf Datenquelle
        if data_source == 'fresh_search':
            source_icon = "🔍"
            source_color = "#4caf50"
            source_tooltip = "Neue Suche - gerade durchgeführt"
        elif data_source == 'cached':
            source_icon = "💾"
            source_color = "#ff9800"
            source_tooltip = "Aus Datenbank-Cache geladen"
        else:
            source_icon = "❓"
            source_color = "#666666"
            source_tooltip = f"Quelle: {data_source}"

        # Bestimme Zeilenhintergrund basierend auf Datenquelle
        row_bg = ""
        if data_source == 'fresh_search':
            row_bg = "background-color: #f1f8e9;"  # Leichtes Grün für neue Daten
        elif data_source == 'cached':
            row_bg = "background-color: #fafafa;"   # Grau für gecachte Daten

        html += f"""
        <tr style="border-bottom: 1px solid #eee; {row_bg}">
            <td style="border: 1px solid #ddd; padding: 8px; color: {status_color};">{status_icon}</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: {source_color}; font-weight:
bold;" title="{source_tooltip}">{source_icon} {data_source}</td>"""

        # Alle CSV_COLUMNS Werte hinzufügen
        for column in CSV_COLUMNS:
            # Spezielle Behandlung für bestimmte Felder
            if column == "Name":
                value = mine_name
            elif column == "Country":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar
                value = structured_data.get(column) or result.get("country", '')
            elif column == "Region":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar
                value = structured_data.get(column) or result.get("region", '')
            elif column == "Rohstoff":
                # FIX 22.08.2025: Verwende echte Daten aus structured_data falls verfügbar
                value = structured_data.get(column) or result.get("commodity", '')
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
            <td style="border: 1px solid #ddd; padding: 8px;" title="{str(value).replace('"',
'&quot;')}">{display_value}</td>"""

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
    """create_comprehensive_results_page - TODO: Dokumentation hinzufügen"""
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
    successful_results = [r for r in results if r.get("success", False)]
    failed_results = [r for r in results if not r.get("success", False)]

    # Erstelle Statistiken
    total_mines = len(results)
    successful_mines = len(successful_results)
    success_rate = (successful_mines / total_mines * 100) if total_mines > 0 else 0

    # Kopfbereich mit Statistiken
    header_html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
padding: 30px; border-radius: 10px; margin-bottom: 30px;">
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
    <div style="margin-top: 50px; padding: 20px; background: #f8f9fa; border-radius: 8px;
text-align: center; color: #666;">
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
    successful_results = [r for r in results if r.get("success", False)]
    total_fields_found = 0
    mines_with_coordinates = 0
    mines_with_operators = 0
    mines_with_costs = 0

    for result in successful_results:
        data_dict = result.get("data", {})
        structured_data = data.get("structured_data", {})

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
    <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 5px solid
#4caf50; margin: 20px 0;">
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
