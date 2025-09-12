"""
Compact HTML Utils
Kompakte Version der HTML Utils

Author: MineSearch Development Team
Date: 2025-01-11
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def html_debug_log(data: Optional[Dict], structured_data: Optional[Dict], result: Dict, mine_name: str, fallback_reason: Optional[str] = None) -> None:
    """Schreibt eine kompakte, sichere Debug-Ausgabe über den App-Logger"""
    try:
        debug_enabled = os.getenv('MINES_HTML_DEBUG', '').lower() in ('1', 'true', 'yes')
        if not debug_enabled:
            return

        is_production = (
            os.getenv('APP_ENV', '').lower() == 'production' or
            os.getenv('ENVIRONMENT', '').lower() == 'production'
        )
        
        if is_production and not os.getenv('MINES_HTML_DEBUG_ALLOW_PROD'):
            return

        # Maskiere sensible Felder
        masked_data = _mask_sensitive_fields(data) if data else None
        masked_structured = _mask_sensitive_fields(structured_data) if structured_data else None

        debug_info = {
            'mine_name': mine_name,
            'data': masked_data,
            'structured_data': masked_structured,
            'result': result,
            'fallback_reason': fallback_reason
        }

        logger.debug(f"HTML Debug: {debug_info}")

    except Exception as e:
        logger.error(f"Fehler beim HTML Debug Log: {e}")


def _mask_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Maskiere sensible Felder"""
    if not data:
        return data

    sensitive_fields = ['password', 'token', 'key', 'secret', 'auth']
    masked_data = {}

    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            masked_data[key] = "***MASKED***"
        else:
            masked_data[key] = value

    return masked_data


def generate_html_response(data: Dict[str, Any], template: str = "default") -> str:
    """Generiere HTML-Response"""
    try:
        if template == "default":
            return _generate_default_html(data)
        elif template == "mining":
            return _generate_mining_html(data)
        elif template == "search":
            return _generate_search_html(data)
        else:
            return _generate_default_html(data)

    except Exception as e:
        logger.error(f"Fehler beim Generieren der HTML-Response: {e}")
        return _generate_error_html(str(e))


def _generate_default_html(data: Dict[str, Any]) -> str:
    """Generiere Standard-HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MineSearch - {data.get('title', 'Default')}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>{data.get('title', 'MineSearch')}</h1>
        <div class="content">
            {data.get('content', 'No content available')}
        </div>
    </body>
    </html>
    """


def _generate_mining_html(data: Dict[str, Any]) -> str:
    """Generiere Mining-HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mining Data - {data.get('mine_name', 'Unknown')}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Mining Data: {data.get('mine_name', 'Unknown')}</h1>
        <div class="mining-data">
            <h2>Basic Information</h2>
            <p><strong>Country:</strong> {data.get('country', 'N/A')}</p>
            <p><strong>Region:</strong> {data.get('region', 'N/A')}</p>
            <p><strong>Commodity:</strong> {data.get('commodity', 'N/A')}</p>
            
            <h2>Production Data</h2>
            <p><strong>Annual Production:</strong> {data.get('annual_production', 'N/A')}</p>
            <p><strong>Capacity:</strong> {data.get('capacity', 'N/A')}</p>
            
            <h2>Operational Status</h2>
            <p><strong>Status:</strong> {data.get('operational_status', 'N/A')}</p>
        </div>
    </body>
    </html>
    """


def _generate_search_html(data: Dict[str, Any]) -> str:
    """Generiere Search-HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results - {data.get('query', 'Search')}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Search Results</h1>
        <div class="search-info">
            <p><strong>Query:</strong> {data.get('query', 'N/A')}</p>
            <p><strong>Results Found:</strong> {data.get('result_count', 0)}</p>
        </div>
        
        <div class="search-results">
            {data.get('results_html', 'No results available')}
        </div>
    </body>
    </html>
    """


def _generate_error_html(error_message: str) -> str:
    """Generiere Error-HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error - MineSearch</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Error</h1>
        <div class="error-message">
            <p>An error occurred: {error_message}</p>
        </div>
    </body>
    </html>
    """


def extract_text_from_html(html_content: str) -> str:
    """Extrahiere Text aus HTML"""
    try:
        import re
        
        # Entferne HTML-Tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Entferne überschüssige Leerzeichen
        text = re.sub(r'\s+', ' ', text)
        
        # Entferne führende/nachfolgende Leerzeichen
        text = text.strip()
        
        return text

    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von Text aus HTML: {e}")
        return ""


def validate_html_content(html_content: str) -> Dict[str, Any]:
    """Validiere HTML-Inhalt"""
    try:
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if not html_content:
            validation_result['valid'] = False
            validation_result['errors'].append("HTML content is empty")
            return validation_result

        # Prüfe auf grundlegende HTML-Struktur
        if '<html>' not in html_content.lower():
            validation_result['warnings'].append("Missing <html> tag")

        if '<head>' not in html_content.lower():
            validation_result['warnings'].append("Missing <head> tag")

        if '<body>' not in html_content.lower():
            validation_result['warnings'].append("Missing <body> tag")

        # Prüfe auf potenzielle Sicherheitsprobleme
        if 'javascript:' in html_content.lower():
            validation_result['warnings'].append("Potential JavaScript injection detected")

        if 'onclick=' in html_content.lower():
            validation_result['warnings'].append("Inline JavaScript detected")

        return validation_result

    except Exception as e:
        logger.error(f"Fehler bei HTML-Validierung: {e}")
        return {
            'valid': False,
            'errors': [str(e)],
            'warnings': []
        }


def sanitize_html_content(html_content: str) -> str:
    """Bereinige HTML-Inhalt"""
    try:
        import re
        
        # Entferne potenziell gefährliche Inhalte
        # Entferne JavaScript
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Entferne JavaScript-Events
        html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Entferne JavaScript-URLs
        html_content = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', html_content, flags=re.IGNORECASE)
        
        return html_content

    except Exception as e:
        logger.error(f"Fehler beim Bereinigen von HTML: {e}")
        return html_content


def format_mining_data_html(mining_data: Dict[str, Any]) -> str:
    """Formatiere Mining-Daten als HTML"""
    try:
        html_parts = []
        
        # Basis-Informationen
        if mining_data.get('mine_name'):
            html_parts.append(f"<h2>Mine: {mining_data['mine_name']}</h2>")
        
        # Land und Region
        if mining_data.get('country'):
            html_parts.append(f"<p><strong>Country:</strong> {mining_data['country']}</p>")
        
        if mining_data.get('region'):
            html_parts.append(f"<p><strong>Region:</strong> {mining_data['region']}</p>")
        
        # Rohstoff
        if mining_data.get('commodity'):
            html_parts.append(f"<p><strong>Commodity:</strong> {mining_data['commodity']}</p>")
        
        # Produktionsdaten
        if mining_data.get('annual_production'):
            html_parts.append(f"<p><strong>Annual Production:</strong> {mining_data['annual_production']}</p>")
        
        if mining_data.get('capacity'):
            html_parts.append(f"<p><strong>Capacity:</strong> {mining_data['capacity']}</p>")
        
        # Betriebsstatus
        if mining_data.get('operational_status'):
            html_parts.append(f"<p><strong>Operational Status:</strong> {mining_data['operational_status']}</p>")
        
        return ''.join(html_parts)

    except Exception as e:
        logger.error(f"Fehler beim Formatieren der Mining-Daten: {e}")
        return f"<p>Error formatting mining data: {str(e)}</p>"


def get_html_template(template_name: str) -> str:
    """Hole HTML-Template"""
    try:
        templates = {
            'default': _generate_default_html({'title': 'Default Template'}),
            'mining': _generate_mining_html({'mine_name': 'Template Mine'}),
            'search': _generate_search_html({'query': 'Template Query'}),
            'error': _generate_error_html('Template Error')
        }
        
        return templates.get(template_name, templates['default'])

    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Templates: {e}")
        return _generate_error_html(str(e))


def render_data_cards_html(data_cards: List[Dict[str, Any]]) -> str:
    """Rendere Datenkarten als HTML"""
    try:
        if not data_cards:
            return "<p>No data cards available</p>"
        
        html_parts = ['<div class="data-cards">']
        
        for card in data_cards:
            html_parts.append('<div class="data-card">')
            html_parts.append(f'<h3>{card.get("title", "Untitled")}</h3>')
            html_parts.append(f'<p>{card.get("content", "No content")}</p>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)

    except Exception as e:
        logger.error(f"Fehler beim Rendern der Datenkarten: {e}")
        return f"<p>Error rendering data cards: {str(e)}</p>"


__all__ = [
    "html_debug_log",
    "generate_html_response",
    "extract_text_from_html",
    "validate_html_content",
    "sanitize_html_content",
    "format_mining_data_html",
    "get_html_template",
    "render_data_cards_html"
]
