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
    def get_quebec_mining_prompt(mine_name: str, field_type: str = "comprehensive") -> str:
        """Quebec-spezifischer Mining-Prompt für lokale Datenquellen"""
        
        return f"""FOKUS: QUEBEC MINING DATA für {mine_name}

PRIORITÄRE QUEBEC-QUELLEN:
1. GESTIM (Système de gestion des titres miniers)
   - https://gestim.mines.gouv.qc.ca/
   - Titre minier details
   - Garanties financières
   - Status d'exploitation

2. MERN (Ministère de l'Énergie et des Ressources naturelles)
   - Mining claims database
   - Environmental permits
   - Closure plans

3. SEDAR (Quebec mining companies)
   - NI 43-101 Technical Reports
   - Annual Reports
   - Feasibility Studies

4. Quebec Government Sources
   - Environmental assessments
   - BAPE reports
   - Mining regulations

BILINGUALE SUCHSTRATEGIE:
FRANZÖSISCH:
- "{mine_name} mine Québec"
- "{mine_name} exploitation minière"
- "{mine_name} titre minier"
- "{mine_name} GESTIM"
- "{mine_name} MERN"
- "{mine_name} garantie financière"
- "{mine_name} plan fermeture"
- "{mine_name} coûts restauration"
- "{mine_name} exploitant"
- "{mine_name} propriétaire"

ENGLISCH:
- "{mine_name} mine Quebec"
- "{mine_name} mining operation"
- "{mine_name} mining title"
- "{mine_name} financial guarantee"
- "{mine_name} closure plan"
- "{mine_name} restoration costs"
- "{mine_name} operator"
- "{mine_name} owner"

QUEBEC MINING TERMINOLOGY:
- Exploitant = Operator
- Propriétaire = Owner
- Titre minier = Mining title
- Claims miniers = Mining claims
- Garantie financière = Financial guarantee
- Cautionnement = Surety bond
- Plan de fermeture = Closure plan
- Coûts de restauration = Restoration costs
- Résidus miniers = Mining waste
- Permis d'exploitation = Operating permit

KRITISCHE FELDER FÜR QUEBEC:
1. Restaurationskosten (CAD$ Beträge)
2. Eigentümer/Betreiber (Quebec corporations)
3. GESTIM Titre minier numbers
4. Environmental permits
5. Financial guarantees (Banque Nationale, Caisse Desjardins, etc.)

VALIDIERUNG:
- Alle Dollarbeträge in CAD konvertieren
- Quebec corporate entities validieren
- GESTIM reference numbers prüfen
- Bilinguale Terminologie respektieren"""

    @staticmethod
    def get_comprehensive_extraction_prompt(mine_name: str, name_variants: List[str], 
                                          country: str, commodity: str, 
                                          discovered_sources: List[Dict] = None) -> str:
        """Umfassender Extraktions-Prompt mit allen verfügbaren Quellen"""
        
        sources_text = ""
        if discovered_sources:
            sources_text = "\n\nVERFÜGBARE QUELLEN:\n"
            for i, source in enumerate(discovered_sources[:10], 1):
                if isinstance(source, dict):
                    url = source.get('url', 'Keine URL')
                    title = source.get('title', source.get('value', 'Kein Titel'))
                    sources_text += f"{i}. {title[:60]}... ({url})\n"
        
        variants_text = ", ".join(name_variants[:5]) if name_variants else mine_name
        
        return f"""COMPREHENSIVE MINING DATA EXTRACTION für {mine_name}

MINE VARIANTS: {variants_text}
LAND: {country}
ROHSTOFF: {commodity}

{sources_text}

SYSTEMATIC FIELD EXTRACTION:
Extrahiere ALLE verfügbaren Informationen für folgende Felder:

1. EIGENTÜMER (Owner)
   - Aktuelle Muttergesellschaft
   - Prozentuale Anteile bei Joint Ventures
   - Änderungen in letzten 5 Jahren

2. BETREIBER (Operator)
   - Operierendes Unternehmen
   - Management Company
   - Unterschied zu Eigentümer

3. RESTAURATIONSKOSTEN (Restoration Costs)
   - Asset Retirement Obligation (ARO)
   - Closure costs/Mine closure costs
   - Environmental liabilities
   - Financial assurance/Closure bonds
   - Betrag, Währung, Jahr der Schätzung

4. KOORDINATEN (Coordinates)
   - GPS-Koordinaten (Dezimalgrad)
   - Latitude/Longitude
   - Zentrum der Mine

5. AKTIVITÄTSSTATUS (Activity Status)
   - Aktueller Betriebsstatus
   - Explorations-/Produktions-/Stilllegungsphase
   - Geplante Änderungen

6. ROHSTOFFABBAU (Commodities)
   - Hauptrohstoffe
   - Nebenprodukte
   - Erzgehalte

7. MINENTYP (Mine Type)
   - Untertage/Open-Pit/Kombination
   - Abbaumethoden

8. PRODUKTION (Production)
   - Produktionsstart/-ende
   - Jährliche Fördermengen
   - Reserven/Ressourcen

9. FLÄCHE (Area)
   - Minenfläche in qkm
   - Konzessionsfläche

EXTRACTION RULES:
- Verwende ALLE verfügbaren Quellen systematisch
- Keine Auslassung bei negativen Zwischenergebnissen
- Plausibilitätsprüfung aller Werte
- Quellenreferenzen für jeden extrahierten Wert
- Bei Unsicherheit: Feld als 'X' markieren (gesucht aber nicht gefunden)
- NIEMALS leere Felder ohne Suchversuch lassen

QUALITY ASSURANCE:
- Mindestens 3 unabhängige Quellen pro kritischem Feld
- Cross-Validation zwischen Quellen
- Aktualitätsprüfung (nicht älter als 5 Jahre)
- Konsistenzprüfung zwischen verwandten Feldern"""

    @staticmethod
    def get_source_discovery_prompt(mine_name: str, name_variants: List[str], 
                                  country: str, commodity: str) -> str:
        """Prompt für systematische Quellenentdeckung"""
        
        variants_text = ", ".join(name_variants[:5]) if name_variants else mine_name
        
        return f"""SOURCE DISCOVERY MISSION für {mine_name}

MINE VARIANTS: {variants_text}
LAND: {country}  
ROHSTOFF: {commodity}

ZIEL: Finde ALLE verfügbaren Datenquellen für diese Mine

PRIORITÄRE QUELLENTYPEN:

1. CORPORATE SOURCES (Höchste Priorität)
   - Unternehmenswebseiten
   - Investor Relations
   - Annual Reports
   - Press Releases
   - Sustainability Reports

2. REGULATORY SOURCES
   - Securities filings (SEDAR, EDGAR)
   - NI 43-101 Technical Reports
   - Environmental Impact Assessments
   - Mining permits and licenses
   - Government databases

3. TECHNICAL SOURCES
   - Feasibility Studies
   - Resource/Reserve Reports
   - Geological surveys
   - Mining engineering reports
   - Academic studies

4. NEWS & INDUSTRY SOURCES
   - Mining news websites
   - Industry publications
   - Trade magazines
   - Conference presentations

5. FINANCIAL SOURCES
   - Stock exchange filings
   - Financial analysis reports
   - Credit rating reports
   - Banking documents

SEARCH STRATEGY:
- Verwende alle Mine-Name Varianten
- Kombiniere mit Rohstoff-Begriffen
- Inklusive historischer Informationen
- Mehrsprachige Suche wenn relevant

OUTPUT FORMAT:
Für jede gefundene Quelle:
- URL (falls verfügbar)
- Titel/Beschreibung
- Quellentyp
- Relevanz-Score (1-5)
- Letzte Aktualisierung
- Sprache

GOAL: Mindestens 10 hochwertige Quellen identifizieren"""
    
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
    
    @staticmethod
    def get_source_discovery_prompt(mine_name: str, country: str = None, 
                                   region: str = None, commodity: str = None) -> str:
        """NEUER PROMPT: Spezialisiert auf Quellensuche"""
        
        location = country if country else "weltweit"
        if region:
            location = f"{region}, {country}" if country else region
        
        return f"""QUELLENSUCHE für {mine_name} Mine {f'in {location}' if location else ''}

AUFGABE: Finde ALLE verfügbaren Quellen, Dokumente und Referenzen zu dieser Mine.

PRIORITÄT 1 - Offizielle Quellen:
- Unternehmenswebseiten (Investor Relations, Projekte)
- Behördendokumente (SEDAR, SEC, ASX, TSX)
- Regierungsportale (Bergbauministerien, Umweltbehörden)
- GESTIM Datenbank (für Quebec)

PRIORITÄT 2 - Technische Dokumente:
- NI 43-101 Technical Reports
- JORC Reports
- Feasibility Studies
- Environmental Impact Assessments
- Mine Closure Plans
- Exploration Reports

PRIORITÄT 3 - Finanzdokumente:
- Annual Reports / Jahresberichte
- Quarterly Reports
- Financial Statements
- MD&A (Management Discussion & Analysis)
- Investor Presentations

PRIORITÄT 4 - Medien und Analysen:
- Mining.com, Northern Miner, Mining Journal
- Reuters, Bloomberg, Financial Post
- Analyst Reports
- Branchennachrichten

PRIORITÄT 5 - Spezialdatenbanken:
- Mining Data Online
- S&P Global Market Intelligence
- Wood Mackenzie
- InfoMine
- USGS, Natural Resources Canada

AUSGABEFORMAT:
[1] URL - Beschreibung (Dokumenttyp, Jahr)
[2] URL - Beschreibung (Dokumenttyp, Jahr)
...

WICHTIG: 
- Gib ALLE gefundenen URLs an
- Kennzeichne Dokumenttyp (PDF, Webseite, Datenbank)
- Notiere das Jahr/Datum wenn verfügbar
- Priorisiere aktuelle Quellen (< 3 Jahre)"""
    
    @staticmethod
    def get_comprehensive_extraction_prompt(mine_name: str, sources: List[str]) -> str:
        """NEUER PROMPT: Umfassende Datenextraktion aus Quellen"""
        
        sources_text = "\n".join([f"[{i+1}] {source}" for i, source in enumerate(sources[:30])])
        
        return f"""UMFASSENDE DATENEXTRAKTION für {mine_name}

AUFGABE: Analysiere ALLE folgenden Quellen und extrahiere JEDE verfügbare Information.

QUELLEN:
{sources_text}

EXTRAKTIONSANWEISUNGEN:

1. LIES JEDE QUELLE SORGFÄLTIG
2. SUCHE in Tabellen, Fußnoten, Anhängen, Grafiken
3. BEACHTE verschiedene Schreibweisen und Sprachen
4. KOMBINIERE Informationen aus mehreren Quellen
5. PRIORISIERE neuere Daten bei Konflikten

DATENFELDER (mit Quellenangabe):

BASISDATEN:
- Name: [exakt] [Quelle: Nr]
- Land: [Land] [Quelle: Nr]
- Region: [Provinz/Staat] [Quelle: Nr]
- Status: [aktiv/geschlossen/geplant] [Quelle: Nr]

EIGENTUM & BETRIEB:
- Eigentümer: [mit %] [Quelle: Nr]
- Betreiber: [Operator] [Quelle: Nr]
- Joint Venture Partner: [falls vorhanden] [Quelle: Nr]

KOORDINATEN (alle Formate):
- Latitude: [Dezimalgrad] [Quelle: Nr]
- Longitude: [Dezimalgrad] [Quelle: Nr]
- UTM: [falls verfügbar] [Quelle: Nr]

FINANZDATEN:
- Restaurationskosten: [Betrag, Währung, Jahr] [Quelle: Nr]
- ARO: [Asset Retirement Obligation] [Quelle: Nr]
- Marktkapitalisierung: [Betrag] [Quelle: Nr]
- Jahresumsatz: [Betrag, Jahr] [Quelle: Nr]
- EBITDA: [Betrag, Jahr] [Quelle: Nr]
- Investitionssumme: [CAPEX] [Quelle: Nr]

PRODUKTION:
- Rohstoffe: [Liste] [Quelle: Nr]
- Jahresproduktion: [Menge, Einheit, Jahr] [Quelle: Nr]
- Produktionsstart: [Jahr] [Quelle: Nr]
- Produktionsende: [Jahr/aktiv] [Quelle: Nr]
- Lebensdauer: [Jahre] [Quelle: Nr]

TECHNISCHE DATEN:
- Minentyp: [Open-Pit/Underground/etc] [Quelle: Nr]
- Fläche: [km²] [Quelle: Nr]
- Tiefe: [m] [Quelle: Nr]
- Reserven: [Menge, Einheit] [Quelle: Nr]
- Ressourcen: [Menge, Einheit] [Quelle: Nr]
- Erzgehalt: [%, g/t] [Quelle: Nr]

WEITERE DATEN:
- Mitarbeiterzahl: [Anzahl] [Quelle: Nr]
- Verarbeitungskapazität: [t/Tag] [Quelle: Nr]
- Infrastruktur: [Beschreibung] [Quelle: Nr]
- Umweltgenehmigungen: [Status] [Quelle: Nr]

WICHTIG:
- Gib ALLE gefundenen Daten an
- Verwende [Quelle: X] für jedes Datenfeld
- Bei mehreren Werten: Alle angeben mit Quelle
- KEINE Platzhalter oder Schätzungen"""