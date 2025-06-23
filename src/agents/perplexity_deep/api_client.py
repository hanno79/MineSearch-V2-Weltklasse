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

class PerplexityAPIClient:
    """API Client für Perplexity Deep Research Calls"""
    
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
        self.base_url = "https://api.perplexity.ai"
        self.logger = get_logger(__name__)
        
        # ÄNDERUNG 23.06.2025: Verwende gültige Perplexity Modelle
        self.models = {
            "deep_research": "sonar-medium-online",  # Verwende sonar-medium als Deep Research
            "reasoning": "sonar-medium-online",  # Reasoning Modell
            "online": "sonar-small-online",  # Standard Online Modell  
            "sonar": "sonar-small-online"  # Sonar für schnelle Suchen
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
            "return_related_questions": True,
            # Hypothetische Deep Research Parameter
            "deep_research": {
                "enabled": True,
                "max_iterations": 5,
                "sources_per_iteration": 20,
                "confidence_threshold": 0.7,
                "auto_refine": True
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    self.logger.error(f"Perplexity API Fehler: {response.status} - {error_msg}")
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