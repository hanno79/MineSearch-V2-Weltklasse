"""
Author: rahn
Datum: 07.07.2025  
Version: 2.0
Beschreibung: Enhanced Multi-Provider Search Service mit zweistufiger Quellensuche
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


class EnhancedMultiProviderSearchService:
    """Enhanced Service für Multi-Provider Mining-Suchen mit zweistufigem Prozess"""
    
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
        
        # ÄNDERUNG 07.07.2025: Tracking für Modell-Performance
        self.model_performance = defaultdict(lambda: {
            'sources_found': 0,
            'fields_found': 0,
            'calls': 0,
            'success_rate': 0.0
        })
    
    async def collect_sources_all_models(self, mine_name: str, country: Optional[str] = None,
                                        commodity: Optional[str] = None, region: Optional[str] = None) -> List[Dict]:
        """
        NEUE METHODE: Phase 1 - Sammle Quellen von ALLEN verfügbaren Modellen
        
        Returns:
            Liste von deduplizierten und gerankten Quellen
        """
        logger.info(f"[PHASE 1] Starte umfassende Quellensammlung für {mine_name}")
        
        # Hole ALLE verfügbaren Modelle
        all_models = list(self.registry.get_all_models().keys())
        logger.info(f"[PHASE 1] Nutze {len(all_models)} Modelle für Quellensuche")
        
        # Generiere Quellen-fokussierte Queries
        name_variants = generate_name_variants(mine_name)
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)
        
        # Spezieller Quellen-Discovery-Prompt
        source_query = f"""QUELLENSUCHE für {mine_name} Mine
        
ZIEL: Finde ALLE verfügbaren Quellen und Dokumente zu dieser Mine.

PRIORITÄT:
1. Offizielle Unternehmensseiten und Berichte
2. Behördendokumente (SEDAR, SEC, ASX, etc.)
3. Technische Berichte (NI 43-101, JORC)
4. Umweltberichte und Genehmigungen
5. Nachrichtenartikel und Analysen
6. Mining-Datenbanken und Portale

AUSGABE: Liste ALLE gefundenen URLs, Dokumente und Organisationen auf."""
        
        # Erstelle Tasks für alle Modelle
        tasks = []
        for model_id in all_models:
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'currency': country_config.get('currency', 'USD'),
                'name_variants': name_variants,
                'multilingual_terms': multilingual_terms,
                'skip_data_extraction': True,  # Nur Quellen sammeln
                'focus': 'sources_only'
            }
            
            # Task mit Timeout
            task = asyncio.create_task(
                self._search_model_with_timeout(
                    model_id, source_query, options, timeout=30
                )
            )
            tasks.append((model_id, task))
        
        # Führe alle Tasks parallel aus
        all_sources = []
        model_source_counts = {}
        
        for model_id, task in tasks:
            try:
                result = await task
                if result and result.get('success') and result.get('sources'):
                    sources = result['sources']
                    all_sources.extend(sources)
                    model_source_counts[model_id] = len(sources)
                    
                    # Update Performance-Tracking
                    self.model_performance[model_id]['sources_found'] += len(sources)
                    self.model_performance[model_id]['calls'] += 1
                    self.model_performance[model_id]['success_rate'] = (
                        self.model_performance[model_id]['sources_found'] / 
                        self.model_performance[model_id]['calls']
                    )
                    
                    logger.info(f"[PHASE 1] {model_id}: {len(sources)} Quellen gefunden")
            except Exception as e:
                logger.error(f"[PHASE 1] Fehler bei {model_id}: {str(e)}")
        
        # Dedupliziere und ranke Quellen
        unique_sources = self._deduplicate_and_rank_sources(all_sources)
        
        logger.info(f"[PHASE 1] Gesamt: {len(all_sources)} Quellen → {len(unique_sources)} unique")
        logger.info(f"[PHASE 1] Top-Sammler: {sorted(model_source_counts.items(), key=lambda x: x[1], reverse=True)[:5]}")
        
        return unique_sources
    
    async def extract_data_from_sources(self, sources: List[Dict], mine_name: str,
                                      country: Optional[str] = None, commodity: Optional[str] = None,
                                      region: Optional[str] = None) -> Dict[str, Any]:
        """
        NEUE METHODE: Phase 2 - Jedes Modell analysiert ALLE gesammelten Quellen
        
        Returns:
            Kombinierte und validierte Ergebnisse aller Modelle
        """
        logger.info(f"[PHASE 2] Starte Datenextraktion aus {len(sources)} Quellen")
        
        if not sources:
            return {
                'success': False,
                'error': 'Keine Quellen für Analyse verfügbar',
                'data': {},
                'confidence_scores': {}
            }
        
        # Hole alle verfügbaren Modelle
        all_models = list(self.registry.get_all_models().keys())
        
        # Generiere spezialisierte Prompts für verschiedene Datentypen
        prompts = self._generate_specialized_prompts(mine_name, country, region, commodity, sources)
        
        # Matrix: Modelle × Prompts × Quellen
        extraction_tasks = []
        
        for model_id in all_models:
            for prompt_type, prompt_content in prompts.items():
                # Erstelle spezialisierten Extraktions-Task
                task = asyncio.create_task(
                    self._extract_with_model_and_prompt(
                        model_id, prompt_type, prompt_content, 
                        mine_name, country, region, commodity, sources
                    )
                )
                extraction_tasks.append((model_id, prompt_type, task))
        
        # Führe alle Extraktions-Tasks parallel aus
        extraction_results = defaultdict(lambda: defaultdict(dict))
        
        for model_id, prompt_type, task in extraction_tasks:
            try:
                result = await task
                if result and result.get('success') and result.get('data'):
                    extraction_results[model_id][prompt_type] = result['data']
                    
                    # Update Performance-Tracking
                    fields_found = len([v for v in result['data'].values() if v])
                    self.model_performance[model_id]['fields_found'] += fields_found
                    
                    logger.debug(f"[PHASE 2] {model_id}/{prompt_type}: {fields_found} Felder extrahiert")
            except Exception as e:
                logger.error(f"[PHASE 2] Fehler bei {model_id}/{prompt_type}: {str(e)}")
        
        # Kombiniere und validiere alle Ergebnisse
        combined_result = self._combine_and_validate_results(extraction_results, sources)
        
        logger.info(f"[PHASE 2] Extraktion abgeschlossen. {len(combined_result['data'])} Felder gefüllt")
        
        return combined_result
    
    async def search_comprehensive(self, mine_name: str, country: Optional[str] = None,
                                 commodity: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Hauptmethode: Führt umfassende zweistufige Suche durch
        
        1. Sammle Quellen von ALLEN Modellen
        2. Analysiere alle Quellen mit ALLEN Modellen
        3. Kombiniere und validiere Ergebnisse
        """
        start_time = datetime.now()
        logger.info(f"[COMPREHENSIVE] Starte umfassende Suche für {mine_name}")
        
        # Phase 1: Quellensammlung
        sources = await self.collect_sources_all_models(mine_name, country, commodity, region)
        
        # Speichere Quellen in Discovery-Datenbank
        if sources and self.enhanced_discovery:
            session = self.enhanced_discovery.start_session(mine_name, country, region)
            for source in sources:
                self.enhanced_discovery.track_source_result(
                    url=source.get('url', source.get('value', '')),
                    success=True,
                    content_type=source.get('type', 'general'),
                    found_data={'phase': 'source_collection'}
                )
            self.enhanced_discovery.finalize_session()
        
        # Phase 2: Datenextraktion
        result = await self.extract_data_from_sources(sources, mine_name, country, commodity, region)
        
        # Füge Metadaten hinzu
        result['metadata'] = {
            'search_duration': (datetime.now() - start_time).total_seconds(),
            'sources_collected': len(sources),
            'models_used': len(self.registry.get_all_models()),
            'top_performing_models': self._get_top_performing_models(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Füge Quellendetails hinzu
        result['sources'] = sources[:50]  # Top 50 Quellen
        
        logger.info(f"[COMPREHENSIVE] Suche abgeschlossen in {result['metadata']['search_duration']:.1f}s")
        
        return result
    
    def _generate_specialized_prompts(self, mine_name: str, country: str, 
                                    region: str, commodity: str, sources: List[Dict]) -> Dict[str, str]:
        """Generiert spezialisierte Prompts für verschiedene Datentypen"""
        
        # Quellen-Text für alle Prompts
        sources_text = self._format_sources_for_prompt(sources[:30])  # Top 30 Quellen
        
        prompts = {
            'financial': f"""FINANZDATEN-EXTRAKTION für {mine_name}

Analysiere die folgenden Quellen und extrahiere ALLE finanziellen Daten:
- Restaurationskosten / ARO / Closure Costs (mit Jahr und Währung)
- Marktkapitalisierung
- Jahresumsatz
- Investitionssumme
- EBITDA / Cashflow
- Reservenwert

{sources_text}

Gib konkrete Zahlen mit Währung und Jahr an.""",

            'technical': f"""TECHNISCHE DATEN-EXTRAKTION für {mine_name}

Analysiere die folgenden Quellen und extrahiere:
- GPS-Koordinaten (Latitude, Longitude)
- Minentyp (Open-Pit, Underground, etc.)
- Fläche in km²
- Tiefe / Ausdehnung
- Verarbeitungskapazität
- Infrastruktur

{sources_text}

Fokus auf präzise technische Angaben.""",

            'operational': f"""BETRIEBSDATEN-EXTRAKTION für {mine_name}

Analysiere die folgenden Quellen und extrahiere:
- Eigentümer (mit Prozentanteilen)
- Betreiber / Operator
- Status (aktiv, geschlossen, geplant)
- Mitarbeiterzahl
- Gewerkschaften
- Sicherheitsstatistiken

{sources_text}

Aktuelle Informationen sind wichtig.""",

            'production': f"""PRODUKTIONSDATEN-EXTRAKTION für {mine_name}

Analysiere die folgenden Quellen und extrahiere:
- Jahresproduktion (nach Rohstoff)
- Produktionsstart
- Produktionsende / Lebensdauer
- Reserven und Ressourcen
- Erzgehalt / Grade
- Recovery Rate

{sources_text}

Mit Einheiten und Zeitangaben.""",

            'comprehensive': SpecializedPrompts.get_enhanced_query(
                mine_name, country, region, commodity,
                focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
            ) + f"\n\nQUELLEN:\n{sources_text}"
        }
        
        return prompts
    
    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        """Formatiert Quellen für Prompt-Einbindung"""
        sources_text = ""
        for i, source in enumerate(sources, 1):
            url = source.get('url', source.get('value', ''))
            title = source.get('title', '')
            src_type = source.get('type', 'web')
            
            if title:
                sources_text += f"[{i}] {url} - {title} ({src_type})\n"
            else:
                sources_text += f"[{i}] {url} ({src_type})\n"
        
        return sources_text
    
    async def _search_model_with_timeout(self, model_id: str, query: str, 
                                       options: Dict, timeout: int = 30) -> Dict[str, Any]:
        """Führt Suche mit Timeout durch"""
        try:
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {'success': False, 'error': f'Provider für {model_id} nicht gefunden'}
            
            provider_name, model_key = model_id.split(':')
            
            # Erstelle Task mit Timeout
            search_task = provider.search(query, model_key, options)
            result = await asyncio.wait_for(search_task, timeout=timeout)
            
            # Konvertiere zu Standard-Format
            return self._convert_to_standard_format(
                result, model_id, 
                options.get('mine_name', ''),
                options.get('country')
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] {model_id} überschritt {timeout}s Timeout")
            return {'success': False, 'error': f'Timeout nach {timeout}s'}
        except Exception as e:
            logger.error(f"[ERROR] {model_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _extract_with_model_and_prompt(self, model_id: str, prompt_type: str,
                                           prompt_content: str, mine_name: str,
                                           country: str, region: str, commodity: str,
                                           sources: List[Dict]) -> Dict[str, Any]:
        """Extrahiert Daten mit spezifischem Modell und Prompt"""
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'prompt_type': prompt_type,
            'discovered_sources': sources,
            'phase': 'data_extraction'
        }
        
        return await self._search_model_with_timeout(
            model_id, prompt_content, options, 
            timeout=60  # Längeres Timeout für Extraktion
        )
    
    def _deduplicate_and_rank_sources(self, sources: List[Dict]) -> List[Dict]:
        """Dedupliziert und rankt Quellen nach Qualität"""
        # URL-basierte Deduplizierung
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('url', source.get('value', ''))
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        # Ranking nach Qualitätskriterien
        def source_score(source):
            score = 0
            url = source.get('url', source.get('value', '')).lower()
            
            # Tier 1: Offizielle Quellen (+100)
            tier1_domains = ['sedar.com', 'sec.gov', 'asx.com', '.gov', 'agnicoeagle.com']
            if any(domain in url for domain in tier1_domains):
                score += 100
            
            # Tier 2: Fachmedien (+50)
            tier2_domains = ['mining.com', 'reuters.com', 'bloomberg.com']
            if any(domain in url for domain in tier2_domains):
                score += 50
            
            # Dokumenttypen
            if source.get('type') == 'document':
                score += 30
            if 'ni 43-101' in url or 'technical report' in url:
                score += 50
            if 'annual report' in url or 'financial' in url:
                score += 40
            
            # Aktualität (wenn Datum verfügbar)
            if source.get('date'):
                try:
                    date = datetime.fromisoformat(source['date'])
                    age_days = (datetime.now() - date).days
                    if age_days < 365:
                        score += 20
                    elif age_days < 730:
                        score += 10
                except:
                    pass
            
            return score
        
        # Sortiere nach Score
        unique_sources.sort(key=source_score, reverse=True)
        
        return unique_sources
    
    def _combine_and_validate_results(self, extraction_results: Dict[str, Dict[str, Dict]], 
                                     sources: List[Dict]) -> Dict[str, Any]:
        """Kombiniert und validiert Ergebnisse aller Modelle"""
        combined_data = {}
        field_confidence = defaultdict(lambda: {'values': [], 'sources': []})
        
        # Sammle alle Werte pro Feld
        for model_id, prompt_results in extraction_results.items():
            for prompt_type, data in prompt_results.items():
                for field, value in data.items():
                    if value and str(value).strip():
                        field_confidence[field]['values'].append({
                            'value': value,
                            'model': model_id,
                            'prompt_type': prompt_type
                        })
        
        # Wähle beste Werte basierend auf Häufigkeit und Modell-Performance
        for field, info in field_confidence.items():
            if not info['values']:
                continue
            
            # Zähle Vorkommen jedes Werts
            value_counts = defaultdict(list)
            for item in info['values']:
                value_str = str(item['value']).strip()
                value_counts[value_str].append(item)
            
            # Wähle häufigsten Wert oder den von bestem Modell
            if value_counts:
                # Sortiere nach Häufigkeit
                sorted_values = sorted(value_counts.items(), key=lambda x: len(x[1]), reverse=True)
                best_value = sorted_values[0][0]
                confidence = len(sorted_values[0][1]) / len(info['values'])
                
                combined_data[field] = best_value
                field_confidence[field]['confidence'] = confidence
                field_confidence[field]['agreement_count'] = len(sorted_values[0][1])
                field_confidence[field]['total_findings'] = len(info['values'])
        
        # Berechne Gesamt-Konfidenz
        total_confidence = 0
        if field_confidence:
            total_confidence = sum(f['confidence'] for f in field_confidence.values()) / len(field_confidence)
        
        return {
            'success': True,
            'data': combined_data,
            'confidence_scores': {
                field: {
                    'confidence': info['confidence'],
                    'agreement': f"{info['agreement_count']}/{info['total_findings']}",
                    'value': combined_data.get(field)
                }
                for field, info in field_confidence.items()
                if 'confidence' in info
            },
            'overall_confidence': total_confidence,
            'total_fields_found': len(combined_data),
            'high_confidence_fields': len([f for f in field_confidence.values() if f.get('confidence', 0) > 0.7])
        }
    
    def _get_top_performing_models(self, limit: int = 10) -> List[Dict]:
        """Gibt die Top-performenden Modelle zurück"""
        performance_list = []
        
        for model_id, stats in self.model_performance.items():
            if stats['calls'] > 0:
                avg_sources = stats['sources_found'] / stats['calls']
                avg_fields = stats['fields_found'] / stats['calls']
                
                performance_list.append({
                    'model': model_id,
                    'avg_sources_per_call': round(avg_sources, 1),
                    'avg_fields_per_call': round(avg_fields, 1),
                    'total_calls': stats['calls'],
                    'success_rate': round(stats['success_rate'], 2)
                })
        
        # Sortiere nach durchschnittlichen Feldern
        performance_list.sort(key=lambda x: x['avg_fields_per_call'], reverse=True)
        
        return performance_list[:limit]
    
    def _convert_to_standard_format(self, provider_result: SearchResult, model_id: str,
                                   mine_name: str, country: Optional[str] = None) -> Dict[str, Any]:
        """Konvertiert Provider-Result in Standard-Format"""
        if isinstance(provider_result, SearchResult):
            # Berechne Datenqualität - Fallback wenn Methode nicht existiert
            data_quality = {}
            if hasattr(self.quality_calculator, 'calculate_quality'):
                data_quality = self.quality_calculator.calculate_quality(
                    provider_result.structured_data,
                    provider_result.sources
                )
            else:
                # Einfache Qualitätsberechnung als Fallback
                filled_fields = len([v for v in (provider_result.structured_data or {}).values() if v])
                data_quality = {
                    'field_coverage': filled_fields,
                    'source_count': len(provider_result.sources or [])
                }
            
            return {
                "success": provider_result.success,
                "error": provider_result.error,
                "status": "completed" if provider_result.success else "error",
                "data": provider_result.structured_data or {},
                "sources": provider_result.sources or [],
                "metadata": {
                    "model": model_id,
                    "provider": provider_result.metadata.get('provider', model_id.split(':')[0]) if provider_result.metadata else model_id.split(':')[0],
                    "search_timestamp": datetime.now().isoformat(),
                    "search_duration": provider_result.search_duration or 0,
                    "data_quality": data_quality
                }
            }
        else:
            # Fallback für nicht-standard Results
            return {
                "success": False,
                "error": "Invalid result format",
                "status": "error",
                "data": {},
                "sources": [],
                "metadata": {
                    "model": model_id,
                    "search_timestamp": datetime.now().isoformat()
                }
            }