"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: HTML-Utility-Funktionen für MineSearch Frontend-Generierung
"""

from typing import Dict, List, Any, Optional
from config import CSV_COLUMNS, FIELDS_WITHOUT_SOURCES

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
                
            value = structured.get(field, '-')
            sources_refs = ''
            
            # Hole Quellennummern nur bei echten Infos und erlaubten Feldern
            if (field not in FIELDS_WITHOUT_SOURCES and 
                field in data_with_sources and
                value and 
                value != '-' and
                value.lower() not in ['k.a', 'k.a.', 'keine daten', 'nicht gefunden']):
                sources = data_with_sources[field].get('sources', [])
                if sources:
                    sources_refs = f' <span style="color: #6b7280; font-size: 0.85em;">[{",".join(map(str, sources))}]</span>'
            
            # Spezielle Formatierung für verschiedene Spaltentypen
            row_style = ''
            display_value = value
            
            # Finanzspalten gelb hinterlegen
            if field in finanz_spalten:
                row_style = 'style="background-color: #fef3c7;"'
                
                # Restaurationskosten rot hervorheben wenn vorhanden
                if field == 'Restaurationskosten' and value != '-' and value:
                    display_value = f'<span style="color: #dc2626; font-weight: bold;">{value}</span>'
                elif value == '-':
                    display_value = '<span style="color: #9ca3af; font-style: italic;">Keine Daten gefunden</span>'
            
            # Status farbig darstellen
            elif field == 'Aktivitätsstatus' and value != '-':
                if 'aktiv' in value.lower():
                    display_value = f'<span style="color: #10b981; font-weight: 500;">{value}</span>'
                elif 'geplant' in value.lower():
                    display_value = f'<span style="color: #f59e0b; font-weight: 500;">{value}</span>'
                elif 'geschlossen' in value.lower():
                    display_value = f'<span style="color: #ef4444; font-weight: 500;">{value}</span>'
            
            # Füge Quellennummern an
            display_value += sources_refs
            
            structured_html += f"""
            <tr {row_style}>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>{field}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{display_value}</td>
            </tr>
            """
        
        structured_html += "</table>"
    
    # Quellen-Anzeige
    sources_html = ""
    if 'sources' in data and data['sources']:
        sources = data['sources']
        source_summary = data.get('source_summary', {})
        
        sources_html = f"""
        <h5 style="margin-top: 20px;">📚 Gefundene Quellen ({source_summary.get('total', 0)} insgesamt):</h5>
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px;">
        """
        
        # URLs
        url_sources = [s for s in sources if s['type'] == 'url']
        if url_sources:
            sources_html += "<strong>🌐 Websites:</strong><ul style='margin: 5px 0;'>"
            for source in url_sources[:5]:  # Max 5 URLs anzeigen
                sources_html += f"<li><a href='{source['value']}' target='_blank' style='color: #0066cc;'>{source['value']}</a></li>"
            if len(url_sources) > 5:
                sources_html += f"<li><em>... und {len(url_sources) - 5} weitere URLs</em></li>"
            sources_html += "</ul>"
        
        # Dokumente
        doc_sources = [s for s in sources if s['type'] == 'document']
        if doc_sources:
            sources_html += "<strong>📄 Dokumente:</strong><ul style='margin: 5px 0;'>"
            for source in doc_sources[:5]:
                sources_html += f"<li>{source['value']}</li>"
            if len(doc_sources) > 5:
                sources_html += f"<li><em>... und {len(doc_sources) - 5} weitere Dokumente</em></li>"
            sources_html += "</ul>"
        
        # Organisationen
        org_sources = [s for s in sources if s['type'] == 'organization']
        if org_sources:
            sources_html += "<strong>🏢 Organisationen/Datenbanken:</strong><ul style='margin: 5px 0;'>"
            for source in org_sources[:3]:
                sources_html += f"<li>{source['value']}</li>"
            if len(org_sources) > 3:
                sources_html += f"<li><em>... und {len(org_sources) - 3} weitere Organisationen</em></li>"
            sources_html += "</ul>"
        
        sources_html += "</div>"
    
    # Source Discovery Tab
    source_discovery_html = ""
    if 'source_discovery_session' in data:
        source_discovery_html = create_source_discovery_tab(data['source_discovery_session'])
    
    # CSV Download-Link
    csv_download = ""
    if 'structured_data' in data:
        # Verwende | als Trennzeichen und füge Quellennummern hinzu
        csv_values = []
        data_with_sources = data.get('structured_data_with_sources', {})
        
        for col in CSV_COLUMNS:
            val = data['structured_data'].get(col, '')
            # Füge Quellennummern hinzu wenn vorhanden
            if col in data_with_sources and data_with_sources[col].get('sources'):
                sources = data_with_sources[col]['sources']
                val += f" [{','.join(map(str, sources))}]"
            csv_values.append(val)
        
        csv_line = "|".join(csv_values)
        csv_download = f"""
        <details style="margin-top: 10px;">
            <summary>CSV-Format (zum Kopieren)</summary>
            <pre style="font-size: 0.8em; background: #f5f5f5; padding: 10px; overflow-x: auto;">{csv_line}</pre>
        </details>
        """
    
    # Original-Antwort als Details
    original_content = f"""
    <details style="margin-top: 10px;">
        <summary>Vollständige Antwort anzeigen</summary>
        <pre style="font-size: 0.9em; max-height: 300px; overflow-y: auto;">{data.get('content', 'Keine Daten')}</pre>
    </details>
    """
    
    return f"""
    <div class="result-card success">
        <h4>✓ {mine['mine_name']}</h4>
        <div class="result-content">
            {structured_html}
            {sources_html}
            {source_discovery_html}
            {csv_download}
            {original_content}
        </div>
    </div>
    """

def create_error_card(error: Dict) -> str:
    """Erstelle HTML für einen Fehler"""
    mine = error['mine']
    err = error['error']
    
    # ÄNDERUNG 02.07.2025: Verbesserte Fehlerdarstellung mit Lösungshinweisen
    error_html = f"""
    <div class="result-card error">
        <h4>❌ {mine['mine_name']}</h4>
    """
    
    # Spezielle Behandlung für API-Fehler
    if "🔐" in err or "💳" in err or "🔑" in err:
        # Formatiere mehrzeilige Fehlermeldungen besser
        error_lines = err.split('\n')
        error_html += "<div style='background: #fee; padding: 15px; border-radius: 5px; margin: 10px 0;'>"
        
        for line in error_lines:
            if line.strip():
                if "→" in line:
                    # Lösungshinweise hervorheben
                    error_html += f"<p style='margin: 5px 0; padding-left: 20px; color: #666;'>➜ {line.replace('→', '').strip()}</p>"
                elif "http" in line:
                    # Links klickbar machen
                    url_match = line.split()[-1] if line.split() else ""
                    if url_match.startswith('http'):
                        error_html += f"<p style='margin: 10px 0;'><a href='{url_match}' target='_blank' style='color: #0066cc; text-decoration: underline;'>🔗 {url_match}</a></p>"
                    else:
                        error_html += f"<p style='margin: 5px 0;'>{line}</p>"
                elif any(emoji in line for emoji in ['🔐', '💳', '🔑', '⏱️', '🔧', '❓']):
                    # Zeilen mit Emojis hervorheben
                    error_html += f"<p style='margin: 8px 0; font-weight: bold; color: #d32f2f;'>{line}</p>"
                else:
                    # Normale Zeilen
                    error_html += f"<p style='margin: 5px 0;'>{line}</p>"
        
        error_html += "</div>"
        
        # Zusätzliche Hilfe-Box je nach Fehlertyp
        if "Budget" in err or "aufgebraucht" in err or "💳" in err:
            error_html += """
            <div style='background: #fff3cd; padding: 12px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #ffc107;'>
                <strong>💡 Schnelle Lösung:</strong>
                <ol style='margin: 5px 0 0 20px;'>
                    <li>Öffnen Sie <a href='https://www.perplexity.ai/settings/api' target='_blank'>Perplexity API Settings</a></li>
                    <li>Laden Sie Ihr API-Guthaben auf</li>
                    <li>Starten Sie die Suche erneut</li>
                </ol>
            </div>
            """
        elif "ungültig" in err or "abgelaufen" in err or "🔑" in err:
            error_html += """
            <div style='background: #fff3cd; padding: 12px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #ffc107;'>
                <strong>💡 Schnelle Lösung:</strong>
                <ol style='margin: 5px 0 0 20px;'>
                    <li>Generieren Sie einen neuen API-Key: <a href='https://www.perplexity.ai/settings/api' target='_blank'>Perplexity API</a></li>
                    <li>Ersetzen Sie den Key in der .env Datei</li>
                    <li>Starten Sie den Server neu</li>
                </ol>
            </div>
            """
        elif "Rate Limit" in err or "⏱️" in err:
            error_html += """
            <div style='background: #e3f2fd; padding: 12px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #2196f3;'>
                <strong>ℹ️ Info:</strong> Das API-Limit wurde temporär erreicht. 
                Die Suche wird automatisch in wenigen Minuten wieder funktionieren.
            </div>
            """
    else:
        # Standard-Fehlerbehandlung
        error_html += f"<p style='padding: 10px; background: #fee; border-radius: 5px;'>Fehler: {err}</p>"
    
    error_html += "</div>"
    return error_html

def create_batch_results_table(results: List[Dict]) -> str:
    """Erstelle HTML-Tabelle für Batch-Ergebnisse"""
    if not results:
        return ""
    
    # CSV-Daten für Export vorbereiten
    csv_lines_with_sources = [";".join(CSV_COLUMNS)]  # Header
    
    # HTML-Tabelle vorbereiten
    csv_table_html = f"""
    <div style="margin: 20px 0; padding: 15px; background: #f0fff4; border-radius: 5px;">
        <h4>📊 Ergebnistabelle mit Quellenreferenzen</h4>
        <p style="margin-bottom: 10px;">Die Tabelle zeigt alle gefundenen Daten. Zahlen in eckigen Klammern [1,2,3] verweisen auf die Quellen unten.</p>
        
        <div style="overflow-x: auto;">
            <table id="results-table" style="width: 100%; border-collapse: collapse; font-size: 14px; background: white;">
                <thead>
                    <tr style="background: #4CAF50; color: white;">
    """
    
    # Tabellen-Header
    for col in CSV_COLUMNS:
        csv_table_html += f'<th style="padding: 10px; border: 1px solid #ddd; text-align: left; position: sticky; top: 0; background: #4CAF50;">{col}</th>'
    csv_table_html += '</tr></thead><tbody>'
    
    # Tabellen-Zeilen
    for idx, r in enumerate(results):
        if 'structured_data' in r['data']:
            row_style = 'style="background: #f9f9f9;"' if idx % 2 == 0 else ''
            csv_table_html += f'<tr {row_style}>'
            
            # CSV-Zeile für Export vorbereiten
            csv_values = []
            
            for col in CSV_COLUMNS:
                value = r['data']['structured_data'].get(col, '')
                display_value = value if value else '-'
                
                # Quellenreferenzen hinzufügen
                if (col not in FIELDS_WITHOUT_SOURCES and 
                    'structured_data_with_sources' in r['data'] and
                    value and value != '-'):
                    source_data = r['data']['structured_data_with_sources'].get(col, {})
                    if source_data.get('sources'):
                        sources_str = ','.join(map(str, source_data['sources']))
                        display_value += f' <span style="color: #6b7280; font-size: 0.85em;">[{sources_str}]</span>'
                        csv_values.append(f"{value} [{sources_str}]")
                    else:
                        csv_values.append(value)
                else:
                    csv_values.append(value)
                
                # Spezielle Formatierung
                cell_style = 'padding: 8px; border: 1px solid #ddd;'
                
                # Finanzspalten hervorheben
                if col in ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes']:
                    cell_style += ' background-color: #fef3c7;'
                    if col == 'Restaurationskosten' and value and value != '-':
                        display_value = f'<strong style="color: #dc2626;">{display_value}</strong>'
                
                # Status farbig
                elif col == 'Aktivitätsstatus' and value and value != '-':
                    if 'aktiv' in value.lower():
                        display_value = f'<span style="color: #10b981; font-weight: 600;">{display_value}</span>'
                    elif 'geplant' in value.lower():
                        display_value = f'<span style="color: #f59e0b; font-weight: 600;">{display_value}</span>'
                    elif 'geschlossen' in value.lower():
                        display_value = f'<span style="color: #ef4444; font-weight: 600;">{display_value}</span>'
                
                csv_table_html += f'<td style="{cell_style}">{display_value}</td>'
            
            csv_table_html += '</tr>'
            csv_lines_with_sources.append(";".join(csv_values))
    
    csv_table_html += """
                </tbody>
            </table>
        </div>
        
        <div style="margin-top: 15px; display: flex; gap: 10px;">
            <button onclick="copyTableAsCSV()" style="padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
                📋 Als CSV kopieren
            </button>
            <button onclick="copyTableAsHTML()" style="padding: 8px 15px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">
                📋 Als Tabelle kopieren
            </button>
        </div>
        
        <script>
            function copyTableAsCSV() {
                const csvData = `""" + '\\n'.join(csv_lines_with_sources).replace('`', '\\`') + """`;
                navigator.clipboard.writeText(csvData).then(() => {
                    alert('CSV-Daten wurden in die Zwischenablage kopiert!');
                });
            }
            
            function copyTableAsHTML() {
                const table = document.getElementById('results-table');
                const range = document.createRange();
                range.selectNode(table);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand('copy');
                window.getSelection().removeAllRanges();
                alert('Tabelle wurde in die Zwischenablage kopiert!');
            }
        </script>
    </div>
    """
    
    # Source Discovery Zusammenfassung für Batch
    source_discovery_summary = _create_batch_source_summary(results)
    if source_discovery_summary:
        csv_table_html += source_discovery_summary
    
    return csv_table_html

def _create_batch_source_summary(results: List[Dict]) -> str:
    """Erstelle Zusammenfassung aller Source Discovery Sessions für Batch-Ergebnisse"""
    
    # Sammle alle Sessions
    sessions = []
    for r in results:
        if 'data' in r and 'source_discovery_session' in r['data']:
            session = r['data']['source_discovery_session']
            if session:
                sessions.append({
                    'mine_name': r['data'].get('mine_name', 'Unbekannt'),
                    'stats': session.get('statistics', {}),
                    'duration': session.get('duration_seconds', 0)
                })
    
    if not sessions:
        return ""
    
    # Berechne Gesamtstatistiken
    total_discovered = sum(s['stats'].get('discovered', 0) for s in sessions)
    total_searched = sum(s['stats'].get('searched', 0) for s in sessions)
    total_successful = sum(s['stats'].get('successful', 0) for s in sessions)
    avg_success_rate = (total_successful / total_searched * 100) if total_searched > 0 else 0
    total_duration = sum(s['duration'] for s in sessions)
    
    html = f"""
    <div style="margin: 20px 0; padding: 15px; background: #f0f9ff; border-radius: 5px;">
        <h4>📊 Source Discovery Zusammenfassung</h4>
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 10px;">
            <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                <div style="font-size: 20px; font-weight: bold; color: #3b82f6;">{len(sessions)}</div>
                <div style="font-size: 12px; color: #6b7280;">Minen durchsucht</div>
            </div>
            <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                <div style="font-size: 20px; font-weight: bold; color: #8b5cf6;">{total_discovered}</div>
                <div style="font-size: 12px; color: #6b7280;">Quellen entdeckt</div>
            </div>
            <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                <div style="font-size: 20px; font-weight: bold; color: #f59e0b;">{total_searched}</div>
                <div style="font-size: 12px; color: #6b7280;">Quellen durchsucht</div>
            </div>
            <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                <div style="font-size: 20px; font-weight: bold; color: #10b981;">{total_successful}</div>
                <div style="font-size: 12px; color: #6b7280;">Erfolgreiche Quellen</div>
            </div>
            <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                <div style="font-size: 20px; font-weight: bold; color: {'#10b981' if avg_success_rate >= 50 else '#f59e0b'};">{avg_success_rate:.0f}%</div>
                <div style="font-size: 12px; color: #6b7280;">Ø Erfolgsquote</div>
            </div>
        </div>
        <p style="margin-top: 10px; font-size: 12px; color: #6b7280;">
            ⏱️ Gesamtdauer: {total_duration:.1f} Sekunden ({total_duration/60:.1f} Minuten)
        </p>
    </div>
    """
    
    return html

def create_source_discovery_tab(session_data: Dict[str, Any]) -> str:
    """Erstelle HTML für Source Discovery Tab"""
    if not session_data:
        return ""
    
    stats = session_data.get('statistics', {})
    sources = session_data.get('sources', {})
    
    html = f"""
    <div class="source-discovery-tab" style="margin: 20px 0; padding: 15px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
        <h4>🔍 Quellen-Discovery für {session_data.get('mine_name', 'Mine')}</h4>
        
        <!-- Statistiken -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">
            <div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #3b82f6;">{stats.get('discovered', 0)}</div>
                <div style="font-size: 12px; color: #6b7280;">Entdeckte Quellen</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #8b5cf6;">{stats.get('searched', 0)}</div>
                <div style="font-size: 12px; color: #6b7280;">Durchsuchte Quellen</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #10b981;">{stats.get('successful', 0)}</div>
                <div style="font-size: 12px; color: #6b7280;">Erfolgreiche Quellen</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: {
                    '#10b981' if stats.get('success_rate', 0) >= 50 else '#f59e0b' if stats.get('success_rate', 0) >= 25 else '#ef4444'
                };">
                    {stats.get('success_rate', 0):.0f}%
                </div>
                <div style="font-size: 12px; color: #6b7280;">Erfolgsquote</div>
            </div>
        </div>
        
        <!-- Erfolgreiche Quellen -->
        {_create_sources_section('Erfolgreiche Quellen', sources.get('successful', []), '#10b981', True)}
        
        <!-- Fehlgeschlagene Quellen -->
        {_create_sources_section('Durchsuchte Quellen ohne Ergebnis', sources.get('failed', []), '#ef4444', False)}
        
        <!-- Dauer -->
        <div style="margin-top: 15px; font-size: 12px; color: #6b7280;">
            ⏱️ Suchdauer: {session_data.get('duration_seconds', 0):.1f} Sekunden
        </div>
    </div>
    """
    
    return html

def _create_sources_section(title: str, sources: List[Dict], color: str, show_details: bool) -> str:
    """Hilfsfunktion für expandierbare Quellenlisten"""
    if not sources:
        return ""
    
    section_id = title.lower().replace(' ', '-')
    
    html = f"""
    <details style="margin-top: 15px;">
        <summary style="cursor: pointer; font-weight: 500; color: {color};">
            {title} ({len(sources)})
        </summary>
        <div style="margin-top: 10px; padding-left: 20px;">
    """
    
    for i, source in enumerate(sources[:10]):  # Zeige max 10
        url = source.get('url', '')
        timestamp = source.get('timestamp', '')
        details = source.get('details', {})
        
        # Kürze lange URLs
        display_url = url if len(url) <= 80 else url[:77] + '...'
        
        html += f"""
        <div style="margin: 5px 0; padding: 5px; background: white; border-radius: 4px;">
            <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none; font-size: 14px;">
                {display_url}
            </a>
            """
        
        if show_details and details:
            fields = details.get('fields', [])
            if fields:
                html += f"""
                <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">
                    Gefundene Felder: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}
                </div>
                """
        
        html += "</div>"
    
    if len(sources) > 10:
        html += f"""
        <div style="margin-top: 5px; font-style: italic; color: #6b7280; font-size: 12px;">
            ... und {len(sources) - 10} weitere Quellen
        </div>
        """
    
    html += """
        </div>
    </details>
    """
    
    return html