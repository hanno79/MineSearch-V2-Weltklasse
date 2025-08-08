"""
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: Performance Optimizer für Real-Time Deduplication System - Optimiert für 30-Sekunden Auto-Refresh
"""

import logging
import hashlib
import time
import asyncio
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
import difflib

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Datenklasse für Performance-Metriken"""
    operation_name: str
    start_time: float
    end_time: float = 0.0
    items_processed: int = 0
    memory_usage_mb: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000
    
    @property
    def items_per_second(self) -> float:
        duration = self.end_time - self.start_time
        return self.items_processed / duration if duration > 0 else 0

class FastDeduplicationEngine:
    """
    Hochperformante Deduplizierungs-Engine optimiert für Real-Time Operations
    
    FEATURES:
    - Hash-basierte O(1) Duplikat-Erkennung
    - Synonym-Matching für Mine-Namen und Rohstoffe
    - Memory-effiziente Datenstrukturen
    - LRU-Caching für 30-Sekunden Auto-Refresh
    - Parallel-Processing-Ready
    """
    
    def __init__(self, cache_size: int = 10000, auto_refresh_interval: int = 30):
        self.cache_size = cache_size
        self.auto_refresh_interval = auto_refresh_interval
        
        # High-Performance Caches
        self._url_hash_cache = OrderedDict()
        self._content_hash_cache = OrderedDict()
        self._synonym_cache = OrderedDict()
        self._consolidated_data_cache = OrderedDict()
        
        # Synonym-Matching-System
        self._mine_name_synonyms = self._build_mine_synonyms()
        self._commodity_synonyms = self._build_commodity_synonyms()
        
        # Performance-Tracking
        self._metrics = []
        self._cache_statistics = {
            'url_hits': 0, 'url_misses': 0,
            'content_hits': 0, 'content_misses': 0,
            'synonym_hits': 0, 'synonym_misses': 0,
            'consolidation_hits': 0, 'consolidation_misses': 0
        }
        
        logger.info(f"[FAST-DEDUP] Engine initialisiert mit Cache-Größe: {cache_size}, Auto-Refresh: {auto_refresh_interval}s")
    
    def _build_mine_synonyms(self) -> Dict[str, Set[str]]:
        """Erstellt Synonym-Mapping für Mine-Namen"""
        synonyms = {
            # Quebec-spezifische Mine-Namen
            'eleonore': {'eleonore', 'éléonore', 'eleonore mine', 'éléonore mine'},
            'canadian_malartic': {'canadian malartic', 'malartic', 'canadian malartic mine'},
            'raglan': {'raglan', 'raglan mine', 'mine raglan'},
            'lac_shortt': {'lac shortt', 'shortt', 'lac shortt gold'},
            
            # Allgemeine Mine-Synonyme
            'mine': {'mine', 'mining operation', 'mining site', 'project', 'operation'},
            'pit': {'pit', 'open pit', 'open-pit', 'surface mine'},
            'underground': {'underground', 'underground mine', 'subsurface'},
            
            # Französisch-Englisch Übersetzungen
            'mine_fr': {'mine', 'exploitation minière', 'site minier'},
            'carriere': {'carrière', 'quarry', 'pit'},
        }
        
        # Expandiere zu bidirektionalem Mapping
        expanded = {}
        for key, synonym_set in synonyms.items():
            for synonym in synonym_set:
                expanded[synonym.lower()] = synonym_set
        
        return expanded
    
    def _build_commodity_synonyms(self) -> Dict[str, Set[str]]:
        """Erstellt Synonym-Mapping für Rohstoffe"""
        synonyms = {
            # Metalle
            'gold': {'gold', 'au', 'or', 'aurum'},
            'silver': {'silver', 'ag', 'argent', 'argentum'},
            'copper': {'copper', 'cu', 'cuivre', 'cuprum'},
            'iron': {'iron', 'fe', 'fer', 'ferrum', 'iron ore'},
            'zinc': {'zinc', 'zn', 'zinc ore'},
            'lead': {'lead', 'pb', 'plomb', 'plumbum'},
            'nickel': {'nickel', 'ni'},
            'platinum': {'platinum', 'pt', 'platine'},
            'palladium': {'palladium', 'pd'},
            'uranium': {'uranium', 'u', 'uraninite'},
            
            # Seltene Erden
            'lithium': {'lithium', 'li', 'spodumene', 'lepidolite'},
            'cobalt': {'cobalt', 'co'},
            'tantalum': {'tantalum', 'ta', 'tantalite', 'coltan'},
            'niobium': {'niobium', 'nb', 'columbium'},
            
            # Industriemineralien
            'diamond': {'diamond', 'diamonds', 'diamant', 'kimberlite'},
            'graphite': {'graphite', 'c'},
            'quartz': {'quartz', 'silica', 'silicon dioxide'},
            'feldspar': {'feldspar', 'feldspath'},
            
            # Energierohstoffe
            'coal': {'coal', 'charbon', 'anthracite', 'bituminous'},
            'oil': {'oil', 'petroleum', 'crude oil', 'pétrole'},
            'gas': {'gas', 'natural gas', 'gaz naturel'},
        }
        
        # Expandiere zu bidirektionalem Mapping
        expanded = {}
        for key, synonym_set in synonyms.items():
            for synonym in synonym_set:
                expanded[synonym.lower()] = synonym_set
        
        return expanded
    
    @lru_cache(maxsize=1000)
    def _calculate_fast_hash(self, content: str) -> str:
        """Berechnet schnellen SHA-256 Hash für Content"""
        return hashlib.sha256(content.encode('utf-8', errors='ignore')).hexdigest()[:16]
    
    @lru_cache(maxsize=1000)
    def _normalize_url(self, url: str) -> str:
        """Normalisiert URL für konsistente Deduplizierung"""
        # Entferne Query-Parameter, Fragmente und trailing slashes
        url = url.lower().strip()
        url = re.sub(r'[?#].*$', '', url)  # Remove query params and fragments
        url = url.rstrip('/')
        
        # Normalisiere häufige URL-Varianten
        url = re.sub(r'/(index\.(html?|php)?)$', '', url)
        url = re.sub(r'/+', '/', url)  # Multiple slashes to single
        
        return url
    
    def _manage_cache_size(self, cache: OrderedDict, max_size: int):
        """Verwaltet Cache-Größe mit LRU-Eviction"""
        while len(cache) > max_size:
            cache.popitem(last=False)
    
    async def deduplicate_sources_fast(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hochperformante Quellen-Deduplizierung
        
        OPTIMIERUNGEN:
        - O(1) Hash-basierte Duplikat-Erkennung
        - Parallele Content-Verarbeitung
        - Cache-optimierte URL-Normalisierung
        """
        metrics = PerformanceMetrics("source_deduplication", time.time())
        
        if not sources:
            return []
        
        unique_sources = []
        seen_url_hashes = set()
        seen_content_hashes = set()
        
        for source in sources:
            url = source.get('url', '').strip()
            if not url:
                continue
                
            # URL-Normalisierung mit Cache
            normalized_url = self._normalize_url(url)
            url_hash = self._calculate_fast_hash(normalized_url)
            
            # URL-Duplikat-Check
            if url_hash in seen_url_hashes:
                self._cache_statistics['url_hits'] += 1
                continue
                
            self._cache_statistics['url_misses'] += 1
            seen_url_hashes.add(url_hash)
            
            # Content-Duplikat-Check (optional für tiefere Deduplizierung)
            content = source.get('content', '') or source.get('title', '') or source.get('snippet', '')
            if content:
                content_hash = self._calculate_fast_hash(content[:500])  # Erste 500 Zeichen
                if content_hash in seen_content_hashes:
                    self._cache_statistics['content_hits'] += 1
                    continue
                seen_content_hashes.add(content_hash)
                self._cache_statistics['content_misses'] += 1
            
            # Erweitere Source mit Performance-Metadaten
            enhanced_source = source.copy()
            enhanced_source['_dedup_url_hash'] = url_hash
            enhanced_source['_dedup_content_hash'] = content_hash if content else None
            enhanced_source['_dedup_normalized_url'] = normalized_url
            
            unique_sources.append(enhanced_source)
        
        # Cache-Management
        if len(self._url_hash_cache) > self.cache_size:
            self._manage_cache_size(self._url_hash_cache, self.cache_size)
        
        metrics.end_time = time.time()
        metrics.items_processed = len(sources)
        self._metrics.append(metrics)
        
        logger.debug(f"[FAST-DEDUP] Quellen dedupliziert: {len(sources)} -> {len(unique_sources)} "
                    f"({metrics.duration_ms:.1f}ms, {metrics.items_per_second:.1f} items/s)")
        
        return unique_sources
    
    async def consolidate_structured_data_fast(self, individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimierte Structured Data Konsolidierung mit Synonym-Matching
        
        FEATURES:
        - Intelligente Feld-Konsolidierung
        - Synonym-basiertes Value-Matching
        - Memory-effiziente Aggregation
        - Konfidenz-Score-basierte Priorisierung
        """
        metrics = PerformanceMetrics("data_consolidation", time.time())
        
        # Cache-Key für gesamte Operation
        cache_key = self._calculate_fast_hash(json.dumps(individual_results, sort_keys=True, default=str))
        
        if cache_key in self._consolidated_data_cache:
            self._cache_statistics['consolidation_hits'] += 1
            cached_result = self._consolidated_data_cache[cache_key]
            # Move to end (LRU)
            del self._consolidated_data_cache[cache_key]
            self._consolidated_data_cache[cache_key] = cached_result
            return cached_result
        
        self._cache_statistics['consolidation_misses'] += 1
        
        # Erfolgreiche Ergebnisse extrahieren
        successful_results = {
            k: v for k, v in individual_results.items() 
            if v.get('success') and v.get('data')
        }
        
        if not successful_results:
            empty_result = {'structured_data': {}, 'sources': [], 'model_contributions': {}}
            self._consolidated_data_cache[cache_key] = empty_result
            return empty_result
        
        # Konsolidierungs-Container
        consolidated = {
            'structured_data': {},
            'sources': [],
            'model_contributions': defaultdict(list),
            'field_confidence': {},
            'synonym_matches': {},
            'deduplication_stats': {
                'total_models': len(successful_results),
                'fields_merged': 0,
                'duplicates_found': 0,
                'synonyms_matched': 0
            }
        }
        
        # Alle Quellen sammeln und deduplizieren
        all_sources = []
        for result in successful_results.values():
            sources = result['data'].get('sources', [])
            all_sources.extend(sources)
        
        consolidated['sources'] = await self.deduplicate_sources_fast(all_sources)
        
        # Feld-by-Feld Konsolidierung mit Synonym-Matching
        field_values = defaultdict(list)  # field -> [(value, model_id, confidence)]
        
        for model_id, result in successful_results.items():
            structured_data = result['data'].get('structured_data', {})
            
            for field, value in structured_data.items():
                if value and str(value).strip():
                    # Basis-Konfidenz basierend auf Modell-Performance (vereinfacht)
                    base_confidence = self._get_model_confidence(model_id)
                    
                    # Zusätzliche Konfidenz basierend auf Wert-Qualität
                    value_confidence = self._calculate_value_confidence(field, value)
                    
                    total_confidence = (base_confidence + value_confidence) / 2
                    
                    field_values[field].append((str(value).strip(), model_id, total_confidence))
        
        # Konsolidiere jeden Feld mit Synonym-Matching
        for field, values in field_values.items():
            if not values:
                continue
                
            # Sortiere nach Konfidenz (höchste zuerst)
            values.sort(key=lambda x: x[2], reverse=True)
            
            # Finde beste Werte mit Synonym-Matching
            best_value, best_model, best_confidence = self._find_best_value_with_synonyms(field, values)
            
            if best_value:
                consolidated['structured_data'][field] = best_value
                consolidated['model_contributions'][best_model].append(field)
                consolidated['field_confidence'][field] = best_confidence
                consolidated['deduplication_stats']['fields_merged'] += 1
        
        # Cache-Management
        if len(self._consolidated_data_cache) >= self.cache_size:
            self._manage_cache_size(self._consolidated_data_cache, self.cache_size)
        
        # Speichere im Cache
        self._consolidated_data_cache[cache_key] = consolidated
        
        metrics.end_time = time.time()
        metrics.items_processed = len(successful_results)
        self._metrics.append(metrics)
        
        logger.debug(f"[FAST-DEDUP] Daten konsolidiert: {len(successful_results)} Modelle -> "
                    f"{len(consolidated['structured_data'])} Felder "
                    f"({metrics.duration_ms:.1f}ms)")
        
        return consolidated
    
    def _get_model_confidence(self, model_id: str) -> float:
        """Ermittelt Modell-spezifische Konfidenz basierend auf historischer Performance"""
        # Vereinfachte Modell-Konfidenz (kann später aus Performance-DB geladen werden)
        model_confidence_map = {
            'abacus:deep-agent': 0.95,
            'perplexity:sonar-reasoning-pro': 0.90,
            'perplexity:sonar-pro': 0.85,
            'openrouter:claude-3.5-sonnet': 0.88,
            'openrouter:deepseek-free': 0.75,
            'openrouter:kimi-k2': 0.70,
        }
        
        return model_confidence_map.get(model_id, 0.60)  # Default-Konfidenz
    
    def _calculate_value_confidence(self, field: str, value: str) -> float:
        """Berechnet Konfidenz basierend auf Wert-Qualität"""
        confidence = 0.5  # Basis-Konfidenz
        
        # Längen-basierte Konfidenz
        if len(value) > 100:
            confidence += 0.2
        elif len(value) > 50:
            confidence += 0.1
        elif len(value) < 5:
            confidence -= 0.2
        
        # Numerische Werte
        if field in ['latitude', 'longitude', 'elevation', 'depth']:
            try:
                float(value)
                confidence += 0.3
            except:
                confidence -= 0.1
        
        # Strukturierte Formate
        if field in ['established_date', 'closure_date']:
            if re.match(r'\d{4}-\d{2}-\d{2}', value) or re.match(r'\d{4}', value):
                confidence += 0.2
        
        # Plausibilität
        if 'unknown' in value.lower() or 'n/a' in value.lower() or value.strip() == '-':
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _find_best_value_with_synonyms(self, field: str, values: List[Tuple[str, str, float]]) -> Tuple[Optional[str], Optional[str], float]:
        """
        Findet besten Wert mit Synonym-Matching für bessere Konsolidierung
        """
        if not values:
            return None, None, 0.0
        
        # Für Mine-Namen und Rohstoffe: Synonym-Matching
        if field in ['mine_name', 'project_name', 'property_name']:
            return self._match_mine_synonyms(values)
        elif field in ['commodity', 'primary_commodity', 'commodities']:
            return self._match_commodity_synonyms(values)
        else:
            # Standard: höchste Konfidenz
            best_value, best_model, best_confidence = values[0]
            return best_value, best_model, best_confidence
    
    def _match_mine_synonyms(self, values: List[Tuple[str, str, float]]) -> Tuple[Optional[str], Optional[str], float]:
        """Findet beste Mine-Namen mit Synonym-Matching"""
        if len(values) == 1:
            return values[0]
        
        # Groupiere Synonyme
        synonym_groups = defaultdict(list)
        
        for value, model_id, confidence in values:
            normalized_value = value.lower().strip()
            
            # Finde Synonym-Gruppe
            matched_group = None
            for synonym_key, synonym_set in self._mine_name_synonyms.items():
                if any(synonym in normalized_value for synonym in synonym_set):
                    matched_group = synonym_key
                    break
            
            group_key = matched_group or normalized_value
            synonym_groups[group_key].append((value, model_id, confidence))
        
        # Finde beste Gruppe (höchste kombinierte Konfidenz)
        best_group = None
        best_group_confidence = 0.0
        
        for group_key, group_values in synonym_groups.items():
            group_confidence = sum(conf for _, _, conf in group_values) / len(group_values)
            if group_confidence > best_group_confidence:
                best_group_confidence = group_confidence
                best_group = group_values
        
        if best_group:
            # Innerhalb der besten Gruppe: höchste Einzelkonfidenz
            best_group.sort(key=lambda x: x[2], reverse=True)
            return best_group[0]
        
        return values[0]  # Fallback
    
    def _match_commodity_synonyms(self, values: List[Tuple[str, str, float]]) -> Tuple[Optional[str], Optional[str], float]:
        """Findet beste Rohstoff-Namen mit Synonym-Matching"""
        if len(values) == 1:
            return values[0]
        
        # Ähnlich zu mine_synonyms, aber für Rohstoffe
        synonym_groups = defaultdict(list)
        
        for value, model_id, confidence in values:
            normalized_value = value.lower().strip()
            
            # Finde Synonym-Gruppe
            matched_group = None
            for synonym_key, synonym_set in self._commodity_synonyms.items():
                if normalized_value in synonym_set:
                    matched_group = synonym_key
                    break
            
            group_key = matched_group or normalized_value
            synonym_groups[group_key].append((value, model_id, confidence))
        
        # Finde beste Gruppe
        best_group = None
        best_group_confidence = 0.0
        
        for group_key, group_values in synonym_groups.items():
            # Bevorzuge standardisierte Rohstoff-Namen
            group_confidence = sum(conf for _, _, conf in group_values) / len(group_values)
            
            # Bonus für bekannte Synonym-Gruppen
            if group_key in self._commodity_synonyms:
                group_confidence += 0.1
            
            if group_confidence > best_group_confidence:
                best_group_confidence = group_confidence
                best_group = group_values
        
        if best_group:
            best_group.sort(key=lambda x: x[2], reverse=True)
            return best_group[0]
        
        return values[0]  # Fallback
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Liefert detaillierte Performance-Metriken"""
        if not self._metrics:
            return {'status': 'no_metrics_available'}
        
        # Aggregiere Metriken
        total_operations = len(self._metrics)
        total_duration_ms = sum(m.duration_ms for m in self._metrics)
        total_items = sum(m.items_processed for m in self._metrics)
        
        avg_duration_ms = total_duration_ms / total_operations if total_operations > 0 else 0
        avg_items_per_second = sum(m.items_per_second for m in self._metrics) / total_operations if total_operations > 0 else 0
        
        # Cache-Effizienz
        total_cache_ops = sum(self._cache_statistics.values())
        cache_hit_rate = (
            (self._cache_statistics['url_hits'] + 
             self._cache_statistics['content_hits'] + 
             self._cache_statistics['synonym_hits'] + 
             self._cache_statistics['consolidation_hits']) / total_cache_ops * 100
            if total_cache_ops > 0 else 0
        )
        
        return {
            'operation_summary': {
                'total_operations': total_operations,
                'total_duration_ms': total_duration_ms,
                'total_items_processed': total_items,
                'average_duration_ms': avg_duration_ms,
                'average_items_per_second': avg_items_per_second
            },
            'cache_statistics': self._cache_statistics.copy(),
            'cache_efficiency': {
                'overall_hit_rate_percent': cache_hit_rate,
                'url_cache_size': len(self._url_hash_cache),
                'content_cache_size': len(self._content_hash_cache),
                'synonym_cache_size': len(self._synonym_cache),
                'consolidation_cache_size': len(self._consolidated_data_cache)
            },
            'performance_rating': self._calculate_performance_rating(avg_duration_ms, cache_hit_rate),
            'optimization_recommendations': self._generate_optimization_recommendations(avg_duration_ms, cache_hit_rate)
        }
    
    def _calculate_performance_rating(self, avg_duration_ms: float, cache_hit_rate: float) -> str:
        """Berechnet Performance-Rating basierend auf Metriken"""
        if avg_duration_ms < 10 and cache_hit_rate > 80:
            return "EXCELLENT"
        elif avg_duration_ms < 50 and cache_hit_rate > 60:
            return "GOOD"
        elif avg_duration_ms < 100 and cache_hit_rate > 40:
            return "ACCEPTABLE"
        else:
            return "NEEDS_OPTIMIZATION"
    
    def _generate_optimization_recommendations(self, avg_duration_ms: float, cache_hit_rate: float) -> List[str]:
        """Generiert Optimierungs-Empfehlungen"""
        recommendations = []
        
        if avg_duration_ms > 100:
            recommendations.append("Consider increasing cache size or optimizing hash algorithms")
        
        if cache_hit_rate < 50:
            recommendations.append("Cache hit rate low - review caching strategy")
        
        if len(self._consolidated_data_cache) >= self.cache_size * 0.9:
            recommendations.append("Consolidation cache near capacity - consider increasing size")
        
        if len(self._metrics) > 1000:
            recommendations.append("Metrics collection growing large - implement periodic cleanup")
        
        return recommendations
    
    async def benchmark_performance(self, test_data_size: int = 1000) -> Dict[str, Any]:
        """
        Führt Performance-Benchmark durch
        
        Args:
            test_data_size: Anzahl Test-Datensätze
            
        Returns:
            Benchmark-Ergebnisse
        """
        logger.info(f"[FAST-DEDUP] Starte Performance-Benchmark mit {test_data_size} Test-Datensätzen")
        
        # Generiere Test-Daten
        test_sources = self._generate_test_sources(test_data_size)
        test_results = self._generate_test_results(test_data_size // 10)
        
        benchmark_results = {
            'test_configuration': {
                'test_data_size': test_data_size,
                'cache_size': self.cache_size,
                'auto_refresh_interval': self.auto_refresh_interval
            },
            'benchmark_timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test 1: Source Deduplication
        start_time = time.time()
        deduplicated_sources = await self.deduplicate_sources_fast(test_sources)
        source_dedup_time = (time.time() - start_time) * 1000
        
        benchmark_results['tests']['source_deduplication'] = {
            'input_sources': len(test_sources),
            'output_sources': len(deduplicated_sources),
            'deduplication_ratio': len(deduplicated_sources) / len(test_sources) if test_sources else 0,
            'duration_ms': source_dedup_time,
            'sources_per_second': len(test_sources) / (source_dedup_time / 1000) if source_dedup_time > 0 else 0
        }
        
        # Test 2: Data Consolidation
        start_time = time.time()
        consolidated_data = await self.consolidate_structured_data_fast(test_results)
        consolidation_time = (time.time() - start_time) * 1000
        
        benchmark_results['tests']['data_consolidation'] = {
            'input_results': len(test_results),
            'output_fields': len(consolidated_data.get('structured_data', {})),
            'duration_ms': consolidation_time,
            'results_per_second': len(test_results) / (consolidation_time / 1000) if consolidation_time > 0 else 0
        }
        
        # Test 3: Memory Efficiency
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        benchmark_results['tests']['memory_efficiency'] = {
            'memory_usage_mb': memory_info.rss / 1024 / 1024,
            'cache_memory_estimate_mb': (
                len(self._url_hash_cache) * 0.1 +  # Rough estimate
                len(self._content_hash_cache) * 0.1 +
                len(self._consolidated_data_cache) * 0.5
            ),
            'memory_per_item_kb': (memory_info.rss / 1024) / test_data_size if test_data_size > 0 else 0
        }
        
        # Test 4: Cache Performance
        cache_metrics = self.get_performance_metrics()
        benchmark_results['tests']['cache_performance'] = cache_metrics['cache_efficiency']
        
        # Gesamtbewertung
        overall_performance_score = self._calculate_overall_benchmark_score(benchmark_results)
        benchmark_results['overall_performance_score'] = overall_performance_score
        benchmark_results['performance_grade'] = self._get_performance_grade(overall_performance_score)
        
        logger.info(f"[FAST-DEDUP] Benchmark abgeschlossen: {overall_performance_score:.1f}/100 "
                   f"({benchmark_results['performance_grade']})")
        
        return benchmark_results
    
    def _generate_test_sources(self, count: int) -> List[Dict[str, Any]]:
        """Generiert Test-Quellen für Benchmark"""
        test_sources = []
        base_urls = [
            'https://mining.com/news/mine-report-',
            'https://miningglobal.com/data/project-',
            'https://government.ca/mines/details-',
            'https://company.mining/operations-',
            'https://infomine.com/properties-'
        ]
        
        for i in range(count):
            # Erstelle realistische Duplikate (20% Duplikat-Rate)
            if i % 5 == 0 and i > 0:
                # Dupliziere frühere Quelle mit kleinen Variationen
                base_idx = i - 5
                base_url = test_sources[base_idx]['url']
                url = base_url + '?timestamp=' + str(i)  # Query-Parameter als Variation
            else:
                base_url = base_urls[i % len(base_urls)]
                url = f"{base_url}{i}"
            
            test_sources.append({
                'url': url,
                'title': f'Mine Report {i}',
                'content': f'This is test content for mine {i} with some details...',
                'score': 0.8 + (i % 3) * 0.1
            })
        
        return test_sources
    
    def _generate_test_results(self, count: int) -> Dict[str, Any]:
        """Generiert Test-Ergebnisse für Konsolidierungs-Benchmark"""
        test_results = {}
        
        models = ['abacus:deep-agent', 'perplexity:sonar-pro', 'openrouter:claude-3.5-sonnet']
        mine_names = ['Eleonore Mine', 'Canadian Malartic', 'Raglan Mine']
        commodities = ['Gold', 'Or', 'AU']  # Synonyme für Test
        
        for i, model in enumerate(models):
            test_results[model] = {
                'success': True,
                'data': {
                    'structured_data': {
                        'mine_name': mine_names[i % len(mine_names)],
                        'commodity': commodities[i % len(commodities)],
                        'country': 'Canada',
                        'region': 'Quebec',
                        'latitude': f"{48.0 + i * 0.1}",
                        'longitude': f"{-77.0 - i * 0.1}",
                        f'test_field_{i}': f'unique_value_{i}'
                    },
                    'sources': [
                        {'url': f'https://test-source-{model}-{j}.com', 'title': f'Source {j}'}
                        for j in range(3)
                    ]
                }
            }
        
        return test_results
    
    def _calculate_overall_benchmark_score(self, results: Dict[str, Any]) -> float:
        """Berechnet Gesamt-Performance-Score (0-100)"""
        scores = []
        
        # Source Deduplication Score (0-25 points)
        source_test = results['tests']['source_deduplication']
        if source_test['sources_per_second'] > 1000:
            scores.append(25)
        elif source_test['sources_per_second'] > 500:
            scores.append(20)
        elif source_test['sources_per_second'] > 100:
            scores.append(15)
        else:
            scores.append(10)
        
        # Data Consolidation Score (0-25 points)
        consolidation_test = results['tests']['data_consolidation']
        if consolidation_test['results_per_second'] > 100:
            scores.append(25)
        elif consolidation_test['results_per_second'] > 50:
            scores.append(20)
        elif consolidation_test['results_per_second'] > 20:
            scores.append(15)
        else:
            scores.append(10)
        
        # Memory Efficiency Score (0-25 points)
        memory_test = results['tests']['memory_efficiency']
        if memory_test['memory_per_item_kb'] < 1:
            scores.append(25)
        elif memory_test['memory_per_item_kb'] < 5:
            scores.append(20)
        elif memory_test['memory_per_item_kb'] < 10:
            scores.append(15)
        else:
            scores.append(10)
        
        # Cache Performance Score (0-25 points)
        cache_test = results['tests']['cache_performance']
        hit_rate = cache_test.get('overall_hit_rate_percent', 0)
        if hit_rate > 80:
            scores.append(25)
        elif hit_rate > 60:
            scores.append(20)
        elif hit_rate > 40:
            scores.append(15)
        else:
            scores.append(10)
        
        return sum(scores)
    
    def _get_performance_grade(self, score: float) -> str:
        """Konvertiert numerischen Score zu Leistungsgrad"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"

# Globale Performance Optimizer Instanz
performance_optimizer = FastDeduplicationEngine()