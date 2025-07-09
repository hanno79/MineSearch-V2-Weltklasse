"""
Author: rahn
Datum: 08.07.2025
Version: 1.0
Beschreibung: DeepSeek Provider für Mining-Suchen (via OpenRouter API)
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_provider import AbstractProvider, ModelConfig, SearchResult

# ÄNDERUNG 08.07.2025: Absolute Imports für Provider-Kompatibilität
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, get_country_config, generate_multilingual_search_terms
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class DeepSeekProvider(AbstractProvider):
    """Provider für DeepSeek API (via OpenRouter)"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        # DeepSeek nutzt OpenRouter als Proxy
        self.api_url = config.get('base_url', 'https://openrouter.ai/api/v1') + '/chat/completions'
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere DeepSeek Modelle aus Config
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='deepseek',
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=model_config.get('is_free', False)
            )
        
        return models
    
    def _get_headers(self) -> Dict[str, str]:
        """Hole API Headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Provider': 'deepseek'  # Wichtig für OpenRouter
        }
    
    async def _call_api(self, model_id: str, messages: List[Dict[str, str]], 
                       max_tokens: int = 4000) -> str:
        """Rufe DeepSeek API auf"""
        headers = self._get_headers()
        
        data = {
            'model': model_id,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.3,  # Niedrig für konsistente Ergebnisse
            'stream': False
        }
        
        timeout = httpx.Timeout(180.0, connect=30.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"Unerwartete API-Antwort: {result}")
                    return ""
                    
            except httpx.TimeoutException:
                logger.error(f"Timeout bei DeepSeek API für Modell {model_id}")
                raise
            except Exception as e:
                logger.error(f"Fehler bei DeepSeek API: {str(e)}")
                raise
    
    def _create_search_prompt(self, query: str, mine_type: str, 
                            country: str = None, language: str = None) -> str:
        """Erstelle Suchprompt für DeepSeek"""
        # DeepSeek ist besonders gut im logischen Denken
        prompt = f"""Du bist ein Experte für Mining-Projekte und sollst präzise Informationen extrahieren.

MINING PROJEKT: {query}
TYP: {mine_type}
"""
        
        if country:
            prompt += f"LAND: {country}\n"
        if language:
            prompt += f"SPRACHE: {language}\n"
            
        prompt += """
AUFGABE:
1. Analysiere das Mining-Projekt systematisch
2. Verwende dein Reasoning für komplexe Zusammenhänge
3. Extrahiere alle relevanten Daten strukturiert

WICHTIGE FELDER:
- Name der Mine und Betreiber
- Standort (Land, Region, Koordinaten)
- Mineralien/Rohstoffe
- Produktionsdaten und Reserven
- Kosten (CAPEX, OPEX, AISC)
- Umweltaspekte und Genehmigungen
- Aktuelle News und Entwicklungen

Gib die Informationen strukturiert und vollständig zurück.
"""
        
        return prompt
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit DeepSeek aus"""
        # Extrahiere model_key aus model_id (Format: deepseek:model_key)
        model_key = model_id.split(':')[-1] if ':' in model_id else model_id
        logger.info(f"DeepSeek Suche: {query} mit Modell {model_key}")
        
        if model_key not in self.models:
            raise ValueError(f"Unbekanntes Modell: {model_key}")
            
        model = self.models[model_key]
        mine_type = options.get('mine_type', 'Unknown')
        country = options.get('country')
        language = options.get('language', 'de')
        
        try:
            # Erstelle Prompt
            prompt = self._create_search_prompt(query, mine_type, country, language)
            
            messages = [
                {"role": "system", "content": "Du bist ein Mining-Experte mit tiefem Verständnis für Bergbauprojekte."},
                {"role": "user", "content": prompt}
            ]
            
            # API-Aufruf
            content = await self._call_api(
                model.id,
                messages,
                max_tokens=model.max_tokens
            )
            
            if not content:
                return self._create_error_result(query, "Keine Antwort von API erhalten")
            
            # Extrahiere Daten
            extracted_data = await self.data_extractor.extract_from_text(
                content, 
                mine_type, 
                query
            )
            
            # Extrahiere Quellen
            sources = extract_sources_from_content(content)
            
            return SearchResult(
                success=True,
                content=content,
                structured_data=extracted_data,
                sources=sources,
                metadata={
                    'provider': 'deepseek',
                    'model': model_key,
                    'mine_type': mine_type,
                    'country': country,
                    'language': language,
                    'model_info': {
                        'name': model.name,
                        'supports_reasoning': model.supports_deep_research
                    },
                    'timestamp': datetime.now().isoformat()
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Fehler bei DeepSeek Suche: {str(e)}")
            return self._create_error_result(query, str(e))
    
    def _create_error_result(self, query: str, error: str) -> SearchResult:
        """Erstelle Fehler-Ergebnis"""
        return SearchResult(
            success=False,
            content='',
            structured_data={},
            sources=[],
            metadata={
                'provider': 'deepseek',
                'query': query,
                'timestamp': datetime.now().isoformat()
            },
            error=error
        )
    
    def get_available_models(self) -> List[str]:
        """Gibt Liste der verfügbaren Modelle zurück"""
        return list(self.models.keys())
    
    def get_model_info(self, model_key: str) -> Optional[ModelConfig]:
        """Gibt Informationen zu einem spezifischen Modell zurück"""
        return self.models.get(model_key)
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt alle verfügbaren Modelle zurück"""
        return self.models
    
    def get_system_prompt(self, mine_type: str = None) -> str:
        """Gibt System-Prompt für das Modell zurück"""
        return "Du bist ein Experte für Mining-Projekte mit tiefem Verständnis für Bergbauprojekte."
    
    def validate_config(self) -> bool:
        """Validiere Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[DEEPSEEK] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[DEEPSEEK] Keine Modelle konfiguriert")
            return False
            
        return True