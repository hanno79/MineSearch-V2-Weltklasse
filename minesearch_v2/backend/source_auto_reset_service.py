"""
Author: rahn
Datum: 23.07.2025
Version: 1.0
Beschreibung: Auto-Reset Service für schlechte Source-Performance
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from source_stats_manager import source_stats_manager, SourcePerformanceMetrics
from config.base import config

logger = logging.getLogger(__name__)


@dataclass
class ResetOperation:
    """Einzelne Reset-Operation"""
    url: str
    reason: str
    timestamp: datetime
    pre_reset_stats: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'pre_reset_stats': self.pre_reset_stats
        }


class SourceAutoResetService:
    """
    Service für automatisches Zurücksetzen von Quellen mit schlechter Performance
    
    Features:
    - Periodische Prüfung aller Quellen
    - Intelligente Reset-Kriterien
    - Backup der Statistiken vor Reset
    - Comprehensive Logging und Reporting
    """
    
    def __init__(self):
        self.stats_manager = source_stats_manager
        self.reset_history: List[ResetOperation] = []
        self.running = False
        
        # Konfiguration
        self.check_interval_hours = 24  # Täglich prüfen
        self.max_consecutive_failures = 10
        self.min_success_rate_threshold = 0.1  # 10%
        self.stale_days_threshold = 180  # 6 Monate
        self.min_attempts_for_reset = 5
        
        logger.info("[AUTO-RESET] Service initialisiert")
    
    async def start_service(self):
        """Startet den Auto-Reset Service"""
        if self.running:
            logger.warning("[AUTO-RESET] Service läuft bereits")
            return
        
        self.running = True
        logger.info(f"[AUTO-RESET] Service gestartet - Prüfung alle {self.check_interval_hours}h")
        
        while self.running:
            try:
                await self._perform_reset_check()
                
                # Warte bis zur nächsten Prüfung
                await asyncio.sleep(self.check_interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"[AUTO-RESET] Fehler im Service: {e}")
                # Bei Fehler: Warte 1 Stunde und versuche erneut
                await asyncio.sleep(3600)
    
    def stop_service(self):
        """Stoppt den Auto-Reset Service"""
        self.running = False
        logger.info("[AUTO-RESET] Service gestoppt")
    
    async def _perform_reset_check(self):
        """Führt eine vollständige Reset-Prüfung durch"""
        try:
            logger.info("[AUTO-RESET] Starte Reset-Prüfung...")
            
            start_time = datetime.now()
            
            # Identifiziere Reset-Kandidaten
            reset_candidates = await self.stats_manager.get_sources_needing_reset()
            
            if not reset_candidates:
                logger.info("[AUTO-RESET] Keine Quellen für Reset gefunden")
                return
            
            # Kategorisiere Reset-Kandidaten
            categorized = self._categorize_reset_candidates(reset_candidates)
            
            # Protokolliere Kandidaten
            self._log_reset_candidates(categorized)
            
            # Führe Resets durch
            reset_count = 0
            for category, candidates in categorized.items():
                if candidates:
                    category_resets = await self._reset_category(category, candidates)
                    reset_count += category_resets
            
            # Update Performance Summary
            summary = await self.stats_manager.get_performance_summary()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[AUTO-RESET] Reset-Prüfung abgeschlossen: {reset_count} Quellen resettet in {duration:.1f}s")
            
            # Optional: Sende Report per Email/Webhook (falls konfiguriert)
            await self._send_reset_report(reset_count, categorized, summary)
            
        except Exception as e:
            logger.error(f"[AUTO-RESET] Fehler bei Reset-Prüfung: {e}")
    
    def _categorize_reset_candidates(self, candidates: List[SourcePerformanceMetrics]) -> Dict[str, List[SourcePerformanceMetrics]]:
        """Kategorisiert Reset-Kandidaten nach Grund"""
        categories = {
            'high_failure_rate': [],
            'consecutive_failures': [],
            'stale_sources': [],
            'low_quality': [],
            'manual_flagged': []
        }
        
        for candidate in candidates:
            if candidate.consecutive_failures >= self.max_consecutive_failures:
                categories['consecutive_failures'].append(candidate)
            elif candidate.total_attempts >= self.min_attempts_for_reset:
                success_rate = candidate.successful_attempts / candidate.total_attempts
                if success_rate < self.min_success_rate_threshold:
                    categories['high_failure_rate'].append(candidate)
            
            if candidate.last_success and (datetime.now() - candidate.last_success).days > self.stale_days_threshold:
                categories['stale_sources'].append(candidate)
            
            if candidate.quality_score < 20.0 and candidate.total_attempts >= 10:
                categories['low_quality'].append(candidate)
            
            if candidate.needs_reset and candidate.reset_reason:
                categories['manual_flagged'].append(candidate)
        
        return categories
    
    def _log_reset_candidates(self, categorized: Dict[str, List[SourcePerformanceMetrics]]):
        """Protokolliert Reset-Kandidaten detailliert"""
        total_candidates = sum(len(candidates) for candidates in categorized.values())
        
        if total_candidates == 0:
            return
        
        logger.info(f"[AUTO-RESET] {total_candidates} Reset-Kandidaten identifiziert:")
        
        for category, candidates in categorized.items():
            if candidates:
                logger.info(f"  {category}: {len(candidates)} Quellen")
                for candidate in candidates[:3]:  # Zeige nur die ersten 3
                    success_rate = (candidate.successful_attempts / max(candidate.total_attempts, 1)) * 100
                    logger.info(f"    - {candidate.domain}: {success_rate:.1f}% success, "
                              f"{candidate.consecutive_failures} consecutive failures")
                
                if len(candidates) > 3:
                    logger.info(f"    ... und {len(candidates) - 3} weitere")
    
    async def _reset_category(self, category: str, candidates: List[SourcePerformanceMetrics]) -> int:
        """Resettet alle Kandidaten einer Kategorie"""
        if not candidates:
            return 0
        
        logger.info(f"[AUTO-RESET] Resette {len(candidates)} Quellen in Kategorie '{category}'")
        
        urls_to_reset = []
        
        for candidate in candidates:
            # Backup der Statistiken vor Reset
            pre_reset_stats = {
                'total_attempts': candidate.total_attempts,
                'successful_attempts': candidate.successful_attempts,
                'quality_score': candidate.quality_score,
                'reliability_score': candidate.reliability_score,
                'consecutive_failures': candidate.consecutive_failures,
                'last_success': candidate.last_success.isoformat() if candidate.last_success else None,
                'reset_category': category
            }
            
            # Dokumentiere Reset-Operation
            reset_op = ResetOperation(
                url=candidate.url,
                reason=f"Auto-reset: {category} - {candidate.reset_reason or 'Performance criteria met'}",
                timestamp=datetime.now(),
                pre_reset_stats=pre_reset_stats
            )
            self.reset_history.append(reset_op)
            
            urls_to_reset.append(candidate.url)
        
        # Bulk-Reset durchführen
        reset_count = await self.stats_manager.perform_bulk_reset(urls_to_reset)
        
        logger.info(f"[AUTO-RESET] {reset_count} Quellen in Kategorie '{category}' erfolgreich resettet")
        return reset_count
    
    async def _send_reset_report(self, reset_count: int, categorized: Dict[str, List[SourcePerformanceMetrics]], 
                               summary: Dict[str, Any]):
        """Sendet Reset-Report (falls konfiguriert)"""
        try:
            if reset_count == 0:
                return
            
            # Erstelle Report-Daten
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'total_resets': reset_count,
                'categories': {
                    cat: len(candidates) for cat, candidates in categorized.items() if candidates
                },
                'system_performance': {
                    'total_sources': summary.get('source_statistics', {}).get('total_sources', 0),
                    'overall_success_rate': summary.get('source_statistics', {}).get('overall_success_rate', 0),
                    'average_reliability': summary.get('source_statistics', {}).get('average_reliability_score', 0)
                },
                'recent_resets': [op.to_dict() for op in self.reset_history[-10:]]  # Letzte 10 Resets
            }
            
            # TODO: Implementiere Email/Webhook/Slack Benachrichtigung falls gewünscht
            # Für jetzt: Ausführliches Logging
            logger.info(f"[AUTO-RESET] REPORT: {reset_count} Quellen resettet")
            logger.info(f"[AUTO-RESET] System-Performance: {report_data['system_performance']}")
            
        except Exception as e:
            logger.error(f"[AUTO-RESET] Fehler beim Senden des Reports: {e}")
    
    async def manual_reset_source(self, url: str, reason: str) -> bool:
        """
        Manuelles Reset einer einzelnen Quelle
        
        Args:
            url: URL der Quelle
            reason: Grund für das Reset
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # Lade aktuelle Performance-Metriken
            metrics = await self.stats_manager.get_source_performance(url)
            if not metrics:
                logger.warning(f"[AUTO-RESET] Quelle nicht gefunden für manuelles Reset: {url}")
                return False
            
            # Backup der Statistiken
            pre_reset_stats = {
                'total_attempts': metrics.total_attempts,
                'successful_attempts': metrics.successful_attempts,
                'quality_score': metrics.quality_score,
                'reliability_score': metrics.reliability_score,
                'consecutive_failures': metrics.consecutive_failures,
                'manual_reset': True
            }
            
            # Dokumentiere Reset-Operation
            reset_op = ResetOperation(
                url=url,
                reason=f"Manual reset: {reason}",
                timestamp=datetime.now(),
                pre_reset_stats=pre_reset_stats
            )
            self.reset_history.append(reset_op)
            
            # Führe Reset durch
            reset_count = await self.stats_manager.perform_bulk_reset([url])
            
            if reset_count > 0:
                logger.info(f"[AUTO-RESET] Manuelles Reset erfolgreich: {url} - {reason}")
                return True
            else:
                logger.error(f"[AUTO-RESET] Manuelles Reset fehlgeschlagen: {url}")
                return False
                
        except Exception as e:
            logger.error(f"[AUTO-RESET] Fehler beim manuellen Reset: {e}")
            return False
    
    def get_reset_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Holt Reset-Historie
        
        Args:
            limit: Maximale Anzahl Einträge
            
        Returns:
            Liste der Reset-Operationen
        """
        return [op.to_dict() for op in self.reset_history[-limit:]]
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Holt Service-Status
        
        Returns:
            Status-Informationen
        """
        return {
            'running': self.running,
            'check_interval_hours': self.check_interval_hours,
            'total_resets_performed': len(self.reset_history),
            'last_reset': self.reset_history[-1].to_dict() if self.reset_history else None,
            'configuration': {
                'max_consecutive_failures': self.max_consecutive_failures,
                'min_success_rate_threshold': self.min_success_rate_threshold,
                'stale_days_threshold': self.stale_days_threshold,
                'min_attempts_for_reset': self.min_attempts_for_reset
            }
        }


# Global Auto-Reset Service instance
auto_reset_service = SourceAutoResetService()