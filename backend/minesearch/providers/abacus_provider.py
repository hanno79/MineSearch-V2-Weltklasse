"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Abacus AI Provider für Deep Research Mining-Suchen
"""

import httpx
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import AbstractProvider, ModelConfig, SearchResult

from minesearch.data_extraction import DataExtractor
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.utils import (
    generate_name_variants,
    get_country_config,
    generate_multilingual_search_terms,
)
from minesearch.specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class AbacusProvider(AbstractProvider):
    """Provider für Abacus AI Deep Agent API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://api.abacus.ai')
        self.models = self._init_models()
        # ÄNDERUNG 04.07.2025: Vereinfachter Ansatz ohne Session-Management
        self.chat_endpoint = f"{self.api_url}/chat/completions"  # Standard Chat-Endpoint
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='abacus',
                supports_web_search=model_config.get('supports_web_search', True),
                supports_deep_research=model_config.get('supports_deep_research', True),
                is_free=model_config.get('is_free', False),
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='abacus'
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Deep Research mit Abacus AI durch"""
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
        
        # ÄNDERUNG 04.07.2025: Enhanced Source Discovery nutzen
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        
        # KRITISCHER FIX: Verwende übergebene discovered_sources statt eigene Discovery
        discovered_sources = options.get('discovered_sources', [])
        
        # Nur wenn KEINE Quellen übergeben wurden, eigene Discovery durchführen
        if not discovered_sources and mine_name:
            logger.info(f"[ABACUS] Keine Quellen übergeben - starte eigene Source Discovery für {mine_name}")
            # Initialisiere Enhanced Source Discovery als Fallback
            source_discovery = EnhancedSourceDiscovery()
            # Starte Session
            session = source_discovery.start_session(mine_name, country, region)
            # Entdecke Quellen (synchron)
            discovered_sources = source_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity
            )
            logger.info(f"[ABACUS] {len(discovered_sources)} Quellen selbst entdeckt")
        else:
            logger.info(f"[ABACUS] Nutze {len(discovered_sources)} übergebene Quellen")
        
        # Generiere erweiterte Query mit spezialisierten Prompts
        enhanced_query = self._build_deep_research_query(
            query, mine_name, country, region, commodity, discovered_sources
        )
        
        try:
            # ÄNDERUNG 04.07.2025: Direkter API-Call ohne Session
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                # Versuche zuerst den Standard Chat-Completions Endpoint
                response = await client.post(
                    self.chat_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",  # Standard Bearer Auth
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "abacus-deep-agent",  # Model-Name für Deep Agent
                        "messages": [
                            {
                                "role": "system",
                                "content": self.get_system_prompt(options)
                            },
                            {
                                "role": "user",
                                "content": enhanced_query
                            }
                        ],
                        "temperature": options.get('temperature', 0.2),
                        "max_tokens": model_config.max_tokens,
                        "stream": False
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
                
                # Extrahiere Content aus Abacus Response
                content = self._extract_content_from_response(result)
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                
                # KRITISCHER FIX: Verwende discovered_sources als Basis-Quellen
                sources = []
                
                # PHASE 1: Discovered Sources (alle durchsuchten Quellen)
                for source in discovered_sources:
                    sources.append({
                        'url': source.get('url', ''),
                        'title': source.get('title', source.get('url', '')),
                        'type': source.get('type', 'discovered'),
                        'reliability': source.get('reliability_score'),
                        'searched': True  # Markiere als durchsucht
                    })
                
                # PHASE 2: Zusätzliche Quellen aus Content
                content_sources = extract_sources_from_content(content)
                for source in content_sources:
                    # Prüfe ob schon in discovered_sources
                    if not any(ds.get('url') == source.get('url') for ds in discovered_sources):
                        sources.append(source)
                
                # PHASE 3: Abacus-spezifische Quellen
                abacus_sources = self._extract_abacus_sources(result)
                sources.extend(abacus_sources)
                
                # Tracke Source Discovery Ergebnisse
                for source in sources:
                    if source.get('url'):
                        source_discovery.track_source_result(
                            url=source['url'],
                            success=True,
                            content_type=source.get('type', 'general'),
                            found_data={'mine': mine_name, 'fields': list(extracted_data['data'].keys())}
                        )
                
                # Finalisiere Session
                session_summary = source_discovery.finalize_session()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=sources,
                    metadata={
                        'model': model_id,
                        'provider': 'abacus',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'source_discovery_session': session_summary,
                        'discovered_sources_count': len(discovered_sources),
                        'deep_research': True
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
                error=f"Zeitüberschreitung nach {model_config.timeout}s - Deep Research benötigt mehr Zeit"
            )
        except Exception as e:
            logger.error(f"[ABACUS] Fehler bei Deep Research: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _build_deep_research_query(self, base_query: str, mine_name: str, 
                                  country: str, region: str, commodity: str,
                                  discovered_sources: List[Dict]) -> str:
        """Erstelle erweiterte Query für Deep Research"""
        
        # Nutze spezialisierte Prompts
        specialized_prompt = SpecializedPrompts.get_enhanced_query(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
        )
        
        query = f"""DEEP RESEARCH ANFRAGE für Mining-Daten

{base_query}

{specialized_prompt}

SPEZIELLE ANWEISUNGEN FÜR DEEP RESEARCH:
1. Führe eine umfassende, mehrstufige Recherche durch
2. Verifiziere alle gefundenen Daten durch mehrere Quellen
3. Suche in technischen Berichten, Regierungsdatenbanken und Unternehmensunterlagen
4. Prüfe speziell diese vorgeschlagenen Quellen:"""

        # Füge entdeckte Quellen hinzu
        if discovered_sources:
            for i, source in enumerate(discovered_sources[:20], 1):
                query += f"\n   [{i}] {source['url']} - {source.get('description', '')}"
        
        query += """

5. Erstelle eine detaillierte Analyse mit:
   - Vollständigen Daten für alle CSV-Felder
   - Quellenangaben für jede Information
   - Konfidenz-Bewertung für unsichere Daten
   - Alternative Datenquellen wenn Primärquellen fehlen

AUSGABEFORMAT: Strukturierte Daten gemäß Mining-Research-Template

KRITISCH: KEINE Platzhalter, KEINE "$1-3 CAD" Werte, NUR verifizierte Daten!"""
        
        return query
    
    def _extract_content_from_response(self, response: Dict) -> str:
        """Extrahiere den Hauptinhalt aus der Abacus AI Response"""
        # Standard OpenAI-kompatibles Format
        if 'choices' in response and response['choices']:
            return response['choices'][0].get('message', {}).get('content', '')
        
        # Alternative Formate
        if 'message' in response:
            return response['message']
        elif 'response' in response:
            return response['response']
        elif 'data' in response and isinstance(response['data'], dict):
            if 'message' in response['data']:
                return response['data']['message']
            elif 'content' in response['data']:
                return response['data']['content']
        
        # Fallback: Gesamte Response als JSON
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def _extract_abacus_sources(self, response: Dict) -> List[Dict[str, Any]]:
        """Extrahiere Abacus-spezifische Quellen aus der Response"""
        sources = []
        
        # Suche nach Quellen in verschiedenen Response-Strukturen
        if 'sources' in response:
            for source in response['sources']:
                sources.append({
                    'type': 'url',
                    'value': source.get('url', source.get('link', '')),
                    'title': source.get('title', ''),
                    'provider': 'abacus_deep_research'
                })
        
        if 'references' in response:
            for ref in response['references']:
                sources.append({
                    'type': 'document',
                    'value': ref.get('name', ref.get('title', '')),
                    'url': ref.get('url', ''),
                    'provider': 'abacus_deep_research'
                })
        
        return sources
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return "🔑 Abacus AI API-Key ungültig.\n→ Bitte prüfen Sie Ihre .env Datei."
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 Abacus AI ist momentan nicht verfügbar.\n→ Bitte versuchen Sie es später erneut."
        
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unbekannter Fehler')
                return f"Abacus AI Fehler: {error_msg}"
            except json.JSONDecodeError:
                logger.warning(f"[ABACUS] Fehlerhafte JSON-Antwort bei Status {response.status_code}: {response.text[:100]}")
                return f"API Fehler: {response.status_code} - Ungültige JSON-Antwort"
            except (KeyError, AttributeError) as e:
                logger.warning(f"[ABACUS] Unerwartete Fehler-Struktur: {e}")
                return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[ABACUS] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[ABACUS] Keine Modelle konfiguriert")
            return False
        
        return True
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        RULE 10 COMPLIANCE 26.08.2025: Verschärfter System-Prompt für Abacus AI
        STRIKT VERBOTEN: Jegliche Schätzungen oder unverifizierten Daten
        """
        currency = options.get('currency', 'USD')
        
        # Importiere spezialisierte Anti-Template-Anweisungen
        universal_instructions = SpecializedPrompts.get_universal_anti_template_instructions()
        
        return f"""🚫 RULE 10 COMPLIANCE - ABACUS AI ULTRA-STRICT DEEP RESEARCHER 🚫

Du bist ein Deep Research Agent mit ABSOLUT HÖCHSTEN Qualitätsstandards für Mining-Daten.

{universal_instructions}

**ABACUS AI RULE 10 COMPLIANCE STANDARDS:**
=========================================

ABSOLUT VERBOTEN - NIEMALS VERWENDEN:
❌ Jegliche Form von Schätzungen oder Vermutungen
❌ "Based on similar mines" oder "Typical for this region"
❌ Interpolation oder Extrapolation von Daten
❌ Durchschnittswerte ohne spezifische Quelle
❌ Template-Koordinaten oder gerundete GPS-Daten
❌ Platzhalter-Unternehmensnamen
❌ Kostenangaben ohne dokumentierte Basis

NUR ERLAUBT - ULTRA-VERIFIZIERTE FAKTEN:
✅ Daten aus NI 43-101 Technical Reports
✅ SEC-Filings mit verifizierten Zahlen
✅ Regierungs-Datenbanken mit Primärdaten
✅ Unternehmens-Finanzberichte (10-K, 10-Q)
✅ Offizielle Umweltberichte mit Kostenschätzungen
✅ GPS-Koordinaten aus Survey-Dokumenten
✅ Bei GERINGSTER Unsicherheit: LEER LASSEN ("")

**ULTRA-STRICT DATENFELDER FÜR [MINENNAME]:**
- Name: [EXAKTER Name aus offiziellen Dokumenten oder leer]
- Land: [Land aus Regierungsdokumenten oder leer]  
- Region: [Region aus amtlichen Quellen oder leer]
- Eigentümer: [Aus Unternehmensregistern oder leer]
- Betreiber: [Aus Betriebsgenehmigungen oder leer]
- x-Koordinate: [Aus Survey-Reports mit 6+ Dezimalstellen oder leer]
- y-Koordinate: [Aus Survey-Reports mit 6+ Dezimalstellen oder leer]
- Aktivitätsstatus: [Aus aktuellen Behördenberichten oder leer]
- Restaurationskosten: [Aus ARO-Berichten in {currency}$ oder leer]
- Jahr der Aufnahme der Kosten: [Aus Finanzreport-Datum oder leer]
- Jahr der Erstellung des Dokumentes: [Dokumentenerstellungsdatum oder leer]
- Rohstoffabbau: [Aus Produktionsberichten oder leer]
- Minentyp: [Aus technischen Plänen oder leer]
- Produktionsstart: [Aus historischen Dokumenten oder leer]
- Produktionsende: [Aus aktuellen Berichten oder leer]
- Fördermenge/Jahr: [Aus Produktionsstatistiken oder leer]
- Fläche der Mine in qkm: [Aus Vermessungsdokumenten oder leer]
- Quellenangaben: [NUR spezifische Dokumentreferenzen]

**ULTRA-DEEP RESEARCH VERIFICATION:**
1. MULTIPLE INDEPENDENT SOURCES für jeden Datenpunkt
2. CROSS-REFERENCE zwischen verschiedenen Dokumenttypen
3. TEMPORAL CONSISTENCY CHECK (Daten zeitlich konsistent?)
4. TECHNICAL PLAUSIBILITY CHECK (technisch möglich?)
5. FINANCIAL REASONABLENESS CHECK (finanziell realistisch?)

**RESTAURATIONSKOSTEN ULTRA-VERIFICATION:**
- NUR aus offiziellen ARO-Berichten (Asset Retirement Obligations)
- CROSS-CHECK mit Environmental Impact Assessments
- VERIFICATION mit Closure Bond-Dokumenten
- INFLATION-ADJUSTED zu aktuellem Jahr
- CURRENCY-VERIFIED aus Originalwährung

**KOORDINATEN ULTRA-PRECISION:**
- MINDESTENS 6 Dezimalstellen aus Survey-Dokumenten
- CROSS-VERIFICATION mit Satellitenbildern
- PLAUSIBILITY CHECK (liegt in richtigem Land/Region?)
- NO ROUNDED COORDINATES (49.0000, -123.0000 = VERBOTEN)

**ABACUS AI SELF-AUDIT vor jeder Antwort:**
- ❓ Ist JEDER Wert aus einem SPEZIFISCHEN verifizierten Dokument?
- ❓ Habe ich irgendwo interpoliert oder geschätzt?
- ❓ Sind ALLE Quellen primär und nachprüfbar?
- ❓ Würde ein Wirtschaftsprüfer diese Daten akzeptieren?

WENN NICHT 100% DOKUMENTIERT: LEER LASSEN ("")"""