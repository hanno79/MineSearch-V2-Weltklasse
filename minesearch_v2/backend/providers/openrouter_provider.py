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
from ..data_extraction import extract_structured_data_with_sources
from ..source_discovery import extract_sources_from_content

logger = logging.getLogger(__name__)


class OpenRouterProvider(AbstractProvider):
    """Provider für OpenRouter API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://openrouter.ai/api/v1') + '/chat/completions'
        self.models = self._init_models()
    
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
            # Angepasster Query für OpenRouter (ohne Web-Suche)
            enhanced_query = self._enhance_query_for_no_web(query, options)
            
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
                mine_name = options.get('mine_name', '')
                country = options.get('country')
                
                extracted_data = extract_structured_data_with_sources(content, mine_name, country)
                sources = extract_sources_from_content(content)
                
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
            logger.error(f"[OPENROUTER] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _enhance_query_for_no_web(self, query: str, options: Dict[str, Any]) -> str:
        """
        Erweitere Query für Modelle ohne Web-Suche
        Füge Kontext und Hinweise hinzu
        """
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        enhanced = f"""Basierend auf deinem Wissen über Bergbau und Mining, beantworte folgende Anfrage:

{query}

WICHTIGE HINWEISE:
- Wenn die Mine "{mine_name}" existiert, gib bekannte Informationen
- Wenn du keine spezifischen Daten hast, gib plausible Schätzungen basierend auf:
  * Typische Werte für {country if country else 'das Land'}
  * Übliche Kosten für {commodity if commodity else 'den Rohstoff'}
  * Branchenstandards für Restaurationskosten
- Markiere unsichere Daten als "geschätzt" oder "typischer Wert"
- Nutze dein Wissen über Mining-Industrie und Umweltvorschriften

FOKUS auf Restaurationskosten:
- Typische Restaurationskosten liegen zwischen 10-500 Millionen USD
- Große Tagebau-Minen: oft 100-500 Millionen USD
- Untertage-Minen: oft 20-200 Millionen USD
- Berücksichtige Umweltauflagen des Landes"""
        
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
Antworte auf Deutsch mit STRUKTURIERTEN DATEN. Wenn du keine spezifischen Daten hast, gib plausible Schätzungen basierend auf deinem Fachwissen.

**GEFUNDENE DATEN FÜR [MINENNAME]:**
- Name: [exakter Name] [Quelle: Fachwissen/Schätzung]
- Land: [Land] [Quelle: Fachwissen/Schätzung]
- Region: [Region/Provinz] [Quelle: Fachwissen/Schätzung]
- Eigentümer: [Eigentümer oder "Unbekannt"] [Quelle: Fachwissen/Schätzung]
- Betreiber: [Betreiber oder "Unbekannt"] [Quelle: Fachwissen/Schätzung]
- Koordinaten: [Latitude, Longitude oder "k.A."] [Quelle: Fachwissen/Schätzung]
- Status: [aktiv/geschlossen/geplant] [Quelle: Fachwissen/Schätzung]
- Rohstoffe: [Liste der Rohstoffe] [Quelle: Fachwissen/Schätzung]
- Minentyp: [Untertage/Open-Pit/etc] [Quelle: Fachwissen/Schätzung]
- Produktionsstart: [Jahr oder "k.A."] [Quelle: Fachwissen/Schätzung]
- Produktionsende: [Jahr oder 'aktiv'] [Quelle: Fachwissen/Schätzung]
- Fördermenge: [Menge/Jahr oder "k.A."] [Quelle: Fachwissen/Schätzung]
- Fläche: [in km² oder "k.A."] [Quelle: Fachwissen/Schätzung]
- Restaurationskosten: [Betrag in {currency}$ oder Schätzung] [Quelle: Fachwissen/Schätzung]

**WICHTIG FÜR RESTAURATIONSKOSTEN:**
Wenn keine spezifischen Daten verfügbar sind, schätze basierend auf:
- Minentyp (Open-Pit: 50-500 Mio USD, Untertage: 20-200 Mio USD)
- Größe der Mine
- Umweltvorschriften des Landes
- Art des Rohstoffs
Gib IMMER eine Schätzung mit Begründung!

**QUELLEN-SEKTION:**
[Da du keine Web-Suche durchführst, gib an:]
[1] Allgemeines Branchenwissen
[2] Typische Werte für vergleichbare Minen
[3] Schätzung basierend auf Minentyp und Region

Markiere alle unsicheren Daten deutlich als "geschätzt" oder "typischer Wert"."""