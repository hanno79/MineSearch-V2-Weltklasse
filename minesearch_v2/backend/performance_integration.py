"""
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: Performance Integration Layer - Ersetzt bestehende Deduplizierungs-Methoden mit optimierten Algorithmen
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)

class PerformanceIntegration:
    """
    Integration Layer für Performance-optimierte Deduplication
    
    ZWECK:
    - Drop-in Replacement für bestehende Deduplizierungs-Methoden
    - Nahtlose Integration in existing Batch-Services
    - Backward-Compatibility mit bestehenden APIs
    - Performance-Monitoring und Alerting
    """
    
    def __init__(self):
        self.optimizer = performance_optimizer
        self.integration_stats = {
            'operations_optimized': 0,
            'performance_gains': [],
            'compatibility_issues': 0
        }
        logger.info("[PERF-INTEGRATION] Performance Integration Layer initialisiert")
    
    async def optimize_source_deduplication(self, sources: List[Dict], legacy_method_name: str = None) -> List[Dict]:
        """
        Optimierte Quellen-Deduplizierung als Drop-in Replacement
        
        Args:
            sources: Liste der zu deduplizierenden Quellen
            legacy_method_name: Name der ersetzten Legacy-Methode (für Logging)
            
        Returns:
            Deduplizierte Quellenliste mit Performance-Verbesserungen
        """
        if legacy_method_name:
            logger.debug(f"[PERF-INTEGRATION] Optimiere {legacy_method_name} -> FastDeduplicationEngine")
        
        try:
            # Verwende optimierte Deduplication
            result = await self.optimizer.deduplicate_sources_fast(sources)
            
            # Statistik-Update
            self.integration_stats['operations_optimized'] += 1
            performance_gain = len(sources) - len(result)
            self.integration_stats['performance_gains'].append(performance_gain)
            
            logger.debug(f"[PERF-INTEGRATION] Quellen optimiert: {len(sources)} -> {len(result)} "
                        f"({performance_gain} Duplikate entfernt)")
            
            return result
            
        except Exception as e:
            logger.error(f"[PERF-INTEGRATION] Fehler bei Quellen-Optimierung: {str(e)}")
            self.integration_stats['compatibility_issues'] += 1
            
            # Fallback auf einfache Deduplizierung
            return self._fallback_source_deduplication(sources)
    
    async def optimize_data_consolidation(self, individual_results: Dict[str, Any], 
                                        legacy_method_name: str = None) -> Dict[str, Any]:
        """
        Optimierte Daten-Konsolidierung als Drop-in Replacement
        
        Args:
            individual_results: Individuelle Modell-Ergebnisse
            legacy_method_name: Name der ersetzten Legacy-Methode
            
        Returns:
            Konsolidierte Daten mit Performance-Verbesserungen
        """
        if legacy_method_name:
            logger.debug(f"[PERF-INTEGRATION] Optimiere {legacy_method_name} -> FastConsolidation")
        
        try:
            # Verwende optimierte Konsolidierung
            result = await self.optimizer.consolidate_structured_data_fast(individual_results)
            
            # Statistik-Update
            self.integration_stats['operations_optimized'] += 1
            
            # Erweitere Ergebnis mit Legacy-Kompatibilität
            legacy_compatible_result = self._ensure_legacy_compatibility(result)
            
            logger.debug(f"[PERF-INTEGRATION] Daten konsolidiert: {len(individual_results)} Modelle -> "
                        f"{len(result.get('structured_data', {}))} Felder")
            
            return legacy_compatible_result
            
        except Exception as e:
            logger.error(f"[PERF-INTEGRATION] Fehler bei Daten-Konsolidierung: {str(e)}")
            self.integration_stats['compatibility_issues'] += 1
            
            # Fallback auf Legacy-Konsolidierung
            return self._fallback_data_consolidation(individual_results)
    
    def _ensure_legacy_compatibility(self, optimized_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stellt sicher, dass optimierte Ergebnisse mit Legacy-APIs kompatibel sind
        """
        # Basis-Kompatibilität: stelle sicher, dass erforderliche Keys existieren
        if 'structured_data' not in optimized_result:
            optimized_result['structured_data'] = {}
        
        if 'sources' not in optimized_result:
            optimized_result['sources'] = []
        
        if 'model_contributions' not in optimized_result:
            optimized_result['model_contributions'] = {}
        
        # Legacy-spezifische Felder hinzufügen falls erforderlich
        if 'contributing_models' not in optimized_result:
            optimized_result['contributing_models'] = list(optimized_result.get('model_contributions', {}).keys())
        
        return optimized_result
    
    def _fallback_source_deduplication(self, sources: List[Dict]) -> List[Dict]:
        """Fallback für Quellen-Deduplizierung bei Fehlern"""
        logger.warning("[PERF-INTEGRATION] Verwende Fallback für Quellen-Deduplizierung")
        
        # Einfache URL-basierte Deduplizierung
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('url', '').strip().lower()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _fallback_data_consolidation(self, individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback für Daten-Konsolidierung bei Fehlern"""
        logger.warning("[PERF-INTEGRATION] Verwende Fallback für Daten-Konsolidierung")
        
        # Einfache First-Match Konsolidierung
        combined_structured_data = {}
        combined_sources = []
        model_contributions = {}
        
        successful_results = {
            k: v for k, v in individual_results.items() 
            if v.get('success') and v.get('data')
        }
        
        for model_id, result in successful_results.items():
            structured_data = result['data'].get('structured_data', {})
            sources = result['data'].get('sources', [])
            
            model_contributions[model_id] = []
            
            for field, value in structured_data.items():
                if value and str(value).strip() and not combined_structured_data.get(field):
                    combined_structured_data[field] = value
                    model_contributions[model_id].append(field)
            
            combined_sources.extend(sources)
        
        return {
            'structured_data': combined_structured_data,
            'sources': combined_sources,
            'model_contributions': model_contributions,
            'contributing_models': list(successful_results.keys())
        }
    
    async def performance_health_check(self) -> Dict[str, Any]:
        """
        Überprüft Performance-Gesundheit des Systems
        
        Returns:
            Detaillierte Performance-Gesundheitsbericht
        """
        logger.info("[PERF-INTEGRATION] Führe Performance Health Check durch...")
        
        # Performance-Metriken vom Optimizer holen
        optimizer_metrics = self.optimizer.get_performance_metrics()
        
        # Integration-spezifische Metriken
        avg_performance_gain = (
            sum(self.integration_stats['performance_gains']) / 
            len(self.integration_stats['performance_gains'])
            if self.integration_stats['performance_gains'] else 0
        )
        
        compatibility_rate = (
            (self.integration_stats['operations_optimized'] - 
             self.integration_stats['compatibility_issues']) / 
            max(1, self.integration_stats['operations_optimized']) * 100
        )
        
        # Gesundheitsbewertung
        health_score = self._calculate_health_score(optimizer_metrics, compatibility_rate)
        
        health_report = {
            'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0, "", (), None)) if logger.handlers else "N/A",
            'overall_health_score': health_score,
            'health_status': self._get_health_status(health_score),
            'optimizer_metrics': optimizer_metrics,
            'integration_statistics': {
                'total_operations_optimized': self.integration_stats['operations_optimized'],
                'average_performance_gain': avg_performance_gain,
                'compatibility_rate_percent': compatibility_rate,
                'compatibility_issues': self.integration_stats['compatibility_issues']
            },
            'recommendations': self._generate_health_recommendations(optimizer_metrics, compatibility_rate),
            'system_ready_for_production': health_score > 75 and compatibility_rate > 95
        }
        
        logger.info(f"[PERF-INTEGRATION] Health Check abgeschlossen: {health_report['health_status']} "
                   f"(Score: {health_score}/100)")
        
        return health_report
    
    def _calculate_health_score(self, optimizer_metrics: Dict[str, Any], compatibility_rate: float) -> float:
        """Berechnet Gesamt-Gesundheitsscore"""
        scores = []
        
        # Optimizer Performance (40% Gewichtung)
        if optimizer_metrics.get('status') != 'no_metrics_available':
            perf_rating = optimizer_metrics.get('performance_rating', 'NEEDS_OPTIMIZATION')
            if perf_rating == 'EXCELLENT':
                scores.append(40)
            elif perf_rating == 'GOOD':
                scores.append(32)
            elif perf_rating == 'ACCEPTABLE':
                scores.append(24)
            else:
                scores.append(16)
        else:
            scores.append(20)  # Neutral wenn keine Metriken
        
        # Kompatibilität (30% Gewichtung)
        if compatibility_rate > 95:
            scores.append(30)
        elif compatibility_rate > 90:
            scores.append(24)
        elif compatibility_rate > 80:
            scores.append(18)
        else:
            scores.append(12)
        
        # Cache-Effizienz (20% Gewichtung)
        cache_hit_rate = optimizer_metrics.get('cache_efficiency', {}).get('overall_hit_rate_percent', 0)
        if cache_hit_rate > 80:
            scores.append(20)
        elif cache_hit_rate > 60:
            scores.append(16)
        elif cache_hit_rate > 40:
            scores.append(12)
        else:
            scores.append(8)
        
        # Operations Volume (10% Gewichtung)
        total_ops = self.integration_stats['operations_optimized']
        if total_ops > 100:
            scores.append(10)
        elif total_ops > 50:
            scores.append(8)
        elif total_ops > 10:
            scores.append(6)
        else:
            scores.append(4)
        
        return sum(scores)
    
    def _get_health_status(self, health_score: float) -> str:
        """Konvertiert Health Score zu Status"""
        if health_score >= 90:
            return "EXCELLENT"
        elif health_score >= 75:
            return "GOOD"
        elif health_score >= 60:
            return "ACCEPTABLE"
        elif health_score >= 40:
            return "NEEDS_ATTENTION"
        else:
            return "CRITICAL"
    
    def _generate_health_recommendations(self, optimizer_metrics: Dict[str, Any], 
                                       compatibility_rate: float) -> List[str]:
        """Generiert Gesundheits-Empfehlungen"""
        recommendations = []
        
        if compatibility_rate < 95:
            recommendations.append("Investigate compatibility issues with legacy systems")
        
        if self.integration_stats['operations_optimized'] < 50:
            recommendations.append("Increase usage of performance optimizations")
        
        # Optimizer-spezifische Empfehlungen hinzufügen
        if optimizer_metrics.get('optimization_recommendations'):
            recommendations.extend(optimizer_metrics['optimization_recommendations'])
        
        if not recommendations:
            recommendations.append("System performance is optimal - continue monitoring")
        
        return recommendations

# Monkey-Patch Integration für bestehende Services
async def patch_enhanced_search_operations():
    """Patcht enhanced_search_operations.py für Performance-Optimierung"""
    try:
        from enhanced_search_operations import EnhancedSearchOperations
        
        # Backup der originalen Methode
        if not hasattr(EnhancedSearchOperations, '_original_deduplicate_and_rank_sources'):
            EnhancedSearchOperations._original_deduplicate_and_rank_sources = EnhancedSearchOperations._deduplicate_and_rank_sources
        
        # Ersetze mit optimierter Version
        async def optimized_deduplicate_and_rank_sources(self, sources):
            return await performance_integration.optimize_source_deduplication(
                sources, 
                legacy_method_name="_deduplicate_and_rank_sources"
            )
        
        EnhancedSearchOperations._deduplicate_and_rank_sources = optimized_deduplicate_and_rank_sources
        logger.info("[PERF-INTEGRATION] Enhanced Search Operations erfolgreich gepatcht")
        
    except ImportError:
        logger.warning("[PERF-INTEGRATION] Enhanced Search Operations nicht verfügbar für Patching")
    except Exception as e:
        logger.error(f"[PERF-INTEGRATION] Fehler beim Patching Enhanced Search Operations: {str(e)}")

async def patch_enhanced_multi_model_batch_service():
    """Patcht enhanced_multi_model_batch_service.py für Performance-Optimierung"""
    try:
        from enhanced_multi_model_batch_service import EnhancedMultiModelBatchService
        
        # Backup der originalen Methode
        if not hasattr(EnhancedMultiModelBatchService, '_original_create_combined_data_view'):
            EnhancedMultiModelBatchService._original_create_combined_data_view = EnhancedMultiModelBatchService._create_combined_data_view
        
        # Ersetze mit optimierter Version
        async def optimized_create_combined_data_view(self, individual_results):
            return await performance_integration.optimize_data_consolidation(
                individual_results,
                legacy_method_name="_create_combined_data_view"
            )
        
        EnhancedMultiModelBatchService._create_combined_data_view = optimized_create_combined_data_view
        logger.info("[PERF-INTEGRATION] Enhanced Multi Model Batch Service erfolgreich gepatcht")
        
    except ImportError:
        logger.warning("[PERF-INTEGRATION] Enhanced Multi Model Batch Service nicht verfügbar für Patching")
    except Exception as e:
        logger.error(f"[PERF-INTEGRATION] Fehler beim Patching Enhanced Multi Model Batch Service: {str(e)}")

async def initialize_performance_integration():
    """Initialisiert Performance Integration und patcht bestehende Services"""
    logger.info("[PERF-INTEGRATION] Initialisiere Performance Integration...")
    
    # Patche bestehende Services
    await patch_enhanced_search_operations()
    await patch_enhanced_multi_model_batch_service()
    
    # Führe initialen Health Check durch
    health_report = await performance_integration.performance_health_check()
    
    logger.info(f"[PERF-INTEGRATION] Initialization complete - Health: {health_report['health_status']}")
    
    return health_report

# Globale Integration-Instanz
performance_integration = PerformanceIntegration()

# Auto-Initialization wenn Modul importiert wird
async def _auto_init():
    """Auto-Initialisierung für nahtlose Integration"""
    try:
        await initialize_performance_integration()
    except Exception as e:
        logger.error(f"[PERF-INTEGRATION] Auto-Initialization fehlgeschlagen: {str(e)}")

# Starte Auto-Initialization (falls Event Loop verfügbar)
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Verwende task scheduling für laufende Event Loop
        asyncio.create_task(_auto_init())
    else:
        loop.run_until_complete(_auto_init())
except RuntimeError:
    # Keine Event Loop verfügbar - Integration wird beim ersten Import durchgeführt
    logger.info("[PERF-INTEGRATION] Integration wird beim ersten Service-Import durchgeführt")