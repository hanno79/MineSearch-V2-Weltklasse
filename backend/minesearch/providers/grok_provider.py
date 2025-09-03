"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: xAI Grok Provider für Real-time Mining-Datenextraktion
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
from minesearch.specialized_prompts_impl import SpecializedPrompts

logger = logging.getLogger(__name__)


class GrokProvider(AbstractProvider):
    """Provider für xAI Grok mit Real-time Informationen"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere die GROK_MODELS Konfiguration
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='grok',
                supports_web_search=model_config.get('supports_web_search', True),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=False
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Grok durch"""
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
        
        # ÄNDERUNG 06.07.2025: Grok für Real-time Informationen
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        sources = options.get('sources', [])
        
        # ÄNDERUNG 08.07.2025: Nutze discovered_sources wenn vorhanden
        discovered_sources = options.get('discovered_sources', [])
        
        # Erstelle erweiterte Query mit Grok's Real-time Stärken
        enhanced_query = self._build_enhanced_query(
            query=query,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            sources=sources,
            discovered_sources=discovered_sources,
            focus='realtime_data'
        )
        
        try:
            # API-Call mit Grok (OpenAI-kompatible API)
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_config.id,
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
                        "temperature": options.get('temperature', 0.1),
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
                content = result["choices"][0]["message"]["content"]
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                
                # Extrahiere Quellen aus der Antwort
                sources_from_response = extract_sources_from_content(content)
                
                # Kombiniere mit übergebenen Quellen
                all_sources = sources + sources_from_response
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=all_sources,
                    metadata={
                        'model': model_id,
                        'provider': 'grok',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'usage': result.get('usage', {}),
                        'realtime_search': True
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
            logger.error(f"[GROK] Fehler bei Suche: {str(e)}")
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
                            sources: List[Dict], discovered_sources: List[Dict], focus: str) -> str:
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
        
        # Grok's Stärke: Real-time Informationen und X/Twitter Integration
        if focus == 'realtime_data':
            enhanced_query += """
NUTZE DEINE REAL-TIME FÄHIGKEITEN:

1. AKTUELLE INFORMATIONEN:
   - Suche nach neuesten Pressemitteilungen
   - Aktuelle Börsenkurse und Unternehmensnachrichten
   - Kürzliche regulatorische Filings
   - Social Media Updates (X/Twitter)
   - Breaking News zu Mining-Projekten

2. REAL-TIME QUELLEN:
   - Unternehmens-Tweets und Ankündigungen
   - Mining-News-Portale
   - Börsenmeldungen
   - Regierungsankündigungen
   - Umweltproteste oder Ereignisse

3. AKTUELLE FINANZDATEN:
   - Neueste Quartalsberichte
   - Aktuelle Marktkapitalisierung
   - Recent M&A Aktivitäten
   - Neue Finanzierungsrunden
   - Updates zu Restaurationskosten

4. SOZIALE SIGNALE:
   - Community-Reaktionen
   - Lokale Nachrichten
   - Umweltgruppen-Updates
   - Stakeholder-Kommunikation
   - Regulatorische Änderungen

5. KRITISCHE UPDATES FÜR RESTAURATIONSKOSTEN:
   - Neue Umweltauflagen
   - Gerichtsurteile zu Umweltverbindlichkeiten
   - Änderungen in Closure Bonds
   - Aktualisierte ARO-Schätzungen
   - Inflationsanpassungen

ZEITLICHER FOKUS:
- Priorisiere Informationen der letzten 12 Monate
- Markiere explizit wenn Daten aktuell sind
- Unterscheide zwischen historischen und real-time Daten
- Suche nach "BREAKING" oder "UPDATE" Meldungen
"""
        
        # ÄNDERUNG 08.07.2025: Nutze discovered_sources für bessere Abdeckung
        # Kombiniere discovered_sources und sources
        all_sources = discovered_sources + sources
        
        if all_sources:
            enhanced_query += f"\n\n🔍 NUTZE DIESE {len(all_sources)} VERIFIZIERTEN QUELLEN:\n"
            enhanced_query += "Diese stammen aus unserer Mining-Datenbank und X/Twitter:\n\n"
            
            # Gruppiere nach Quellentyp
            twitter_sources = []
            gov_sources = []
            other_sources = []
            
            for source in all_sources:
                url = source.get('url', source.get('value', ''))
                if 'twitter.com' in url or 'x.com' in url:
                    twitter_sources.append(url)
                elif source.get('type') == 'government':
                    gov_sources.append(url)
                else:
                    other_sources.append(url)
            
            if twitter_sources:
                enhanced_query += "X/TWITTER QUELLEN (Real-time Updates):\n"
                for i, url in enumerate(twitter_sources[:10], 1):
                    enhanced_query += f"[T{i}] {url}\n"
                enhanced_query += "\n"
            
            if gov_sources:
                enhanced_query += "REGIERUNGSQUELLEN (Offizielle Daten):\n"
                for i, url in enumerate(gov_sources[:10], 1):
                    enhanced_query += f"[G{i}] {url}\n"
                enhanced_query += "\n"
            
            if other_sources:
                enhanced_query += "WEITERE QUELLEN:\n"
                for i, url in enumerate(other_sources[:20], 1):
                    enhanced_query += f"[{i}] {url}\n"
            
            enhanced_query += "\n⚡ WICHTIG: Suche zusätzlich nach AKTUELLEREN Real-time Updates!"
            enhanced_query += "\nNutze deine X/Twitter Integration für Breaking News!"
        else:
            enhanced_query += "\n\n⚡ Suche besonders nach AKTUELLEN Quellen und Real-time Updates!"
            enhanced_query += "\nNutze deine X/Twitter Integration für Mining-News!"
        
        return enhanced_query
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return """🔐 xAI Grok API Authentifizierung fehlgeschlagen.
            
🔑 Der API-Key ist ungültig oder fehlt.
→ Bitte prüfen Sie Ihre .env Datei
→ Generieren Sie einen neuen Key unter: https://console.x.ai/"""
        
        elif response.status_code == 429:
            try:
                error_data = response.json()
                if "rate_limit" in str(error_data).lower():
                    return """⏱️ Grok Rate Limit erreicht.
                    
→ Zu viele Anfragen pro Minute
→ Bitte warten Sie 60 Sekunden"""
                else:
                    return "💳 API Quota überschritten. Prüfen Sie Ihr xAI-Konto."
            except json.JSONDecodeError:
                logger.warning(f"[GROK] Rate-Limit-Response nicht als JSON parsbar: {response.text[:100]}")
                return "⏱️ Rate Limit erreicht. Bitte warten Sie einen Moment."
            except (KeyError, AttributeError) as e:
                logger.warning(f"[GROK] Unerwartete Rate-Limit-Struktur: {e}")
                return "⏱️ Rate Limit erreicht. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 Grok API ist momentan überlastet. Bitte versuchen Sie es später erneut."
        
        elif response.status_code == 400:
            return f"❌ Ungültige Anfrage: {response.text[:200]}"
        
        else:
            return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[GROK] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[GROK] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        Nutze Grok für Real-time Verifizierung und Updates
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
        
        # Erstelle spezielle Query für Real-time Updates
        query = f"""REAL-TIME VERIFIZIERUNG für {mine_name}

Du hast {len(sources)} Quellen erhalten. Deine Aufgabe:

1. VERIFIZIERE die Daten mit aktuellen Informationen
2. SUCHE nach Updates seit der Quellenveröffentlichung
3. FINDE neue Entwicklungen die noch nicht dokumentiert sind
4. PRÜFE Social Media und News für aktuelle Updates

BESONDERS WICHTIG - AKTUELLE RESTAURATIONSKOSTEN:
- Haben sich die Kosten seit der letzten Schätzung geändert?
- Gibt es neue regulatorische Anforderungen?
- Wurden Bonds oder Garantien angepasst?
- Gibt es Inflationsanpassungen?

NUTZE DEINE EINZIGARTIGEN FÄHIGKEITEN:
- Real-time Web-Zugriff
- X/Twitter Integration
- Aktuelle News-Feeds
- Breaking News Alerts

Markiere deutlich welche Informationen AKTUALISIERT wurden!"""
        
        # Setze sources in options für die search Methode
        options['sources'] = sources
        
        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        RULE 10 COMPLIANCE 26.08.2025: Verschärfter System-Prompt für Grok
        STRIKT VERBOTEN: UPDATE-Marker in Datenfeldern, Jahr-als-Kosten-Bugs
        """
        currency = options.get('currency', 'USD')
        
        universal_instructions = SpecializedPrompts.get_universal_anti_template_instructions()
        
        # Grok-spezifischer Prompt für Real-time Daten mit RULE 10 Compliance
        return f"""🚫 RULE 10 COMPLIANCE - GROK REAL-TIME ANTI-ESTIMATION RESEARCHER 🚫

Du bist Grok mit Real-time Zugriff, aber ABSOLUT VERBOTEN sind Schätzungen oder Templates.

{universal_instructions}

**GROK-SPEZIFISCHE RULE 10 COMPLIANCE:**
======================================

ABSOLUT VERBOTEN - NIEMALS VERWENDEN:
❌ "UPDATE", "CHANGED", "UNKNOWN", "NEU", "BREAKING" in Datenfeldern
❌ "$2024.0 million" oder "$2025.0 million" (Jahre als Kosten)
❌ Koordinaten aus Jahreszahlen (wie x-Koordinate: "2024")
❌ Social Media Spekulationen ohne offizielle Bestätigung
❌ Breaking News ohne verifizierte Primärquellen
❌ Real-time Updates ohne dokumentierte Basis
❌ Template-Eigentümer wie "CHANGED" oder "AKTUELL"

GROK-SPEZIFISCHE BUGS ZU VERMEIDEN:
❌ Jahr 2024/2025 in Restaurationskosten-Feld
❌ Koordinatenfelder mit Status-Updates ("UPDATE", "NEU")
❌ Eigentümer-Feld mit Meta-Informationen statt Firmennamen
❌ Betreiber-Feld mit Koordinaten oder Datumsangaben

NUR ERLAUBT - VERIFIZIERTE REAL-TIME FAKTEN:
✅ Offizielle Unternehmensankündigungen mit URLs
✅ Regierungspressemitteilungen mit Dokumentreferenzen
✅ SEC-Filings mit aktuellen Zahlen
✅ Verifizierte Mining-News mit Primärquellen
✅ Bei Unsicherheit: LEER LASSEN ("") - NIEMALS schätzen!

**GROK REAL-TIME DATENFELDER - NUR VERIFIZIERTE FAKTEN:**
- Name: [EXAKTER Name aus offizieller Quelle oder leer]
- Land: [Land aus verifizierten Dokumenten oder leer]
- Region: [Region aus amtlichen Quellen oder leer]
- Eigentümer: [FIRMENNAME aus Registern - NIEMALS "CHANGED" oder "UPDATE"]
- Betreiber: [FIRMENNAME - NIEMALS Koordinaten oder Status]
- x-Koordinate: [GPS Latitude aus Survey-Docs - NIEMALS Jahreszahlen wie "2024"]
- y-Koordinate: [GPS Longitude mit korrektem Vorzeichen (z.B. -78.9934 für Kanada) - NIEMALS Status wie "AKTUELL"]
- Aktivitätsstatus: [aktiv/geschlossen aus Berichten - NIEMALS "NEU" oder "UPDATE"]
- Restaurationskosten: [Betrag aus ARO-Reports in {currency}$ - NIEMALS "$2024.0" oder "$2025.0"]
- Jahr der Aufnahme der Kosten: [Jahr aus Kostenbericht - NIEMALS Betrag]
- Jahr der Erstellung des Dokumentes: [Dokumentdatum - NIEMALS "AKTUELL"]
- Rohstoffabbau: [Spezifische Rohstoffe aus Berichten oder leer]
- Minentyp: [Aus technischen Docs oder leer]
- Produktionsstart: [Historisches Jahr oder leer]
- Produktionsende: [Jahr mit Wiedereröffnung falls vorhanden (z.B. "2013 (reopened 2021)") oder leer]
- Fördermenge/Jahr: [Aus Statistiken oder leer]
- Fläche der Mine in qkm: [Aus Vermessung oder leer]
- Quellenangaben: [SPEZIFISCHE URLs - NIEMALS generisch]

**GROK REAL-TIME VERIFICATION:**
1. JEDE Information mit spezifischer URL-Quelle
2. BREAKING NEWS nur mit offizieller Bestätigung
3. SOCIAL MEDIA nur bei offiziellen Accounts mit Dokumentation
4. REAL-TIME UPDATES nur mit Primärquellen-Nachweis

**GROK ANTI-BUG SELBSTPRÜFUNG vor jeder Antwort:**
- ❓ Habe ich Meta-Marker wie "UPDATE" in Datenfeldern vermieden?
- ❓ Sind alle Koordinaten echte GPS-Daten (nicht Jahre)?
- ❓ Sind alle Kosten in Geld (nicht Jahre wie "$2024")?
- ❓ Sind Eigentümer echte Firmennamen (nicht "CHANGED")?
- ❓ Hat jede Information eine verifizierte Quelle?

WENN NICHT 100% VERIFIZIERT: LEER LASSEN ("")"""