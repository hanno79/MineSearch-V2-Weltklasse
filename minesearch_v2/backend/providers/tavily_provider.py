"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Tavily Search Provider für moderne KI-gestützte Websuche
"""

import httpx
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import AbstractProvider, ModelConfig, SearchResult

# ÄNDERUNG 06.07.2025: Absolute Imports für Provider-Kompatibilität
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from utils import generate_name_variants, get_country_config, generate_multilingual_search_terms

logger = logging.getLogger(__name__)


class TavilyProvider(AbstractProvider):
    """Provider für Tavily Search API - moderne KI-gestützte Websuche"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://api.tavily.com')
        self.models = self._init_models()
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
                provider='tavily',
                supports_web_search=model_config.get('supports_web_search', True),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=model_config.get('is_free', False)
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Tavily durch"""
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
        
        # Mining-spezifische Parameter
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        commodity = options.get('commodity')
        region = options.get('region')
        
        # Erstelle erweiterte Query für Mining-Recherche
        enhanced_query = self._build_mining_query(query, mine_name, country, commodity, region)
        
        try:
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                # ÄNDERUNG 05.07.2025: Tavily hat keinen separaten research endpoint
                # Deep Research wird über search_depth parameter gesteuert
                endpoint = f"{self.api_url}/search"
                
                # Angepasste Parameter für Deep Research
                search_params = {
                    "api_key": self.api_key,
                    "query": enhanced_query,
                    "max_results": 50 if model_id == 'deep-research' else 20,  # Mehr Ergebnisse für Deep Research
                    "search_depth": "advanced" if model_id == 'deep-research' else "basic",
                    "include_answer": True,
                    "include_raw_content": True,  # Wichtig für tiefe Datenextraktion
                    "include_domains": self._get_priority_domains(country),
                    "exclude_domains": ["wikipedia.org", "facebook.com", "twitter.com"],
                    "topic": "general"
                }
                
                response = await client.post(
                    endpoint,
                    headers={
                        "Content-Type": "application/json"
                    },
                    json=search_params
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
                
                # Extrahiere Content und Quellen
                content = self._build_content_from_results(result, mine_name)
                sources = self._extract_tavily_sources(result)
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=sources,
                    metadata={
                        'model': model_id,
                        'provider': 'tavily',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'results_count': len(result.get('results', [])),
                        'answer_provided': bool(result.get('answer'))
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
            logger.error(f"[TAVILY] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _build_mining_query(self, base_query: str, mine_name: str, 
                           country: str, commodity: str, region: str) -> str:
        """Erstelle optimierte Query für Mining-Recherche"""
        
        # ÄNDERUNG 06.07.2025: Query auf 400 Zeichen begrenzen für Tavily API
        # Basis-Query mit Mining-Fokus - Priorisiere wichtigste Begriffe
        query_parts = []
        
        # Höchste Priorität: Minenname
        query_parts.append(f'"{mine_name}" mine')
        
        # Zweite Priorität: Land und Rohstoff
        if country:
            query_parts.append(country)
        
        if commodity:
            query_parts.append(commodity)
        
        # Dritte Priorität: Kritische Datenpunkte (kurz gefasst)
        priority_terms = [
            'restoration costs ARO',
            'operator owner',
            'coordinates GPS',
            'production'
        ]
        
        # Baue Query schrittweise auf und prüfe Länge
        current_query = ' '.join(query_parts)
        
        for term in priority_terms:
            test_query = f"{current_query} {term}"
            if len(test_query) < 350:  # 350 Zeichen Limit, um Puffer zu lassen
                current_query = test_query
            else:
                break
        
        # Füge Region hinzu wenn noch Platz
        if region and len(f"{current_query} {region}") < 380:
            current_query = f"{current_query} {region}"
        
        # Stelle sicher dass Query nicht zu lang ist
        if len(current_query) > 400:
            # Fallback: Nur Minenname und Land
            current_query = f'"{mine_name}" mine {country or ""}'.strip()
            if len(current_query) > 400:
                # Extremer Fallback: Kürze Minenname
                current_query = f'"{mine_name[:100]}" mine'
        
        logger.info(f"[TAVILY] Query-Länge: {len(current_query)} Zeichen")
        return current_query
    
    def _build_content_from_results(self, tavily_response: Dict, mine_name: str) -> str:
        """Erstelle strukturierten Content aus Tavily-Ergebnissen"""
        content_parts = []
        
        # Tavily Answer wenn vorhanden
        if tavily_response.get('answer'):
            content_parts.append(f"**Zusammenfassung für {mine_name}:**\n{tavily_response['answer']}\n")
        
        # Detaillierte Ergebnisse
        content_parts.append(f"\n**Detaillierte Informationen aus {len(tavily_response.get('results', []))} Quellen:**\n")
        
        for idx, result in enumerate(tavily_response.get('results', []), 1):
            content_parts.append(f"\n[Quelle {idx}] {result.get('title', 'Unbekannt')}")
            content_parts.append(f"URL: {result.get('url', '')}")
            
            # Raw content wenn verfügbar
            if result.get('raw_content'):
                content_parts.append(f"Inhalt: {result['raw_content'][:2000]}...")
            elif result.get('content'):
                content_parts.append(f"Zusammenfassung: {result['content']}")
            
            content_parts.append("")
        
        return '\n'.join(content_parts)
    
    def _extract_tavily_sources(self, response: Dict) -> List[Dict[str, Any]]:
        """Extrahiere Quellen aus Tavily Response"""
        sources = []
        
        for idx, result in enumerate(response.get('results', []), 1):
            source = {
                'type': 'url',
                'value': result.get('url', ''),
                'title': result.get('title', ''),
                'description': result.get('content', '')[:200] if result.get('content') else '',
                'score': result.get('score', 0),
                'provider': 'tavily'
            }
            sources.append(source)
        
        return sources
    
    def _get_priority_domains(self, country: str) -> List[str]:
        """Hole prioritäre Domains für ein Land"""
        if not country:
            return []
        
        country_config = get_country_config(country)
        return country_config.get('priority_domains', [])
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return "🔑 Tavily API-Key ungültig.\n→ Bitte prüfen Sie Ihre .env Datei."
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 402:
            return "💳 Tavily API-Guthaben aufgebraucht.\n→ Bitte laden Sie Ihr Konto auf."
        
        else:
            try:
                error_data = response.json()
                return f"Tavily API Fehler: {error_data.get('detail', 'Unbekannter Fehler')}"
            except:
                return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[TAVILY] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[TAVILY] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def health_check(self) -> bool:
        """Prüfe ob Tavily API erreichbar ist"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.api_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": "test",
                        "max_results": 1
                    }
                )
                return response.status_code in [200, 401]  # 401 = Key ungültig, aber API erreichbar
        except:
            return False
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """Gibt den System-Prompt für Tavily zurück"""
        return """Du bist ein Mining-Recherche-Spezialist der Tavily Search nutzt.
        
Fokussiere dich auf:
- Aktuelle Mining-Informationen und Nachrichten
- Technische Berichte und Dokumente
- Betreiber- und Eigentümer-Informationen
- Restaurationskosten und Umweltverbindlichkeiten
- Koordinaten und Standortdaten

Nutze die erweiterten Suchfähigkeiten von Tavily für präzise und aktuelle Ergebnisse."""