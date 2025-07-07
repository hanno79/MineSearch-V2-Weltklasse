"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: OpenRouter Provider für Mining-Suchen
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_provider import AbstractProvider, ModelConfig, SearchResult

# ÄNDERUNG 06.07.2025: Absolute Imports für Provider-Kompatibilität
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, get_country_config, generate_multilingual_search_terms
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class OpenRouterProvider(AbstractProvider):
    """Provider für OpenRouter API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://openrouter.ai/api/v1') + '/chat/completions'
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere OpenRouter Modelle aus Config
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='openrouter',
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=False,
                is_free=model_config.get('is_free', True)
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit OpenRouter durch"""
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
        
        try:
            # ÄNDERUNG 04.07.2025: Enhanced Source Discovery nutzen
            mine_name = options.get('mine_name', '')
            country = options.get('country')
            region = options.get('region')
            
            # ÄNDERUNG 06.07.2025: Nutze übergebene Quellen wenn vorhanden
            discovered_sources = options.get('discovered_sources', [])
            skip_discovery = options.get('skip_source_discovery', False)
            
            # Initialisiere source_discovery immer
            source_discovery = EnhancedSourceDiscovery()
            
            if not discovered_sources and not skip_discovery and mine_name:
                # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
                logger.info(f"[OPENROUTER] Starte eigene Source Discovery für {mine_name}")
                discovered_sources = source_discovery.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region
                )
                logger.info(f"[OPENROUTER] {len(discovered_sources)} Quellen selbst entdeckt")
            else:
                logger.info(f"[OPENROUTER] Nutze {len(discovered_sources)} übergebene Quellen")
            
            # Generiere Sprachvarianten
            name_variants = generate_name_variants(mine_name) if mine_name else []
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)
            
            # Angepasster Query für OpenRouter mit Quellen
            enhanced_query = self._enhance_query_for_no_web(
                query, options, 
                discovered_sources=discovered_sources,
                name_variants=name_variants,
                multilingual_terms=multilingual_terms
            )
            
            # API-Call
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://minesearch.app",  # Optional für OpenRouter
                        "X-Title": "MineSearch v2"  # Optional für OpenRouter
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
                        "temperature": options.get('temperature', 0.3),  # Etwas höher für Kreativität
                        "max_tokens": model_config.max_tokens,
                        "top_p": 0.9
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
                
                # OpenRouter Response Format
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content']
                else:
                    content = result.get('message', 'Keine Antwort erhalten')
                
                # Extrahiere strukturierte Daten
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
                        'provider': 'openrouter',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'usage': result.get('usage', {}),
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
            logger.error(f"[OPENROUTER] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _enhance_query_for_no_web(self, query: str, options: Dict[str, Any], 
                                  discovered_sources: List[Dict] = None,
                                  name_variants: List[str] = None,
                                  multilingual_terms: Dict[str, List[str]] = None) -> str:
        """
        Erweitere Query für Modelle ohne Web-Suche
        Füge Kontext, Quellen und Sprachvarianten hinzu
        """
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        region = options.get('region', '')
        
        # ÄNDERUNG 04.07.2025: Nutze spezialisierte Prompts
        # ÄNDERUNG 05.07.2025: Verstärkter Fokus auf Restaurationskosten
        specialized_prompt = SpecializedPrompts.get_enhanced_query(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
        )
        
        # Füge zusätzlichen spezifischen Restaurationskosten-Prompt hinzu
        restoration_prompt = SpecializedPrompts.get_restoration_costs_prompt(mine_name, country, commodity)
        
        # ÄNDERUNG 04.07.2025: Füge Quellen-URLs hinzu
        sources_text = ""
        if discovered_sources:
            sources_text = "\n\nRELEVANTE QUELLEN (bitte nutze dein Wissen über diese Quellen):\n"
            for i, source in enumerate(discovered_sources[:20], 1):  # Top 20 Quellen
                sources_text += f"[{i}] {source['url']} ({source.get('description', source.get('type', 'Quelle'))})\n"
        
        # Füge Namensvarianten hinzu
        variants_text = ""
        if name_variants:
            variants_text = f"\n\nMÖGLICHE SCHREIBWEISEN: {', '.join(name_variants[:5])}"
        
        # Füge mehrsprachige Begriffe hinzu
        multilingual_text = ""
        if multilingual_terms:
            key_terms = []
            for term_type, terms in multilingual_terms.items():
                if term_type == 'restoration_costs' and terms:
                    key_terms.extend(terms[:5])  # Top 5 Begriffe
            if key_terms:
                multilingual_text = f"\n\nSUCHBEGRIFFE für Restaurationskosten: {', '.join(key_terms)}"
        
        enhanced = f"""Basierend auf deinem Wissen über Bergbau und Mining, beantworte folgende Anfrage:

{query}

MINE: {mine_name}
LAND: {country if country else 'Unbekannt'}
REGION: {region if region else 'Unbekannt'}
ROHSTOFF: {commodity if commodity else 'Unbekannt'}
{variants_text}
{multilingual_text}
{sources_text}

{specialized_prompt}

{restoration_prompt}

ANTWORTE IM STRUKTURIERTEN FORMAT wie im System-Prompt beschrieben."""
        
        return enhanced
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return "🔑 OpenRouter API-Key ungültig.\n→ Bitte prüfen Sie Ihre .env Datei."
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 OpenRouter API ist momentan nicht verfügbar.\n→ Bitte versuchen Sie es später erneut."
        
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unbekannter Fehler')
                return f"OpenRouter Fehler: {error_msg}"
            except:
                return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[OPENROUTER] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[OPENROUTER] Keine Modelle konfiguriert")
            return False
        
        return True
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für OpenRouter (angepasst für Modelle ohne Web-Suche)"""
        currency = options.get('currency', 'USD')
        
        return f"""Du bist ein Mining-Recherche-Experte mit umfassendem Wissen über die globale Bergbauindustrie. 
Antworte auf Deutsch mit STRUKTURIERTEN DATEN.

**GEFUNDENE DATEN FÜR [MINENNAME]:**
- Name: [exakter Name] [Quelle: Fachwissen/Schätzung]
- Land: [Land] [Quelle: Fachwissen/Schätzung]
- Region: [Region/Provinz] [Quelle: Fachwissen/Schätzung]
- Eigentümer: [Eigentümer oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Betreiber: [Betreiber oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Koordinaten: [Latitude, Longitude oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Status: [aktiv/geschlossen/geplant] [Quelle: Fachwissen/Schätzung]
- Rohstoffe: [Liste der Rohstoffe] [Quelle: Fachwissen/Schätzung]
- Minentyp: [Untertage/Open-Pit/etc] [Quelle: Fachwissen/Schätzung]
- Produktionsstart: [Jahr oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Produktionsende: [Jahr oder 'aktiv'] [Quelle: Fachwissen/Schätzung]
- Fördermenge: [Menge/Jahr oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Fläche: [in km² oder LEER lassen] [Quelle: Fachwissen/Schätzung]
- Restaurationskosten: [NUR realistische Beträge in {currency}$ oder LEER] [Quelle: Fachwissen/Schätzung]

**KRITISCHE REGELN FÜR RESTAURATIONSKOSTEN:**
- NIEMALS "$1 CAD", "$2 CAD", "$3 CAD" oder ähnliche Platzhalter verwenden!
- Nur realistische Schätzungen basierend auf:
  * Minentyp (Open-Pit: 50-500 Mio USD, Untertage: 20-200 Mio USD)
  * Größe der Mine und Umweltvorschriften
- Mindestbetrag: $10,000 - darunter ist unrealistisch
- Wenn unsicher: Feld LEER lassen, KEINE Minimalwerte!

**VERBOTENE PLATZHALTER:**
- KEINE "k.A.", "n/a", "-", "unbekannt", "nicht gefunden"
- KEINE Minimalwerte wie $1, $2, $3
- Wenn keine Daten: Feld einfach LEER lassen

**QUELLEN-SEKTION:**
[Da du keine Web-Suche durchführst, gib an:]
[1] Allgemeines Branchenwissen
[2] Typische Werte für vergleichbare Minen
[3] Schätzung basierend auf Minentyp und Region

Markiere alle unsicheren Daten deutlich als "geschätzt" oder "typischer Wert"."""