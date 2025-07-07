"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Spezialisierte Prompts für kritische Felder in Mining-Recherchen
"""

from typing import Dict, List, Optional


class SpecializedPrompts:
    """Generiert spezialisierte Prompts für kritische Datenfelder"""
    
    @staticmethod
    def get_restoration_costs_prompt(mine_name: str, country: str, commodity: str = None) -> str:
        """Spezialisierter Prompt für Restaurationskosten"""
        
        return f"""FOKUS: RESTAURATIONSKOSTEN für {mine_name} in {country}

SUCHE GEZIELT NACH:
1. Asset Retirement Obligation (ARO)
2. Closure costs / Mine closure costs
3. Environmental liabilities
4. Restoration provision / Rehabilitation provision
5. Decommissioning costs
6. Financial assurance / Closure bonds
7. Post-closure monitoring costs
8. Progressive rehabilitation costs

QUELLEN PRIORISIERUNG:
- Jahresberichte (Annual Reports) der letzten 5 Jahre
- NI 43-101 Technical Reports
- Feasibility Studies
- Environmental Impact Assessments
- Securities Filings (SEDAR, EDGAR)
- Regierungsdokumente zu Umweltauflagen
- Konzessionsdokumente und Genehmigungen
- Managementpläne (Mine Management Plans)
- GESTIM Datenbank (für Quebec)
- Umweltgenehmigungen (Environmental Permits)
- Exploration Closure Plans

WICHTIGE SUCHBEGRIFFE:
- "{mine_name} closure costs"
- "{mine_name} ARO"
- "{mine_name} environmental liability"
- "{mine_name} restoration provision"
- "{mine_name} financial assurance"
- "{mine_name} mine closure plan"
- "{mine_name} exploration closure"
- "{mine_name} initial restoration"
- "{mine_name} konzession" (für Konzessionsdokumente)
- "{mine_name} management plan"
- "{mine_name} GESTIM" (für Quebec)
- "{mine_name} environmental permit"

BETRAGSERMITTLUNG:
- Suche nach ALLEN konkreten Dollarbeträgen (auch kleine Beträge ab $1,000)
- WICHTIG: Auch Beträge unter $100,000 sind relevant!
- Explorationsminen können Restaurationskosten von nur $5,000 - $50,000 haben
- Berücksichtige unterschiedliche Währungen (CAD, USD, AUD, etc.)
- Achte auf Bezeichnungen wie "thousand", "k", "tausend"
- Notiere das Jahr der Schätzung/Berechnung
- Unterscheide zwischen bereits gezahlten und geplanten Kosten

BEISPIELE VALIDER BETRÄGE:
- "$5,000 CAD" (Exploration)
- "$25k USD" (kleine Mine)
- "$150,000 AUD" (Teilsanierung)
- "$2.5 million" (mittlere Mine)
- "$45 million" (große Mine)

VERBOTEN:
- KEINE Platzhalter wie $1, $2, $3
- KEINE "k.A.", "n/a", "unbekannt"
- Wenn keine Daten: Feld LEER lassen"""
    
    @staticmethod
    def get_coordinates_prompt(mine_name: str, region: str = None) -> str:
        """Spezialisierter Prompt für GPS-Koordinaten"""
        
        region_hint = f" in {region}" if region else ""
        
        return f"""FOKUS: GPS-KOORDINATEN für {mine_name}{region_hint}

SUCHE GEZIELT NACH:
1. Dezimalgrad-Koordinaten (z.B. -45.123456, 123.456789)
2. Grad-Minuten-Sekunden Format (z.B. 45°12'34.56"N, 123°45'67.89"W)
3. UTM-Koordinaten (Universal Transverse Mercator)
4. Zentrumskoordinaten der Mine
5. Koordinaten in technischen Berichten

QUELLEN PRIORISIERUNG:
- Technische Berichte (NI 43-101)
- Bergbaubehörden-Datenbanken
- Umweltverträglichkeitsprüfungen
- Geologische Surveys
- Mining Claims Maps

VALIDIERUNG:
- Latitude: Zwischen -90 und +90
- Longitude: Zwischen -180 und +180
- Für {region if region else 'die Region'}: Plausible Koordinatenbereiche prüfen

FORMAT:
- Bevorzugt: Dezimalgrad mit 6 Nachkommastellen
- Trenne Latitude und Longitude klar
- Notiere das Koordinatensystem wenn verfügbar

VERBOTEN:
- KEINE ungenauen Koordinaten (z.B. nur 2 Nachkommastellen)
- KEINE offensichtlich falschen Koordinaten
- Wenn unsicher: Feld LEER lassen"""
    
    @staticmethod
    def get_ownership_prompt(mine_name: str, country: str) -> str:
        """Spezialisierter Prompt für Eigentümer/Betreiber-Informationen"""
        
        return f"""FOKUS: EIGENTÜMER UND BETREIBER für {mine_name} in {country}

UNTERSCHEIDE KLAR ZWISCHEN:
1. EIGENTÜMER (Owner):
   - Juristische Person/Unternehmen mit Eigentumsrechten
   - Joint Venture Partner mit Eigentumsanteilen
   - Muttergesellschaft bei 100% Tochterunternehmen
   
2. BETREIBER (Operator):
   - Unternehmen das den täglichen Betrieb führt
   - Operating Company / Management Company
   - Kann vom Eigentümer verschieden sein

QUELLEN PRIORISIERUNG:
- Unternehmenswebseiten
- Jahresberichte
- Pressemitteilungen zu Übernahmen/Verkäufen
- Mining-Datenbanken
- Behördliche Register

WICHTIGE INFORMATIONEN:
- Prozentuale Eigentumsanteile (z.B. "70% Company A, 30% Company B")
- Änderungen in den letzten 5 Jahren
- Joint Venture Strukturen
- Tochtergesellschaften

FORMAT:
- Bei mehreren Eigentümern: Alle mit Prozentangaben
- Bei Betreiber: Nur das operierende Unternehmen
- Aktuelle Informationen (nicht älter als 2 Jahre)

BEISPIELE:
- Eigentümer: "Barrick Gold Corp. (100%)"
- Eigentümer: "Newmont (51%), Sumitomo (49%)"
- Betreiber: "Operated by Barrick Gold Corp."

VERBOTEN:
- KEINE historischen Eigentümer ohne Datumsangabe
- KEINE Vermutungen oder Spekulationen
- Wenn unklar: Feld LEER lassen"""
    
    @staticmethod
    def get_production_data_prompt(mine_name: str, commodity: str = None) -> str:
        """Spezialisierter Prompt für Produktionsdaten"""
        
        commodity_hint = f" ({commodity})" if commodity else ""
        
        return f"""FOKUS: PRODUKTIONSDATEN für {mine_name}{commodity_hint}

SUCHE NACH:
1. JAHRESPRODUKTION:
   - Aktuelle Produktionszahlen (letzte 3 Jahre)
   - Produktionskapazität vs. tatsächliche Produktion
   - Einheiten klar angeben (oz, t, Mt, kg, etc.)
   
2. PRODUKTIONSZEITRAUM:
   - Produktionsstart (Jahr)
   - Produktionsende (Jahr) oder "aktiv"
   - Unterbrechungen/Stilllegungen
   
3. FÖRDERMENGEN:
   - Nach Rohstoff aufgeschlüsselt
   - Durchschnittliche Jahresproduktion
   - Peak-Produktion

QUELLEN PRIORISIERUNG:
- Quartals-/Jahresberichte
- Produktions-Updates
- Technische Berichte
- Branchenstatistiken

FORMAT BEISPIELE:
- "125,000 oz Gold/Jahr (2023)"
- "2.5 Mt Kupfererz/Jahr @ 0.85% Cu"
- "Produktion: 2010-2021 (stillgelegt)"

EINHEITEN-KONVERTIERUNG:
- Gold/Silber: Unzen (oz) oder Kilogramm (kg)
- Basismetalle: Tonnen (t) oder Kilotonnen (kt)
- Kohle/Eisenerz: Millionen Tonnen (Mt)

VERBOTEN:
- KEINE Schätzungen ohne Kennzeichnung
- KEINE veralteten Daten (älter als 5 Jahre) ohne Datum
- Bei Unsicherheit: Feld LEER lassen"""
    
    @staticmethod
    def get_enhanced_query(mine_name: str, country: str, region: str = None, 
                          commodity: str = None, focus_fields: List[str] = None) -> str:
        """Erstellt eine erweiterte Query mit Fokus auf kritische Felder"""
        
        if not focus_fields:
            focus_fields = ['restoration_costs', 'coordinates', 'ownership', 'production']
        
        query_parts = [f"Detaillierte Informationen über {mine_name} in {country}"]
        
        if region:
            query_parts.append(f"Region: {region}")
        
        if commodity:
            query_parts.append(f"Rohstoff: {commodity}")
        
        # Füge spezialisierte Abschnitte für kritische Felder hinzu
        if 'restoration_costs' in focus_fields:
            query_parts.append("\n\n" + SpecializedPrompts.get_restoration_costs_prompt(
                mine_name, country, commodity
            ))
        
        if 'coordinates' in focus_fields:
            query_parts.append("\n\n" + SpecializedPrompts.get_coordinates_prompt(
                mine_name, region
            ))
        
        if 'ownership' in focus_fields:
            query_parts.append("\n\n" + SpecializedPrompts.get_ownership_prompt(
                mine_name, country
            ))
        
        if 'production' in focus_fields:
            query_parts.append("\n\n" + SpecializedPrompts.get_production_data_prompt(
                mine_name, commodity
            ))
        
        return "\n".join(query_parts)
    
    @staticmethod
    def get_field_validation_rules() -> Dict[str, Dict]:
        """Gibt Validierungsregeln für kritische Felder zurück"""
        
        return {
            'Restaurationskosten': {
                'min_value': 10000,
                'forbidden_patterns': [r'^\$?[1-3]\s*(?:CAD|USD|AUD)?$'],
                'required_patterns': [r'\$?\s*[\d,]+(?:\.\d+)?'],
                'empty_if_invalid': True
            },
            'x-Koordinate': {
                'min_value': -90,
                'max_value': 90,
                'decimal_places': 4,  # Mindestens 4 Nachkommastellen
                'empty_if_invalid': True
            },
            'y-Koordinate': {
                'min_value': -180,
                'max_value': 180,
                'decimal_places': 4,
                'empty_if_invalid': True
            },
            'Eigentümer': {
                'forbidden_values': ['unknown', 'unbekannt', 'n/a', 'k.a.'],
                'empty_if_invalid': True
            },
            'Betreiber': {
                'forbidden_values': ['unknown', 'unbekannt', 'n/a', 'k.a.'],
                'empty_if_invalid': True
            }
        }