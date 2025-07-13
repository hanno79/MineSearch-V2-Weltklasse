"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Phasen-Logik für Multi-Provider Suchen
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SearchPhaseManager:
    """Manager für verschiedene Such-Phasen"""
    
    def __init__(self):
        # Zwei-Phasen-Suche Konfiguration
        self.phase1_models = ['perplexity:sonar']  # Schnelle Web-Suche
        self.phase2_models = ['perplexity:sonar-reasoning-pro', 'perplexity:sonar-pro']  # Tiefe Analyse
        self.phase3_models = ['abacus:deep-agent']  # Optional: Ultra-Deep Research
    
    def should_trigger_phase3(self, combined_data: Dict) -> bool:
        """Entscheide ob Phase 3 notwendig ist"""
        
        # Kritische Felder für Mining-Recherche
        critical_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate']
        
        # Prüfe ob kritische Felder fehlen
        missing_critical = 0
        for field in critical_fields:
            if not combined_data['best_data'].get(field):
                missing_critical += 1
        
        # Prüfe Gesamt-Datenabdeckung
        total_fields = len(combined_data['best_data'])
        filled_fields = sum(1 for v in combined_data['best_data'].values() if v)
        coverage = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        
        # Trigger Phase 3 wenn:
        # - Mindestens 1 kritisches Feld fehlt UND
        # - Gesamt-Abdeckung unter 70%
        return missing_critical > 0 and coverage < 70
    
    def build_phase2_query(self, mine_name: str, country: str, region: str, 
                          commodity: str, sources: List[Dict]) -> str:
        """Erstelle spezialisierte Query für Phase 2 - ERWEITERT für Restaurationskosten"""
        
        query = f"""DETAILLIERTE FINANZ- UND DATENEXTRAKTION für {mine_name}

PRIORITÄT 1 - RESTAURATIONSKOSTEN (ARO/Closure Costs):
- Asset Retirement Obligations (ARO)
- Environmental liabilities/provisions
- Closure costs/bonds
- Rehabilitation provisions
- Decommissioning obligations
- Site restoration costs
- Mine closure bonds/guarantees

PRIORITÄT 2 - WEITERE KRITISCHE FELDER:
2. GPS-Koordinaten (exakte Latitude/Longitude)
3. Eigentümer und Betreiber (aktuelle Struktur)
4. Produktionsdaten (Jahresproduktion, Start/Ende)
5. Rohstoffe und Minentyp

SUCHE SPEZIFISCH NACH:
- Geschäftsberichten (Annual Reports, 10-K, NI 43-101)
- ESG-Berichten (Environmental, Social, Governance)
- Behördendokumenten (Umweltgenehmigungen)
- Börsenunterlagen (SEDAR, SEC filings)

NUTZE DIESE VERIFIZIERTEN QUELLEN:"""
        
        # Füge Top-Quellen hinzu
        for i, source in enumerate(sources[:10], 1):
            query += f"\n[{i}] {source.get('url', source.get('value', ''))}"
        
        query += f"\n\nBITTE EXTRAHIERE ALLE VERFÜGBAREN DATEN im strukturierten Format."
        
        return query
    
    def build_phase3_query(self, mine_name: str, country: str, region: str,
                          commodity: str, current_data: Dict, sources: List) -> str:
        """Erstelle hochspezialisierte Query für Phase 3"""
        
        # Identifiziere fehlende Felder
        missing_fields = []
        critical_missing = []
        
        for field in ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 
                     'Eigentümer', 'Betreiber', 'Produktionsstart', 'Produktionsende']:
            if not current_data.get(field):
                missing_fields.append(field)
                if field in ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate']:
                    critical_missing.append(field)
        
        query = f"""ULTRA-DEEP RESEARCH für {mine_name}

KRITISCH FEHLENDE DATEN:
{', '.join(critical_missing)}

BEREITS GEFUNDENE DATEN (nicht wiederholen):
"""
        
        for field, value in current_data.items():
            if value:
                query += f"- {field}: {value}\n"
        
        query += f"""

SPEZIFISCHER FOKUS FÜR RESTAURATIONSKOSTEN:
1. Suche nach Finanzberichten mit ESG/Environmental-Sektionen
2. Prüfe Regierungsdatenbanken für Umweltgenehmigungen
3. Analysiere Börsenunterlagen für ARO/Environmental Provisions
4. Nutze mehrsprachige Suche (Englisch, Französisch, Spanisch, lokale Sprachen)
5. Fokus auf Millionen-/Tausender-Beträge mit Währungsangaben
3. Prüfe HISTORISCHE DOKUMENTE und Archive
4. Konsultiere SPEZIALISIERTE Mining-Datenbanken
5. Analysiere REGIERUNGSDOKUMENTE und offizielle Berichte

BEREITS GEPRÜFTE QUELLEN (suche ANDERE):
"""
        
        for i, source in enumerate(sources[:10], 1):
            query += f"[{i}] {source.get('url', source.get('value', ''))}\n"
        
        query += """

VERWENDE ALTERNATIVE SUCHMETHODEN für fehlende Daten!"""
        
        return query
    
    def build_source_sharing_query(self, mine_name: str, country: str, region: str,
                                  commodity: str, sources: List[Dict]) -> str:
        """Erstelle Query für Source-Sharing Phase 2"""
        
        query = f"""PHASE 2: DETAILLIERTE DATENEXTRAKTION aus verifizierten Quellen

Mine: {mine_name}
Land: {country}
Region: {region}
Rohstoff: {commodity}

AUFGABE: Extrahiere ALLE verfügbaren Daten aus den folgenden {len(sources)} verifizierten Quellen.
Fokussiere besonders auf numerische Daten, Koordinaten und Restaurationskosten.

VERIFIZIERTE QUELLEN:
"""
        
        # Gruppiere Quellen nach Typ
        url_sources = [s for s in sources if s.get('type') in ['url', 'website']]
        doc_sources = [s for s in sources if s.get('type') == 'document']
        org_sources = [s for s in sources if s.get('type') == 'organization']
        
        if url_sources:
            query += f"\n\nWEBSEITEN ({len(url_sources)}):\n"
            for i, source in enumerate(url_sources[:15], 1):
                query += f"[{i}] {source.get('value', '')} - {source.get('title', '')}\n"
        
        if doc_sources:
            query += f"\n\nDOKUMENTE ({len(doc_sources)}):\n"
            for i, source in enumerate(doc_sources[:10], 1):
                query += f"[D{i}] {source.get('value', '')} - {source.get('title', '')}\n"
        
        if org_sources:
            query += f"\n\nORGANISATIONEN ({len(org_sources)}):\n"
            for i, source in enumerate(org_sources[:5], 1):
                query += f"[O{i}] {source.get('value', '')}\n"
        
        query += """

EXTRAKTIONS-PRIORITÄTEN:
1. GPS-Koordinaten (auch aus Karten oder technischen Berichten)
2. Restaurationskosten / ARO / Closure Costs (mit Jahr)
3. Eigentümer und Betreiber (aktuelle Struktur)
4. Produktionsdaten (Start, Ende, Jahresproduktion)
5. Technische Details (Minentyp, Fläche)

WICHTIG: Nutze ALLE angegebenen Quellen für maximale Datenabdeckung!"""
        
        return query
    
    def calculate_average_coverage(self, results: List[Dict]) -> float:
        """Berechne durchschnittliche Datenabdeckung"""
        if not results:
            return 0.0
            
        total_coverage = 0
        valid_results = 0
        
        for result in results:
            if result.get('success') and result.get('data'):
                data = result['data']
                filled = sum(1 for v in data.values() if v and v != '-')
                total = len(data)
                if total > 0:
                    coverage = (filled / total) * 100
                    total_coverage += coverage
                    valid_results += 1
        
        return total_coverage / valid_results if valid_results > 0 else 0.0