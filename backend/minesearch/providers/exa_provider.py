"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Exa AI Provider für neuronale und semantische Suche
"""

import httpx
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import AbstractProvider, ModelConfig, SearchResult

from minesearch.data_extraction import DataExtractor
from minesearch.source_discovery import EnhancedSourceDiscovery, extract_sources_from_content
from minesearch.utils import (
    generate_name_variants,
    get_country_config,
    generate_multilingual_search_terms,
)
from minesearch.specialized_prompts import SpecializedPrompts
from minesearch.specialized_prompts_impl import SpecializedPrompts as SpecializedPromptsImpl

logger = logging.getLogger(__name__)


class ExaProvider(AbstractProvider):
    """Provider für Exa AI - Neuronale/Semantische Suche"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://api.exa.ai')
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
                provider='exa',
                supports_web_search=model_config.get('supports_web_search', True),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=model_config.get('is_free', False),
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='exa'
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Exa durch"""
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
        
        # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
        discovered_sources = options.get('discovered_sources', [])
        use_all_sources = options.get('use_all_sources', False)
        skip_discovery = options.get('skip_discovery', False)
        
        source_discovery = EnhancedSourceDiscovery()
        
        if not discovered_sources and not skip_discovery and mine_name:
            # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
            logger.info(f"[EXA] Starte eigene Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region
            )
            logger.info(f"[EXA] {len(discovered_sources)} Quellen selbst entdeckt")
        else:
            if use_all_sources:
                logger.info(f"[EXA] 🔥 2-PHASEN WORKFLOW: Nutze ALLE {len(discovered_sources)} übergebenen DB-Quellen ohne Filter")
            else:
                logger.info(f"[EXA] Nutze {len(discovered_sources)} übergebene Quellen")
        
        # Generiere Sprachvarianten (wie OpenRouter)
        name_variants = generate_name_variants(mine_name) if mine_name else []
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # ÄNDERUNG 05.07.2025: Nutze Specialized Prompts für bessere Ergebnisse
        # Erstelle semantische Query für Mining-Recherche
        enhanced_query = self._build_semantic_query(query, mine_name, country, commodity, region, model_id)
        
        # Füge spezialisierte Restaurationskosten-Begriffe hinzu
        restoration_prompt = SpecializedPrompts.get_restoration_costs_prompt(mine_name, country, commodity)
        enhanced_query = f"{enhanced_query}\n\n{restoration_prompt}"
        
        # ÄNDERUNG 08.07.2025: Erweitere Query mit discovered_sources
        if discovered_sources:
            sources_hint = f"\n\nRelevante Quellen für {mine_name}:\n"
            # Füge Top 20 Quellen zur Query hinzu
            for i, source in enumerate(discovered_sources[:20], 1):
                url = source.get('url', '')
                if url:
                    sources_hint += f"- {url}\n"
            enhanced_query += sources_hint
        
        try:
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                # Exa API Request
                endpoint = f"{self.api_url}/search"
                
                # ÄNDERUNG 09.07.2025: Research-Modelle nutzen normalen search Endpoint
                if 'research' in model_id:
                    # Research nutzt normalen search endpoint mit erweiterten Parametern
                    endpoint = f"{self.api_url}/search"
                    request_data = {
                        "query": enhanced_query,
                        "num_results": 50 if 'pro' in model_id else 30,  # Mehr Ergebnisse für Research
                        "type": "neural",  # Nutze neuronale Suche für Research
                        "useAutoprompt": True,
                        "includeDomains": self._get_mining_domains(country, discovered_sources),
                        "startCrawlDate": "2020-01-01",
                        "endCrawlDate": datetime.now().strftime("%Y-%m-%d"),
                        "category": "company",
                        "contents": {
                            "text": True,
                            "highlights": True
                        }
                    }
                else:
                    # Standard Neural/Keyword Search
                    request_data = {
                        "query": enhanced_query,
                        "num_results": 30,  # Mehr Ergebnisse für bessere Abdeckung
                        "type": "neural" if model_id == 'neural-search' else "keyword",
                        "useAutoprompt": True,  # Exa optimiert die Query automatisch
                        "includeDomains": self._get_mining_domains(country, discovered_sources),
                        "startCrawlDate": "2020-01-01",  # Nur aktuelle Informationen
                        "endCrawlDate": datetime.now().strftime("%Y-%m-%d"),
                        "category": "company",  # Fokus auf Unternehmensseiten
                        "contents": {
                            "text": True,
                            "highlights": True  # Wichtige Passagen hervorheben
                        }
                    }
                
                # Similarity Search wenn gewählt
                if model_id == 'similarity-search' and options.get('reference_url'):
                    endpoint = f"{self.api_url}/find-similar"
                    request_data = {
                        "url": options['reference_url'],
                        "num_results": 20,  # ÄNDERUNG 05.07.2025: Korrigiert zu snake_case (Exa API Standard)
                        "includeDomains": self._get_mining_domains(country, discovered_sources),
                        "excludeSourceDomain": True
                    }
                
                response = await client.post(
                    endpoint,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json=request_data
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
                sources = self._extract_exa_sources(result)
                
                # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
                logger.info(f"[EXA] Sende EXA-Ergebnisse durch AI-Modell für strukturierte Extraktion")
                ai_response = await self._send_to_ai_model(
                    content=content,
                    mine_name=mine_name,
                    country=country,
                    commodity=commodity,
                    region=region,
                    discovered_sources=discovered_sources
                )
                
                # OPENROUTER WORKFLOW STEP 3: DataExtractor auf AI-Response anwenden (wie OpenRouter)
                extracted_data = self.data_extractor.extract_structured_data_with_sources(ai_response, mine_name, country)
                
                # OPENROUTER WORKFLOW STEP 4: Quality Gates (wie OpenRouter)
                extracted_data = self._apply_quality_gates(extracted_data, mine_name)
                
                # Konvertiere discovered_sources zu standardisierten Source-Format (wie OpenRouter)
                all_sources = sources  # EXA-Quellen
                for source in discovered_sources:  # Alle Discovery-Quellen hinzufügen
                    all_sources.append({
                        'url': source.get('url', ''),
                        'title': source.get('title', source.get('url', '')),
                        'type': source.get('type', 'unknown'),
                        'reliability': source.get('reliability_score')  # REGEL 10: Keine 0.5 Fallbacks
                    })
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=ai_response,  # AI-Response als Content
                    structured_data=extracted_data['data'],
                    sources=all_sources,  # Alle Quellen (EXA + Discovery)
                    metadata={
                        'model': model_id,
                        'provider': 'exa',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'results_count': len(result.get('results', [])),
                        'search_type': 'neural' if model_id == 'neural-search' else 'similarity',
                        'discovery_sources': len(discovered_sources),
                        'unified_workflow': True  # Markierung für neuen Workflow
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
            logger.error(f"[EXA] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _build_semantic_query(self, base_query: str, mine_name: str, 
                             country: str, commodity: str, region: str, model_id: str) -> str:
        """Erstelle semantisch optimierte Query für Mining-Recherche"""
        
        # ÄNDERUNG 05.07.2025: Erweiterte Queries für Deep Search
        if model_id in ['neural-search', 'research', 'research-pro']:
            # Natürlichsprachliche Query für neuronale/research Suche
            query_parts = [
                f"Find comprehensive and detailed information about {mine_name} mine",
                f"including specific restoration costs, closure costs, environmental liabilities with exact dollar amounts",
                f"precise GPS coordinates, location data, latitude and longitude in decimal degrees",
                f"current operator, owner, parent company, mining company ownership structure",
                f"production data, annual output in tonnes, historical production figures",
                f"mine area in square kilometers, mine type (open-pit, underground)",
                f"operational status, start and end dates of production"
            ]
            
            if country:
                query_parts.append(f"located in {country}")
            
            if commodity:
                query_parts.append(f"producing {commodity}")
            
            if region:
                query_parts.append(f"in the {region} region")
            
            # Spezielle Anweisungen für Research-Modelle
            if 'research' in model_id:
                query_parts.extend([
                    "Search technical reports, NI 43-101 documents, annual reports",
                    "Extract data from PDFs, government databases, company filings",
                    "Cross-reference multiple sources for accuracy",
                    "Include data from subpages and embedded documents"
                ])
            
            return ' '.join(query_parts)
        
        else:
            # Keyword-basierte Query für similarity search
            keywords = [
                f'"{mine_name}"',
                'mine OR mining',
                'restoration costs OR closure costs OR "asset retirement obligation" OR ARO',
                'coordinates OR latitude OR longitude OR GPS',
                'operator OR owner OR company',
                'production OR output OR tonnage',
                'technical report OR feasibility study',
                'PDF OR document'
            ]
            
            if country:
                keywords.append(country)
            
            if commodity:
                keywords.append(commodity)
            
            return ' '.join(keywords)
    
    def _build_content_from_results(self, exa_response: Dict, mine_name: str) -> str:
        """Erstelle strukturierten Content aus Exa-Ergebnissen"""
        content_parts = []
        
        content_parts.append(f"**Exa Neural Search Ergebnisse für {mine_name}:**\n")
        
        for idx, result in enumerate(exa_response.get('results', []), 1):
            content_parts.append(f"\n[Quelle {idx}] {result.get('title', 'Unbekannt')}")
            content_parts.append(f"URL: {result.get('url', '')}")
            content_parts.append(f"Score: {result.get('score', 0):.3f}")
            
            # Text-Content
            if result.get('text'):
                content_parts.append(f"\nInhalt:\n{result['text'][:2000]}...")
            
            # Highlights wenn vorhanden
            if result.get('highlights'):
                content_parts.append("\nWichtige Passagen:")
                for highlight in result['highlights'][:3]:
                    content_parts.append(f"• {highlight}")
            
            content_parts.append("")
        
        return '\n'.join(content_parts)
    
    def _extract_exa_sources(self, response: Dict) -> List[Dict[str, Any]]:
        """Extrahiere Quellen aus Exa Response"""
        sources = []
        
        for idx, result in enumerate(response.get('results', []), 1):
            source = {
                'type': 'url',
                'value': result.get('url', ''),
                'title': result.get('title', ''),
                'description': result.get('snippet', '')[:200] if result.get('snippet') else '',
                'score': result.get('score', 0),
                'published_date': result.get('published_date', ''),
                'author': result.get('author', ''),
                'provider': 'exa'
            }
            
            # Füge Highlights als zusätzliche Info hinzu
            if result.get('highlights'):
                source['highlights'] = result['highlights'][:3]
            
            sources.append(source)
        
        return sources
    
    def _get_mining_domains(self, country: str, discovered_sources: List[Dict] = None) -> List[str]:
        """Hole Mining-spezifische Domains"""
        domains = [
            "mining.com",
            "minexplore.com", 
            "northernminer.com",
            "miningweekly.com",
            "mining-technology.com",
            "resourceworld.com",
            "infomine.com",
            "kitco.com"
        ]
        
        # ÄNDERUNG 08.07.2025: Füge Domains aus discovered_sources hinzu
        if discovered_sources:
            import urllib.parse
            for source in discovered_sources:
                url = source.get('url', '')
                if url:
                    try:
                        parsed = urllib.parse.urlparse(url)
                        if parsed.netloc and parsed.netloc not in domains:
                            domains.append(parsed.netloc)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse URL {url}: {e}")
                        pass
        
        # Länderspezifische Domains hinzufügen
        if country:
            country_config = get_country_config(country)
            priority_domains = country_config.get('priority_domains', [])
            domains.extend(priority_domains)
        
        return domains
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return "🔑 Exa API-Key ungültig.\n→ Bitte prüfen Sie Ihre .env Datei."
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 402:
            return "💳 Exa API-Guthaben aufgebraucht.\n→ Bitte laden Sie Ihr Konto auf."
        
        else:
            try:
                error_data = response.json()
                return f"Exa API Fehler: {error_data.get('detail', error_data.get('error', 'Unbekannter Fehler'))}"
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Could not parse error response: {e}")
                return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[EXA] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[EXA] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def health_check(self) -> bool:
        """Prüfe ob Exa API erreichbar ist"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.api_url}/health",
                    headers={
                        "x-api-key": self.api_key
                    }
                )
                return response.status_code in [200, 401]  # 401 = Key ungültig, aber API erreichbar
        except (httpx.RequestError, httpx.HTTPStatusError, Exception) as e:
            logger.warning(f"Exa API health check failed: {e}")
            return False
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """Gibt den System-Prompt für Exa zurück"""
        return """Du bist ein Mining-Recherche-Spezialist der Exa's neuronale Suche nutzt.
        
Fokussiere dich auf:
- Semantische Verbindungen zwischen Mining-Informationen
- Technische Dokumente und Berichte
- Mining-spezifische Domains und Quellen
- Ähnliche Minen und Projekte
- Detaillierte Betreiber- und Kostendaten

Nutze Exa's neuronale Suchfähigkeiten für tiefgehende semantische Analysen."""
    
    # OPENROUTER WORKFLOW HELPER METHODS
    
    async def _send_to_ai_model(
        self,
        content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        discovered_sources: List[Dict] = None
    ) -> str:
        """Sendet EXA-Ergebnisse an AI-Modell für strukturierte Extraktion (wie OpenRouter)"""
        
        # Nutze unified_extraction_service
        from minesearch.unified_extraction_service import get_unified_extractor
        import os
        
        try:
            # Hole API-Key aus Environment
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if not openrouter_key:
                logger.error("[EXA] OPENROUTER_API_KEY nicht gefunden - verwende Fallback")
                return content  # Fallback: Return raw content
            
            # Nutze Unified Extractor für AI-Verarbeitung
            extractor = get_unified_extractor(openrouter_key)
            
            # AI-Extraktion durchführen
            result = await extractor.extract_from_raw_content(
                raw_content=content,
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region
            )
            
            # Konvertiere strukturierte Daten zurück zu Text für DataExtractor
            ai_response = self._convert_structured_to_text(result, mine_name)
            
            logger.info(f"[EXA] AI-Verarbeitung erfolgreich für {mine_name}")
            return ai_response
            
        except Exception as e:
            logger.error(f"[EXA] Fehler bei AI-Verarbeitung: {e}")
            # Fallback: Return raw content
            return content
    
    def _convert_structured_to_text(self, structured_data: Dict[str, Any], mine_name: str) -> str:
        """Konvertiert strukturierte Daten zurück zu Text für DataExtractor"""
        
        text_parts = [f"Mining Information for {mine_name}:"]
        
        for field, value in structured_data.items():
            if field.startswith('_'):
                continue  # Skip metadata
            
            if value and str(value).strip():
                text_parts.append(f"{field}: {value}")
        
        return "\n".join(text_parts)
    
    def _apply_quality_gates(self, extracted_data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """Anwendung der Quality Gates (wie OpenRouter)"""
        
        # Kopiere OpenRouter Quality Gates
        data = extracted_data.get('data', {})
        
        # Verhindere "Koordinaten" als Betreiber (wie OpenRouter)
        if data.get('Betreiber'):
            betreiber = str(data['Betreiber']).strip()
            if betreiber.lower() in ['koordinaten', 'coordinates', 'coords', 'koordinate'] or 'koordinaten:' in betreiber.lower():
                logger.warning(f"[EXA] Ungültiger Betreiber entfernt: {betreiber}")
                data['Betreiber'] = ""
                # Entferne auch aus data_with_sources
                if 'Betreiber' in extracted_data.get('data_with_sources', {}):
                    extracted_data['data_with_sources']['Betreiber'] = {"value": "", "sources": []}
        
        # Validiere Restaurationskosten (wie OpenRouter)
        if data.get('Restaurationskosten'):
            resto = data['Restaurationskosten']
            logger.info(f"[EXA-DEBUG] Restaurationskosten extrahiert: '{resto}'")
            
            # Prüfe auf verdächtige Werte
            suspicious_values = ['USD$1.0 million', 'CAD$1.0 million', '$1.0 million', '1.0 million', 
                               'USD$1 million', 'CAD$1 million', '$1 million', '1 million',
                               'CAD$10000.0 million', 'USD$10000.0 million']
            if resto in suspicious_values or (isinstance(resto, str) and any(sv in resto for sv in suspicious_values)):
                logger.warning(f"[EXA] Verdächtiger Restaurationswert entfernt: {resto}")
                data['Restaurationskosten'] = ""
                # Entferne auch aus data_with_sources
                if 'Restaurationskosten' in extracted_data.get('data_with_sources', {}):
                    extracted_data['data_with_sources']['Restaurationskosten'] = {"value": "", "sources": []}
        
        return extracted_data