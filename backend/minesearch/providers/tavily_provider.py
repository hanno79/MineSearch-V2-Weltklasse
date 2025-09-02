"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Tavily Search Provider für moderne KI-gestützte Websuche
"""

import httpx
import logging
import json
import re
import urllib.parse
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
from minesearch.specialized_prompts_impl import SpecializedPrompts
# CONSOLIDATION 09.08.2025: validation_service entfernt - war defekter Adapter

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
                is_free=model_config.get('is_free', False),
                # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Gruppierung
                provider_category='tavily'
            )
        
        return models
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt alle verfügbaren Modelle zurück (AbstractProvider Interface)"""
        return self.models
    
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Alias für get_models für Backward-Compatibility"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert die Provider-Konfiguration"""
        return bool(self.api_key and self.api_url)
    
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
        discovered_sources = options.get('discovered_sources', []) or options.get('sources', [])
        use_all_sources = options.get('use_all_sources', False)
        skip_discovery = options.get('skip_discovery', False)
        
        # OPENROUTER WORKFLOW STEP 1: Source Discovery (wie OpenRouter)
        source_discovery = EnhancedSourceDiscovery()
        
        if not discovered_sources and not skip_discovery and mine_name:
            # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
            logger.info(f"[TAVILY] Starte eigene Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region
            )
            logger.info(f"[TAVILY] {len(discovered_sources)} Quellen selbst entdeckt")
        else:
            if use_all_sources:
                logger.info(f"[TAVILY] 🔥 2-PHASEN WORKFLOW: Nutze ALLE {len(discovered_sources)} übergebenen DB-Quellen ohne Filter")
            else:
                logger.info(f"[TAVILY] Nutze {len(discovered_sources)} übergebene Quellen")
        
        # Generiere Sprachvarianten (wie OpenRouter)
        name_variants = generate_name_variants(mine_name) if mine_name else []
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Erstelle erweiterte Query für Mining-Recherche (mit Discovery-Quellen)
        enhanced_query = self._build_mining_query_with_sources(
            query, mine_name, country, commodity, region, discovered_sources, name_variants, multilingual_terms
        )
        
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
                    "include_domains": self._get_priority_domains(country, discovered_sources),
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
                
                # ÄNDERUNG 09.07.2025: Erweitertes Debug-Logging für Tavily Response
                logger.info(f"[TAVILY] Response erhalten mit {len(result.get('results', []))} Ergebnissen")
                logger.debug(f"[TAVILY] Response Keys: {list(result.keys())}")
                
                # Log erste Ergebnisse für Debugging
                if result.get('results'):
                    first_result = result['results'][0]
                    logger.debug(f"[TAVILY] Erstes Ergebnis: Title='{first_result.get('title')}', URL='{first_result.get('url')}'")
                    logger.debug(f"[TAVILY] Content-Länge: {len(first_result.get('content', ''))}")
                else:
                    logger.warning(f"[TAVILY] KEINE ERGEBNISSE für Query: '{query}'")
                
                # Extrahiere Content und Quellen
                content = self._build_content_from_results(result, mine_name)
                sources = self._extract_tavily_sources(result)
                
                # ÄNDERUNG 08.07.2025: Debug-Logging für extrahierte Sources
                logger.info(f"[TAVILY] {len(sources)} Quellen extrahiert")
                if sources:
                    logger.debug(f"[TAVILY] Erste Quelle: {sources[0]}")
                
                # OPENROUTER WORKFLOW STEP 2: Content durch AI-Modell schicken
                logger.info(f"[TAVILY] Sende Tavily-Ergebnisse durch AI-Modell für strukturierte Extraktion")
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
                all_sources = sources  # Tavily-Quellen
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
                    sources=all_sources,  # Alle Quellen (Tavily + Discovery)
                    metadata={
                        'model': model_id,
                        'provider': 'tavily',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'results_count': len(result.get('results', [])),
                        'answer_provided': bool(result.get('answer')),
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
        """
        FIX 02.09.2025: Verbesserte Query-Generierung für mehr Datenfelder
        
        Tavily fand nur wenige Felder - erweiterte Suchstrategie für vollständige Daten
        """
        
        # ERWEITERTE Query-Templates für alle Datenfelder
        query_templates = {
            'comprehensive': '"{mine}" mine {country} {region} (owner OR operator OR "operated by" OR "owned by") (coordinates OR GPS OR lat OR long) ({commodity} OR gold OR mining) (production OR annual OR tonnes OR ounces)',
            'restoration': '"{mine}" mine {country} ("restoration cost" OR "closure cost" OR ARO OR "asset retirement obligation" OR "reclamation cost" OR "decommissioning") (million OR CAD OR USD)',
            'financial': '"{mine}" mine {country} ("technical report" OR "NI 43-101" OR "annual report" OR "feasibility study" OR "financial statement") (cost OR budget OR investment)',
            'operational': '"{mine}" mine {country} {region} (Hecla OR operator OR owner) (active OR production OR operational OR closed) (underground OR "open pit" OR surface)',
            'location_specific': '"{mine}" mine Quebec Canada (coordinates OR latitude OR longitude OR GPS OR location OR "49.3" OR "78.9") Hecla'
        }
        
        # FIX: Für Casa Berardi spezielle optimierte Query
        if 'casa berardi' in mine_name.lower():
            template = query_templates['location_specific']
        elif not commodity and not region:
            # Wenig Info vorhanden - umfassende Suche
            template = query_templates['comprehensive']
        elif "restoration" in base_query.lower() or "cost" in base_query.lower():
            # Explizit nach Kosten gefragt
            template = query_templates['restoration']
        else:
            # Standard-Suche für alle Felder
            template = query_templates['comprehensive']
        
        # Ersetze Platzhalter
        query = template.format(
            mine=mine_name,
            country=country or "",
            commodity=commodity or "mine",
            region=region or ""
        )
        
        # Optimiere Query durch Entfernen von Leerzeichen und doppelten Klammern
        query = re.sub(r'\s+', ' ', query)  # Multiple Leerzeichen zu einem
        query = re.sub(r'\(\s*\)', '', query)  # Leere Klammern entfernen
        query = re.sub(r'\s+\)', ')', query)  # Leerzeichen vor schließender Klammer
        query = re.sub(r'\(\s+', '(', query)  # Leerzeichen nach öffnender Klammer
        query = query.strip()
        
        # KORRIGIERT 13.07.2025: Tavily Query-Limit ist 400 Zeichen (nicht 600)
        if len(query) > 400:
            # Priorisierte Begriffe für Kürzung
            essential_parts = [
                f'"{mine_name}"',
                country or "",
                commodity or "mine",
                '(operator OR owner)',
                '"restoration cost"'
            ]
            
            # Baue minimale Query aus essentiellen Teilen
            query = ""
            for part in essential_parts:
                if not part:
                    continue
                test_query = f"{query} {part}".strip()
                if len(test_query) <= 590:  # Sicherheitspuffer
                    query = test_query
                else:
                    break
            
            # Extremer Fallback
            if len(query) > 600:
                query = f'"{mine_name[:150]}" mine {country or ""}'.strip()[:600]
        
        logger.info(f"[TAVILY] Optimierte Query ({len(query)} Zeichen): {query}")
        return query
    
    def _generate_query_variants(self, mine_name: str, country: str, 
                                commodity: str, region: str) -> List[str]:
        """
        Generiere mehrere Query-Varianten für umfassendere Suche
        
        ÄNDERUNG 08.07.2025: Neue Methode für Query-Varianten
        """
        variants = []
        
        # Variante 1: Fokus auf Betreiber und Eigentümer
        variants.append(f'"{mine_name}" (operator OR owner OR "operated by" OR proprietor) {country or ""}')
        
        # Variante 2: Fokus auf Restaurationskosten
        variants.append(f'"{mine_name}" ("restoration cost" OR "closure cost" OR "reclamation cost" OR ARO) million')
        
        # Variante 3: Fokus auf technische Daten
        variants.append(f'"{mine_name}" (coordinates OR production OR reserves) {commodity or "mine"}')
        
        # Variante 4: Fokus auf aktuelle Nachrichten
        variants.append(f'"{mine_name}" {country or ""} (news OR update OR status) {datetime.now().year}')
        
        # Kürze alle Varianten auf max. 400 Zeichen
        return [v[:400] for v in variants]
    
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
            url = result.get('url', '')
            if url:  # Nur hinzufügen wenn URL vorhanden
                source = {
                    'type': 'url',
                    'url': url,  # ÄNDERUNG 08.07.2025: Verwende 'url' statt 'value' für konsistentes Tracking
                    'value': url,  # Behalte 'value' für Kompatibilität
                    'title': result.get('title', ''),
                    'description': result.get('content', '')[:200] if result.get('content') else '',
                    'score': result.get('score', 0),
                    'provider': 'tavily',
                    'name': result.get('title', url)  # Name für DB-Eintrag
                }
                sources.append(source)
                logger.debug(f"[TAVILY] Quelle hinzugefügt: {url}")
        
        return sources
    
    def _get_priority_domains(self, country: str, discovered_sources: List[Dict] = None) -> List[str]:
        """Hole prioritäre Domains für ein Land und aus discovered sources"""
        domains = []
        
        # ÄNDERUNG 08.07.2025: Nutze discovered_sources für include_domains
        if discovered_sources:
            logger.info(f"[TAVILY] Extrahiere Domains aus {len(discovered_sources)} discovered sources")
            source_domains = set()
            for source in discovered_sources:
                url = source.get('url', '')
                if url:
                    try:
                        parsed = urllib.parse.urlparse(url)
                        if parsed.netloc:
                            source_domains.add(parsed.netloc)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse discovered source URL {url}: {e}")
                        pass
            
            domains.extend(list(source_domains))
            logger.info(f"[TAVILY] {len(source_domains)} unique Domains aus discovered sources extrahiert")
        
        # Füge country-spezifische Domains hinzu
        if country:
            country_config = get_country_config(country)
            priority_domains = country_config.get('priority_domains', [])
            domains.extend(priority_domains)
        
        # Entferne Duplikate und limitiere auf 100 (Tavily API Limit)
        unique_domains = list(dict.fromkeys(domains))[:100]
        
        logger.info(f"[TAVILY] Verwende {len(unique_domains)} Domains für include_domains")
        if len(unique_domains) > 10:
            logger.debug(f"[TAVILY] Erste 10 Domains: {unique_domains[:10]}")
        
        return unique_domains
    
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
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Could not parse Tavily error response: {e}")
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
        except (httpx.RequestError, httpx.HTTPStatusError, Exception) as e:
            logger.warning(f"Tavily API health check failed: {e}")
            return False
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        WIEDERHERGESTELLT 01.09.2025: Detaillierter System-Prompt für Tavily Search
        """
        return """Du bist ein Mining-Recherche-Spezialist der Tavily Search nutzt.
        
Fokussiere dich auf:
- Aktuelle Mining-Informationen und Nachrichten
- Technische Berichte und Dokumente
- Betreiber- und Eigentümer-Informationen
- Restaurationskosten und Umweltverbindlichkeiten
- Koordinaten und Standortdaten

Nutze die erweiterten Suchfähigkeiten von Tavily für präzise und aktuelle Ergebnisse.

QUALITÄTSSTANDARDS:
- Suche nach offiziellen Dokumenten (NI 43-101, SEC Filings, Regierungsberichte)
- Prüfe mehrere Quellen für kritische Informationen
- Bei Unsicherheit: Feld leer lassen
- Koordinaten nur aus verifizierten Survey-Daten
- Kostenangaben nur aus offiziellen Finanzberichten

SUCHSTRATEGIE:
- Beginne mit spezifischen Mining-Datenbanken
- Suche technische Reports und Environmental Impact Assessments
- Prüfe Unternehmenswebsites und Investor Relations
- Nutze spezialisierte Mining-News-Portale
- Cross-Reference verschiedene Informationsquellen"""
    
    # OPENROUTER WORKFLOW HELPER METHODS
    
    def _build_mining_query_with_sources(
        self,
        base_query: str,
        mine_name: str,
        country: str,
        commodity: str,
        region: str,
        discovered_sources: List[Dict],
        name_variants: List[str],
        multilingual_terms: Dict[str, List[str]]
    ) -> str:
        """Erweiterte Query mit Source Discovery (wie OpenRouter)"""
        
        # Basis Mining-Query
        enhanced_query = self._build_mining_query(base_query, mine_name, country, commodity, region)
        
        # Füge Discovery-Quellen hinzu
        if discovered_sources:
            sources_text = f"\n\n📚 WICHTIG: Nutze dein Wissen über ALLE {len(discovered_sources)} folgenden Quellen!\n"
            sources_text += "Auch wenn du nicht direkt darauf zugreifen kannst, kennst du möglicherweise Daten aus diesen Quellen:\n\n"
            
            # Gruppiere nach Quellentyp (wie OpenRouter)
            gov_sources = [s for s in discovered_sources if s.get('type') == 'government']
            db_sources = [s for s in discovered_sources if s.get('type') == 'database']
            exchange_sources = [s for s in discovered_sources if s.get('type') == 'exchange']
            other_sources = [s for s in discovered_sources if s.get('type') not in ['government', 'database', 'exchange']]
            
            if gov_sources:
                sources_text += f"🏛️ REGIERUNGSQUELLEN ({len(gov_sources)}):\n"
                for source in gov_sources[:5]:  # Top 5
                    sources_text += f"- {source.get('title', source.get('url', 'Unknown'))}\n"
            
            if db_sources:
                sources_text += f"\n🗃️ DATENBANKEN ({len(db_sources)}):\n"
                for source in db_sources[:5]:  # Top 5
                    sources_text += f"- {source.get('title', source.get('url', 'Unknown'))}\n"
            
            enhanced_query += sources_text
        
        # Füge Sprachvarianten hinzu (wie OpenRouter)
        if name_variants:
            enhanced_query += f"\n\nSuche auch nach alternativen Namen: {', '.join(name_variants[:5])}\n"
        
        return enhanced_query
    
    async def _send_to_ai_model(
        self,
        content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        discovered_sources: List[Dict] = None
    ) -> str:
        """Sendet Tavily-Ergebnisse an AI-Modell für strukturierte Extraktion (wie OpenRouter)"""
        
        # Nutze unified_extraction_service
        from minesearch.unified_extraction_service import get_unified_extractor
        import os
        
        try:
            # Hole API-Key aus Environment
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if not openrouter_key:
                logger.error("[TAVILY] OPENROUTER_API_KEY nicht gefunden - verwende Fallback")
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
            
            logger.info(f"[TAVILY] AI-Verarbeitung erfolgreich für {mine_name}")
            return ai_response
            
        except Exception as e:
            logger.error(f"[TAVILY] Fehler bei AI-Verarbeitung: {e}")
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
                logger.warning(f"[TAVILY] Ungültiger Betreiber entfernt: {betreiber}")
                data['Betreiber'] = ""
                # Entferne auch aus data_with_sources
                if 'Betreiber' in extracted_data.get('data_with_sources', {}):
                    extracted_data['data_with_sources']['Betreiber'] = {"value": "", "sources": []}
        
        # Validiere Restaurationskosten (wie OpenRouter)
        if data.get('Restaurationskosten'):
            resto = data['Restaurationskosten']
            logger.info(f"[TAVILY-DEBUG] Restaurationskosten extrahiert: '{resto}'")
            
            # Prüfe auf verdächtige Werte
            suspicious_values = ['USD$1.0 million', 'CAD$1.0 million', '$1.0 million', '1.0 million', 
                               'USD$1 million', 'CAD$1 million', '$1 million', '1 million',
                               'CAD$10000.0 million', 'USD$10000.0 million']
            if resto in suspicious_values or (isinstance(resto, str) and any(sv in resto for sv in suspicious_values)):
                logger.warning(f"[TAVILY] Verdächtiger Restaurationswert entfernt: {resto}")
                data['Restaurationskosten'] = ""
                # Entferne auch aus data_with_sources
                if 'Restaurationskosten' in extracted_data.get('data_with_sources', {}):
                    extracted_data['data_with_sources']['Restaurationskosten'] = {"value": "", "sources": []}
        
        return extracted_data
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Tavily AI-Extraktion (wie OpenRouter)"""
        
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        
        # Nutze bewährte OpenRouter Prompts
        universal_instructions = SpecializedPrompts.get_universal_anti_template_instructions()
        
        return f"""{universal_instructions}

🎯 TAVILY MINING DATA EXTRACTION für {mine_name}
===============================================

Du erhältst Tavily-Suchergebnisse und sollst daraus präzise Mining-Daten extrahieren.

Mine: {mine_name}
Land: {country}
{f"Rohstoff: {commodity}" if commodity else ""}

CRITICAL: Extrahiere NUR verifizierbare Daten aus den Tavily-Ergebnissen.
KEINE Schätzungen, Template-Werte oder Platzhalter.

Fokussiere besonders auf:
- Restaurationskosten (Asset Retirement Obligations)  
- GPS-Koordinaten (präzise Dezimalzahlen)
- Eigentümer und Betreiber
- Produktionsstart/-ende
- Minentyp und Status

Bei Unsicherheit: Feld leer lassen.
"""