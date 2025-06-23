"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Proxy-Management für BrightData Agent
"""

from typing import Dict, Any
from urllib.parse import urlparse


class ProxyManager:
    """Verwaltet Proxy-Konfiguration und -Auswahl für BrightData"""
    
    def __init__(self):
        # Proxy-Konfiguration
        self.proxy_config = {
            'datacenter': True,
            'residential': False,  # Für sensible Seiten
            'mobile': False
        }
        
    def select_proxy_type(self, url: str) -> str:
        """
        Wählt optimalen Proxy-Typ basierend auf URL
        
        ÄNDERUNG 17.06.2025: Dynamische Proxy-Auswahl
        Regierungsseiten werden generisch erkannt
        """
        if self._is_government_site(url):
            return 'residential'
        
        # Geschützte Datenbanken
        if any(db in url for db in ['gestim', 'sigeom', 'sedar']):
            return 'residential'
        
        # Standard-Seiten
        return 'datacenter'
    
    def needs_javascript(self, url: str) -> bool:
        """Bestimmt ob JavaScript-Rendering nötig ist"""
        js_sites = [
            'gestim', 'sigeom', 'claimaps',
            'mining-technology.com', 'infomine.com'
        ]
        
        return any(site in url.lower() for site in js_sites)
    
    def _is_government_site(self, url: str) -> bool:
        """
        Erkennt Regierungsseiten dynamisch
        
        ÄNDERUNG 17.06.2025: Generische Regierungsseiten-Erkennung
        """
        government_indicators = [
            '.gov', 'government', 'gouv', 'gobierno', 'regierung', 
            'ministry', 'ministere', 'ministerio', 'department',
            'federal', 'national', 'state', 'province'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in government_indicators)
    
    def get_scrape_params(self, url: str, country_code: str, languages: list, timeout: int = 30000) -> Dict[str, Any]:
        """Erstellt Scraping-Parameter basierend auf URL"""
        proxy_type = self.select_proxy_type(url)
        
        params = {
            "url": url,
            "proxy_type": proxy_type,
            "country": country_code,
            "render_js": self.needs_javascript(url),
            "wait_for": "networkidle" if self.needs_javascript(url) else None,
            "timeout": timeout,
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; MineSearchBot/1.0)",
                "Accept-Language": self._get_accept_languages(languages)
            }
        }
        
        return params
    
    def _get_accept_languages(self, languages: list) -> str:
        """Erstellt Accept-Language Header"""
        if not languages:
            return "en-US,en;q=0.9"
        
        # Erstelle Header mit abnehmender Priorität
        parts = []
        for i, lang in enumerate(languages[:3]):  # Max 3 Sprachen
            if i == 0:
                parts.append(f"{lang}")
            else:
                parts.append(f"{lang};q={0.9 - i*0.1}")
        
        return ",".join(parts)