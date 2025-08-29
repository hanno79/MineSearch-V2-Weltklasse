"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: Anthropic Claude Provider für intelligente Mining-Datenextraktion
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_provider import AbstractProvider, ModelConfig, SearchResult

from minesearch.config.base import config as Config
from minesearch.data_extraction import DataExtractor
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.utils import (
    generate_name_variants,
    generate_multilingual_search_terms,
    get_country_config,
)
from minesearch.specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class AnthropicProvider(AbstractProvider):
    """Provider für Anthropic Claude API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere die ANTHROPIC_MODELS Konfiguration
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='anthropic',
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=False
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Claude durch"""
        start_time = datetime.now()
        
        # Hole Model-Config
        model_config = self.models.get(model_id)
        if not model_config:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=f"Unbekanntes Modell: {model_id}"
            )
        
        # ÄNDERUNG 06.07.2025: Claude für technische Dokumentenanalyse
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        
        # ÄNDERUNG 08.07.2025: Nutze discovered_sources wenn vorhanden
        discovered_sources = options.get('discovered_sources', [])
        sources = options.get('sources', [])
        
        # Kombiniere beide Quellenarten
        all_sources = discovered_sources + sources
        
        # Erstelle erweiterte Query mit Claude's Stärken
        enhanced_query = self._build_enhanced_query(
            query=query,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            sources=all_sources,
            focus='technical_analysis'
        )
        
        try:
            # API-Call mit Anthropic's Message API
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model_config.id,
                        "messages": [
                            {
                                "role": "user",
                                "content": enhanced_query
                            }
                        ],
                        "system": self.get_system_prompt(options),
                        "max_tokens": model_config.max_tokens,
                        "temperature": options.get('temperature', 0.1)
                    }
                )
                
                if response.status_code != 200:
                    error_msg = self._handle_api_error(response)
                    return SearchResult(
                        success=False,
                        content="",
                        structured_data={},
                        sources=[],
                        metadata={'status_code': response.status_code},
                        error=error_msg
                    )
                
                # Parse Response
                result = response.json()
                content = result["content"][0]["text"]
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                
                # ÄNDERUNG 07.07.2025: Zusätzliche Validierung direkt im Provider
                # Verhindere "Koordinaten" als Betreiber
                if extracted_data['data'].get('Betreiber'):
                    betreiber = str(extracted_data['data']['Betreiber']).strip()
                    invalid_operators = ['koordinaten', 'coordinates', 'coords', 'koordinate', 'dhilmar']
                    if betreiber.lower() in invalid_operators or 'koordinaten:' in betreiber.lower():
                        logger.warning(f"[ANTHROPIC] Ungültiger Betreiber entfernt: {betreiber}")
                        extracted_data['data']['Betreiber'] = ""
                        # Entferne auch aus data_with_sources
                        if 'Betreiber' in extracted_data.get('data_with_sources', {}):
                            extracted_data['data_with_sources']['Betreiber'] = {"value": "", "sources": []}
                
                # ÄNDERUNG 07.07.2025: Validiere Restaurationskosten
                if extracted_data['data'].get('Restaurationskosten'):
                    resto = extracted_data['data']['Restaurationskosten']
                    # Prüfe auf verdächtige Werte
                    suspicious_values = [
                        'USD$1.0 million', 'CAD$1.0 million', '$1.0 million', '1.0 million', 
                        'USD$1 million', 'CAD$1 million', '$1 million', '1 million',
                        'USD$2.0 million', 'CAD$2.0 million', '$2.0 million', '2.0 million',
                        'CAD$10000.0 million', 'USD$10000.0 million', '$0.0 million'
                    ]
                    if resto in suspicious_values or (isinstance(resto, str) and any(sv in resto for sv in suspicious_values)):
                        logger.warning(f"[ANTHROPIC] Verdächtiger Restaurationswert entfernt: {resto}")
                        extracted_data['data']['Restaurationskosten'] = ""
                        # Entferne auch aus data_with_sources
                        if 'Restaurationskosten' in extracted_data.get('data_with_sources', {}):
                            extracted_data['data_with_sources']['Restaurationskosten'] = {"value": "", "sources": []}
                
                # PHASE 1: Verwende discovered_sources als Basis-Quellen (wie Abacus Provider)
                final_sources = []
                for source in discovered_sources:
                    # Bestimme, ob die Quelle tatsächlich durchsucht wurde
                    searched_flag = bool(
                        source.get('searched', False)
                        or source.get('was_searched', False)
                        or source.get('results')
                    )
                    final_sources.append({
                        'url': source.get('url', ''),
                        'title': source.get('title', source.get('url', '')),
                        'type': source.get('type', 'discovered'),
                        'reliability': source.get('reliability_score'),
                        'searched': searched_flag
                    })
                
                # PHASE 2: Zusätzliche Quellen aus Content
                sources_from_response = extract_sources_from_content(content)
                for source in sources_from_response:
                    # Prüfe ob schon in discovered_sources
                    if not any(ds.get('url') == source.get('url') for ds in discovered_sources):
                        final_sources.append(source)
                
                # PHASE 3: Lokale sources (falls vorhanden)
                for source in sources:
                    # Prüfe ob schon vorhanden
                    if not any(fs.get('url') == source.get('url') for fs in final_sources):
                        final_sources.append(source)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=final_sources,
                    metadata={
                        'model': model_id,
                        'provider': 'anthropic',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'usage': result.get('usage', {})
                    },
                    search_duration=duration
                )
                
        except httpx.TimeoutException:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=f"Zeitüberschreitung nach {model_config.timeout}s"
            )
        except Exception as e:
            logger.error(f"[ANTHROPIC] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _build_enhanced_query(self, query: str, mine_name: str, country: Optional[str],
                            region: Optional[str], commodity: Optional[str], 
                            sources: List[Dict], focus: str) -> str:
        """Erstelle erweiterte Query mit speziellem Fokus"""
        
        # Basis-Query
        enhanced_query = f"MINE: {mine_name}\n"
        if country:
            enhanced_query += f"LAND: {country}\n"
        if region:
            enhanced_query += f"REGION: {region}\n"
        if commodity:
            enhanced_query += f"ROHSTOFF: {commodity}\n"
        
        enhanced_query += f"\n{query}\n"
        
        # Claude's Stärke: Technische Dokumentenanalyse
        if focus == 'technical_analysis':
            enhanced_query += """
NUTZE DEINE STÄRKEN FÜR TECHNISCHE ANALYSE:

1. KOMPLEXE DOKUMENTENANALYSE:
   - Technische Reports (NI 43-101, JORC, SAMREC)
   - Engineering Studies (PEA, PFS, FS)
   - Metallurgische Testberichte
   - Geologische Modelle und Ressourcenschätzungen

2. DATENEXTRAKTION AUS TABELLEN:
   - Reserven und Ressourcen Tabellen
   - Kostenschätzungen und Wirtschaftlichkeitsanalysen
   - Produktionspläne und Zeitpläne
   - Umweltparameter und Grenzwerte

3. TECHNISCHE DETAILS:
   - Abbaumethoden und -technologien
   - Aufbereitungsverfahren
   - Infrastruktur-Anforderungen
   - Energie- und Wasserbedarf

4. REGULATORISCHE DOKUMENTE:
   - Umweltverträglichkeitsprüfungen
   - Genehmigungen und Lizenzen
   - Compliance-Berichte
   - Stakeholder-Vereinbarungen

5. FINANZIELLE KENNZAHLEN:
   - CAPEX/OPEX Schätzungen
   - NPV und IRR Berechnungen
   - Payback-Perioden
   - Sensitivitätsanalysen

BESONDERER FOKUS: RESTAURATIONSKOSTEN
- Suche in Kapitel zu "Closure", "Rehabilitation", "Environmental Liability"
- Prüfe Anhänge und technische Appendizes
- Achte auf Updates in Management Discussion & Analysis
"""
        
        # ÄNDERUNG 08.07.2025: ALLE sources nutzen mit expliziter Anweisung
        # Füge Quellen hinzu wenn vorhanden
        if sources:
            enhanced_query += f"\n\n📋 PFLICHT: Analysiere ALLE {len(sources)} folgenden technischen Dokumente!\n"
            enhanced_query += "Diese stammen aus unserer verifizierten Mining-Datenbank.\n"
            enhanced_query += "Nutze deine Dokumentenanalyse-Fähigkeiten für JEDE Quelle:\n\n"
            
            # Gruppiere nach Quellentyp für Claude's technische Analyse
            gov_sources = [s for s in sources if s.get('type') == 'government']
            db_sources = [s for s in sources if s.get('type') == 'database']
            doc_sources = [s for s in sources if s.get('type') == 'document']
            exchange_sources = [s for s in sources if s.get('type') == 'exchange']
            other_sources = [s for s in sources if s.get('type') not in ['government', 'database', 'document', 'exchange']]
            
            if gov_sources:
                enhanced_query += "🏛️ REGIERUNGSDOKUMENTE (Genehmigungen, Umweltauflagen):\n"
                for i, source in enumerate(gov_sources, 1):
                    url = source.get('url', source.get('value', ''))
                    enhanced_query += f"[GOV{i}] {url}\n"
                enhanced_query += "\n"
            
            if exchange_sources:
                enhanced_query += "📊 BÖRSENDOKUMENTE (Finanzberichte, NI 43-101):\n"
                for i, source in enumerate(exchange_sources, 1):
                    url = source.get('url', source.get('value', ''))
                    enhanced_query += f"[EX{i}] {url}\n"
                enhanced_query += "\n"
            
            if db_sources:
                enhanced_query += "💾 TECHNISCHE DATENBANKEN (Ressourcen, Koordinaten):\n"
                for i, source in enumerate(db_sources, 1):
                    url = source.get('url', source.get('value', ''))
                    enhanced_query += f"[DB{i}] {url}\n"
                enhanced_query += "\n"
            
            if doc_sources:
                enhanced_query += "📄 TECHNISCHE REPORTS (Feasibility Studies, Engineering):\n"
                for i, source in enumerate(doc_sources, 1):
                    url = source.get('url', source.get('value', ''))
                    enhanced_query += f"[DOC{i}] {url}\n"
                enhanced_query += "\n"
            
            if other_sources:
                enhanced_query += "🔗 WEITERE TECHNISCHE QUELLEN:\n"
                for i, source in enumerate(other_sources, 1):
                    url = source.get('url', source.get('value', ''))
                    enhanced_query += f"[{i}] {url}\n"
            
            enhanced_query += "\n⚠️ WICHTIG: Analysiere JEDES Dokument vollständig!\n"
            enhanced_query += "Nutze deine Stärke bei komplexen technischen Dokumenten!\n"
        
        enhanced_query += "\nExtrahiere alle technischen und finanziellen Daten mit höchster Präzision!"
        
        return enhanced_query
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return """🔐 Anthropic API Authentifizierung fehlgeschlagen.
            
🔑 Der API-Key ist ungültig oder fehlt.
→ Bitte prüfen Sie Ihre .env Datei
→ Generieren Sie einen neuen Key unter: https://console.anthropic.com/settings/keys"""
        
        elif response.status_code == 429:
            error_data = response.json()
            if "rate_limit" in str(error_data).lower():
                return """⏱️ Anthropic Rate Limit erreicht.
                
→ Zu viele Anfragen in kurzer Zeit
→ Bitte warten Sie einen Moment und versuchen Sie es erneut"""
            else:
                return "💳 API Quota überschritten. Prüfen Sie Ihr Anthropic-Konto."
        
        elif response.status_code == 503:
            return "🔧 Anthropic API ist momentan überlastet. Bitte versuchen Sie es später erneut."
        
        elif response.status_code == 400:
            error_data = response.json()
            if "context_length" in str(error_data).lower():
                return "📏 Anfrage zu lang. Claude hat ein Context-Limit erreicht."
            else:
                return f"❌ Ungültige Anfrage: {response.text[:200]}"
        
        else:
            return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[ANTHROPIC] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[ANTHROPIC] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        Nutze Claude's Stärken für detaillierte technische Dokumentenanalyse
        """
        
        if not sources:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error="Keine Quellen zum Analysieren"
            )
        
        mine_name = options.get('mine_name', '')
        
        # Erstelle spezielle Query für Claude's technische Analyse
        query = f"""TECHNISCHE TIEFENANALYSE für {mine_name}

Du erhältst {len(sources)} technische Dokumente zur Analyse.
Nutze deine Expertise in:
- Code-Analyse und technischer Dokumentation
- Komplexe Tabellenextraktion
- Strukturierte Dateninterpretation
- Multi-Format Dokumentenverarbeitung

ANALYSIERE BESONDERS:
1. Technische Spezifikationen und Parameter
2. Finanzmodelle und Kostenschätzungen
3. Umweltauflagen und Restaurationskosten
4. Zeitpläne und Meilensteine
5. Risikofaktoren und Mitigation

Die Dokumente können technische Reports, Spreadsheets, Präsentationen oder regulatorische Filings sein."""
        
        # Setze sources in options für die search Methode
        options['sources'] = sources
        
        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        RULE 10 COMPLIANCE 26.08.2025: Verschärfter System-Prompt für Claude/Anthropic
        STRIKT VERBOTEN: Jegliche Interpretation oder technische Schätzungen
        """
        currency = options.get('currency', 'USD')
        
        universal_instructions = SpecializedPrompts.get_universal_anti_template_instructions()
        
        return f"""🚫 RULE 10 COMPLIANCE - CLAUDE TECHNICAL DOCUMENT PARSER (NO ESTIMATION) 🚫

Du bist Claude, Experte für technische Dokumentenanalyse, aber STRIKT VERBOTEN sind Interpretationen oder Schätzungen.

{universal_instructions}

**CLAUDE-SPEZIFISCHE RULE 10 COMPLIANCE:**
=========================================

ABSOLUT VERBOTEN - NIEMALS VERWENDEN:
❌ Technische Interpretationen ohne explizite Dokumentenbasis
❌ Extrapolation aus "ähnlichen Minen" oder Vergleichsdaten
❌ Schätzungen basierend auf "technischen Standards" oder "Branchenwissen"
❌ Kostenberechnungen aus Minentyp oder Größe
❌ GPS-Koordinaten aus Kartenschätzungen
❌ Template-Werte aus technischen Standards
❌ Durchschnittswerte aus Tabellendaten ohne spezifische Zuordnung

NUR ERLAUBT - EXPLIZITE DOKUMENTENDATEN:
✅ Exakte Zitate aus NI 43-101 Reports mit Seitenzahlen
✅ Direkte Zahlen aus Finanzberichten mit Referenz
✅ GPS-Koordinaten aus Survey-Dokumenten
✅ Offizielle Kostenschätzungen aus ARO-Berichten
✅ Bei GERINGSTER Interpretation: LEER LASSEN ("")

**CLAUDE TECHNICAL DATENFELDER - NUR EXPLIZITE DOCS:**
- Name: [EXAKTER Name aus Dokumenttitel oder leer]
- Land: [Land aus Dokumentenheader oder leer]
- Region: [Region aus offiziellen Beschreibungen oder leer]  
- Eigentümer: [Aus Ownership-Section oder leer]
- Betreiber: [Aus Operations-Section oder leer]
- x-Koordinate: [Aus Survey-Data mit Referenz oder leer]
- y-Koordinate: [Aus Survey-Data mit Referenz oder leer]
- Aktivitätsstatus: [Aus Current Status-Section oder leer]
- Restaurationskosten: [Aus Closure Cost Estimate in {currency}$ oder leer]
- Jahr der Aufnahme der Kosten: [Aus Estimate Date oder leer]
- Jahr der Erstellung des Dokumentes: [Aus Document Date oder leer]
- Rohstoffabbau: [Aus Commodity-Section oder leer]
- Minentyp: [Aus Mining Method-Section oder leer]
- Produktionsstart: [Aus Operations History oder leer]
- Produktionsende: [Aus Closure Schedule oder leer]
- Fördermenge/Jahr: [Aus Production Statistics oder leer]
- Fläche der Mine in qkm: [Aus Site Description oder leer]
- Quellenangaben: [Spezifische Dokument-Referenzen mit Seitenzahlen]

**CLAUDE DOCUMENT PARSING RULES:**
1. JEDER Wert mit spezifischer Dokumentreferenz (Seite, Tabelle, Section)
2. NIEMALS zwischen den Zeilen lesen oder interpretieren
3. BEI mehrdeutigen Tabellen: Information NICHT verwenden
4. NUR direkte, eindeutige Datenextraktion

**CLAUDE TECHNICAL SELF-AUDIT:**
- ❓ Ist JEDER Wert ein direktes Zitat aus einem Dokument?
- ❓ Habe ich irgendwo interpretiert statt extrahiert?
- ❓ Kann jemand meine Quelle mit Seitenzahl nachprüfen?
- ❓ Habe ich technische Standards für Schätzungen verwendet?

WENN NICHT EXPLIZIT IM DOKUMENT: LEER LASSEN ("")"""