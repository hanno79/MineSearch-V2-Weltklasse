"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: API Client für Perplexity Deep Research
"""

import aiohttp
import json
from typing import Dict, Any, Optional, List
from src.core.logger import get_logger
from src.utils.model_validation import get_model_validator

class PerplexityAPIClient:
    """API Client für Perplexity Deep Research Calls"""
    
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
        self.base_url = "https://api.perplexity.ai"
        self.logger = get_logger(__name__)
        
        # ÄNDERUNG 26.06.2025: Aktualisierte Perplexity Models - verifiziert mit API Test
        self.models = {
            "deep_research": "sonar-deep-research",  # Deep research model - braucht ~60s Response Zeit
            "reasoning": "sonar-reasoning",  # Reasoning model (funktioniert)
            "online": "sonar",  # Standard online model (funktioniert)
            "sonar": "sonar",  # Basic model für schnelle Suchen (funktioniert)
            "pro": "sonar-pro"  # Advanced search model (funktioniert)
        }
    
    async def deep_research_search(self, message: str, system_prompt: str,
                                  model: str = "deep_research") -> Optional[Dict[str, Any]]:
        """Führt Deep Research API Call durch"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Wähle das richtige Modell
        model_name = self.models.get(model, self.models["online"])
        
        # ÄNDERUNG 24.06.2025: Validiere Model
        validator = get_model_validator()
        model_name = validator.auto_fix_model("perplexity", model_name)
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "return_citations": True,
            "search_recency_filter": "month",  # Fokus auf aktuelle Informationen
            "return_images": False,
            "return_related_questions": True
            # ÄNDERUNG 24.06.2025: Entfernt hypothetische Deep Research Parameter
        }
        
        try:
            # ÄNDERUNG 24.06.2025: Robustere Session-Prüfung
            if self.session.closed:
                self.logger.error("Session ist geschlossen - kann keinen API Call durchführen")
                return None
                
            # ÄNDERUNG 26.06.2025: Erhöhtes Timeout für Deep Research (kann bis zu 60s dauern)
            timeout_seconds = 180 if model == "deep_research" else 120
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    self.logger.error(f"Perplexity API Fehler: {response.status} - {error_msg}")
                    return None
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Fehler bei Perplexity API Call (ClientError): {e}")
            return None
        except Exception as e:
            self.logger.error(f"Fehler bei Perplexity API Call: {e}")
            return None
    
    async def standard_search(self, message: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        """Führt Standard Perplexity Suche durch"""
        return await self.deep_research_search(message, system_prompt, model="online")
    
    async def quick_search(self, message: str) -> Optional[Dict[str, Any]]:
        """Führt schnelle Suche mit Sonar durch"""
        system_prompt = "You are a helpful assistant that provides concise, factual answers."
        return await self.deep_research_search(message, system_prompt, model="sonar")
    
    def parse_citations(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extrahiert Zitate aus der Antwort"""
        citations = []
        
        if "citations" in response:
            for citation in response["citations"]:
                citations.append({
                    "url": citation.get("url", ""),
                    "title": citation.get("title", ""),
                    "snippet": citation.get("snippet", "")
                })
        
        return citations
    
    def parse_research_phases(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrahiert Research-Phasen aus Deep Research Antwort"""
        phases = []
        
        # Hypothetische Struktur für Deep Research Antwort
        if "research_phases" in response:
            for phase in response["research_phases"]:
                phases.append({
                    "phase_number": phase.get("number", 0),
                    "focus": phase.get("focus", ""),
                    "sources_analyzed": phase.get("sources_analyzed", 0),
                    "key_findings": phase.get("findings", []),
                    "confidence": phase.get("confidence", 0.0)
                })
        
        return phases