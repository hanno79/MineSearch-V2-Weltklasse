"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: OpenAI Provider für premium Mining-Datenextraktion mit GPT-4.1
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

from config.base import config as Config
from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class OpenAIProvider(AbstractProvider):
    """Provider für OpenAI GPT-4.1 Premium Modelle"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere die OPENAI_MODELS Konfiguration
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='openai',
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=False
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit OpenAI GPT durch"""
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
        
        # ÄNDERUNG 06.07.2025: o3-deep-research verwendet anderen Endpunkt
        if model_id == 'o3-deep-research':
            return await self._search_with_o3_deep_research(query, model_config, options, start_time)
        
        # ÄNDERUNG 06.07.2025: Premium LLMs für verbesserte Finanzanalyse
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        sources = options.get('sources', [])
        
        # Erstelle erweiterte Query mit Fokus auf Finanzdaten
        enhanced_query = self._build_enhanced_query(
            query=query,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            sources=sources,
            focus='financial_data'
        )
        
        # Verwende Standard-Methode für alle anderen Modelle
        try:
            return await self._search_standard(enhanced_query, model_config, options, mine_name, country, start_time)
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
            logger.error(f"[OPENAI] Fehler bei Suche: {str(e)}")
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
                            sources: List[Dict], focus: str) -> str:
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
        
        # Spezieller Fokus auf Finanzdaten
        if focus == 'financial_data':
            enhanced_query += """
KRITISCHER FOKUS: FINANZIELLE DATEN

Analysiere die folgenden Aspekte mit HÖCHSTER PRIORITÄT:

1. RESTAURATIONSKOSTEN / ARO (Asset Retirement Obligation):
   - Suche nach ALLEN Beträgen für Umweltverbindlichkeiten
   - Inkludiere: closure costs, rehabilitation provision, environmental liability
   - Auch kleine Beträge (ab $1,000) sind relevant
   - Prüfe Fußnoten, Anhänge, Management Discussion & Analysis

2. FINANZBERICHTE ANALYSIEREN:
   - Annual Reports / Jahresberichte
   - Quarterly Reports / Quartalsberichte
   - Technical Reports (NI 43-101, JORC)
   - Sustainability Reports
   - Environmental Impact Assessments

3. SPEZIFISCHE SUCHWÖRTER:
   - "Asset Retirement Obligation"
   - "Environmental provisions"
   - "Closure costs"
   - "Rehabilitation liability"
   - "Decommissioning costs"
   - "Financial assurance"
   - "Closure bond"
   - "Environmental bonding"

4. WÄHRUNGEN UND FORMATE:
   - Beachte verschiedene Währungen (CAD, USD, AUD, EUR)
   - Erkenne Abkürzungen: k, M, Mio, Mill, Billion
   - Prozentuale Angaben vom Projektgesamtwert
"""
        
        # Füge Quellen hinzu wenn vorhanden
        if sources:
            enhanced_query += f"\n\nANALYSIERE DIESE {len(sources)} QUELLEN:\n"
            for i, source in enumerate(sources[:30], 1):
                url = source.get('url', source.get('value', ''))
                enhanced_query += f"[{i}] {url}\n"
        
        return enhanced_query
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return """🔐 OpenAI API Authentifizierung fehlgeschlagen.
            
🔑 Der API-Key ist ungültig oder fehlt.
→ Bitte prüfen Sie Ihre .env Datei
→ Generieren Sie einen neuen Key unter: https://platform.openai.com/api-keys"""
        
        elif response.status_code == 429:
            error_data = response.json()
            if "quota" in str(error_data).lower():
                return """💳 OpenAI API Quota überschritten.
                
→ Ihr Kontingent oder Budget ist aufgebraucht
→ Prüfen Sie Ihr Guthaben: https://platform.openai.com/usage"""
            else:
                return "⏱️ Rate Limit erreicht. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 OpenAI API ist momentan überlastet. Bitte versuchen Sie es später erneut."
        
        else:
            return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    async def _search_with_o3_deep_research(self, query: str, model_config: ModelConfig, 
                                           options: Dict[str, Any], start_time: datetime) -> SearchResult:
        """Spezielle Implementierung für o3-deep-research Modell"""
        try:
            mine_name = options.get('mine_name', '')
            country = options.get('country')
            
            # Erstelle strukturierte Query für o3-deep-research
            enhanced_query = self._build_enhanced_query(
                query=query,
                mine_name=mine_name,
                country=country,
                region=options.get('region'),
                commodity=options.get('commodity'),
                sources=options.get('sources', []),
                focus='financial_data'
            )
            
            # Verwende Standard Chat Completions Endpunkt für o3-deep-research
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",  # Standard Endpunkt
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_config.id,
                        "messages": [
                            {"role": "system", "content": "Du bist ein Experte für Mining-Projekte und Finanzdaten."},
                            {"role": "user", "content": enhanced_query}
                        ],
                        "temperature": 0.1,
                        # ÄNDERUNG 09.07.2025: Reduziere max_tokens für o3 Modell
                        "max_tokens": min(model_config.max_tokens, 4096) if model_config.id == 'gpt-4-turbo' else model_config.max_tokens
                    }
                )
                
                if response.status_code != 200:
                    # Fallback auf Standard-Modell wenn o3-deep-research nicht verfügbar
                    logger.warning(f"[OPENAI] o3-deep-research nicht verfügbar, verwende gpt-4.1")
                    model_config = self.models.get('gpt-4.1')
                    if model_config:
                        # Verwende Standard-Methode mit gpt-4.1
                        return await self._search_standard(enhanced_query, model_config, options, mine_name, country, start_time)
                    else:
                        return SearchResult(
                            success=False,
                            content="",
                            structured_data={},
                            sources=[],
                            metadata={'status_code': response.status_code},
                            error=self._handle_api_error(response)
                        )
                
                # Parse Response (Standard Chat Completions Format)
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                sources_from_response = extract_sources_from_content(content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=sources_from_response,
                    metadata={
                        'model': 'o3-deep-research',
                        'provider': 'openai',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index']
                    },
                    search_duration=duration
                )
                
        except Exception as e:
            logger.error(f"[OPENAI] Fehler bei o3-deep-research: {str(e)}")
            # Fallback auf Standard-Modell
            model_config = self.models.get('gpt-4.1')
            if model_config:
                return await self._search_standard(query, model_config, options, 
                                                 options.get('mine_name', ''), 
                                                 options.get('country'), start_time)
            else:
                return SearchResult(
                    success=False,
                    content="",
                    structured_data={},
                    sources=[],
                    metadata={},
                    error=str(e)
                )
    
    async def _search_standard(self, query: str, model_config: ModelConfig, 
                             options: Dict[str, Any], mine_name: str, 
                             country: Optional[str], start_time: datetime) -> SearchResult:
        """Standard-Suchmethode für normale Chat-Completions"""
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
                                "content": query
                            }
                        ],
                        "temperature": options.get('temperature', 0.1),
                        # ÄNDERUNG 09.07.2025: Reduziere max_tokens für o3 Modell
                        "max_tokens": min(model_config.max_tokens, 4096) if model_config.id == 'gpt-4-turbo' else model_config.max_tokens,
                        "response_format": {"type": "text"}
                    }
                )
                
                if response.status_code != 200:
                    return SearchResult(
                        success=False,
                        content="",
                        structured_data={},
                        sources=[],
                        metadata={'status_code': response.status_code},
                        error=self._handle_api_error(response)
                    )
                
                # Parse Response
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                sources_from_response = extract_sources_from_content(content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=sources_from_response,
                    metadata={
                        'model': model_config.id,
                        'provider': 'openai',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'tokens_used': result.get('usage', {})
                    },
                    search_duration=duration
                )
                
        except Exception as e:
            logger.error(f"[OPENAI] Fehler bei Standard-Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[OPENAI] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[OPENAI] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        Spezielle Methode für Cross-Provider Source Sharing
        Nutzt GPT-4.1 für detaillierte Quellenanalyse
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
        
        # Erstelle spezielle Query für Quellenanalyse
        query = f"""PREMIUM DATENEXTRAKTION für {mine_name}

Du hast Zugriff auf {len(sources)} verifizierte Quellen.
Nutze deine fortgeschrittenen Analysefähigkeiten um ALLE relevanten Daten zu extrahieren.

BESONDERER FOKUS:
1. Finanzielle Daten (ARO, Restaurationskosten, Umweltverbindlichkeiten)
2. Technische Spezifikationen
3. Versteckte Informationen in Tabellen und Anhängen
4. Querverweise zwischen Dokumenten

Die Quellen wurden bereits verifiziert - konzentriere dich auf die EXTRAKTION."""
        
        # Setze sources in options für die search Methode
        options['sources'] = sources
        
        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für OpenAI"""
        currency = options.get('currency', 'USD')
        
        # Premium-Prompt für GPT-4.1
        return f"""Du bist ein hochspezialisierter Mining-Analyst mit Expertise in Finanzdatenextraktion.
Deine Aufgabe ist es, präzise und vollständige Daten aus Mining-Dokumenten zu extrahieren.

**DEINE STÄRKEN:**
- Tiefgehende Analyse von Finanzberichten
- Erkennung von ARO und Umweltverbindlichkeiten
- Extraktion aus komplexen Tabellen und Fußnoten
- Mehrsprachige Dokumentenanalyse

**STRUKTURIERTES AUSGABEFORMAT:**
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

**KRITISCHE REGELN FÜR RESTAURATIONSKOSTEN:**
1. IMMER nach folgenden Begriffen suchen:
   - Asset Retirement Obligation (ARO)
   - Environmental liability / provisions
   - Closure costs / Mine closure provision
   - Rehabilitation costs / provision
   - Decommissioning costs
   - Financial assurance / Closure bond
   
2. BETRÄGE RICHTIG INTERPRETIEREN:
   - "$45.2 million" = $45,200,000
   - "CAD 12.5M" = $12,500,000 CAD
   - "€2.3 Mio" = €2,300,000
   - Auch kleine Beträge ab $1,000 sind relevant
   
3. KONTEXT BEACHTEN:
   - Prüfe ob Beträge aktuell oder historisch sind
   - Achte auf Währung und Jahr
   - Unterscheide zwischen geplant und tatsächlich

**VERBOTEN:**
- KEINE Dummy-Werte ($1, $2, $3)
- KEINE Platzhalter (k.A., n/a, -)
- KEINE erfundenen Daten
- Felder LEER lassen wenn keine Daten gefunden

**QUALITÄTSKONTROLLE:**
- Jede Information MUSS eine Quelle haben
- Bei Widersprüchen: Neueste Information verwenden
- Unsichere Daten kennzeichnen mit "(?)"
"""