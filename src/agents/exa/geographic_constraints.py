"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Geographic Constraints für Exa Search
"""

from typing import List, Dict
from ..enhanced_search import get_country_specific_domains

class GeographicConstraintBuilder:
    """Erstellt geografische Einschränkungen für Exa Search"""
    
    def __init__(self):
        self.regional_markers = self._initialize_regional_markers()
        self.technical_domains = self._initialize_technical_domains()
        
    def _initialize_regional_markers(self) -> Dict[str, List[str]]:
        """Initialisiert regionale Marker"""
        return {
            "quebec": ["Quebec province", "Province de Québec", "QC Canada"],
            "ontario": ["Ontario province", "ON Canada"],
            "british columbia": ["British Columbia", "BC Canada"],
            "alberta": ["Alberta province", "AB Canada"],
            "saskatchewan": ["Saskatchewan", "SK Canada"],
            "manitoba": ["Manitoba", "MB Canada"],
            "nova scotia": ["Nova Scotia", "NS Canada"],
            "new brunswick": ["New Brunswick", "NB Canada"],
            "newfoundland": ["Newfoundland and Labrador", "NL Canada"]
        }
    
    def _initialize_technical_domains(self) -> Dict[str, List[str]]:
        """Initialisiert technische Domains nach Land"""
        return {
            "canada": ["sedar.com", "tsx.com", "cse-cst.org"],
            "usa": ["sec.gov", "nasdaq.com", "nyse.com"],
            "australia": ["asx.com.au", "asic.gov.au"],
            "uk": ["londonstockexchange.com", "fca.org.uk"],
            "south africa": ["jse.co.za"],
            "brazil": ["b3.com.br"],
            "india": ["bseindia.com", "nseindia.com"]
        }
    
    def create_geographic_constraints(self, region: str, country: str) -> str:
        """
        ÄNDERUNG 21.06.2025: Verbesserte geografische Einschränkungen mit positiver Formulierung
        
        Exa funktioniert besser mit positiven Ortsangaben statt negativen Ausschlüssen
        """
        # Erstelle positive geografische Verstärkungen
        positive_constraints = []
        
        # Füge spezifische positive Formulierungen hinzu
        positive_constraints.extend([
            f'specifically in {region}',
            f'located in {country}',
            f'"{region}, {country}"'
        ])
        
        # Füge regionale Marker hinzu
        if region.lower() in self.regional_markers:
            positive_constraints.extend([
                f'"{marker}"' for marker in self.regional_markers[region.lower()]
            ])
        
        # WICHTIG: Verwende NOT statt - für Ausschlüsse (Exa-spezifisch)
        exclusions = []
        
        # Spezifische Ausschlüsse für Quebec/Canada
        if country.lower() == "canada" and region.lower() == "quebec":
            exclusions = [
                'NOT Greenland',
                'NOT Grönland',
                'NOT Iceland',
                'NOT "Northwest Territories"',
                'NOT Nunavut'
            ]
        elif country.lower() == "canada":
            exclusions = [
                'NOT Greenland',
                'NOT Alaska',
                'NOT "United States"'
            ]
        
        # Kombiniere positive und negative Constraints
        all_constraints = positive_constraints + exclusions
        constraint_string = " ".join(all_constraints)
        
        return constraint_string
    
    def get_region_specific_domains(self, country: str, technical: bool = False) -> List[str]:
        """
        ÄNDERUNG 19.06.2025: Gibt länderspezifische Domains zurück
        """
        # Import von enhanced_search um Duplikation zu vermeiden
        country_domains = get_country_specific_domains(country)
        
        # Füge technische Domains hinzu wenn benötigt
        if technical and country.lower() in self.technical_domains:
            country_domains.extend(self.technical_domains[country.lower()])
        
        # Füge allgemeine Mining-Domains hinzu
        general_domains = ["mining.com", "mindat.org", "infomine.com"]
        
        # Kombiniere und entferne Duplikate
        all_domains = list(set(country_domains + general_domains))
        
        return all_domains[:15]  # Maximal 15 Domains