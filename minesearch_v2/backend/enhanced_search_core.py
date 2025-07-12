"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Core-Funktionen für Enhanced Multi-Provider Search Service
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict

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
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class EnhancedSearchCore:
    """Core-Funktionen für Enhanced Multi-Provider Search Service"""
    
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
        
        # Tracking für Modell-Performance
        self.model_performance = defaultdict(lambda: {
            'total_searches': 0,
            'successful_searches': 0,
            'filled_fields_avg': 0.0,
            'response_time_avg': 0.0,
            'last_used': None
        })
        
        # Spezialisierte Prompts
        self.specialized_prompts = SpecializedPrompts()
    
    def _calculate_simple_quality(self, data: Dict[str, Any]) -> float:
        """
        Berechnet einfache Datenqualität basierend auf gefüllten Feldern
        
        Args:
            data: Strukturierte Daten
            
        Returns:
            Qualitäts-Score zwischen 0 und 1
        """
        if not data:
            return 0.0
        
        # Zähle gefüllte Felder
        filled_fields = 0
        total_fields = len(data)
        
        for value in data.values():
            if value and str(value).strip() and str(value).lower() not in ['n/a', 'unknown', 'keine angabe']:
                filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _convert_to_standard_format(self, provider_result: SearchResult, model_id: str,
                                  mine_name: str, country: Optional[str] = None) -> Dict[str, Any]:
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
            structured_data = provider_result.structured_data or {}
            sources = provider_result.sources or []
            raw_data = provider_result.content or ""
            
            # Qualität berechnen
            quality_score = self._calculate_simple_quality(structured_data)
            
            result["data"] = {
                "structured_data": structured_data,
                "raw_data": raw_data,
                "sources": sources,
                "quality_score": quality_score,
                "metadata": {
                    "provider": model_id.split(":")[0],
                    "model": model_id.split(":")[1] if ":" in model_id else model_id,
                    "extraction_time": provider_result.search_duration or 0,
                    "confidence": quality_score
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[ENHANCED-CORE] Fehler bei Format-Konvertierung: {e}")
            return {
                "success": False,
                "error": f"Format-Konvertierung fehlgeschlagen: {str(e)}",
                "model_id": model_id,
                "mine_name": mine_name,
                "country": country,
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }
    
    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        """
        Formatiert Quellen für Prompt-Einbindung
        
        Args:
            sources: Liste der Quellen
            
        Returns:
            Formatierter String für Prompt
        """
        if not sources:
            return "Keine spezifischen Quellen verfügbar."
        
        formatted_sources = []
        for i, source in enumerate(sources[:10], 1):  # Limitiere auf 10 Quellen
            source_info = f"{i}. "
            
            if source.get('title'):
                source_info += f"Titel: {source['title'][:100]}"
            
            if source.get('url'):
                source_info += f" | URL: {source['url']}"
            
            if source.get('description'):
                source_info += f" | Beschreibung: {source['description'][:150]}"
            
            formatted_sources.append(source_info)
        
        return "\n".join(formatted_sources)
    
    def _deduplicate_and_rank_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Entfernt Duplikate und rankt Quellen nach Qualität
        
        Args:
            sources: Liste der Quellen
            
        Returns:
            Deduplizierte und gerankte Quellenliste
        """
        if not sources:
            return []
        
        # Deduplizierung basierend auf URL
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('url', '').strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        # Ranking-Funktion
        def source_score(source):
            score = 0.0
            
            # Bonus für spezifische Mining-Domains
            url = source.get('url', '').lower()
            mining_domains = ['mining.com', 'miningglobal.com', 'miningweekly.com', 
                            'infomine.com', 'mining-technology.com']
            if any(domain in url for domain in mining_domains):
                score += 2.0
            
            # Bonus für Regierungsseiten
            if any(gov in url for gov in ['.gov', '.gouv', 'government']):
                score += 1.5
            
            # Bonus für Unternehmensseiten
            if any(corp in url for corp in ['corp.', 'company', 'mining']):
                score += 1.0
            
            # Bonus für Titel-Relevanz
            title = source.get('title', '').lower()
            if 'mine' in title or 'mining' in title:
                score += 0.5
            
            # Malus für PDF/Doc (schwerer zu verarbeiten)
            if url.endswith(('.pdf', '.doc', '.docx')):
                score -= 0.5
            
            return score
        
        # Sortiere nach Score (absteigend)
        unique_sources.sort(key=source_score, reverse=True)
        
        return unique_sources
    
    def _get_top_performing_models(self, limit: int = 10) -> List[Dict]:
        """
        Holt die besten Modelle basierend auf Performance-Metriken
        
        Args:
            limit: Maximale Anzahl zurückzugebender Modelle
            
        Returns:
            Liste der besten Modelle mit Performance-Daten
        """
        try:
            # Berechne Performance-Score für jedes Modell
            model_scores = []
            
            for model_id, stats in self.model_performance.items():
                if stats['total_searches'] == 0:
                    continue
                
                success_rate = stats['successful_searches'] / stats['total_searches']
                avg_filled_fields = stats['filled_fields_avg']
                
                # Gewichteter Score: 60% Erfolgsrate, 40% Feldabdeckung
                performance_score = (success_rate * 0.6) + (avg_filled_fields * 0.4)
                
                model_scores.append({
                    'model_id': model_id,
                    'performance_score': performance_score,
                    'success_rate': success_rate,
                    'avg_filled_fields': avg_filled_fields,
                    'total_searches': stats['total_searches'],
                    'last_used': stats['last_used']
                })
            
            # Sortiere nach Performance-Score
            model_scores.sort(key=lambda x: x['performance_score'], reverse=True)
            
            return model_scores[:limit]
            
        except Exception as e:
            logger.error(f"[ENHANCED-CORE] Fehler beim Abrufen der Top-Modelle: {e}")
            return []
    
    async def prepare_search_context(self, mine_name: str, country: Optional[str] = None,
                                   region: Optional[str] = None, commodity: Optional[str] = None) -> Dict[str, Any]:
        """
        Bereitet erweiterten Suchkontext vor
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            region: Region (optional)
            commodity: Rohstoff (optional)
            
        Returns:
            Erweiterter Suchkontext
        """
        try:
            # Basis-Kontext
            name_variants = generate_name_variants(mine_name)
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)
            
            # Enhanced Source Discovery
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
                    logger.info(f"[ENHANCED-CORE] {len(discovered_sources)} Quellen entdeckt")
            except Exception as e:
                logger.warning(f"[ENHANCED-CORE] Source Discovery Fehler: {e}")
            
            # Top performing models
            top_models = self._get_top_performing_models(15)
            
            return {
                'mine_name': mine_name,
                'country': country,
                'region': region,
                'commodity': commodity,
                'name_variants': name_variants,
                'country_config': country_config,
                'multilingual_terms': multilingual_terms,
                'session': session,
                'discovered_sources': discovered_sources,
                'top_models': top_models,
                'search_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[ENHANCED-CORE] Fehler beim Vorbereiten des Suchkontexts: {e}")
            return {
                'mine_name': mine_name,
                'country': country,
                'region': region,
                'commodity': commodity,
                'name_variants': generate_name_variants(mine_name),
                'country_config': {},
                'multilingual_terms': [],
                'session': None,
                'discovered_sources': [],
                'top_models': [],
                'search_timestamp': datetime.now().isoformat()
            }
    
    def update_model_performance(self, model_id: str, success: bool, filled_fields: int = 0, response_time: float = 0.0):
        """
        Aktualisiert Performance-Metriken für ein Modell
        
        Args:
            model_id: Modell-ID
            success: Ob die Suche erfolgreich war
            filled_fields: Anzahl gefüllter Felder
            response_time: Antwortzeit in Sekunden
        """
        try:
            stats = self.model_performance[model_id]
            
            # Aktualisiere Zähler
            stats['total_searches'] += 1
            if success:
                stats['successful_searches'] += 1
            
            # Aktualisiere Durchschnittswerte
            current_count = stats['total_searches']
            
            # Rolling average für gefüllte Felder
            if success and filled_fields > 0:
                stats['filled_fields_avg'] = (
                    (stats['filled_fields_avg'] * (current_count - 1)) + filled_fields
                ) / current_count
            
            # Rolling average für Antwortzeit
            if response_time > 0:
                stats['response_time_avg'] = (
                    (stats['response_time_avg'] * (current_count - 1)) + response_time
                ) / current_count
            
            # Timestamp aktualisieren
            stats['last_used'] = datetime.now().isoformat()
            
            logger.debug(f"[ENHANCED-CORE] Performance aktualisiert für {model_id}: "
                        f"Success: {success}, Fields: {filled_fields}, Time: {response_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[ENHANCED-CORE] Fehler beim Aktualisieren der Performance für {model_id}: {e}")