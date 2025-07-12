"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Core Funktionen für Multi-Provider Search Service
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse

from config import config, Config, SOURCE_SHARING_CONFIG
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config
from source_aggregator import SourceAggregator
from search_phases import SearchPhaseManager
from search_utils import SearchQueryBuilder, DataQualityCalculator, SourceCacheManager, ResultCombiner
from search_result_combiner import SearchResultCombiner
from search_async_utils import AsyncSearchUtils
from shared_sources_analyzer import SharedSourcesAnalyzer
from database import db_manager, Source

logger = logging.getLogger(__name__)


class SearchServiceCore:
    """Core-Funktionen für den Multi-Provider Search Service"""
    
    def __init__(self):
        # Initialisiere Provider Registry
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
        
        # Helper-Klassen initialisieren
        self.phase_manager = SearchPhaseManager()
        self.query_builder = SearchQueryBuilder()
        self.quality_calculator = DataQualityCalculator()
        self.cache_manager = SourceCacheManager()
        self.result_combiner = ResultCombiner()
        self.search_result_combiner = SearchResultCombiner()
        self.async_utils = AsyncSearchUtils()
        self.sources_analyzer = SharedSourcesAnalyzer(self.registry)
        
        # ÄNDERUNG 05.07.2025: Phase-Modelle für Two-Phase Search
        self.phase1_models = self.phase_manager.phase1_models
        self.phase2_models = self.phase_manager.phase2_models
        self.phase3_models = self.phase_manager.phase3_models
    
    def _convert_to_standard_format(self, provider_result: SearchResult,
                                  model_id: str, mine_name: str, 
                                  country: Optional[str] = None) -> Dict[str, Any]:
        """
        Konvertiert Provider-spezifisches Ergebnis in Standard-Format
        
        Args:
            provider_result: Provider-spezifisches Suchergebnis
            model_id: Modell-ID
            mine_name: Mine-Name
            country: Land (optional)
            
        Returns:
            Standardisiertes Suchergebnis
        """
        try:
            # Basis-Struktur erstellen
            result = {
                "success": provider_result.success,
                "model_id": model_id,
                "mine_name": mine_name,
                "country": country,
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }
            
            # Fehlerbehandlung
            if not provider_result.success:
                result["error"] = provider_result.error or "Unbekannter Fehler"
                return result
            
            # Daten konvertieren
            result["data"] = {
                "structured_data": provider_result.structured_data or {},
                "raw_data": provider_result.content or "",
                "sources": provider_result.sources or [],
                "metadata": {
                    "provider": model_id.split(":")[0],
                    "model": model_id.split(":")[1] if ":" in model_id else model_id,
                    "extraction_time": provider_result.search_duration or 0,
                    "confidence": 0.0
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[CORE] Fehler bei Format-Konvertierung: {e}")
            return {
                "success": False,
                "error": f"Format-Konvertierung fehlgeschlagen: {str(e)}",
                "model_id": model_id,
                "mine_name": mine_name,
                "country": country,
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }
    
    async def _track_used_sources(self, result_sources: List[Dict], discovered_sources: List[Dict]):
        """
        Verfolgt welche Quellen verwendet wurden
        
        Args:
            result_sources: Quellen aus dem Ergebnis
            discovered_sources: Entdeckte Quellen
        """
        try:
            if not result_sources:
                return
            
            # URLs aus result_sources extrahieren
            result_urls = set()
            for source in result_sources:
                if isinstance(source, dict):
                    url = source.get('url', '')
                    if url:
                        result_urls.add(url)
            
            # Prüfe welche discovered_sources verwendet wurden
            used_count = 0
            for discovered in discovered_sources:
                discovered_url = discovered.get('url', '')
                if discovered_url in result_urls:
                    used_count += 1
                    # Markiere als erfolgreich verwendet in DB
                    try:
                        with db_manager.get_session() as db_session:
                            db_source = db_session.query(Source).filter_by(url=discovered_url).first()
                            if db_source:
                                db_source.last_successful_access = datetime.now()
                                db_session.commit()
                    except Exception as e:
                        logger.debug(f"[CORE] Fehler beim Markieren der verwendeten Quelle: {e}")
            
            logger.info(f"[CORE] {used_count}/{len(discovered_sources)} entdeckte Quellen wurden verwendet")
            
        except Exception as e:
            logger.error(f"[CORE] Fehler beim Verfolgen verwendeter Quellen: {e}")
    
    async def prepare_search_context(self, mine_name: str, country: Optional[str] = None,
                                   region: Optional[str] = None, commodity: Optional[str] = None) -> Dict[str, Any]:
        """
        Bereitet Suchkontext vor (Source Discovery, Name Variants, etc.)
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            region: Region (optional)
            commodity: Rohstoff (optional)
            
        Returns:
            Suchkontext mit allen relevanten Daten
        """
        try:
            # Starte Source Discovery Session
            session = None
            discovered_sources = []
            
            try:
                session = self.enhanced_discovery.start_session(mine_name, country, region)
                if session:
                    discovered_sources = self.enhanced_discovery.discover_sources_for_mine(
                        mine_name=mine_name, 
                        country=country, 
                        region=region,
                        commodity=commodity
                    )
                    logger.info(f"[CORE] {len(discovered_sources)} Quellen für {mine_name} entdeckt")
                    
                    # Markiere alle discovered sources als "attempted"
                    await self._mark_sources_as_attempted(discovered_sources)
                else:
                    logger.warning("[CORE] Konnte keine Source Discovery Session starten")
            except Exception as e:
                logger.warning(f"[CORE] Fehler bei Source Discovery: {str(e)}")
            
            # Erstelle Name Variants und multilingual terms
            name_variants = generate_name_variants(mine_name)
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)
            
            return {
                'session': session,
                'discovered_sources': discovered_sources,
                'name_variants': name_variants,
                'country_config': country_config,
                'multilingual_terms': multilingual_terms
            }
            
        except Exception as e:
            logger.error(f"[CORE] Fehler beim Vorbereiten des Suchkontexts: {e}")
            return {
                'session': None,
                'discovered_sources': [],
                'name_variants': generate_name_variants(mine_name),
                'country_config': {},
                'multilingual_terms': []
            }
    
    async def _mark_sources_as_attempted(self, discovered_sources: List[Dict]):
        """
        Markiert entdeckte Quellen als 'attempted' in der Datenbank
        
        Args:
            discovered_sources: Liste der entdeckten Quellen
        """
        try:
            marked_count = 0
            for source in discovered_sources:
                try:
                    url = source.get('url', '')
                    if url:
                        parsed = urllib.parse.urlparse(url)
                        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                        
                        with db_manager.get_session() as db_session:
                            # Versuche zuerst mit normalisierter URL
                            db_source = db_session.query(Source).filter_by(url=normalized_url).first()
                            
                            # Fallback: Suche mit Original-URL
                            if not db_source:
                                db_source = db_session.query(Source).filter_by(url=url).first()
                            
                            # Fallback: Suche nach Domain
                            if not db_source and parsed.netloc:
                                db_source = db_session.query(Source).filter_by(domain=parsed.netloc).first()
                            
                            if db_source:
                                db_source.last_attempted_access = datetime.now()
                                db_session.commit()
                                marked_count += 1
                            else:
                                logger.debug(f"[CORE] Quelle nicht in DB gefunden: {url}")
                except Exception as e:
                    logger.debug(f"[CORE] Fehler beim Markieren der Quelle als attempted: {e}")
            
            logger.info(f"[CORE] {marked_count}/{len(discovered_sources)} Quellen als 'attempted' markiert")
            
        except Exception as e:
            logger.error(f"[CORE] Fehler beim Markieren der Quellen: {e}")