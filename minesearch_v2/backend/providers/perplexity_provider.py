"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Perplexity Provider für Mining-Suchen
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import AbstractProvider, ModelConfig, SearchResult

# ÄNDERUNG 06.07.2025: Absolute Imports für Provider-Kompatibilität
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class PerplexityProvider(AbstractProvider):
    """Provider für Perplexity API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere die bestehende PERPLEXITY_MODELS Konfiguration
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='perplexity',
                supports_web_search=True,
                supports_deep_research=model_key == 'sonar-deep-research',
                is_free=False
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Perplexity durch"""
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
        
        # ÄNDERUNG 03.07.2025: Enhanced Source Discovery für ALLE Provider
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        
        # ÄNDERUNG 06.07.2025: Nutze übergebene Quellen wenn vorhanden
        discovered_sources = options.get('discovered_sources', [])
        skip_discovery = options.get('skip_source_discovery', False)
        
        # Initialisiere source_discovery immer
        source_discovery = EnhancedSourceDiscovery()
        
        if not discovered_sources and not skip_discovery and mine_name:
            # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
            logger.info(f"[PERPLEXITY] Starte eigene Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity
            )
            logger.info(f"[PERPLEXITY] {len(discovered_sources)} Quellen selbst entdeckt")
        else:
            logger.info(f"[PERPLEXITY] Nutze {len(discovered_sources)} übergebene Quellen")
        
        # Generiere Namensvarianten und mehrsprachige Begriffe
        name_variants = generate_name_variants(mine_name) if mine_name else []
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # ÄNDERUNG 04.07.2025: Nutze spezialisierte Prompts für kritische Felder
        # ÄNDERUNG 05.07.2025: Verstärkter Fokus auf Restaurationskosten
        # Erweitere Query mit spezialisierten Prompts
        enhanced_query = SpecializedPrompts.get_enhanced_query(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
        )
        
        # Füge zusätzlichen spezifischen Restaurationskosten-Prompt hinzu
        restoration_prompt = SpecializedPrompts.get_restoration_costs_prompt(mine_name, country, commodity)
        
        # Kombiniere alle Queries mit Restaurationskosten-Fokus
        enhanced_query = f"{query}\n\n{enhanced_query}\n\n{restoration_prompt}"
        
        # Erweitere Query mit entdeckten Quellen
        if discovered_sources:
            # Füge Top-Quellen zur Query hinzu
            sources_text = "\n\nVERIFIZIERTE QUELLEN (nutze diese bevorzugt):\n"
            for i, source in enumerate(discovered_sources[:15], 1):  # Top 15 Quellen
                sources_text += f"[{i}] {source['url']} - {source.get('description', source.get('type', 'Quelle'))}\n"
            enhanced_query += sources_text
        
        try:
            # API-Call mit enhanced query
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
                        "temperature": options.get('temperature', 0.2),
                        "max_tokens": model_config.max_tokens
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
                mine_name = options.get('mine_name', '')
                country = options.get('country')
                
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                sources = extract_sources_from_content(content)
                
                # ÄNDERUNG 04.07.2025: Tracke Source Discovery Ergebnisse
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
                        'provider': 'perplexity',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'source_discovery_session': session_summary,
                        'discovered_sources_count': len(discovered_sources)
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
            logger.error(f"[PERPLEXITY] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            response_text = response.text.lower()
            error_msg = "🔐 Perplexity API Authentifizierung fehlgeschlagen.\n\n"
            
            if "quota" in response_text or "budget" in response_text:
                error_msg += "💳 Ihr API-Budget ist aufgebraucht.\n"
                error_msg += "→ Bitte prüfen Sie Ihr Perplexity-Konto und laden Sie Ihr Guthaben auf.\n"
            elif "invalid" in response_text or "unauthorized" in response_text:
                error_msg += "🔑 Der API-Key ist ungültig oder abgelaufen.\n"
                error_msg += "→ Bitte prüfen Sie Ihre .env Datei und generieren Sie ggf. einen neuen Key.\n"
            else:
                error_msg += "❓ Authentifizierungsproblem mit dem API-Key.\n"
            
            error_msg += "\n📍 API-Verwaltung: https://www.perplexity.ai/settings/api"
            return error_msg
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 Perplexity API ist momentan nicht verfügbar.\n→ Bitte versuchen Sie es später erneut."
        
        else:
            return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[PERPLEXITY] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[PERPLEXITY] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        ÄNDERUNG 05.07.2025: Spezielle Methode für Cross-Provider Source Sharing
        Extrahiert Daten aus vorgegebenen Quellen
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
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        # Erstelle spezielle Query für Quellenanalyse
        query = f"""DETAILLIERTE DATENEXTRAKTION für {mine_name}

Analysiere die folgenden {len(sources)} verifizierten Quellen und extrahiere ALLE Mining-Daten.
Fokussiere besonders auf:
- GPS-Koordinaten (verschiedene Formate)
- Restaurationskosten / ARO / Closure Costs
- Eigentümer und Betreiber
- Produktionsdaten
- Technische Details

QUELLEN ZUM ANALYSIEREN:
"""
        
        # Füge Quellen zur Query hinzu
        for i, source in enumerate(sources[:20], 1):
            url = source.get('url') or source.get('value', '')
            title = source.get('title', '')
            query += f"\n[{i}] {url}"
            if title:
                query += f" - {title}"
        
        query += "\n\nExtrahiere ALLE verfügbaren Daten im strukturierten Format!"
        
        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Perplexity"""
        currency = options.get('currency', 'USD')
        
        # ÄNDERUNG 05.07.2025: Angepasster Prompt für Source Sharing Phase
        if options.get('phase') == 'source_analysis':
            return self._get_source_analysis_prompt(options)
        
        return f"""Du bist ein Mining-Recherche-Experte. Antworte auf Deutsch mit STRUKTURIERTEN DATEN im folgenden Format:

**GEFUNDENE DATEN FÜR [MINENNAME]:**
- Name: [exakter Name] [Quelle: URL/Dokument]
- Land: [Land] [Quelle: URL/Dokument]
- Region: [Region/Provinz] [Quelle: URL/Dokument]
- Eigentümer: [Eigentümer der Mine] [Quelle: URL/Dokument]
- Betreiber: [Betreiber/Operator] [Quelle: URL/Dokument]
- Koordinaten: [Latitude, Longitude] [Quelle: URL/Dokument]
- Status: [aktiv/geschlossen/geplant] [Quelle: URL/Dokument]
- Rohstoffe: [Liste der Rohstoffe] [Quelle: URL/Dokument]
- Minentyp: [Untertage/Open-Pit/etc] [Quelle: URL/Dokument]
- Produktionsstart: [Jahr] [Quelle: URL/Dokument]
- Produktionsende: [Jahr oder 'aktiv'] [Quelle: URL/Dokument]
- Fördermenge: [Menge/Jahr mit Einheit] [Quelle: URL/Dokument]
- Fläche: [in km²] [Quelle: URL/Dokument]
- Restaurationskosten: [Betrag in {currency}$ mit Jahr] [Quelle: URL/Dokument]

**WICHTIG FÜR RESTAURATIONSKOSTEN:**
Suche nach: ARO, closure costs, environmental liability, restoration provision, rehabilitation costs, 
decommissioning costs, closure bond, financial assurance, pasivos ambientales, costos de cierre,
biaya reklamasi, jaminan reklamasi. Gib ALLE gefundenen Beträge an, auch wenn in verschiedenen Währungen!

**QUELLEN-SEKTION:**
[Liste ALLE verwendeten Quellen nummeriert auf]
[1] URL oder Dokumentname
[2] URL oder Dokumentname
[3] URL oder Dokumentname
... etc.

**KRITISCHE QUELLEN-REGELN:**
1. JEDE einzelne Information MUSS mit [Quelle: ...] gekennzeichnet werden!
2. Verwende [Quelle: Perplexity Search] wenn keine spezifische URL verfügbar ist
3. PRIORISIERTE QUELLEN-SUCHE nach Tiers (siehe Dokumentation)
4. WICHTIG: Lasse Felder LEER wenn keine Daten gefunden - KEINE Platzhalter!

**VERBOTENE PLATZHALTER:**
- NIEMALS "$1 CAD", "$2 CAD", "$3 CAD" oder ähnliche Minimalwerte verwenden
- KEINE "k.A.", "n/a", "-", "unbekannt", "nicht gefunden" etc.
- Bei Restaurationskosten: NUR realistische Beträge (mind. $10,000) oder LEER lassen
- Wenn keine Daten gefunden: Feld einfach LEER lassen"""
    
    def _get_source_analysis_prompt(self, options: Dict[str, Any]) -> str:
        """Spezieller System-Prompt für Source Sharing Phase 2"""
        currency = options.get('currency', 'USD')
        
        return f"""Du bist ein Mining-Datenextraktions-Spezialist in PHASE 2 der Recherche.

DEINE AUFGABE: Analysiere die bereitgestellten Quellen GRÜNDLICH und extrahiere ALLE verfügbaren Daten.

**EXTRAKTIONS-STRATEGIE:**
1. Prüfe JEDE angegebene Quelle sorgfältig
2. Suche nach versteckten Daten in Tabellen, Fußnoten, Anhängen
3. Achte auf verschiedene Schreibweisen und Sprachen
4. Kombiniere Informationen aus mehreren Quellen

**STRUKTURIERTES AUSGABEFORMAT:**
- Name: [exakter Name] [Quelle: Nummer aus Liste]
- Land: [Land] [Quelle: Nummer]
- Region: [Region/Provinz] [Quelle: Nummer]
- Eigentümer: [Owner] [Quelle: Nummer]
- Betreiber: [Operator] [Quelle: Nummer]
- Koordinaten: [Lat, Long] [Quelle: Nummer]
- Status: [aktiv/geschlossen] [Quelle: Nummer]
- Rohstoffe: [Liste] [Quelle: Nummer]
- Minentyp: [Typ] [Quelle: Nummer]
- Produktionsstart: [Jahr] [Quelle: Nummer]
- Produktionsende: [Jahr] [Quelle: Nummer]
- Fördermenge: [Menge/Jahr] [Quelle: Nummer]
- Fläche: [km²] [Quelle: Nummer]
- Restaurationskosten: [{currency}$ mit Jahr] [Quelle: Nummer]

**KRITISCHE SUCHWÖRTER für Restaurationskosten:**
- Asset Retirement Obligation (ARO)
- Closure costs / Mine closure
- Environmental liability
- Rehabilitation provision
- Decommissioning costs
- Closure bond / Financial assurance
- Provisiones ambientales
- Pasivos ambientales

**PHASE 2 REGELN:**
1. Nutze die Quellennummern [1], [2], etc. aus der bereitgestellten Liste
2. Extrahiere AUCH Teilinformationen (z.B. nur Latitude ohne Longitude)
3. Bei Widersprüchen: Neueste Information verwenden
4. KEINE eigene Web-Suche - NUR die angegebenen Quellen nutzen
5. Lasse Felder LEER wenn keine Daten in den Quellen gefunden"""