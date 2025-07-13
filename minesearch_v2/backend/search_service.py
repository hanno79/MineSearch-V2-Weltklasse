"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored MineSearchService (CLAUDE.md konform)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from utils import normalize_accents, generate_name_variants, generate_multilingual_search_terms, get_country_config
from data_extraction import DataExtractor, assign_sources_to_data
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from cache_service import get_cache_service, cached_search
from search_service_legacy import LegacySearchFunctions

logger = logging.getLogger(__name__)


class MineSearchService(LegacySearchFunctions):
    """Hauptklasse für Mining-Suchen mit Provider-Unterstützung"""
    
    def __init__(self):
        super().__init__()
        # Provider-basierte Architektur
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
    
    async def search_mine(self, mine_name: str, model: str, country: Optional[str] = None, 
                         commodity: Optional[str] = None, region: Optional[str] = None, 
                         _is_auto_enhanced: bool = False) -> Dict[str, Any]:
        """
        Hauptsuchfunktion für Mining-Informationen
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Zu verwendendes Modell
            region: Region (optional)
            _is_auto_enhanced: Intern - verhindert Rekursion
            
        Returns:
            Strukturiertes Suchergebnis
        """
        logger.info(f"[SEARCH] Starte Suche für: {mine_name}, Land: {country}, Modell: {model}")
        
        # Cache-Check
        cache_key = f"{mine_name}_{country}_{model}_{commodity}_{region}"
        cached_result = await self._check_cache(cache_key)
        if cached_result:
            logger.info(f"[SEARCH] Cache-Hit für {mine_name}")
            return cached_result
        
        # Prüfe ob Modell verfügbar ist
        if not self.registry.is_model_available(f"perplexity:{model}"):
            # Fallback auf direkte API-Nutzung
            return await self._legacy_search(mine_name, country, commodity, model, region)
        
        # Verwende Provider-basierte Suche
        try:
            result = await self._search_with_provider(mine_name, country, commodity, model, region)
            
            # Cache das Ergebnis
            if result.get('success'):
                await self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"[SEARCH] Provider-Fehler für {mine_name}: {e}")
            # Fallback auf Legacy-Suche
            return await self._legacy_search(mine_name, country, commodity, model, region)
    
    async def enhanced_search(self, mine_name: str, model: str, country: Optional[str] = None,
                            commodity: Optional[str] = None, region: Optional[str] = None, 
                            _from_auto: bool = False) -> Dict[str, Any]:
        """
        Erweiterte Zwei-Phasen-Suche für umfangreichere Ergebnisse
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Zu verwendendes Modell
            region: Region (optional)
            _from_auto: Verhindert Rekursion
            
        Returns:
            Erweiterte Suchergebnisse
        """
        logger.info(f"[ENHANCED] Starte erweiterte Zwei-Phasen-Suche für: {mine_name}")
        
        # Phase 1: Initiale Suche mit Rekursionsschutz
        phase1_result = await self.search_mine(
            mine_name, country, commodity, model, region, 
            _is_auto_enhanced=_from_auto
        )
        
        if not phase1_result.get('success') or not phase1_result.get('data'):
            return phase1_result
        
        # Extrahiere Quellen für Phase 2
        sources = phase1_result['data'].get('sources', [])
        logger.info(f"[ENHANCED] Phase 1 Quellen gefunden: {len(sources)}")
        
        # Filtere valide Quellen
        valid_sources = [s for s in sources if 
            s.get('type') == 'url' or 
            (s.get('type') == 'document' and len(s.get('value', '')) > 5)]
        
        if not valid_sources:
            logger.info("[ENHANCED] Keine validen Quellen für Phase 2 gefunden")
            return phase1_result
        
        # Phase 2: Vertiefende Suche mit gefundenen Quellen
        phase2_results = []
        for i, source in enumerate(valid_sources[:5]):  # Limitiere auf 5 Quellen
            try:
                phase2_result = await self._search_phase2(source, mine_name, country, model)
                if phase2_result.get('success'):
                    phase2_results.append(phase2_result)
            except Exception as e:
                logger.warning(f"[ENHANCED] Phase 2 Quelle {i+1} fehlgeschlagen: {e}")
        
        # Kombiniere Phase 1 und Phase 2 Ergebnisse
        combined_result = self._combine_phase_results(phase1_result, phase2_results)
        
        logger.info(f"[ENHANCED] Erweiterte Suche abgeschlossen: {len(phase2_results)} zusätzliche Quellen")
        return combined_result
    
    async def _search_with_provider(self, mine_name: str, country: Optional[str],
                                  commodity: Optional[str], model: str, 
                                  region: Optional[str]) -> Dict[str, Any]:
        """
        Suche mit Provider-System
        
        Args:
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff
            model: Modell
            region: Region
            
        Returns:
            Provider-basiertes Suchergebnis
        """
        # Hole Provider für Perplexity
        provider = self.registry.get_provider("perplexity")
        if not provider:
            raise Exception("Perplexity Provider nicht verfügbar")
        
        # Bereite Suchkontext vor
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Erstelle Suchanfrage
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('restoration_cost_terms', ['restoration costs'])
        
        query = self._build_search_query(
            mine_name, name_variants, country, currency, restoration_terms
        )
        
        # Provider-Optionen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': currency,
            'name_variants': name_variants,
            'multilingual_terms': multilingual_terms
        }
        
        # Führe Suche durch
        result = await provider.search(query, model, options)
        
        # Verarbeite Ergebnis
        return await self._process_search_result(result, mine_name, country, model)
    
    async def _legacy_search(self, mine_name: str, country: Optional[str],
                           commodity: Optional[str], model: str, 
                           region: Optional[str]) -> Dict[str, Any]:
        """
        Legacy-Suche mit direkter API-Nutzung
        
        Args:
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff
            model: Modell
            region: Region
            
        Returns:
            Legacy-Suchergebnis
        """
        logger.info(f"[LEGACY] Verwende Legacy-Suche für {mine_name}")
        
        # Bereite Suchkontext vor
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('restoration_cost_terms', ['restoration costs'])
        
        # Erstelle Suchanfrage
        query = self._build_search_query(
            mine_name, name_variants, country, currency, restoration_terms
        )
        
        # Modell-Konfiguration
        model_config = {
            "model": model,
            "temperature": 0.2,
            "max_tokens": 4000,
            "top_p": 0.9
        }
        
        # API-Aufruf
        api_result = await self._call_perplexity_api(query, model_config)
        
        if not api_result.get('success'):
            return {
                "success": False,
                "error": api_result.get('error', 'Legacy-API-Fehler'),
                "data": {}
            }
        
        # Verarbeite Legacy-Ergebnis
        content = api_result.get('content', '')
        sources = api_result.get('sources', [])
        
        # Validiere Ergebnis
        is_valid, confidence = self._validate_result(content, mine_name, name_variants)
        
        if not is_valid:
            return {
                "success": False,
                "error": "Unzureichende Suchergebnisse",
                "data": {}
            }
        
        # Extrahiere strukturierte Daten
        structured_data = self.data_extractor.extract_structured_data(
            content, mine_name, name_variants
        )
        
        # Füge Quellen zu strukturierten Daten hinzu
        structured_data = assign_sources_to_data(
            structured_data, content, sources
        )
        
        # Berechne Datenqualität
        quality_metrics = self._calculate_data_quality(structured_data)
        
        return {
            "success": True,
            "data": {
                "raw_content": content,
                "structured_data": structured_data,
                "sources": sources,
                "quality_metrics": quality_metrics,
                "model_used": model,
                "confidence": confidence,
                "search_type": "legacy"
            }
        }
    
    async def _process_search_result(self, result: SearchResult, mine_name: str, 
                                   country: Optional[str], model: str) -> Dict[str, Any]:
        """
        Verarbeitet Provider-Suchergebnis
        
        Args:
            result: Provider-Suchergebnis
            mine_name: Name der Mine
            country: Land
            model: Verwendetes Modell
            
        Returns:
            Verarbeitetes Suchergebnis
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error or "Provider-Fehler",
                "data": {}
            }
        
        # Extrahiere Daten
        content = result.content or ""
        sources = result.sources or []
        structured_data = result.structured_data or {}
        
        # Falls keine strukturierten Daten vorhanden, extrahiere sie
        if not structured_data and content:
            name_variants = generate_name_variants(mine_name)
            structured_data = self.data_extractor.extract_structured_data(
                content, mine_name, name_variants
            )
            
            # Füge Quellen hinzu
            structured_data = assign_sources_to_data(
                structured_data, content, sources
            )
        
        # Berechne Qualitäts-Metriken
        quality_metrics = self._calculate_data_quality(structured_data)
        
        return {
            "success": True,
            "data": {
                "raw_content": content,
                "structured_data": structured_data,
                "sources": sources,
                "quality_metrics": quality_metrics,
                "model_used": model,
                "confidence": result.metadata.get("confidence", 0.8),
                "search_type": "provider"
            }
        }
    
    async def _search_phase2(self, source: Dict, mine_name: str, 
                           country: Optional[str], model: str) -> Dict[str, Any]:
        """
        Phase 2 Suche mit spezifischer Quelle
        
        Args:
            source: Quellen-Information
            mine_name: Name der Mine
            country: Land
            model: Modell
            
        Returns:
            Phase 2 Suchergebnis
        """
        # Erstelle spezifische Query für diese Quelle
        query = self._build_phase2_query(source, mine_name, country)
        
        # Modell-Konfiguration für Phase 2
        model_config = {
            "model": model,
            "temperature": 0.1,  # Niedrigere Temperatur für präzise Extraktion
            "max_tokens": 2000
        }
        
        # API-Aufruf
        api_result = await self._call_perplexity_api(query, model_config)
        
        if api_result.get('success'):
            content = api_result.get('content', '')
            name_variants = generate_name_variants(mine_name)
            
            # Extrahiere strukturierte Daten
            structured_data = self.data_extractor.extract_structured_data(
                content, mine_name, name_variants
            )
            
            return {
                "success": True,
                "data": {
                    "structured_data": structured_data,
                    "raw_content": content,
                    "source": source
                }
            }
        
        return {"success": False, "error": api_result.get('error', 'Phase 2 Fehler')}
    
    def _build_phase2_query(self, source: Dict[str, str], mine_name: str, 
                          country: Optional[str]) -> str:
        """Erstellt Phase 2 Query für spezifische Quelle"""
        location = f" in {country}" if country else ""
        
        if source.get('type') == 'url':
            return f"""
            Basierend auf der Quelle {source['value']}, finde spezifische Details über die Mine "{mine_name}"{location}:
            
            1. Exakte GPS-Koordinaten
            2. Aktueller Betreiber/Eigentümer
            3. Rohstoffproduktion (Mengen und Werte)
            4. Restaurations-/Rekultivierungskosten
            5. Mitarbeiterzahl
            6. Umweltauswirkungen
            
            Antworte nur mit verifizierten Informationen aus dieser spezifischen Quelle.
            """
        else:
            return f"""
            Analysiere folgende Information über die Mine "{mine_name}"{location}:
            
            {source['value'][:500]}...
            
            Extrahiere:
            1. GPS-Koordinaten
            2. Betreiber
            3. Produktionsdaten
            4. Kosten
            5. Status
            
            Gib nur die konkret erwähnten Fakten an.
            """
    
    def _combine_phase_results(self, phase1: Dict, phase2_results: List[Dict]) -> Dict:
        """Kombiniert Phase 1 und Phase 2 Ergebnisse"""
        combined_data = phase1['data']['structured_data'].copy()
        all_sources = phase1['data']['sources'].copy()
        
        # Integriere Phase 2 Daten
        for phase2 in phase2_results:
            if phase2.get('success') and phase2.get('data'):
                phase2_data = phase2['data'].get('structured_data', {})
                
                # Aktualisiere leere Felder mit Phase 2 Daten
                for key, value in phase2_data.items():
                    if value and not combined_data.get(key):
                        combined_data[key] = value
                
                # Füge Phase 2 Quelle hinzu
                if phase2['data'].get('source'):
                    all_sources.append(phase2['data']['source'])
        
        # Aktualisiere Qualitäts-Metriken
        quality_metrics = self._calculate_data_quality(combined_data)
        
        # Erstelle kombiniertes Ergebnis
        result = phase1.copy()
        result['data'].update({
            'structured_data': combined_data,
            'sources': all_sources,
            'quality_metrics': quality_metrics,
            'search_type': 'enhanced_two_phase',
            'phase2_sources_used': len(phase2_results)
        })
        
        return result
    
    async def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Prüft Cache auf vorhandenes Ergebnis"""
        try:
            cache_service = get_cache_service()
            return await cache_service.get(cache_key)
        except Exception as e:
            logger.debug(f"[CACHE] Cache-Check fehlgeschlagen: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict):
        """Speichert Ergebnis im Cache"""
        try:
            cache_service = get_cache_service()
            await cache_service.set(cache_key, result, ttl=3600)  # 1 Stunde TTL
        except Exception as e:
            logger.debug(f"[CACHE] Cache-Speicherung fehlgeschlagen: {e}")


# Globale Service-Instanz
search_service = MineSearchService()