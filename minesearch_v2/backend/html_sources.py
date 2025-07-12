"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: HTML-Quellen-Discovery für MineSearch Frontend
"""

from typing import Dict, List, Any, Optional


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
    
    html += "</div></details>"
    
    return html


def create_sources_overview(all_sources: List[Dict], title: str = "Quellenübersicht") -> str:
    """
    Erstellt eine übersichtliche Darstellung aller Quellen
    
    Args:
        all_sources: Liste aller Quellen
        title: Titel der Übersicht
        
    Returns:
        HTML-String mit Quellenübersicht
    """
    if not all_sources:
        return ""
    
    # Kategorisiere Quellen nach Typ/Domain
    categorized_sources = {}
    
    for source in all_sources:
        url = source.get('url', '')
        domain = _extract_domain(url)
        category = _categorize_source(domain)
        
        if category not in categorized_sources:
            categorized_sources[category] = []
        
        categorized_sources[category].append(source)
    
    html = f"""
    <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
        <h4>📚 {title}</h4>
        <p style="color: #666; margin-bottom: 15px;">
            Insgesamt {len(all_sources)} Quellen gefunden, kategorisiert nach Typ:
        </p>
    """
    
    # Zeige jede Kategorie
    for category, sources in categorized_sources.items():
        if sources:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h5 style="color: #333; margin-bottom: 10px;">
                    {_get_category_icon(category)} {category} ({len(sources)})
                </h5>
                <div style="margin-left: 20px;">
            """
            
            for i, source in enumerate(sources[:5]):  # Zeige max 5 pro Kategorie
                url = source.get('url', '')
                title_text = source.get('title', _extract_domain(url))
                
                html += f"""
                <div style="margin-bottom: 5px;">
                    <a href="{url}" target="_blank" style="color: #007bff; text-decoration: none;">
                        {title_text[:100]}{'...' if len(title_text) > 100 else ''}
                    </a>
                </div>
                """
            
            if len(sources) > 5:
                html += f"""
                <div style="color: #666; font-style: italic; margin-top: 5px;">
                    ... und {len(sources) - 5} weitere {category.lower()}-Quellen
                </div>
                """
            
            html += "</div></div>"
    
    html += "</div>"
    
    return html


def _extract_domain(url: str) -> str:
    """Extrahiert Domain aus URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return url[:50] if url else "unbekannt"


def _categorize_source(domain: str) -> str:
    """Kategorisiert Quelle nach Domain"""
    domain_lower = domain.lower()
    
    if any(gov in domain_lower for gov in ['.gov', '.gouv', 'government', 'ministry']):
        return "Regierungsquellen"
    elif any(mining in domain_lower for mining in ['mining', 'mineral', 'geology']):
        return "Bergbau-Fachseiten"
    elif any(news in domain_lower for news in ['news', 'press', 'media', 'times', 'post']):
        return "Nachrichtenquellen"
    elif any(corp in domain_lower for corp in ['.com', 'corp', 'company', 'inc']):
        return "Unternehmensseiten"
    elif any(academic in domain_lower for academic in ['.edu', '.ac.', 'university', 'research']):
        return "Akademische Quellen"
    else:
        return "Sonstige Quellen"


def _get_category_icon(category: str) -> str:
    """Holt passendes Icon für Kategorie"""
    icons = {
        "Regierungsquellen": "🏛️",
        "Bergbau-Fachseiten": "⛏️",
        "Nachrichtenquellen": "📰",
        "Unternehmensseiten": "🏢",
        "Akademische Quellen": "🎓",
        "Sonstige Quellen": "🔗"
    }
    return icons.get(category, "📄")