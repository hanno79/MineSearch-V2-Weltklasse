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
from ..config import Config
from ..data_extraction import extract_structured_data_with_sources
from ..source_discovery import extract_sources_from_content

logger = logging.getLogger(__name__)


class PerplexityProvider(AbstractProvider):
    """Provider für Perplexity API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.models = self._init_models()
    
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
        
        try:
            # API-Call
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
                                "content": query
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
                        'provider': 'perplexity',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index']
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
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Perplexity"""
        currency = options.get('currency', 'USD')
        
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
4. Nutze 'k.A.' für nicht gefundene Daten"""