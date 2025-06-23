"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Gemeinsamer Query Builder für Suchanfragen
"""

from typing import List, Dict, Optional, Set
from ..base_agent import MineQuery
import re
from urllib.parse import quote_plus

class QueryBuilder:
    """Basis-Klasse für Query Building"""
    
    def __init__(self):
        """Initialisiert den Query Builder"""
        self.common_mining_terms = {
            "en": ["mine", "mining", "minerals", "extraction", "quarry", "deposit"],
            "fr": ["mine", "exploitation", "minière", "extraction", "carrière", "gisement"],
            "es": ["mina", "minería", "minerales", "extracción", "cantera", "yacimiento"],
            "de": ["bergwerk", "bergbau", "mineralien", "abbau", "steinbruch", "lagerstätte"]
        }
        
        self.location_prefixes = {
            "en": ["near", "in", "at", "located"],
            "fr": ["près de", "à", "dans", "situé"],
            "es": ["cerca de", "en", "ubicado"],
            "de": ["nahe", "in", "bei", "gelegen"]
        }
    
    def build_search_query(self, 
                          mine_query: MineQuery,
                          language: str = "en",
                          include_operators: bool = True) -> str:
        """
        Baut eine Suchanfrage aus einem MineQuery Objekt
        
        Args:
            mine_query: Die Minen-Suchanfrage
            language: Zielsprache für die Suche
            include_operators: Ob Such-Operatoren verwendet werden sollen
            
        Returns:
            Formatierte Suchanfrage
        """
        parts = []
        
        # Hauptbegriff (Minenname)
        if mine_query.mine_name:
            name_variants = self._get_name_variants(mine_query.mine_name)
            if include_operators and len(name_variants) > 1:
                parts.append(f'({" OR ".join(name_variants)})')
            else:
                parts.append(name_variants[0])
        
        # Standort (nutze region oder country)
        location = getattr(mine_query, 'location', None) or mine_query.region
        if location:
            location_query = self._build_location_query(
                location, 
                language, 
                include_operators
            )
            parts.append(location_query)
        
        # Bergbauart
        if mine_query.mining_type:
            type_query = self._build_type_query(
                mine_query.mining_type,
                language,
                include_operators
            )
            parts.append(type_query)
        
        # Allgemeine Bergbau-Begriffe hinzufügen
        if language in self.common_mining_terms:
            mining_terms = self.common_mining_terms[language][:2]
            if include_operators:
                parts.append(f'({" OR ".join(mining_terms)})')
            else:
                parts.extend(mining_terms)
        
        # Query zusammenbauen
        if include_operators:
            return " AND ".join(parts)
        else:
            return " ".join(parts)
    
    def build_url_query(self, 
                       mine_query: MineQuery,
                       base_url: str,
                       param_name: str = "q",
                       additional_params: Optional[Dict[str, str]] = None) -> str:
        """
        Baut eine vollständige Such-URL
        
        Args:
            mine_query: Die Minen-Suchanfrage
            base_url: Basis-URL der Suchmaschine
            param_name: Name des Query-Parameters
            additional_params: Zusätzliche URL-Parameter
            
        Returns:
            Vollständige Such-URL
        """
        query = self.build_search_query(mine_query)
        encoded_query = quote_plus(query)
        
        # Basis-URL mit Query
        url = f"{base_url}?{param_name}={encoded_query}"
        
        # Zusätzliche Parameter
        if additional_params:
            for key, value in additional_params.items():
                url += f"&{key}={quote_plus(str(value))}"
        
        return url
    
    def _get_name_variants(self, mine_name: str) -> List[str]:
        """Generiert Varianten eines Minennamens"""
        variants = [mine_name]
        
        # Mit/ohne "Mine" Suffix
        if not mine_name.lower().endswith("mine"):
            variants.append(f"{mine_name} Mine")
        else:
            base_name = re.sub(r'\s*mine\s*$', '', mine_name, flags=re.IGNORECASE)
            variants.append(base_name)
        
        # Mit Bindestrichen
        if " " in mine_name:
            variants.append(mine_name.replace(" ", "-"))
        
        # Akronyme
        words = mine_name.split()
        if len(words) > 1:
            acronym = "".join(word[0].upper() for word in words)
            variants.append(acronym)
        
        # Possessiv-Formen
        if not mine_name.endswith("'s"):
            variants.append(f"{mine_name}'s")
        
        return list(dict.fromkeys(variants))  # Duplikate entfernen
    
    def _build_location_query(self, 
                            location: str,
                            language: str,
                            include_operators: bool) -> str:
        """Baut Location-Teil der Query"""
        parts = []
        
        # Location mit Präfixen
        if language in self.location_prefixes:
            for prefix in self.location_prefixes[language][:2]:
                parts.append(f'"{prefix} {location}"')
        
        # Location allein
        parts.append(location)
        
        # Region/Land Varianten
        location_variants = self._get_location_variants(location)
        parts.extend(location_variants)
        
        if include_operators and len(parts) > 1:
            return f'({" OR ".join(parts)})'
        else:
            return parts[0]
    
    def _get_location_variants(self, location: str) -> List[str]:
        """Generiert Varianten eines Standorts"""
        variants = []
        
        # Länder-Codes und Namen
        country_map = {
            "USA": ["United States", "America", "US"],
            "UK": ["United Kingdom", "Britain", "England"],
            "DRC": ["Democratic Republic of Congo", "Congo-Kinshasa", "Zaire"],
            "RSA": ["South Africa", "Republic of South Africa"],
        }
        
        for code, names in country_map.items():
            if location.upper() == code or location in names:
                variants.extend(names)
                break
        
        # Regionale Varianten
        if "," in location:
            # z.B. "Toronto, Canada" -> auch "Toronto" und "Canada" einzeln
            parts = [part.strip() for part in location.split(",")]
            variants.extend(parts)
        
        return list(set(variants) - {location})  # Duplikate entfernen, Original ausschließen
    
    def _build_type_query(self,
                         mining_type: str,
                         language: str,
                         include_operators: bool) -> str:
        """Baut Mining-Type Teil der Query"""
        # Übersetzungen für Bergbauarten
        translations = {
            "gold": {
                "en": ["gold", "aurum"],
                "fr": ["or", "aurum"],
                "es": ["oro", "aurum"],
                "de": ["gold", "aurum"]
            },
            "silver": {
                "en": ["silver"],
                "fr": ["argent"],
                "es": ["plata"],
                "de": ["silber"]
            },
            "copper": {
                "en": ["copper"],
                "fr": ["cuivre"],
                "es": ["cobre"],
                "de": ["kupfer"]
            },
            "coal": {
                "en": ["coal", "anthracite", "lignite"],
                "fr": ["charbon", "houille"],
                "es": ["carbón"],
                "de": ["kohle", "steinkohle", "braunkohle"]
            }
        }
        
        type_lower = mining_type.lower()
        if type_lower in translations and language in translations[type_lower]:
            terms = translations[type_lower][language]
            if include_operators and len(terms) > 1:
                return f'({" OR ".join(terms)})'
            else:
                return terms[0]
        
        return mining_type
    
    def extract_keywords(self, mine_query: MineQuery) -> Set[str]:
        """
        Extrahiert alle relevanten Keywords aus einer Query
        
        Args:
            mine_query: Die Minen-Suchanfrage
            
        Returns:
            Set von Keywords
        """
        keywords = set()
        
        # Minenname und Varianten
        if mine_query.mine_name:
            keywords.update(self._get_name_variants(mine_query.mine_name))
        
        # Location und Varianten
        if mine_query.location:
            keywords.add(mine_query.location)
            keywords.update(self._get_location_variants(mine_query.location))
        
        # Mining Type in verschiedenen Sprachen
        if mine_query.mining_type:
            for lang in ["en", "fr", "es", "de"]:
                keywords.add(self._build_type_query(mine_query.mining_type, lang, False))
        
        # Allgemeine Bergbau-Begriffe
        for terms in self.common_mining_terms.values():
            keywords.update(terms[:2])
        
        # Kleinschreibung für einheitliche Vergleiche
        return {kw.lower() for kw in keywords if kw}
    
    def build_advanced_query(self,
                           mine_query: MineQuery,
                           exclude_terms: Optional[List[str]] = None,
                           exact_phrases: Optional[List[str]] = None,
                           date_range: Optional[tuple] = None) -> str:
        """
        Baut eine erweiterte Suchanfrage mit zusätzlichen Optionen
        
        Args:
            mine_query: Die Basis-Suchanfrage
            exclude_terms: Begriffe die ausgeschlossen werden sollen
            exact_phrases: Exakte Phrasen die vorkommen müssen
            date_range: Tupel mit (start_date, end_date)
            
        Returns:
            Erweiterte Suchanfrage
        """
        # Basis-Query
        base = self.build_search_query(mine_query)
        parts = [base]
        
        # Exakte Phrasen
        if exact_phrases:
            for phrase in exact_phrases:
                parts.append(f'"{phrase}"')
        
        # Ausschluss-Begriffe
        if exclude_terms:
            exclusions = " ".join(f"-{term}" for term in exclude_terms)
            parts.append(exclusions)
        
        # Datumsbereich (Google-Style)
        if date_range and len(date_range) == 2:
            start, end = date_range
            parts.append(f"after:{start} before:{end}")
        
        return " ".join(parts)