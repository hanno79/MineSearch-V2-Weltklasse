"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Bilinguale Suchstrategie für Quebec Mining (Französisch/Englisch)
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BilingualSearchTerm:
    """Repräsentiert einen bilingualen Suchbegriff"""
    french: str
    english: str
    context: str
    priority: int  # 1=highest, 5=lowest

class BilingualSearchStrategy:
    """
    Bilinguale Suchstrategie für Quebec Mining Operations
    Generiert optimale französische/englische Suchterm-Kombinationen
    """
    
    def __init__(self):
        # Quebec Mining Terminologie (Französisch → Englisch)
        self.mining_terminology = {
            # Basis Mining Terms
            'mine': 'mine',
            'exploitation minière': 'mining operation',
            'carrière': 'quarry', 
            'sablière': 'sand pit',
            'gravière': 'gravel pit',
            
            # Mining Types
            'mine souterraine': 'underground mine',
            'mine à ciel ouvert': 'open pit mine',
            'fosse': 'pit',
            'galerie': 'gallery',
            'puits': 'shaft',
            
            # Legal/Administrative
            'titre minier': 'mining title',
            'claims miniers': 'mining claims',
            'permis d\'exploitation': 'operating permit',
            'certificat d\'autorisation': 'authorization certificate',
            'bail minier': 'mining lease',
            'concession minière': 'mining concession',
            
            # Companies/Entities
            'exploitant': 'operator',
            'propriétaire': 'owner',
            'détenteur': 'holder',
            'société minière': 'mining company',
            'entreprise minière': 'mining enterprise',
            
            # Commodities
            'or': 'gold',
            'argent': 'silver',
            'cuivre': 'copper',
            'zinc': 'zinc',
            'fer': 'iron',
            'nickel': 'nickel',
            'lithium': 'lithium',
            'spodumène': 'spodumene',
            'graphite': 'graphite',
            'terres rares': 'rare earth elements',
            
            # Financial/Legal
            'coûts de restauration': 'restoration costs',
            'garantie financière': 'financial guarantee',
            'cautionnement': 'surety bond',
            'lettre de crédit': 'letter of credit',
            'plan de fermeture': 'closure plan',
            'plan de restauration': 'restoration plan',
            'obligations environnementales': 'environmental obligations',
            
            # Production/Operations
            'production annuelle': 'annual production',
            'réserves minérales': 'mineral reserves',
            'ressources minérales': 'mineral resources',
            'traitement du minerai': 'ore processing',
            'concentrateur': 'concentrator',
            'usine de traitement': 'processing plant',
            
            # Environmental
            'impact environnemental': 'environmental impact',
            'évaluation environnementale': 'environmental assessment',
            'résidus miniers': 'mining waste',
            'parc à résidus': 'tailings pond',
            'surveillance environnementale': 'environmental monitoring',
            
            # Status Terms
            'en exploitation': 'in operation',
            'en développement': 'in development',
            'en exploration': 'in exploration',
            'fermée': 'closed',
            'suspendue': 'suspended',
            'abandonnée': 'abandoned'
        }
        
        # Quebec Regions (Französisch → Englisch)
        self.quebec_regions = {
            'Nord-du-Québec': 'Northern Quebec',
            'Abitibi-Témiscamingue': 'Abitibi-Temiscamingue',
            'Côte-Nord': 'North Shore',
            'Saguenay-Lac-Saint-Jean': 'Saguenay-Lac-Saint-Jean',
            'Outaouais': 'Outaouais',
            'Mauricie': 'Mauricie',
            'Eeyou Istchee': 'Eeyou Istchee',
            'Baie James': 'James Bay',
            'Nunavik': 'Nunavik'
        }
        
        # Kritische Suchfeld-Prioritäten
        self.field_priorities = {
            'restoration_costs': 1,  # Höchste Priorität
            'owner': 1,
            'operator': 1,
            'coordinates': 2,
            'status': 2,
            'commodity': 2,
            'production': 3,
            'reserves': 3,
            'permits': 4,
            'environmental': 5
        }
    
    def generate_field_specific_terms(self, mine_name: str, field_type: str, region: str = None) -> List[BilingualSearchTerm]:
        """
        Generiere feldspezifische bilinguale Suchbegriffe
        
        Args:
            mine_name: Name der Mine
            field_type: Art des Feldes (restoration_costs, owner, etc.)
            region: Quebec Region (optional)
            
        Returns:
            Liste von BilingualSearchTerm Objekten
        """
        terms = []
        priority = self.field_priorities.get(field_type, 3)
        
        if field_type == 'restoration_costs':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} coûts restauration",
                    english=f"{mine_name} restoration costs",
                    context="restoration_costs_basic",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} garantie financière",
                    english=f"{mine_name} financial guarantee",
                    context="restoration_costs_guarantee",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} plan fermeture",
                    english=f"{mine_name} closure plan",
                    context="restoration_costs_closure",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} cautionnement",
                    english=f"{mine_name} surety bond",
                    context="restoration_costs_bond",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} lettre crédit",
                    english=f"{mine_name} letter of credit",
                    context="restoration_costs_credit",
                    priority=2
                )
            ])
        
        elif field_type == 'owner':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} propriétaire",
                    english=f"{mine_name} owner",
                    context="ownership_basic",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} détenteur titre",
                    english=f"{mine_name} title holder",
                    context="ownership_title",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} société minière",
                    english=f"{mine_name} mining company",
                    context="ownership_company",
                    priority=2
                )
            ])
        
        elif field_type == 'operator':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} exploitant",
                    english=f"{mine_name} operator",
                    context="operator_basic",
                    priority=1
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} exploitation minière",
                    english=f"{mine_name} mining operation",
                    context="operator_operation",
                    priority=1
                )
            ])
        
        elif field_type == 'coordinates':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} coordonnées GPS",
                    english=f"{mine_name} GPS coordinates",
                    context="coordinates_gps",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} localisation",
                    english=f"{mine_name} location",
                    context="coordinates_location",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} position géographique",
                    english=f"{mine_name} geographic position",
                    context="coordinates_geographic",
                    priority=3
                )
            ])
        
        elif field_type == 'commodity':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} substance exploitée",
                    english=f"{mine_name} mined commodity",
                    context="commodity_basic",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} minerai",
                    english=f"{mine_name} ore",
                    context="commodity_ore",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} production minérale",
                    english=f"{mine_name} mineral production",
                    context="commodity_production",
                    priority=2
                )
            ])
        
        elif field_type == 'status':
            terms.extend([
                BilingualSearchTerm(
                    french=f"{mine_name} statut exploitation",
                    english=f"{mine_name} operating status",
                    context="status_basic",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} en exploitation",
                    english=f"{mine_name} in operation",
                    context="status_active",
                    priority=2
                ),
                BilingualSearchTerm(
                    french=f"{mine_name} fermée",
                    english=f"{mine_name} closed",
                    context="status_closed",
                    priority=2
                )
            ])
        
        # Füge region-spezifische Terme hinzu
        if region and region in self.quebec_regions:
            for term in terms:
                # Erweitere mit Region
                term.french += f" {region}"
                term.english += f" {self.quebec_regions[region]}"
        
        return terms
    
    def generate_comprehensive_search_terms(self, mine_name: str, region: str = None, 
                                          priority_fields: List[str] = None) -> Dict[str, List[BilingualSearchTerm]]:
        """
        Generiere umfassende bilinguale Suchbegriffe für alle Felder
        
        Args:
            mine_name: Name der Mine
            region: Quebec Region (optional)
            priority_fields: Liste prioritärer Felder (optional)
            
        Returns:
            Dictionary mit Suchbegriffen pro Feldtyp
        """
        if priority_fields is None:
            priority_fields = ['restoration_costs', 'owner', 'operator', 'coordinates', 'status', 'commodity']
        
        all_terms = {}
        
        for field_type in priority_fields:
            field_terms = self.generate_field_specific_terms(mine_name, field_type, region)
            all_terms[field_type] = field_terms
        
        # Füge allgemeine Quebec-Mining-Terme hinzu
        general_terms = self._generate_general_quebec_terms(mine_name, region)
        all_terms['general'] = general_terms
        
        return all_terms
    
    def _generate_general_quebec_terms(self, mine_name: str, region: str = None) -> List[BilingualSearchTerm]:
        """Generiere allgemeine Quebec-spezifische Suchbegriffe"""
        terms = [
            BilingualSearchTerm(
                french=f"{mine_name} GESTIM",
                english=f"{mine_name} GESTIM",
                context="gestim_database",
                priority=1
            ),
            BilingualSearchTerm(
                french=f"{mine_name} MERN Québec",
                english=f"{mine_name} MERN Quebec",
                context="mern_registry",
                priority=1
            ),
            BilingualSearchTerm(
                french=f"{mine_name} titre minier",
                english=f"{mine_name} mining title",
                context="mining_title",
                priority=2
            ),
            BilingualSearchTerm(
                french=f"{mine_name} claims miniers",
                english=f"{mine_name} mining claims",
                context="mining_claims",
                priority=2
            )
        ]
        
        return terms
    
    def get_prioritized_search_sequence(self, mine_name: str, region: str = None) -> List[str]:
        """
        Hole priorisierte Suchsequenz für systematische Abarbeitung
        
        Args:
            mine_name: Name der Mine
            region: Quebec Region (optional)
            
        Returns:
            Liste von Suchbegriffen in Prioritätsreihenfolge
        """
        all_terms = self.generate_comprehensive_search_terms(mine_name, region)
        
        # Sammle alle Begriffe mit Prioritäten
        prioritized_terms = []
        for field_type, terms in all_terms.items():
            for term in terms:
                search_string = f"{term.french} OR {term.english}"
                prioritized_terms.append((term.priority, search_string, term.context))
        
        # Sortiere nach Priorität (niedrigste Zahl = höchste Priorität)
        prioritized_terms.sort(key=lambda x: x[0])
        
        # Gebe nur die Suchstrings zurück
        return [term[1] for term in prioritized_terms]
    
    def optimize_for_provider(self, search_terms: List[str], provider_name: str) -> List[str]:
        """
        Optimiere Suchbegriffe für spezifischen Provider
        
        Args:
            search_terms: Liste von Suchbegriffen
            provider_name: Name des Providers (perplexity, openrouter, etc.)
            
        Returns:
            Optimierte Suchbegriffe
        """
        optimized = []
        
        for term in search_terms:
            if provider_name.lower() in ['perplexity', 'tavily']:
                # Web-Search Providers: Verwende natürliche Sprache
                optimized.append(f"Find information about {term}")
            elif provider_name.lower() in ['openrouter', 'anthropic']:
                # LLM Providers: Verwende strukturierte Anfragen
                optimized.append(f"Search for mining data: {term}")
            else:
                # Default: Unverändert
                optimized.append(term)
        
        return optimized

# Singleton-Instanz und Quebec Bilingual Search Interface
bilingual_search_strategy = BilingualSearchStrategy()

class QuebecBilingualSearch:
    """Interface-Wrapper für bilingual search strategy mit vereinfachten Methoden"""
    
    def __init__(self):
        self.strategy = bilingual_search_strategy
    
    def generate_bilingual_search_terms(self, mine_name: str, region: str = None) -> List[str]:
        """
        Generiere bilinguale Suchbegriffe für eine Mine
        
        Args:
            mine_name: Name der Mine
            region: Quebec Region (optional)
            
        Returns:
            Liste von bilingualen Suchbegriffen
        """
        all_terms_dict = self.strategy.generate_comprehensive_search_terms(mine_name, region)
        terms_list = []
        
        for field_type, field_terms in all_terms_dict.items():
            for term in field_terms:
                # Kombiniere französisch und englisch
                bilingual_term = f"{term.french} OR {term.english}"
                terms_list.append(bilingual_term)
        
        return terms_list
    
    def is_quebec_context(self, region: str, country: str) -> bool:
        """
        Prüfe ob es sich um Quebec-Kontext handelt
        
        Args:
            region: Region
            country: Land
            
        Returns:
            True wenn Quebec-Kontext
        """
        if not region or not country:
            return False
            
        region_lower = region.lower()
        country_lower = country.lower()
        
        # Quebec-Indikatoren
        quebec_indicators = [
            'quebec', 'québec', 'qc', 'abitibi', 'témiscamingue', 'nord-du-québec',
            'côte-nord', 'saguenay', 'outaouais', 'mauricie', 'james bay', 'baie james'
        ]
        
        # Prüfe Region
        for indicator in quebec_indicators:
            if indicator in region_lower:
                return True
        
        # Prüfe Land (Canada + Quebec Region)
        if 'canada' in country_lower or 'canadian' in country_lower:
            for indicator in quebec_indicators:
                if indicator in region_lower:
                    return True
        
        return False
    
    def get_quebec_region_variants(self, region: str) -> List[str]:
        """
        Hole Quebec Region-Varianten
        
        Args:
            region: Ursprüngliche Region
            
        Returns:
            Liste von Region-Varianten
        """
        if not region:
            return []
            
        region_lower = region.lower()
        variants = [region]  # Original immer dabei
        
        # Quebec Region Mapping
        region_mappings = {
            'abitibi': ['Abitibi-Témiscamingue', 'Abitibi', 'Témiscamingue'],
            'nord-du-quebec': ['Nord-du-Québec', 'Northern Quebec', 'Nord du Quebec'],
            'cote-nord': ['Côte-Nord', 'North Shore', 'Cote Nord'],
            'saguenay': ['Saguenay-Lac-Saint-Jean', 'Saguenay', 'Lac Saint Jean'],
            'james bay': ['Baie James', 'James Bay', 'Eeyou Istchee'],
            'quebec': ['Québec', 'Quebec', 'QC']
        }
        
        for key, mapping in region_mappings.items():
            if key in region_lower:
                variants.extend(mapping)
        
        # Entferne Duplikate
        return list(set(variants))
    
    def normalize_accents(self, text: str) -> str:
        """
        Normalisiere französische Akzente für bessere Suche
        
        Args:
            text: Text mit Akzenten
            
        Returns:
            Text ohne Akzente
        """
        if not text:
            return text
            
        # Akzent-Mapping
        accent_map = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ô': 'o', 'ö': 'o',
            'î': 'i', 'ï': 'i',
            'ç': 'c',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'À': 'A', 'Â': 'A', 'Ä': 'A',
            'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ô': 'O', 'Ö': 'O',
            'Î': 'I', 'Ï': 'I',
            'Ç': 'C'
        }
        
        normalized = text
        for accented, plain in accent_map.items():
            normalized = normalized.replace(accented, plain)
        
        return normalized

# Quebec Bilingual Search Singleton
quebec_bilingual_search = QuebecBilingualSearch()